# Phase 149O.20L.7O.3R — Deterministic Mock/Dry Runtime Adapter Implementation Plan

**Phase ID:** `149O.20L.7O.3R`
**Type:** implementation planning only
**Status:** COMPLETE
**Completeness:** complete for the bounded planning scope
**Phase-entry commit:** `7318230feb619b161c08caa2d5256a5d2a41edf6`
**Public baseline:** `v0.4.3` at
`63580893b1de4782a694ab802ff7bdebdf29b0e6` — unchanged
**Contract baseline:** **RPAC-001 v1.0 — FROZEN**
**Production source modified:** NO
**Implementation started:** NO
**Execution activated:** NO

## 1. Objective

Plan the smallest implementation-ready and independently verifiable
deterministic mock/dry runtime-adapter vertical slice that exercises RPAC-001's
provider-neutral control-plane boundary without a subprocess, network, model,
provider, credential, or runtime-caused repository mutation.

The planned slice is deliberately not a miniature real runtime. It proves:

```text
authoritative fixture context
  -> lightweight PromptArtifact
  -> immutable InvocationRequest with explicit runtime target
  -> separately supplied simulation approval evidence
  -> descriptor/status/capability preflight
  -> existing Permission Broker simulation evaluation
  -> non-authorizing Runtime Enforcement test double
  -> durable simulation record
  -> exact mock adapter lookup
  -> in-process deterministic simulation
  -> normalized RuntimeInvocationResult
  -> producer-neutral intake-candidate mapping
```

It never claims production `APPROVED`, `PERMITTED`, `AUTHORIZED`,
`DISPATCHED`, or `COMPLETED` states. Canonical execution remains unavailable.

## 2. Baseline

| Check | Phase-entry truth |
|---|---|
| Worktree | clean before governed startup |
| Branch | `main...origin/main` |
| `origin/main..HEAD` | 0 commits |
| `HEAD` / `origin/main` | `7318230feb619b161c08caa2d5256a5d2a41edf6` |
| `v0.4.3^{commit}` | `63580893b1de4782a694ab802ff7bdebdf29b0e6` |
| `pcae health` | healthy; idle placeholder; agent lock available |
| `pcae check` | passed |
| `pcae status coherence` | coherent |
| `pcae doctor task-memory` | established historical `tasks/DONE.md` warnings only |
| `pcae push check` | nothing to push; 0 unpushed commits |
| `pcae runtime inspect` | `not_implemented` / `Observed` / `observe` / `unavailable`; 0 plugins, 0 capabilities |
| `pcae notify status` | configured, enabled, ready |
| latest phase report | 3Q complete; 3R recommended; no active governed phase |

The idle task was transitioned to the strict 3R planning task and the
`codex-local` agent lock was acquired. That lock remains descriptive session
identity only.

## 3. RPAC-001 summary

The complete frozen contract and complete 3Q phase document were re-read.
RPAC-001 defines PCAE as the trusted authority-owning kernel and a
`RuntimeAdapter` as a replaceable transport/result normalizer. Agent,
producer, adapter, runtime target, provider, model, principal, invocation, and
attempt identities remain distinct. Selection is explicit with no fallback.
Capability, permission, authorization, and execution are independent.

The current Runtime Registry is the one canonical declarative-catalog
foundation, but its existing Plugin Model is metadata/introspection-only.
Permission Broker can safely evaluate simulations but cannot authorize
execution. Runtime Enforcement is evidence-only and non-authorizing. Generic
intake is the producer-neutral return path. A persistent append-only invocation
record is required before a real adapter and is valuable enough to prove in
mock-v1.

## 4. RPAC requirement classification

Classification rule:

- **MOCK-V1-MANDATORY:** implemented and directly tested in the first slice;
- **REAL-RUNTIME-PREREQUISITE:** deliberately absent from mock-v1 but blocking
  before a process/API runtime;
- **DEFERRED-EXTENSION:** compatible optional evolution, not required for the
  first slice or first real boundary;
- **PURE-INVARIANT:** permanent authority/security rule enforced by structure,
  validation, or static tests rather than a standalone feature.

Counts: **52 MOCK-V1-MANDATORY**, **16 REAL-RUNTIME-PREREQUISITE**,
**8 DEFERRED-EXTENSION**, and **21 PURE-INVARIANT**; total **97**.

For every mandatory row below, `Implementation` identifies the planned module
and symbol and states the fail-closed behavior. Test names are seams, not files;
Section 48 maps them to files.

### Matrix A — RPAC coverage

| RPAC Req | Classification | Implementation | Test | Deferred reason |
|---|---|---|---|---|
| RPAC-REQ-001 | PURE-INVARIANT | `runtime_adapter.py` protocol excludes authority operations; reject adapter authority fields | `test_adapter_surface_has_no_authority_methods` | Permanent boundary |
| RPAC-REQ-002 | MOCK-V1-MANDATORY | `runtime_adapter.py::simulate_invocation`; stop on the first failed simulated gate | `test_mock_vertical_slice_order` | — |
| RPAC-REQ-003 | PURE-INVARIANT | Adapter protocol and AST guard contain no approval/PB/RE/intake/promotion APIs | `test_mock_adapter_cannot_govern` | Permanent boundary |
| RPAC-REQ-004 | PURE-INVARIANT | Provider-neutral common types; no mock/provider name in result-to-intake schema | `test_common_types_are_provider_neutral` | Permanent portability invariant |
| RPAC-REQ-005 | PURE-INVARIANT | `simulation_only` and `execution_effect=none` are non-overridable in mock factory | `test_conformance_does_not_authorize` | Separate activation always required |
| RPAC-REQ-006 | MOCK-V1-MANDATORY | `runtime_invocation.py` identity value fields remain separate; reject missing required identities | `test_identity_layers_are_distinct` | — |
| RPAC-REQ-007 | MOCK-V1-MANDATORY | Request/result validators never derive target/provider/model/producer from agent | `test_agent_target_provider_producer_non_equivalence` | — |
| RPAC-REQ-008 | MOCK-V1-MANDATORY | No identity map in resolver; explicit `codex-ox` + `mock-dry.no-change.v1` accepted | `test_codex_ox_does_not_imply_runtime` | — |
| RPAC-REQ-009 | DEFERRED-EXTENSION | No agent-to-target suggestion mechanism in mock-v1 | `test_no_agent_name_fallback` | Suggestions/UI are unnecessary for explicit test selection |
| RPAC-REQ-010 | MOCK-V1-MANDATORY | Optional provider/model snapshots serialize as `null`; never inferred | `test_mock_provider_model_are_absent` | — |
| RPAC-REQ-011 | MOCK-V1-MANDATORY | `runtime_registry.py::RuntimeDescriptor`; invalid/mutable/effectful descriptor rejected | `test_mock_descriptor_exact_fields` | — |
| RPAC-REQ-012 | PURE-INVARIANT | Descriptor closed field set excludes status, secrets, and governance | `test_descriptor_contains_no_live_or_authority_fields` | Permanent separation |
| RPAC-REQ-013 | MOCK-V1-MANDATORY | `runtime_adapter.py::RuntimeTargetConfiguration` mock projection; missing ID/digest/fixture fails `no_adapter_configured` | `test_mock_target_configuration` | Real command/endpoint/profile fields deferred within the type |
| RPAC-REQ-014 | REAL-RUNTIME-PREREQUISITE | No credential field or resolver in mock-v1 | `test_mock_surface_has_no_credential_value_or_ref` | Credential-reference contract required only for authenticated targets |
| RPAC-REQ-015 | MOCK-V1-MANDATORY | `runtime_adapter.py::RuntimeStatus`; fixed clock; separate simulation availability and real availability | `test_mock_status_separates_simulation_from_execution` | — |
| RPAC-REQ-016 | PURE-INVARIANT | Status type has no approval/permission/authorization/dispatch fields | `test_status_is_fact_only` | Permanent separation |
| RPAC-REQ-017 | MOCK-V1-MANDATORY | Status/preflight vocabulary represents registered/installed/configured/auth-not-required/simulation-available/capable separately | `test_capability_terms_do_not_collapse` | Real authentication/availability probes deferred |
| RPAC-REQ-018 | PURE-INVARIANT | No derived transition between capability, PB, simulated enforcement, or effects | `test_no_state_implication` | Permanent semantic invariant |
| RPAC-REQ-019 | MOCK-V1-MANDATORY | `validate_request_against_target` matches simulation capability, result format, no-effect profile, and platform; otherwise `unsupported_capability` | `test_exact_mock_capability_match` | — |
| RPAC-REQ-020 | MOCK-V1-MANDATORY | `runtime_invocation.py::PromptArtifact`; raw strings rejected by request constructor | `test_request_requires_prompt_artifact` | — |
| RPAC-REQ-021 | MOCK-V1-MANDATORY | `build_prompt_artifact` binds content digest, repo/task/phase, generator, provenance, edits, fixed clock | `test_prompt_artifact_binding_and_digest` | — |
| RPAC-REQ-022 | MOCK-V1-MANDATORY | `SimulationApprovalEvidence` is separate from prompt/request and exact-scope-bound; mismatch stops before adapter | `test_simulated_approval_exact_binding` | Production human approval artifact is a real-runtime prerequisite |
| RPAC-REQ-023 | MOCK-V1-MANDATORY | Approval-binding validator invalidates prompt/target/repo/task/effect change | `test_binding_change_invalidates_simulated_approval` | — |
| RPAC-REQ-024 | PURE-INVARIANT | Mock path has no copy/paste-to-machine approval inference | `test_manual_prompt_delivery_not_machine_approval` | Production approval remains separate |
| RPAC-REQ-025 | MOCK-V1-MANDATORY | `InvocationRequest` mock projection includes IDs, bindings, explicit target/digests, prompt/approval refs, simulation capability/result, no-effect profiles, finite timeout | `test_minimal_request_closed_shape` | Provider/auth/cost details remain explicit null/zero |
| RPAC-REQ-026 | MOCK-V1-MANDATORY | `build_invocation_request` accepts trusted authority snapshot; adapter receives immutable request and cannot rewrite it | `test_adapter_cannot_rebind_request` | — |
| RPAC-REQ-027 | MOCK-V1-MANDATORY | Factory fixes network/write/outside access/process/paid budget to denied/zero; nonzero values fail `unsupported_capability` | `test_mock_effects_default_deny` | — |
| RPAC-REQ-028 | REAL-RUNTIME-PREREQUISITE | Mock provider/model remain absent | `test_mock_does_not_switch_provider_or_model` | Dispatch-time provider/model mismatch needs a real configured target |
| RPAC-REQ-029 | MOCK-V1-MANDATORY | `SimulationDispatchEnvelope` contains request/status/approval/PB/test-double/record digests, expiry, `simulation_only=true`; inconsistency fails `integrity_failure` | `test_simulation_envelope_complete` | — |
| RPAC-REQ-030 | MOCK-V1-MANDATORY | `validate_dispatch_envelope` rejects missing/expired/version/digest drift before adapter | `test_adapter_rejects_invalid_envelope` | — |
| RPAC-REQ-031 | MOCK-V1-MANDATORY | `runtime_adapter.py::RuntimeAdapter` Protocol exposes exactly describe/preflight/dispatch/collect/cancel | `test_adapter_protocol_operation_set` | — |
| RPAC-REQ-032 | MOCK-V1-MANDATORY | Mock methods are in-process and state-bounded; invalid sequence fails `invalid_request` or `malformed_result` | `test_adapter_operation_semantics` | — |
| RPAC-REQ-033 | DEFERRED-EXTENSION | Terminal result only; no event/stream API | `test_no_streaming_surface` | Streaming has no mock-v1 value |
| RPAC-REQ-034 | PURE-INVARIANT | Coordinator owns record/gates/intake; adapter module owns fixture normalization only | `test_kernel_adapter_responsibility_split` | Process/API mechanics await real adapters |
| RPAC-REQ-035 | MOCK-V1-MANDATORY | `RuntimeInvocationResult` mock projection carries exact IDs/digests, simulation observations, bounded payload, effects/provenance/errors | `test_normalized_result_shape` | Real transport/provider fields remain null |
| RPAC-REQ-036 | PURE-INVARIANT | Result type has no accepted-change/promotion/task-success flag | `test_result_completion_is_not_governance_success` | Permanent invariant |
| RPAC-REQ-037 | PURE-INVARIANT | Result marked `untrusted=true`; candidate mapping does not accept/ingest | `test_result_remains_untrusted` | Redaction expansion required before real output |
| RPAC-REQ-038 | DEFERRED-EXTENSION | No opaque provider attachment in mock-v1 | `test_mock_has_no_provider_attachment` | Needed only when a provider has extra bounded data |
| RPAC-REQ-039 | MOCK-V1-MANDATORY | `SimulationStateObservation` uses `SIM_*` states aligned to conceptual order | `test_simulation_state_order` | — |
| RPAC-REQ-040 | MOCK-V1-MANDATORY | Store appends immutable chained observations and explicit `not_observed` markers; conflict is `integrity_failure` | `test_state_log_append_only` | — |
| RPAC-REQ-041 | MOCK-V1-MANDATORY | Mock descriptor/result/envelope require simulation namespace; production state enum never written | `test_mock_never_emits_production_runtime_states` | — |
| RPAC-REQ-042 | MOCK-V1-MANDATORY | Coordinator implements the simulation analogue in frozen order; missing evidence stops | `test_gate_order_and_short_circuit` | Real positive gates remain prerequisites |
| RPAC-REQ-043 | MOCK-V1-MANDATORY | Every pre-dispatch validation failure leaves adapter call counter zero | `test_failed_gate_never_calls_adapter` | — |
| RPAC-REQ-044 | REAL-RUNTIME-PREREQUISITE | Existing PB request remains unchanged; mock only translates to its simulation vocabulary | `test_pb_simulation_is_under_bound_and_non_authorizing` | RPAC-rich PB request amendment required before real dispatch |
| RPAC-REQ-045 | REAL-RUNTIME-PREREQUISITE | Existing Runtime Enforcement not invoked as authority | `test_existing_re_not_treated_as_authorizer` | Production positive pre-dispatch consumer does not exist |
| RPAC-REQ-046 | REAL-RUNTIME-PREREQUISITE | Test double checks bound digests only and labels output non-authorizing | `test_simulated_enforcement_is_not_authorization` | Full fresh production evidence evaluation required |
| RPAC-REQ-047 | REAL-RUNTIME-PREREQUISITE | No process boundary in mock-v1 | `test_mock_has_no_shell_gate_dependency` | Whether/how split matters on first local process |
| RPAC-REQ-048 | REAL-RUNTIME-PREREQUISITE | No argv/shell implementation in mock-v1 | `test_no_command_construction_surface` | Enforcing process policy required before local CLI |
| RPAC-REQ-049 | PURE-INVARIANT | No HATP import or evidence field in common mock contract | `test_runtime_adapter_has_no_hatp_dependency` | Permanent generic-boundary rule |
| RPAC-REQ-050 | MOCK-V1-MANDATORY | Extend the existing `RuntimeRegistry` with adapter-descriptor metadata; resolver composes with it | `test_one_catalog_composed_resolver` | — |
| RPAC-REQ-051 | PURE-INVARIANT | Existing `PluginDescriptor` remains inert; callable resolver is explicit and separate | `test_plugin_model_stays_metadata_only` | Permanent until separately amended |
| RPAC-REQ-052 | MOCK-V1-MANDATORY | Adapter descriptor admission rejects duplicates/digest drift/unknown major | `test_adapter_registration_fail_closed` | — |
| RPAC-REQ-053 | MOCK-V1-MANDATORY | `resolve_exact(runtime_target_id)` requires matching configured target and adapter/digests; unknown target is `no_adapter_configured` | `test_explicit_lookup_no_fallback` | — |
| RPAC-REQ-054 | DEFERRED-EXTENSION | Trusted built-in mock factory only; no entry points/import scanning | `test_no_ambient_adapter_discovery` | External admission is unnecessary for first slice |
| RPAC-REQ-055 | MOCK-V1-MANDATORY | Mock descriptor declares `effect=none`, `simulation_only=true`, `simulation.dry_dispatch`; legacy plugin counts/capabilities and real availability unchanged | `test_mock_registration_is_non_capability` | — |
| RPAC-REQ-056 | DEFERRED-EXTENSION | No CLI change in first implementation; Section 37 specifies additive later view | Existing runtime-inspect regression suite | Public exposure waits for independent core verification |
| RPAC-REQ-057 | REAL-RUNTIME-PREREQUISITE | No executable/argv/process profile in mock-v1 | Static absence tests | Required before generic executable/local CLI |
| RPAC-REQ-058 | REAL-RUNTIME-PREREQUISITE | No environment or secret injection in mock-v1 | `test_mock_reads_no_environment` | Sanitized child environment and secret resolver required |
| RPAC-REQ-059 | REAL-RUNTIME-PREREQUISITE | No endpoint/API/client in mock-v1 | Static absence tests | Required before API provider |
| RPAC-REQ-060 | DEFERRED-EXTENSION | No streaming; terminal result only | `test_terminal_result_only` | Add only with provider evidence |
| RPAC-REQ-061 | MOCK-V1-MANDATORY | Request fixes all filesystem scopes false; store writes only its `.pcae` root; adapter writes nothing | `test_only_controlled_record_store_changes` | — |
| RPAC-REQ-062 | MOCK-V1-MANDATORY | Request carries PCAE-supplied repo-relative cwd `.`; adapter output has no cwd field; absolute/escape rejected | `test_mock_cwd_is_repository_bound` | Realpath enforcement before local process |
| RPAC-REQ-063 | PURE-INVARIANT | Common types use `pathlib`/POSIX-relative logical paths and injected clocks; no signal/platform branch | macOS/Linux CI plus AST test | Permanent core portability rule |
| RPAC-REQ-064 | MOCK-V1-MANDATORY | `new_invocation_id` and `new_attempt_id` use kernel-created UUID4; format validation fails `invalid_request` | `test_invocation_and_attempt_identity` | — |
| RPAC-REQ-065 | MOCK-V1-MANDATORY | `compute_idempotency_key` hashes canonical semantic request excluding time/attempt observations | `test_idempotency_key_stability` | — |
| RPAC-REQ-066 | MOCK-V1-MANDATORY | Store resumes identical ID/content without adapter call; conflict fails `integrity_failure` | `test_same_id_replay_and_collision` | — |
| RPAC-REQ-067 | MOCK-V1-MANDATORY | `RuntimeInvocationStore` create-only request plus chained immutable event/result files under `.pcae/runtime-invocations/mock-v1` | `test_persistent_record_integrity` | — |
| RPAC-REQ-068 | MOCK-V1-MANDATORY | Reducer resumes pre-intent; a persisted simulation intent without terminal result becomes `simulation_ambiguous` and never redispatches | `test_restart_boundaries` | Real ambiguous-effect reconciliation remains prerequisite |
| RPAC-REQ-069 | MOCK-V1-MANDATORY | Same result digest is replay; conflicting result is quarantined `integrity_failure` | `test_duplicate_completion_semantics` | — |
| RPAC-REQ-070 | MOCK-V1-MANDATORY | `build_intake_handoff` derives candidate ID from invocation/attempt/result digest | `test_intake_candidate_identity_is_stable` | — |
| RPAC-REQ-071 | REAL-RUNTIME-PREREQUISITE | Mock has no automatic retry engine | `test_no_automatic_retry` | Delivery-aware retry classes need real transport observations |
| RPAC-REQ-072 | REAL-RUNTIME-PREREQUISITE | Record reserves retry lineage; no retry API in mock-v1 | `test_retry_lineage_defaults_empty` | Fresh gates/attempt authority implemented before real retry |
| RPAC-REQ-073 | MOCK-V1-MANDATORY | Closed `RuntimeFailureCategory` supports mock subset: no adapter, unsupported, invalid request subcode, runtime failure, malformed result, ingestion failure | `test_mock_failure_mapping` | Auth/network/timeout categories stay representable but unexercised |
| RPAC-REQ-074 | DEFERRED-EXTENSION | Reserve subcode field; mock tests `integrity_failure` and `simulation_ambiguous` | `test_additive_subcode_round_trip` | Broader transport mappings wait for adapters |
| RPAC-REQ-075 | PURE-INVARIANT | Result `retryable_hint` is descriptive; no coordinator branch consumes it | `test_retryable_hint_cannot_retry` | Permanent authority invariant |
| RPAC-REQ-076 | MOCK-V1-MANDATORY | Record captures requester, simulated approver/gates, prompt/binding, target/adapter, observations, result and handoff disposition; missing facts explicit | `test_mock_audit_reconstruction` | Real principal/provider facts absent by design |
| RPAC-REQ-077 | PURE-INVARIANT | Reuse SHA-256/canonical JSON/intake patterns; do not import legacy backend stores | `test_no_legacy_backend_store_dependency` | Permanent single-authority rule |
| RPAC-REQ-078 | MOCK-V1-MANDATORY | `AuthoritySnapshot` is supplied by trusted coordinator, derived in E2E fixture from task/session/repository identity; request/runtime claims cannot override | `test_runtime_claim_cannot_change_authority` | Live HEAD adapter deferred with bootstrap wiring |
| RPAC-REQ-079 | MOCK-V1-MANDATORY | `ProducerProvenance` records agent, producer=`pcae.mock-dry-fixture`, target, adapter, null provider/model/principal, result digest | `test_mock_producer_chain` | — |
| RPAC-REQ-080 | MOCK-V1-MANDATORY | `intake.py::build_intake_candidate_from_changes` maps in-memory normalized changes to existing schema; no provider branch; failures `result_ingestion_failure` | `test_result_to_generic_intake_candidate` | Submission/acceptance deferred |
| RPAC-REQ-081 | MOCK-V1-MANDATORY | No-change fixture returns explicit `not_applicable_no_changes`, not a fabricated candidate | `test_text_only_result_creates_no_candidate` | — |
| RPAC-REQ-082 | PURE-INVARIANT | Closed immutable request/envelope and adapter AST guard prevent authority/scope changes | `test_adapter_cannot_broaden_or_authorize` | Permanent security invariant |
| RPAC-REQ-083 | PURE-INVARIANT | Result and candidate carry evidence-only flags; no intake/promotion/task-success call | `test_runtime_result_is_untrusted_evidence` | Permanent lifecycle invariant |
| RPAC-REQ-084 | REAL-RUNTIME-PREREQUISITE | Mock types reject credential-like fields and adapter never reads secrets | `test_no_credential_surface_or_read` | General secret reference/resolver remains missing |
| RPAC-REQ-085 | PURE-INVARIANT | Effect profile is explicit default-deny and mock permits only all-none/zero | `test_independent_effect_denials` | Permanent least-privilege invariant |
| RPAC-REQ-086 | REAL-RUNTIME-PREREQUISITE | Mock descriptor has a pinned built-in digest and is immutable | `test_mock_descriptor_digest_immutable` | General adapter admission/supply-chain verification required |
| RPAC-REQ-087 | MOCK-V1-MANDATORY | Store appends simulation dispatch intent before adapter call; envelope is one attempt, no effect | `test_record_precedes_mock_dispatch` | — |
| RPAC-REQ-088 | MOCK-V1-MANDATORY | `mock_runtime_adapter.py::MockDryRuntimeAdapter` built-in factory | `test_mock_adapter_is_builtin_deterministic` | — |
| RPAC-REQ-089 | MOCK-V1-MANDATORY | Full planned integration covers registry, request, bindings, simulated gates/states, receipt/result, unsupported cancel, failures, replay, intake mapping | `test_mock_vertical_slice_complete` | — |
| RPAC-REQ-090 | MOCK-V1-MANDATORY | `mock_runtime_adapter.py` uses fixed fixtures/isolated imports; adapter has no filesystem write; controlled store only | `test_mock_zero_effect_static_and_dynamic` | — |
| RPAC-REQ-091 | MOCK-V1-MANDATORY | Simulation evidence uses `would_allow`/`SIM_*`, never production ALLOW/authorization/runtime states; inspect constants stay unavailable | `test_simulation_never_claims_real_execution` | — |
| RPAC-REQ-092 | PURE-INVARIANT | Existing plugin registry fields and runtime constants remain unchanged; mock built-in is not auto-registered in CLI | existing runtime regression suites | Permanent compatibility invariant |
| RPAC-REQ-093 | DEFERRED-EXTENSION | No RPAC revision in implementation; extension decoder reserved | contract-version tests | Evolution only when requirements change |
| RPAC-REQ-094 | MOCK-V1-MANDATORY | Validators accept RPAC 1.x understood fields, reject unknown major/unknown effect-authority field | `test_contract_version_fail_closed` | Unknown optional preservation limited to explicit extension map |
| RPAC-REQ-095 | REAL-RUNTIME-PREREQUISITE | No process adapter in mock-v1 | planning assertion only | Next process-bound step after mock verification |
| RPAC-REQ-096 | PURE-INVARIANT | 3S task scope and static guard forbid real adapter/provider/effect/policy/trust changes | `test_mock_scope_no_go` | Permanent until separately authorized |
| RPAC-REQ-097 | REAL-RUNTIME-PREREQUISITE | Mock path imports no legacy invocation path | `test_no_legacy_dispatch_import` | Legacy retirement/routing required before real activation |

## 5. Existing-code reuse

| Existing source | Reuse decision | Reason / limit |
|---|---|---|
| `core/runtime_registry.py` | Extend | One canonical metadata catalog, uniqueness, lookup, empty-state precedent; retain inert Plugin Model |
| `core/runtime_introspection.py` | Reuse unchanged in first slice | Static `Observed`/`observe`/`unavailable` truth must remain authoritative |
| `core/runtime_snapshot.py` | Reuse unchanged in first slice | Current canonical read model remains stable; later additive adapter view only |
| `commands/runtime_inspect.py` | Reuse unchanged in first slice | Avoid public semantics before independent verification |
| `core/repository_identity.py` | Reuse read-only identity validation | Repository instance identity is non-authoritative but stable binding input |
| `core/tasks.py::find_latest_active_task` | Reuse in later live authority builder | Canonical active task; mock E2E uses a test-owned fixture with the same type |
| `core/session.py::read_session_snapshot` | Reuse in later live authority builder | Session observation only; not authorization |
| `core/context.py::build_bootstrap_prompt` | Reuse as prompt-content function | The E2E builds a deterministic `ContextPack` fixture and does not invoke live git-reading helpers |
| `core/permission_broker_foundation.py` | Reuse `PermissionBroker.evaluate` only with `simulation_only=true` | A policy simulation, never permission or authorization; no policy change |
| Runtime Enforcement models in `backend_invocations.py` | Do not directly reuse | They are legacy, design-only, under-bound, non-authorizing, and too broad for the RPAC mock seam |
| `core/intake.py` | Reuse contract, validator, hashes, and provenance semantics | Add one generic in-memory-change candidate builder; do not submit automatically |
| `core/backend_preflight.py` | Do not wire | Backend-name/bootstrap validation is not runtime-target preflight |
| legacy `InvocationRequest`/`PromptArtifact`/adapter models | Historical patterns only | Mutable, backend-coupled, under-bound, and not RPAC-conformant |
| existing canonical JSON/digest idioms | Reuse locally | `json.dumps(sort_keys=True,separators=(",",":"))` + SHA-256; no new dependency |
| repository-local atomic-write idioms | Reuse locally | Create-only immutable records plus fsync/atomic placement; no mutable `latest` authority |

No current shared persistence helper meets append-only invocation semantics.
The new store therefore owns a small local create-only writer rather than
promoting a legacy backend store into authority.

## 6. Proposed production footprint

Five production files are sufficient. Three are new and two are narrow
extensions. No command, schema resource, build, version, or frozen-contract
file is needed.

1. `runtime_registry.py`: adapter descriptor metadata in the existing catalog.
2. `runtime_adapter.py`: target/status/interface/resolver/coordinator seams.
3. `runtime_invocation.py`: prompt/request/envelope/result/state/digest/store.
4. `mock_runtime_adapter.py`: deterministic fixed-fixture implementation.
5. `intake.py`: producer-neutral in-memory change-to-candidate builder.

`runtime_snapshot.py` and `runtime_inspect.py` remain unchanged in the first
implementation. That is an intentional public-surface hold, not an omitted
design.

## 7. Mock-v1 scope

Mock-v1 includes:

- trusted built-in descriptor and explicit test registration;
- explicit `runtime_target_id`, with no agent-name lookup;
- immutable minimal target, status, PromptArtifact, approval fixture, request,
  envelope, receipt, result, and record models;
- fact-only preflight and exact capability/effect/result matching;
- actual existing PB evaluation in simulation mode;
- a separately injected non-authorizing enforcement test double;
- append-only mock record persistence;
- an in-process fixed-fixture adapter with terminal collection and unsupported
  cancellation;
- deterministic no-change, synthetic-change, and simulated-failure fixtures;
- pure mapping of a change result to existing generic intake candidate shape;
- unit, integration, restart, security, identity, and independent E2E tests.

It excludes a public CLI, live bootstrap wiring, real human-approval workflow,
positive Runtime Enforcement, real intake submission, retry orchestration,
streaming, secrets, environment injection, process/API transport, and runtime
activation.

## 8. Non-capability invariant

The existing registry's plugin metadata and new adapter-descriptor metadata
are separate views inside the same catalog:

```text
registered plugin count                    = 0
registered legacy plugin capability count  = 0
registered adapter descriptor count        = 1 (inside an explicit test catalog)
adapter simulation capability              = simulation.dry_dispatch
adapter execution effect                   = none
real execution availability                = unavailable
maximum real capability                    = observe
```

Mock registration is explicit in the internal factory/test composition. The
current CLI continues constructing an empty catalog, so its public 0/0 output
does not change in 3S. A later inspect view may display a mock descriptor, but
must never feed that descriptor into `HealthInfo.execution_availability` or
`CURRENT_MAXIMUM_PLUGIN_CAPABILITY`.

## 9. Registry

`RuntimeRegistry` gains a second metadata collection, not a second registry:

```text
register_adapter_descriptor(descriptor) -> AdapterRegistrationResult
list_adapter_descriptors() -> tuple[RuntimeDescriptor, ...]
get_adapter_descriptor(adapter_id) -> RuntimeDescriptor | None
adapter_catalog_snapshot() -> AdapterCatalogSnapshot
```

Existing plugin methods and `RegistrySnapshot` remain byte-semantically
compatible. Adapter IDs are unique within the adapter namespace. The trusted
`RuntimeAdapterResolver` holds the callable instance separately and requires
the catalog descriptor digest to match. Unknown target, unknown adapter,
duplicate ID, resolver/catalog mismatch, and digest drift fail closed. There
is no candidate ranking or fallback.

The planned built-in adapter ID is `pcae.mock-dry`; test target IDs are
`mock-dry.no-change.v1`, `mock-dry.synthetic-change.v1`, and
`mock-dry.failure.v1`. Fixture selection belongs to explicit target config,
never prompt text or agent identity.

## 10. Descriptor

Minimum `RuntimeDescriptor` fields:

| Field | Mock-v1 value |
|---|---|
| `contract_version` | `RPAC-001/1.0` |
| `adapter_id` | `pcae.mock-dry` |
| `implementation_version` | explicit built-in version |
| `implementation_digest` | stable digest of descriptor identity inputs |
| `adapter_class` | `mock_dry` |
| `transport_kind` | `in_process_fixture` |
| `supported_capabilities` | `simulation.dry_dispatch` |
| `supported_result_formats` | `rpac.terminal-result.v1` |
| `execution_effect` | `none` |
| `locality` | `in_process` |
| `network_required` | `false` |
| `supported_platforms` | `platform_independent` |
| `cancellation_mode` | `unsupported` |
| `simulation_only` | `true` |

The descriptor is frozen, closed, canonical-JSON serializable, and contains no
status, credentials, gate decisions, or task fields.

## 11. Status

`RuntimeStatus` is separately constructed with an injected clock. Mock-v1
fields are: descriptor/target identity, registered, built-in installed,
configured, authentication=`not_required`, simulation readiness, health,
observed simulation capabilities, real-execution-available=`false`, source,
and observed-at.

The word `available` is not used alone in the mock-facing rendering. Tests
assert `simulation_ready=true` and `real_execution_available=false`. Status is
fact evidence only.

## 12. Invocation request

The mock-v1 `InvocationRequest` contains only contract-relevant fields:

- contract, invocation, attempt, and idempotency identities;
- authoritative repository instance/fingerprint, base commit, active task and
  task-contract digest, optional phase/session;
- descriptive requester agent;
- explicit target, expected adapter, descriptor digest, config digest;
- optional provider/model fields fixed to absent;
- PromptArtifact ID/digest and separate simulation-approval reference/digest;
- `simulation.dry_dispatch` and terminal RPAC result format;
- repo-relative cwd policy `.`;
- closed effect profile: no process, network, repository write, temp write, or
  outside-repo access;
- finite logical timeout, cancellation not required, and zero paid budget.

It does not contain PB decision, Runtime Enforcement decision, permission,
authorization, executable path, endpoint, credential reference, raw
environment, or arbitrary extension fields affecting authority/effects.

## 13. Invocation authority

Request construction consumes an immutable `AuthoritySnapshot` supplied to
the trusted coordinator. Its constructor is not exported from adapter code.
The adapter receives the resulting request but has no method to alter it.

Unknown fields named `permission`, `authorized`, `pb_allow`,
`execution_allowed`, or equivalent fail closed during strict decoding rather
than being ignored. Separate gate evidence is accepted only by the envelope
builder. A request can therefore describe what is requested but cannot assert
that the request may proceed.

## 14. Prompt input

Use a lightweight immutable `PromptArtifact`, not a raw prompt and not the
legacy heavy Phase-45 model. The builder accepts existing bootstrap prompt
content plus generator metadata, binds repository/task/phase, hashes UTF-8
content with SHA-256, records human-edit status, and uses an injected clock.

Prompt content is inline in mock-v1 because it is small and avoids a second
artifact store. The request carries the artifact plus its digest. A later
minor-compatible extension can replace content with an immutable reference.

## 15. Bootstrap integration decision

Choose **Option B: adapter/request primitives first**.

3S will test `build_bootstrap_prompt` output as input by constructing a
deterministic `ContextPack` fixture in process. It will not connect
`pcae session bootstrap` to dispatch, add a command, or read live git state.
After independent verification, a separate phase may build a live authority
snapshot and an explicit dry-invocation command. This preserves isolation and
keeps manual bootstrap handoff unchanged.

## 16. Invocation identity

The trusted kernel creates UUID4 `invocation_id` and UUID4 `attempt_id` values.
UUID4 is sufficient as opaque identity; repository/task binding belongs in the
canonical request and idempotency digest, not in a guessable ID.

`idempotency_key` is SHA-256 over a version-tagged canonical request projection
including repository/task/base, prompt digest, target/config, exact no-effect
scope, approval scope, result format, and zero budget. It excludes clocks,
attempt ID, and mutable observations. The external adapter cannot supply any
of these identities.

## 17. Invocation result

Minimum `RuntimeInvocationResult` fields:

- RPAC version and invocation/attempt/idempotency identities;
- exact target, adapter, descriptor/config digests;
- provider/model explicitly absent;
- `simulation_only=true`, `execution_effect=none`, and ordered `SIM_*`
  observations;
- terminal outcome and fixed bounded structured payload;
- empty stdout/stderr/process/provider/principal fields;
- normalized changed-file tuple and optional synthetic patch/content data;
- deterministic payload digest and full result digest;
- descriptive producer chain;
- all observed process/network/filesystem effects false;
- common error category/subcode and retry hint; and
- optional PCAE-added intake handoff reference.

The result has no accepted-change, promotion, task-complete, or authorization
field.

## 18. Determinism

For identical normalized semantic request inputs and target fixture, these are
identical:

- preflight fact payload;
- simulation receipt payload;
- terminal structured content;
- change manifest/content;
- error category/subcode;
- producer claim;
- deterministic payload digest; and
- generic intake candidate content/candidate ID for the same invocation,
  attempt, and result digest.

Invocation/attempt IDs and injected timestamps are envelope metadata and may
differ between new logical requests. Tests use fixed IDs and a fixed clock
when comparing complete records. Host absolute paths, environment values,
unordered mappings, random fixture output, and wall-clock reads inside the
adapter are forbidden.

## 19. Mock result

The default `no-change-v1` fixture returns:

```json
{
  "fixture": "no-change-v1",
  "message": "PCAE deterministic dry simulation completed",
  "proposed_change_count": 0
}
```

The `synthetic-change-v1` test target returns one fixed in-memory create
proposal for `mock-output.txt` with fixed content and digest. It never writes
the file. The test task explicitly allows that path. The `failure-v1` target
returns a fixed `runtime_failure` simulation. Malformed-result behavior is
tested with a dedicated fake adapter, not a hidden prompt-triggered mode.

## 20. Generic intake boundary

Choose **Stage B**.

Mock-v1 converts a normalized synthetic change result into the existing
producer-neutral intake candidate shape through a new generic
`build_intake_candidate_from_changes` helper. It does not call
`validate_and_ingest_intake_candidate`, write an ECP, or automatically accept
anything. The no-change fixture returns an explicit
`not_applicable_no_changes` handoff.

Stage B is the smallest useful slice: it proves schema compatibility and
deterministic candidate identity without expanding the phase into intake
lifecycle automation. Stage C follows only after independent mock verification.

## 21. Producer provenance

Mock provenance is:

```text
requesting_agent = opaque session identity (for example codex-ox)
producer_claim    = pcae.mock-dry-fixture
runtime_target    = explicit mock-dry.* target
adapter           = pcae.mock-dry
provider/model    = absent
principal         = absent
result_digest     = observed result digest
```

The producer does not impersonate Codex, Claude, OpenRouter, or the requester.
No provenance field is authority-bearing.

## 22. Repository/task binding

The coordinator accepts a trusted `AuthoritySnapshot` containing validated
repository identity/fingerprint, base commit, active `TaskContract` identity
and digest, and optional phase/session identity. Mock unit/integration tests
construct this snapshot from controlled PCAE repository fixtures, not adapter
or result data.

A live builder is deferred with bootstrap wiring because existing generic
intake HEAD/fingerprint helpers invoke `git` subprocesses, which would violate
the independent mock E2E's zero-process proof. The mock-v1 public surface is
internal/test-only, so no caller-facing route can inject an untrusted live
binding. A real/live invocation phase must provide a separately verified
trusted repository-state reader.

## 23. Governance gates

Mock-v1 executes these control-plane evaluations:

1. strict request and approval-binding validation;
2. exact target/descriptor/config lookup;
3. fact-only adapter preflight and status/capability match;
4. existing Permission Broker evaluation with `simulation_only=true`;
5. freshness/digest recheck against the supplied immutable fixture snapshot;
6. injected non-authorizing enforcement test double;
7. durable simulation dispatch intent;
8. in-process mock adapter call.

Only steps 1–6 are gates. None is production authority. Their persisted
observations use a simulation namespace.

## 24. Permission Broker

Mock-v1 should consume the existing `PermissionBroker` because it is pure,
side-effect-free, and explicitly supports simulations. The coordinator builds
an `adapter_invocation` / `adapter` request with active task, evidence present,
simulation approval fixture present, requested component `COMP-006`, and
`simulation_only=true`.

An `ALLOW` result is stored as `PB_POLICY_WOULD_ALLOW`; its
`implementation_status=execution_unavailable` is mandatory. It does not create
`PERMITTED`. `DENY` or `HUMAN_REVIEW` stops the simulation. No PB request type,
policy, rule, or production consumer changes in 3S.

## 25. Runtime Enforcement

Do not invoke current Runtime Enforcement as a positive gate. Its public
models are design-only, evidence-only, non-authorizing, and under-bound for
RPAC. Mock-v1 instead injects a tiny test seam:

```text
SimulationEnforcementEvaluator.evaluate(bound_evidence)
  -> SimulationEnforcementObservation(
       outcome = would_allow_simulation | deny_simulation,
       simulation_only = true,
       non_authorizing = true)
```

This verifies ordering, evidence binding, denial short-circuit, and adapter
non-interference without producing `AUTHORIZED`. Replacing the double with
real Runtime Enforcement requires a separately governed contract and
implementation phase.

## 26. Execution Attempt Boundary

**Last allowed mock-v1 operation:** call
`MockDryRuntimeAdapter.dispatch(SimulationDispatchEnvelope)` in process after
a durable `SIM_DISPATCH_INTENT`, where the envelope is simulation-only and its
effect profile is all-none; then collect deterministic in-memory fixture data.

**First operation reserved for a real-runtime phase:** resolve/open an
executable, construct a process or provider client, read/inject credentials or
environment, open a socket, send a request, change a worktree file, or emit a
production `DISPATCHED` observation.

This boundary is enforced by types, imports, call-graph AST tests, dynamic
sentinels, filesystem snapshots, and unchanged runtime introspection.

## 27. No-subprocess proof

Planned proof:

- AST scan every new runtime-adapter module for `subprocess`, `os.system`,
  `popen`, `spawn`, `exec*`, `pty`, `shlex`, and shell imports/calls;
- assert the mock adapter import graph contains no legacy execution module;
- monkeypatch `subprocess.run`, `subprocess.Popen`, `os.system`, and available
  `os.posix_spawn*` calls to raise during the entire integration/E2E path;
- count sentinel calls and require exactly zero; and
- avoid live `build_context_pack` and intake submission because their current
  git helpers intentionally invoke subprocesses outside the adapter.

## 28. No-network proof

Planned proof:

- AST scan for `socket`, `urllib`, `http.client`, provider SDKs, `requests`,
  `httpx`, and endpoint fields in the mock implementation;
- monkeypatch `socket.socket` and `socket.create_connection` to raise;
- install import sentinels for common HTTP/provider client modules during E2E;
- require zero sentinel calls and `network_required=false` plus observed
  network effect false in descriptor/request/result.

## 29. No-credential proof

Planned proof:

- closed mock types contain neither credential values nor references;
- AST scan rejects `os.environ`, `getenv`, `Path.home`, keyring, token-store,
  auth-file, and provider-config access in the adapter/coordinator path;
- dynamic sentinels make environment and home/token access fail the E2E;
- fixture prompt/result secret-marker probes confirm no environment value can
  influence deterministic output.

## 30. Filesystem effects

The adapter itself performs no filesystem I/O. The trusted
`RuntimeInvocationStore` may write only under:

```text
.pcae/runtime-invocations/mock-v1/<invocation_id>/
```

Planned layout:

```text
request.json                         # immutable, create once
attempts/<attempt_id>/
  0001-sim-prepared.json             # immutable chained events
  ...
  result.json                        # immutable terminal result
  intake-handoff.json                # immutable Stage-B disposition
```

Every document is closed, canonical, digest-bearing, and create-only. No
mutable `latest.json` is an authority source. Tests snapshot all files outside
that controlled root and require byte identity before/after. The synthetic
change remains data only.

## 31. Invocation persistence decision

Choose **Option A — required in mock-v1**.

RPAC-REQ-067 requires a persistent record before any real adapter, and the
mock is the safest place to falsify replay/restart/ambiguity semantics. An
in-memory-only prototype would leave the most safety-critical dispatch
boundary untested until process effects exist.

The store is append-only and repository-local. It is audit evidence, not
authority. Corrupt, missing-link, duplicate-sequence, digest-mismatched, or
conflicting records fail closed as `integrity_failure`; no automatic repair or
redispatch occurs.

## 32. Idempotency

Planned behavior:

- same invocation ID + same canonical request: return/reduce existing record;
  adapter call count remains unchanged;
- same invocation ID + different request digest: hard
  `integrity_failure/id_collision`;
- duplicate same-digest result: idempotent replay;
- conflicting result for an attempt: quarantine observation and fail closed;
- repeated handoff mapping: same candidate ID and content;
- repeated actual intake is not exercised in mock-v1, but the candidate ID is
  compatible with the existing intake replay contract.

## 33. Retry

No retry command or automatic retry loop in mock-v1. The record schema reserves
`previous_attempt_id`/`retry_of_attempt_id`, defaulting to absent, and tests
assert no result retryability hint triggers a new call.

Before a real adapter, retry must add a new attempt ID, fresh status, PB,
Runtime Enforcement, and approval-limit checks. Any automatic retry after a
possible effect remains prohibited.

## 34. Failure taxonomy

Mock-v1 exercises:

| Common category | Mock-v1 subcode/example |
|---|---|
| `no_adapter_configured` | unknown target, missing adapter, resolver mismatch |
| `unsupported_capability` | wrong capability/result/effect/platform |
| `permission_denied` | simulated PB `DENY` |
| `enforcement_denied` | non-authorizing test double denies simulation |
| `runtime_failure` | fixed `failure-v1` fixture |
| `malformed_result` | dedicated malformed fake adapter |
| `result_ingestion_failure` | normalized change cannot map to candidate |
| additive `integrity_failure` | ID/digest/event/result conflict |
| additive `simulation_ambiguous` | restart after simulated intent without result |

`invalid_request` is a validation subcode mapped to fail-closed pre-dispatch
failure, not a replacement for the frozen common taxonomy. Authentication,
unavailability, real dispatch error, timeout, rate limiting, and ambiguous
delivery are representable extension cases but not fabricated in mock-v1.

## 35. Cancellation

Keep the RPAC interface but implement the descriptor-declared
`unsupported` mode. Because the adapter completes synchronously, `cancel`
returns either `completed_before_cancel` for a captured attempt or
`unsupported`/`unknown_attempt`; it never creates a fake running window.

Cooperative/process/API cancellation is deferred. This still exercises the
interface required by RPAC-REQ-031/089 without unnecessary concurrency.

## 36. Streaming

Terminal result only. No callbacks, generators, async iterator, event bus, or
provider stream type. The append-only simulation state log is audit evidence,
not a public output stream.

## 37. Runtime inspect

The first implementation does not change `pcae runtime inspect`. After the
core passes independent verification, an additive view may show:

```text
Adapter descriptors:        1
  pcae.mock-dry             simulation-only / effect none
Configured dry targets:     1+
Dry simulation readiness:   available
Real execution availability: unavailable
Runtime state:              Observed
Maximum real capability:    observe
Plugin count:               0
Plugin capability count:    0
```

Static descriptor and dynamic status appear separately. The new adapter count
must not be relabeled plugin count, and simulation readiness must not feed real
health/capability fields.

## 38. CLI decision

Choose **Option A — internal API/test only** for 3S. Do not add
`runtime dry-dispatch` or change `runtime inspect` until independent
verification establishes the semantics. This minimizes public compatibility
risk and prevents a dry tool from being mistaken for agent execution.

## 39. Bootstrap wiring sequence

Normative progression:

1. implement immutable types and internal mock composition;
2. independently verify zero-effect and RPAC coverage;
3. add additive inspect visibility in a separately bounded phase if desired;
4. design an explicit user-facing dry-invocation command and live authority
   snapshot;
5. only then consider opt-in bootstrap/handoff input wiring.

No automatic bootstrap-to-adapter edge is planned in 3S.

## 40. Unit tests

Unit coverage includes descriptor immutability/validation, target/status
separation, exact registry lookup, duplicate/digest failures, request closed
shape, prompt/approval binding, canonical hashes, explicit identity layers,
effect defaults, state reducer, store integrity, deterministic fixture output,
malformed result, terminal cancellation result, and no-capability invariants.

Every failure test asserts the exact common category/subcode and confirms no
adapter call when the failure precedes simulated dispatch.

## 41. Integration tests

Integration coverage composes:

```text
request -> catalog -> target -> resolver -> preflight
        -> PB simulation -> enforcement test double
        -> record intent -> mock dispatch/collect -> normalized result
```

A second integration maps the synthetic change result to a generic intake
candidate and validates its shape/digests without submitting it. A no-change
integration proves no candidate is fabricated.

## 42. Independent E2E

One high-level future test uses a temporary PCAE fixture repository and fixed
clock/IDs:

1. construct active task/session/repository authority fixtures;
2. construct a deterministic `ContextPack` and call the existing
   `build_bootstrap_prompt`;
3. build PromptArtifact, simulation approval evidence, and request;
4. explicitly select `mock-dry.synthetic-change.v1`;
5. run preflight, PB simulation, freshness check, and enforcement test double;
6. persist simulation intent, dispatch and collect the fixed adapter;
7. persist normalized result and build the producer-neutral intake candidate;
8. replay the same request and prove no second adapter call.

Concurrent sentinels prove external process calls = 0, network calls = 0,
credential reads = 0. A before/after hash manifest proves no file outside the
controlled invocation-record directory changed. Runtime introspection remains
`Observed`/`observe`/`unavailable`; existing plugin counts remain 0/0.

## 43. Restart/recovery

Because persistence is included, tests cover:

- restart after immutable request but before simulation intent: resume gate
  validation, no adapter call yet;
- restart after `SIM_DISPATCH_INTENT` without receipt/result: record
  `simulation_ambiguous`, do not redispatch automatically;
- restart after result: return stored result;
- duplicate resume: same reduced state and no new event;
- result already captured plus repeated handoff: same handoff identity.

The conservative ambiguous rule intentionally mirrors real-effect safety even
though the mock has no effect.

## 44. Security tests

### Matrix D — Security proof

| Invariant | Planned implementation mechanism | Planned test |
|---|---|---|
| Adapter cannot self-authorize | No authority fields/methods; envelope minted by coordinator | forged adapter result cannot alter gate evidence |
| Adapter cannot override PB | PB digest stored before call; result decoder rejects governance fields | inject `pb_decision` in fake result and require malformed result |
| Adapter cannot override Runtime Enforcement | Separate non-authorizing simulation evidence; digest-bound envelope | changed enforcement digest rejected before dispatch |
| Adapter cannot choose repo authority | Immutable kernel-built `AuthoritySnapshot` in request | conflicting runtime repo/task claim ignored/quarantined |
| Adapter result is untrusted | `untrusted=true`; Stage B mapping only | no intake acceptance/ECP/promotion call occurs |
| Runtime result != accepted change | Result type omits acceptance state | synthetic change remains candidate data only |
| No subprocess | isolated imports + AST + dynamic sentinels | zero calls in full E2E |
| No network | no endpoint/client + socket sentinels | zero calls in full E2E |
| No credentials | no credential fields/env/home reads | secret-read sentinels remain untouched |
| No repository mutation | adapter has no filesystem API; store path allowlist | outside-store byte manifest unchanged |
| No capability inflation | simulation descriptor/status separated from real health | `Observed`/`observe`/`unavailable`, plugin 0/0 |
| No silent fallback | exact target/config/descriptor lookup | unknown target fails with adapter counter zero |

## 45. Identity tests

Required positive case:

```text
agent_id      = codex-ox
runtime_target = mock-dry.no-change.v1
adapter_id     = pcae.mock-dry
provider/model = absent
```

Required negative assertions: `codex-ox` alone never produces target `codex`,
provider `OpenRouter`, model `ox`, a credential, or a capability. The resolver
has no `agent_id` parameter.

A second case uses `custom-review-agent-17` with the same mock target and
identical semantic output. Only descriptive requester provenance differs.
Hard-coded known-agent validation is prohibited.

## 46. Portability

Core mock behavior uses Python 3.9-compatible standard-library primitives,
frozen dataclasses, `pathlib`, canonical UTF-8 JSON, SHA-256, UUID4, and
injected clocks. It contains no POSIX signals, process groups, shell syntax,
platform executable discovery, macOS-only paths, or Linux-only sandbox fields.

Run the same pure suites on macOS and Linux. Filesystem-store tests use
repository-relative paths and platform-neutral atomic/create-only semantics.
No Dell access is part of the plan.

## 47. Production file plan

### Matrix B — Production footprint

| File | Action | Responsibility | Why needed |
|---|---|---|---|
| `src/pcae/core/runtime_registry.py` | Modify | Add inert `RuntimeDescriptor`, adapter admission/lookup/snapshot beside unchanged plugin metadata | Reuses one canonical catalog and preserves 0-plugin semantics |
| `src/pcae/core/runtime_adapter.py` | New | Minimal target config/status, Protocol, exact callable resolver, fact preflight, simulation coordinator/gate seams | Keeps trusted orchestration outside adapter implementation |
| `src/pcae/core/runtime_invocation.py` | New | PromptArtifact, approval fixture, authority snapshot, request/envelope/receipt/result/state, canonical digests, IDs, append-only store | One cohesive invocation data/lifecycle boundary |
| `src/pcae/core/mock_runtime_adapter.py` | New | Built-in fixed-fixture adapter implementing exactly the RPAC operations | Isolates and statically proves zero transport/effect dependencies |
| `src/pcae/core/intake.py` | Modify | Add generic in-memory normalized-change candidate builder; preserve existing from-files/validation behavior | Reuses producer-neutral intake without provider branch or automatic ingestion |

No `__init__` export is required. Internal modules may be imported explicitly.
No CLI registration file changes.

## 48. Test file plan

| Test file | Purpose | Unit/Integration/E2E |
|---|---|---|
| `tests/test_runtime_adapter_core_3s.py` | Descriptor, target, status, Protocol, resolver, capability/non-capability, contract versions | Unit |
| `tests/test_runtime_invocation_3s.py` | Prompt/request/approval/envelope/result, IDs, digests, states, store, replay/restart/collision | Unit |
| `tests/test_mock_runtime_adapter_3s.py` | Fixed fixtures, determinism, preflight, dispatch/collect/cancel, malformed fake | Unit |
| `tests/test_runtime_adapter_registry_3s.py` | One catalog, duplicate/drift rejection, explicit selection, no fallback, legacy 0/0 compatibility | Unit/integration |
| `tests/test_runtime_adapter_intake_3s.py` | Synthetic change to generic candidate, no-change disposition, stable replay identity | Integration |
| `tests/test_runtime_adapter_e2e_3s.py` | Full simulation flow, PB/test-double gates, persistence/restart, zero effects, identity/portability | Independent E2E |

Existing runtime registry/introspection/snapshot/inspect, PB, bootstrap/context,
and intake suites are mandatory regressions. Static guards inspect only the new
modules and exact call graph so docstring words do not create false positives.

## 49. Contract coverage

Matrix A is the canonical coverage matrix for all 97 requirements. Mechanical
verification for 3S must parse `RPAC-REQ-001..097`, parse the matrix's first
column, and assert an exact set match, one row each, valid classification, and
counts `52/16/8/21`. It must also require every MOCK-V1-MANDATORY row to name
an implementation symbol and test seam.

Coverage does not mean every requirement gets bespoke code. Pure invariants
use structural tests, real-runtime prerequisites remain explicit blockers, and
deferred extensions remain absent by design.

## 50. Implementation sequence

1. Add descriptor/target/status/request/result types and canonical validators.
2. Extend the existing registry with inert adapter metadata and exact lookup.
3. Add the separate callable resolver and fixed mock adapter.
4. Add PromptArtifact, approval fixture, request/envelope builders, IDs, and
   effect/capability validation.
5. Add the append-only record store and deterministic state reducer.
6. Compose PB simulation and non-authorizing enforcement test-double ordering.
7. Add dispatch/collect/unsupported-cancel and normalized result validation.
8. Add generic intake Stage-B mapping.
9. Add replay/restart/failure/security/identity tests.
10. Run independent E2E plus existing regressions and prove runtime posture
    unchanged.

Each step must be independently green before the next. Runtime inspect and CLI
exposure are not steps in 3S.

## 51. Commit plan

Recommended future commits:

1. **adapter core types and catalog metadata** — descriptor, target, status,
   request/result primitives, registry extension, unit tests;
2. **deterministic mock adapter and explicit resolver** — fixed fixtures,
   exact selection, interface tests;
3. **simulation lifecycle persistence and gates** — record store, PB
   simulation, enforcement test seam, replay/restart tests;
4. **generic intake handoff and independent E2E** — Stage-B builder, security
   proof, identity and regression coverage;
5. **canonical implementation evidence** — docs/status/report only after all
   checks pass.

Do not split one invariant across several untestable commits and do not mix a
public CLI or real transport into this sequence.

## 52. Stop conditions

The future implementation stops and returns for human direction if it finds
that the mock slice requires any of:

- Permission Broker request/policy/rule change;
- Runtime Enforcement contract or production behavior change;
- real human-approval authority semantics;
- provider/model/credential access;
- subprocess, shell, network, endpoint, or process supervision;
- real execution availability/capability activation;
- HATP/HMIC/Class-B/CLTR change;
- a public command or bootstrap auto-dispatch edge outside the approved task;
- a production schema/version/build change not explicitly authorized; or
- mutation outside the bounded `.pcae/runtime-invocations/mock-v1` store.

Discovery of one of these is evidence for a separate governed phase, not
permission to expand 3S.

## 53. Real-runtime prerequisites

### Matrix E — Real-runtime deferred prerequisites

| Requirement | Mock-v1 | Required before real adapter | Blocking dependency |
|---|---|---|---|
| Explicit target/descriptor | Proven with fixed target | Pinned executable/endpoint and config admission | Target configuration authority |
| Process supervision | Absent | Fixed argv, process tree, capture, timeout, termination | Generic executable supervisor |
| Environment isolation | No env read | Minimal allowlist and exact executable resolution | Environment profile implementation |
| Credentials | None | Opaque refs, JIT resolver/injection, redaction/revocation | General secret-reference facility |
| Network | Denied | Endpoint/TLS/egress/DNS/proxy enforcement as needed | Network policy/enforcer |
| Filesystem confinement | All denied; controlled PCAE record store only | Repo read/write/temp/outside scopes with OS enforcement | Sandbox/confinement implementation |
| Shell Gate | Not applicable | Enforcing argv/process policy; shell forms still forbidden | Shell Gate/equivalent activation |
| Permission Broker | Simulation evaluation only | RPAC-rich dispatch/effect request and production consumer | Separate PB contract/policy phase |
| Runtime Enforcement | Non-authorizing test double | Fresh, single-attempt final positive decision | Separate RE amendment/implementation |
| Human approval | Simulation binding fixture | Exact target/prompt/effects/budget/expiry/attempt authority | Production InvocationApproval workflow |
| Invocation persistence | Proven append-only | Concurrency, crash consistency, ambiguity reconciliation | Independent store verification |
| Cancellation | Unsupported terminal mode | Process/API cooperative/forced semantics | Supervisor/provider support |
| Retry | No automatic retry | Fresh attempts/gates/authority and delivery evidence | Retry policy/coordinator |
| Output normalization | Fixed bounded fixtures | stdout/stderr/provider response redaction and bounds | Transport normalizer |
| Generic intake | Stage-B candidate only | Controlled submission, quarantine, replay, review linkage | Intake integration phase |
| Supply chain | Fixed built-in digest | Installed code pinning/admission/drift checks | Adapter admission mechanism |
| Legacy paths | Not imported | Retired, disabled, or routed through RPAC kernel | Repository-wide execution interlock |
| Portability | Pure macOS/Linux core | OS-specific profiles independently tested | Platform supervision implementations |

All are blocking before Codex/Claude/API activation; mock success does not
satisfy them by implication.

## 54. First real adapter recommendation

Reassessment confirms 3Q's sequence:

1. after mock implementation and independent verification, implement a
   **generic fixed-argv external executable adapter** against a deterministic
   non-AI fixture;
2. after that boundary is independently verified and all prerequisites above
   are satisfied, use an explicit **Codex CLI RuntimeTarget** as the first
   named AI target;
3. add Claude-local by the same target contract; and
4. defer API providers until secret, egress, budget, rate-limit, and ambiguous
   delivery controls exist.

Generic executable comes first because it isolates process supervision from
model/provider behavior. Codex CLI remains the first named AI recommendation
because it directly proves that `codex-local` and `codex-ox` agent identities
do not select a provider, model, or target. `codex-ox` remains an agent/session
identity only unless an explicit separately configured target is selected.

## 55. Release implications

No release occurs in 3R. The future mock implementation is an internal
non-executing control-plane capability and does not itself justify an execution
claim. The broader runtime chapter may eventually justify `v0.5.0`, but no
version or release scope is frozen here.

## 56. Final verdict

```text
DETERMINISTIC MOCK/DRY ADAPTER IMPLEMENTATION PLAN:
COMPLETE
RPAC-001:
v1.0
REQUIREMENTS CLASSIFIED:
97 / 97
MOCK-V1-MANDATORY:
52
REAL-RUNTIME-PREREQUISITE:
16
DEFERRED-EXTENSION:
8
PURE-INVARIANT:
21
MOCK-V1 SCOPE:
MINIMAL / CONTRACT-CORRECT
REAL SUBPROCESS:
NONE
NETWORK:
NONE
CREDENTIALS:
NONE
PROVIDER/MODEL:
NONE
REAL EXECUTION:
UNAVAILABLE
GENERIC INTAKE:
STAGE B — PURE PRODUCER-NEUTRAL CANDIDATE MAPPING; NO AUTO-INGEST
RUNTIME REGISTRY:
ONE CATALOG; EXPLICIT TEST REGISTRATION; PLUGIN 0/0 SEMANTICS PRESERVED
EXECUTION AVAILABILITY:
UNCHANGED BY MOCK ADAPTER
CLI / BOOTSTRAP WIRING:
DEFERRED UNTIL INDEPENDENT VERIFICATION
IMPLEMENTATION:
NOT STARTED
```

The plan is implementation-ready and independently testable. It does not
convert simulation evidence into permission or authorization.

## 57. Exact next phase

**149O.20L.7O.3S — Deterministic Mock/Dry Runtime Adapter Implementation**

3S should implement only the footprint, 52 mandatory requirements, tests, and
stop conditions frozen by this plan. It must not add a public CLI, bootstrap
auto-dispatch, real transport, real positive enforcement, or execution
availability.

## 58. Human decision required

Human authorization is required to begin 3S. This planning phase grants no
implementation or execution authority and stops here.

### Matrix C — Mock-v1 state flow

| Step | Input | Owner | Output | External effect? |
|---|---|---|---|---|
| `SIM_PREPARED` | authority snapshot + PromptArtifact + request | trusted coordinator | immutable request/record | Controlled `.pcae` record only |
| `SIM_APPROVAL_BOUND` | separate approval fixture + request digest | trusted coordinator | bound non-authorizing evidence | No |
| `SIM_CAPABLE` | descriptor + target + request | adapter preflight/status | fact-only capability observation | No |
| `SIM_PB_EVALUATED` | translated simulation PB request | existing PB | policy-would-allow/deny observation | No |
| `SIM_FRESH` | stored/current fixture digests | trusted coordinator | freshness observation | No |
| `SIM_ENFORCEMENT_EVALUATED` | complete bound simulation evidence | injected test double | would-allow/deny simulation | No |
| `SIM_DISPATCH_INTENT` | validated simulation envelope | invocation store | durable intent | Controlled `.pcae` record only |
| `SIM_DISPATCHED` | exact adapter + simulation envelope | mock adapter | in-memory receipt | No execution effect |
| `SIM_COMPLETED` | fixed target fixture | mock adapter | deterministic terminal data | No |
| `SIM_RESULT_CAPTURED` | normalized result | trusted coordinator/store | immutable result | Controlled `.pcae` record only |
| `SIM_INTAKE_CANDIDATE_BUILT` | normalized changes + authority binding | generic intake builder | candidate or no-change disposition | No submission or mutation |

## Completion boundary

- production source modified: **NO**
- tests/contracts/schemas/version/build modified: **NO**
- adapter implemented or registered: **NO**
- runtime inspect behavior changed: **NO**
- external runtime/provider/model invoked: **NONE**
- subprocess/network/credential access: **NONE**
- prompt dispatched: **NO**
- Permission Broker policy changed: **NO**
- Runtime Enforcement/Shell Gate activated: **NO**
- HATP/HMIC/Class-B/CLTR changed: **NO**
- Dell contacted or mutated: **NO**
- public `v0.4.3` changed: **NO**
- article: **STOPPED and untouched**
- private research repository: **untouched and not inspected**

Phase 3R stops here. Phase 3S has not begun.
