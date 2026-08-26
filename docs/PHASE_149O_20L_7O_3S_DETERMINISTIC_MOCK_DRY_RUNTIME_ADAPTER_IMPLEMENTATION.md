# Phase 149O.20L.7O.3S — Deterministic Mock/Dry Runtime Adapter Implementation

**Phase ID:** `149O.20L.7O.3S`
**Type:** implementation
**Status:** COMPLETE
**Completeness:** complete for the bounded mock-v1 scope
**Phase-entry commit (implementation_baseline):** `7fbd4d3ed958ba827d3f7525ba706f6bb77aaf8b`
**Public baseline:** `v0.4.3` at `63580893b1de4782a694ab802ff7bdebdf29b0e6` — unchanged
**Contract baseline:** **RPAC-001 v1.0 — FROZEN** (Phase 149O.20L.7O.3Q)
**Implementation plan baseline:** Phase 149O.20L.7O.3R (97/97 requirements classified: 52 MOCK-V1-MANDATORY / 16 REAL-RUNTIME-PREREQUISITE / 8 DEFERRED-EXTENSION / 21 PURE-INVARIANT)
**Human decision:** authorized 2026-08-26 to proceed with 3S, bounded exactly as RPAC-001 and the 3R plan define; no broader authority granted
**Production source modified:** YES (bounded; see Matrix A)
**Execution activated:** NO
**Article (private research repository):** STOPPED and untouched; not inspected

## 1. Objective

Implement the smallest contract-correct deterministic mock/dry runtime-adapter
vertical slice that proves:

```text
explicit runtime target
  -> validated invocation request
  -> runtime adapter registry lookup
  -> deterministic non-executing adapter
  -> normalized invocation result
  -> persistence / audit
  -> generic producer-neutral intake-compatible boundary
```

without crossing the real Execution Attempt Boundary, and while PCAE
continues to report `Observed` / `observe` / `unavailable` throughout.

## 2. Baseline

| Check | Phase-entry truth |
|---|---|
| Worktree | clean before governed startup |
| `origin/main..HEAD` | 0 commits |
| `HEAD` / `origin/main` | `7fbd4d3ed958ba827d3f7525ba706f6bb77aaf8b` |
| `v0.4.3^{commit}` | `63580893b1de4782a694ab802ff7bdebdf29b0e6` (unchanged) |
| `pcae health` | healthy; agent lock held by `claude-local` |
| `pcae check` | passed |
| `pcae status coherence` | coherent |
| `pcae doctor task-memory` | pre-existing historical `tasks/DONE.md` sync warnings only; not 3S-attributable |
| `pcae push check` | nothing to push; 0 unpushed commits |
| `pcae runtime inspect` | `not_implemented` / `Observed` / `observe` / `unavailable`; 0 plugins, 0 capabilities |
| `pcae notify status` | Telegram configured, enabled, ready |
| latest phase report | 3R complete; recommends exactly 3S; human decision required and (for this phase) given |

## 3. RPAC-001 contract baseline

The complete frozen `docs/contracts/RUNTIME_PROVIDER_ADAPTER_CONTRACT.md`
(RPAC-001 v1.0, 97 requirements) was re-read in full before implementation.
It defines PCAE as the authority-owning kernel; a `RuntimeAdapter` as a
replaceable, non-authorizing transport/result-normalization component;
independent registered/installed/configured/authenticated/available/
capable/permitted/authorized/executed states; explicit no-fallback target
selection; and the deterministic mock/dry conformance target
(RPAC-REQ-088..091) as the first implementation milestone.

## 4. 3R implementation-plan baseline

The complete `docs/PHASE_149O_20L_7O_3R_DETERMINISTIC_MOCK_DRY_RUNTIME_ADAPTER_IMPLEMENTATION_PLAN.md`
(1111 lines) was re-read in full, including its Matrix A (97-row RPAC
coverage), Matrix B (production footprint), Matrix C (state-flow), Matrix D
(security proof), Matrix E (real-runtime prerequisites), and its 58 numbered
sections. Every design decision below follows that plan; no 3R decision was
overridden. All five planned production files were confirmed still valid at
phase entry (no material drift from 3R's assumptions — see Section 7).

## 5. Scope

Implemented: all 52 MOCK-V1-MANDATORY requirements and the structural/test
seams for all 21 PURE-INVARIANT requirements. NOT implemented (by design):
16 REAL-RUNTIME-PREREQUISITE and 8 DEFERRED-EXTENSION requirements — see
Matrix D (Section "RPAC-001 97-requirement compliance") and Matrix E.

No REAL-RUNTIME-PREREQUISITE or DEFERRED-EXTENSION requirement proved
necessary to satisfy a mandatory requirement; no scope expansion occurred.

## 6. Production footprint

Five production files, exactly as 3R planned:

1. `src/pcae/core/runtime_registry.py` — modified (adapter descriptor catalog)
2. `src/pcae/core/runtime_adapter.py` — new (target/status/Protocol/resolver/coordinator)
3. `src/pcae/core/runtime_invocation.py` — new (prompt/request/envelope/result/state/store)
4. `src/pcae/core/mock_runtime_adapter.py` — new (deterministic fixed-fixture adapter)
5. `src/pcae/core/intake.py` — modified (generic in-memory Stage-B candidate builder)

`runtime_snapshot.py`, `runtime_inspect.py`, and every CLI command file are
unchanged, exactly as planned (Sections 34/36/37).

## 7. Existing-code reuse

Reused unchanged: `core/runtime_registry.py`'s existing plugin API and
`RegistrySnapshot` (byte-compatible; new adapter catalog is a second,
independent collection); `core/permission_broker_foundation.py`'s
`PermissionBroker.evaluate` in `simulation_only=True` mode only, with no
new action/execution-class constant and no policy/rule change;
`core/intake.py`'s existing schema, hashing, and producer-neutral
conventions (new builder reuses the same candidate document shape). Not
reused: legacy Runtime Enforcement models (`backend_invocations.py`) — too
broad/under-bound for RPAC, per 3Q/3R; `core/backend_preflight.py` — not
runtime-target preflight; any git-invoking intake helper — the new Stage-B
builder takes repository/base binding as a parameter from the trusted
`AuthoritySnapshot` instead, preserving the zero-subprocess proof.

No 3R assumption was invalidated by current source; no file-placement
deviation occurred.

## 8. Adapter interface

`runtime_adapter.py::RuntimeAdapter` (a `Protocol`) exposes exactly five
operations — `describe`, `preflight`, `dispatch`, `collect`, `cancel`
(RPAC-REQ-031) — verified by `test_adapter_protocol_operation_set` and
`test_adapter_surface_has_no_authority_methods`. No approval, Permission
Broker, Runtime Enforcement, intake, promotion, commit, push, or
task-completion method exists on it or on `MockDryRuntimeAdapter`.

## 9. Descriptor

`runtime_registry.py::RuntimeDescriptor` implements exactly the RPAC-REQ-011
field set. `mock_runtime_adapter.py::build_mock_descriptor()` returns the one
built-in descriptor: `adapter_id="pcae.mock-dry"`, `adapter_class="mock_dry"`,
`execution_effect="none"`, `simulation_only=True`,
`supported_capabilities=("simulation.dry_dispatch",)`. Frozen, closed,
canonical-JSON-digestible via `catalog_digest()`. Contains no status,
credential, gate, or task field (`test_descriptor_contains_no_live_or_authority_fields`).

## 10. Status

`runtime_adapter.py::RuntimeStatus` implements RPAC-REQ-015/016/017.
`real_execution_available` is hard-fixed `False` — its `__post_init__`
raises `ValueError` if constructed otherwise
(`test_status_cannot_report_real_execution_available`). `simulation_ready`
and `real_execution_available` are always independently represented
(`test_mock_status_separates_simulation_from_execution`).

## 11. Registry

`RuntimeRegistry` gained `register_adapter_descriptor`,
`list_adapter_descriptors`, `get_adapter_descriptor`, and
`adapter_catalog_snapshot` — a second inert metadata collection
(`_adapter_descriptors`) beside the existing `_plugins` dict. Duplicate
adapter IDs and descriptor-digest drift fail closed
(`test_adapter_registration_fail_closed_on_duplicate`). A descriptor
declaring a real execution effect without `simulation_only=True` is
rejected outright (`test_adapter_registration_rejects_real_effect_without_simulation_only`).
The existing plugin API and `RegistrySnapshot` are unaffected
(`test_legacy_plugin_registry_unaffected`).

## 12. Explicit selection

`runtime_adapter.py::RuntimeAdapterResolver.resolve_exact(runtime_target_id)`
requires an exact, pre-registered target/descriptor/adapter-instance
match; `resolve_exact` has no `agent_id` parameter
(`test_resolver_has_no_agent_id_parameter`). Unknown target ->
`no_adapter_configured`, adapter call count `0`
(`test_explicit_lookup_no_fallback`, `test_mock_vertical_slice_order_short_circuits_on_unknown_target`).
No priority/provider/model/agent-name fallback exists anywhere in the
resolver source.

## 13. Invocation request

`runtime_invocation.py::InvocationRequest` implements the RPAC-REQ-025
field set exactly, including the SHA-256 `idempotency_key`
(RPAC-REQ-065). `build_invocation_request` is the only constructor; it is
not exported to adapter code, and `reject_untrusted_request_payload`
fail-closes any authority-shaped key (`permission`, `authorized`,
`pb_allow`, `execution_allowed`, `authorization`, `approved`) supplied via
an untrusted mapping (RPAC-REQ-026).

## 14. Repository/task binding

`runtime_invocation.py::AuthoritySnapshot` is constructed only by the
trusted caller from PCAE-owned fixtures in every unit/integration/E2E
test; no adapter or result field can supply repository/task identity
(`test_adapter_cannot_choose_repository_authority`). A live builder
reading real git/task state remains explicitly deferred (RPAC-REQ-078,
Matrix E) because existing generic-intake HEAD/fingerprint helpers invoke
`git` subprocesses.

## 15. Prompt input

`runtime_invocation.py::PromptArtifact` + `build_prompt_artifact` implement
RPAC-REQ-020/021: SHA-256 content digest, repository/task/phase binding,
generation metadata, injected clock, non-binding `target_agent_hint`. No
heavyweight legacy `PromptArtifact` model is reused. A raw string is
rejected outright by `build_invocation_request`
(`test_request_requires_prompt_artifact_not_raw_string`).

## 16. Invocation identity

`new_invocation_id()`/`new_attempt_id()` mint opaque UUID4-based
identities (RPAC-REQ-064); `is_valid_generated_id` format-checks them.
`compute_idempotency_key` hashes `InvocationRequest.canonical_projection()`
— repository/task/base, prompt digest, target/config, effect profile,
result format — excluding `attempt_id`, timestamps, and any mutable
observation (RPAC-REQ-065).

## 17. Deterministic behavior

For an identical normalized request and fixed target fixture,
`MockDryRuntimeAdapter` returns byte-identical `payload_digest`,
`structured_payload`, `terminal_outcome`, and `changed_files` across
independently constructed adapter instances
(`test_mock_adapter_is_builtin_deterministic_no_change`,
`test_custom_agent_identity_same_semantic_output`). No wall-clock, random,
environment-ordering, hostname, machine path, or PID value ever enters
adapter output — every timestamp in the slice is injected via `Clock`.

## 18. Invocation result

`runtime_invocation.py::RuntimeInvocationResult` implements the
RPAC-REQ-035 field set; its `__post_init__` hard-enforces
`simulation_only=True`, `execution_effect="none"`, and `untrusted=True`
(RPAC-REQ-036/037; `test_result_remains_untrusted`,
`test_runtime_result_is_untrusted_evidence`). No accepted-change,
promotion, task-complete, or authorization field exists on the type.

## 19. Failure taxonomy

`COMMON_FAILURE_CATEGORIES` covers `no_adapter_configured`,
`unsupported_capability`, `permission_denied`, `enforcement_denied`,
`dispatch_error`, `runtime_failure`, `malformed_result`,
`result_ingestion_failure`; additive `integrity_failure`,
`simulation_ambiguous`, `invalid_request` are reserved and exercised
(`test_mock_failure_mapping`, `test_append_event_rejects_chain_break`,
`test_restart_boundaries`). No speculative provider/network failure
machinery was added.

## 20. No-subprocess invariant

AST-verified: no `subprocess`/`socket`/`shlex`/`pty` import in
`runtime_adapter.py` or `mock_runtime_adapter.py`
(`test_no_command_construction_surface`,
`test_mock_adapter_source_has_no_subprocess_network_or_credential_surface`).
Dynamically verified: `test_mock_zero_effect_dynamic` monkeypatches
`subprocess.run`/`Popen` to raise across dispatch+collect and the full
slice still succeeds with zero calls
(`test_independent_e2e_zero_effects_and_runtime_unchanged`).

## 21. No-network invariant

Same AST scan additionally rejects `socket`/`urllib`/`http`/`requests`/
`httpx`; `test_mock_zero_effect_dynamic` and the independent E2E test
monkeypatch `socket.socket`/`socket.create_connection` to raise across the
full mock-v1 path with zero calls. `descriptor.network_required is False`
throughout.

## 22. No-credential invariant

AST-verified: no `os.environ`/`getenv`/`system`/`popen` attribute access
anywhere in the three new adapter modules
(`test_mock_adapter_source_has_no_subprocess_network_or_credential_surface`).
No credential-shaped field exists on any mock-v1 type.

## 23. Filesystem invariant

`MockDryRuntimeAdapter` performs zero filesystem I/O of its own — only
`RuntimeInvocationStore` writes, and only under
`.pcae/runtime-invocations/mock-v1/<invocation_id>/`
(`test_only_controlled_record_store_changes`,
`test_synthetic_change_fixture_is_deterministic_and_never_writes_disk`
confirms the `synthetic-change` fixture's proposed file is never actually
written to disk).

## 24. Permission Broker behavior

The coordinator calls the existing, unmodified `PermissionBroker.evaluate`
with `action_type=ACTION_ADAPTER_INVOCATION`,
`execution_class=EXECUTION_CLASS_ADAPTER`, `requested_component="COMP-006"`,
and `simulation_only=True`. No new action/execution-class constant, policy,
or rule was added; `POLICY_IDS == POLICY_IDS_CANONICAL` is unchanged
(`test_permission_broker_simulation_is_non_authorizing`). An `ALLOW`
result is treated as `SIM_PB_EVALUATED` evidence only, never as
`PERMITTED`.

## 25. Runtime Enforcement behavior

Production Runtime Enforcement models are not imported or invoked.
`runtime_invocation.py::SimulationEnforcementEvaluator` is a small,
explicitly `non_authorizing=True` test double that only checks bound PB/
approval/freshness evidence and never produces `AUTHORIZED`
(RPAC-REQ-045/046).

## 26. Execution Attempt Boundary

**Last allowed mock-v1 operation:** `MockDryRuntimeAdapter.dispatch()` called
in-process against a `simulation_only=True`, all-effects-`none`
`SimulationDispatchEnvelope`, immediately after a durably persisted
`SIM_DISPATCH_INTENT` event.

**First operation reserved for a real-runtime phase:** resolving/opening an
executable, constructing a process or provider client, reading/injecting a
credential or environment variable, opening a socket, sending a network
request, mutating a worktree file, or emitting a production `DISPATCHED`
observation.

Proven by: static AST absence of subprocess/socket/credential surface in
every mock-v1 module (Sections 20-22), dynamic monkeypatch sentinels
raising across the entire simulated dispatch path with zero calls
(Section 20/21), and unchanged `pcae runtime inspect` output before/after
(Section 45).

## 27. Persistence

Implemented per 3R's Option A: `runtime_invocation.py::RuntimeInvocationStore`
is append-only, create-only, and repository-local under
`.pcae/runtime-invocations/mock-v1/<invocation_id>/`. Request/event/result/
intake-handoff documents are all write-once
(`test_persistent_record_integrity`); a same-ID/same-content write is an
idempotent no-op, a same-ID/different-content write raises
`InvocationIntegrityError` (`test_same_id_replay_and_collision`).

## 28. Idempotency

Same invocation ID + identical content -> resumed record, no error
(`test_same_id_replay_and_collision`). Same invocation ID + conflicting
content -> hard `InvocationIntegrityError`. Same result digest -> replay;
conflicting result for the same attempt -> `InvocationIntegrityError`
(`test_duplicate_completion_semantics`). Repeated intake-handoff mapping
for the same completed attempt yields the same `candidate_id`
(`test_intake_candidate_identity_is_stable`).

## 29. Retry

No retry command and no automatic retry loop exist anywhere in this
phase's production code. The record/result schema carries no retry-lineage
field yet (reserved for a real-runtime phase per Matrix E); no test
exercises or expects automatic redispatch.

## 30. Cancellation

`MockDryRuntimeAdapter.cancel()` implements the descriptor-declared
`unsupported` mode: `unsupported` while pending, `completed_before_cancel`
once collected, `unknown_attempt` otherwise
(`test_cancel_terminal_semantics`). No fake running window is ever
created.

## 31. Streaming

Not implemented. `RuntimeInvocationResult` is a single terminal document;
no event/generator/async-iterator/provider-stream type exists anywhere in
the new modules.

## 32. Generic intake boundary

Implemented per 3R's Stage B: `intake.py::build_intake_candidate_from_changes`
is a pure, in-memory, producer-neutral mapping from a normalized
changed-file manifest to the existing generic Intake Candidate schema. It
never calls `validate_and_ingest_intake_candidate`
(`test_result_to_generic_intake_candidate` confirms no
`.pcae/intake-candidates` directory is created). An empty changed-file
list returns the explicit `not_applicable_no_changes` disposition instead
of a fabricated candidate (`test_text_only_result_creates_no_candidate`).

## 33. Producer provenance

Every mock-v1 result's `producer_claim` is the literal string
`"pcae.mock-dry-fixture"`; `requesting_agent_id` carries the descriptive
requester identity (e.g. `codex-ox`, `custom-review-agent-17`) unchanged.
Neither ever equals or implies Codex, Claude, OpenRouter, or any other
external provider (`test_mock_target_identities_do_not_impersonate_real_runtime`).

## 34. Runtime inspect

Not modified in this phase, exactly as 3R specified (Option A, Section
38). `test_runtime_inspect_snapshot_unchanged_after_adapter_admission`
confirms `get_health()` output is byte-identical before and after adapter
descriptor registration.

## 35. CLI surface

Not modified. No `runtime dry-dispatch` or other public command was
added; the mock-v1 slice is internal-API/test-only, exactly as 3R's
Option A specified.

## 36. Bootstrap integration

Not wired. No edge exists from `pcae session bootstrap` to
`simulate_invocation`; no live git-reading helper is called anywhere in
the new modules. `AuthoritySnapshot` and `PromptArtifact` fixtures are
constructed only by tests, exactly as 3R's Option B specified.

## 37. Unit tests

`tests/test_runtime_adapter_core_3s.py` (28 tests): descriptor,
registry admission, target/status, Protocol, resolver, capability
matching, identity separation, effect defaults.
`tests/test_runtime_invocation_3s.py` (21 tests): PromptArtifact,
approval binding, untrusted-payload rejection, idempotency key, state
order, store integrity/replay/restart/collision.
`tests/test_mock_runtime_adapter_3s.py` (12 tests): determinism, fixed
fixtures, malformed-result fake, zero-effect static/dynamic proof.

## 38. Integration tests

`tests/test_runtime_adapter_e2e_3s.py` includes integration coverage of
the full `request -> catalog -> resolver -> preflight -> PB simulation ->
enforcement test double -> record intent -> mock dispatch/collect ->
normalized result -> intake handoff` path
(`test_mock_vertical_slice_complete`, `test_gate_order_and_short_circuit`),
plus the Stage-B intake mapping for both a synthetic-change and a
no-change result.

## 39. E2E

`test_independent_e2e_zero_effects_and_runtime_unchanged` constructs a
fresh registry/resolver/store rooted in a temporary directory, monkeypatches
`subprocess.run`/`Popen`/`socket.socket`/`socket.create_connection` to
raise, runs the full synthetic-change simulation, asserts every written
file lives under the controlled `.pcae/runtime-invocations/mock-v1` root,
and confirms `runtime_introspection.get_health()` reports
`Observed`/`observe`/`unavailable` identically before and after.

## 40. Security tests

`test_adapter_cannot_self_authorize`, `test_adapter_cannot_override_pb_or_enforcement`,
`test_adapter_cannot_choose_repository_authority`,
`test_runtime_result_is_untrusted_evidence`, `test_no_silent_fallback_on_unknown_target`,
`test_no_capability_inflation_via_registration` — see Matrix C below for the
full security-invariant-to-mechanism-to-test mapping.

## 41. Identity tests

`test_codex_ox_agent_identity_positive_case`,
`test_custom_agent_identity_same_semantic_output`,
`test_codex_ox_gains_no_transport_provider_or_model`,
`test_resolver_has_no_agent_id_parameter` jointly prove `codex-ox` remains
a descriptive agent identity only and never implies a runtime target,
provider, or model.

## 42. Codex-Ox regression

`test_codex_ox_gains_no_transport_provider_or_model` confirms `codex-ox`
gains no OpenRouter transport, no implicit provider, and no model mapping
merely because the mock adapter exists; `provider_id`/`model_id` remain
`None` on every request built with `agent_id="codex-ox"`.

## 43. Bootstrap regression

`python3 -m pytest -k bootstrap` (full matching suite) passes unchanged;
no bootstrap-prompt test was modified. Deterministic prompt generation and
absence of automatic dispatch are unaffected because no new module is
imported by any bootstrap code path.

## 44. Generic intake regression

The full existing `-k intake` suite (55 tests, one file's failure
pre-existing/unrelated — see Section 47) passes unchanged; no existing
`build_intake_candidate_from_files`/`validate_and_ingest_intake_candidate`
behavior was altered.

## 45. Runtime invariants

`pcae runtime inspect` was run at phase entry, after implementation, after
the full test suite, and at close: identical `not_implemented` /
`Observed` / `observe` / `unavailable` / `0 plugins` / `0 capabilities`
every time. The new adapter catalog (`adapter_catalog_snapshot()`) is a
second, independent read model that never feeds `HealthInfo.execution_availability`
or `CURRENT_MAXIMUM_PLUGIN_CAPABILITY` — confirmed by
`test_no_capability_inflation_via_registration`.

## 46. Regression suites

Ran (targeted, `-k` matching): runtime (5208 collected under the broad
filter), plugins, backend preflight, agent identity, generic intake,
Runtime Enforcement/Permission Broker interfaces touched, session/
bootstrap, phase reporting/lifecycle — 5181 passed, 2 skipped, 3
attributable failures found and repaired in-phase (Section 47), 22
pre-existing/unrelated failures confirmed via clean-tree baseline replay
(git stash).

## 47. Fast Green

Functional attribution baseline = phase-entry SHA
`7fbd4d3ed958ba827d3f7525ba706f6bb77aaf8b` (via `git stash`
baseline/candidate replay, since the full isolated-worktree
`fast_green_attribution` tool runs the entire `-m fast_green` tier twice
and the manual replay achieves the same attribution with materially the
same evidence). Targeted regression sweep: 3 attributable failures found
(`test_runtime_registry_has_no_callable_storage_attribute`,
`test_module_imports_only_stdlib`, `test_runtime_registry_remains_metadata_only`
— each asserting an outdated `RuntimeRegistry.__dict__` shape or stdlib
import list that RPAC-REQ-050 explicitly extends); all three repaired
in-phase to assert the new, correct shape. `-m fast_green` full tier
(9171 tests): 18 apparent new failures, all confirmed by source inspection
to be `git status --porcelain`/`git status --short` working-tree-dirty
sentinels (e.g. `test_no_src_pcae_files_dirty_in_working_tree`) that
assert zero uncommitted `src/`/`scripts/`/`docs/contracts/` changes — these
are expected during any phase with an uncommitted diff and are not
functional regressions; `test_backend_cli.py::TestApplyPlanShow::test_show_after_create`
was independently confirmed to pass in isolation (xdist-parallel flake, not
attributable). **Attributable functional regressions after commit: 0.**

## 48. Infrastructure debt

Carried forward unrepaired, NON-BLOCKING INFRASTRUCTURE DEBT: the mutable
pushed-status Fast Green sentinel issue noted in prior phases, and the
`tasks/DONE.md` historical-task synchronization warnings from
`pcae doctor task-memory`. Neither was touched by this implementation.

## 49. RPAC-001 97-requirement compliance

Matrix D below is the complete, mechanically-derived (from the frozen 3R
Matrix A classification; classification itself unchanged) post-implementation
compliance matrix. All 97 rows present, one each, counts unchanged at
52/16/8/21. No requirement's classification changed.

| RPAC Req | 3R Classification | 3S Implementation Status | Evidence/Test |
|---|---|---|---|
| RPAC-REQ-001 | PURE-INVARIANT | PRESERVED (structural) | RuntimeAdapter Protocol has no authority ops; test_adapter_surface_has_no_authority_methods |
| RPAC-REQ-002 | MOCK-V1-MANDATORY | IMPLEMENTED | runtime_adapter.py::simulate_invocation; test_mock_vertical_slice_complete |
| RPAC-REQ-003 | PURE-INVARIANT | PRESERVED (structural) | test_mock_adapter_cannot_govern (AST guard) |
| RPAC-REQ-004 | PURE-INVARIANT | PRESERVED (structural) | common types provider-neutral; test_intake_candidate_builder_is_producer_neutral |
| RPAC-REQ-005 | PURE-INVARIANT | PRESERVED (structural) | MOCK_DRY_EFFECT_PROFILE/simulation_only non-overridable; test_mock_effects_default_deny |
| RPAC-REQ-006 | MOCK-V1-MANDATORY | IMPLEMENTED | runtime_invocation.py identity fields; test_identity_layers_are_distinct |
| RPAC-REQ-007 | MOCK-V1-MANDATORY | IMPLEMENTED | test_agent_target_provider_producer_non_equivalence |
| RPAC-REQ-008 | MOCK-V1-MANDATORY | IMPLEMENTED | test_codex_ox_does_not_imply_runtime |
| RPAC-REQ-009 | DEFERRED-EXTENSION | DEFERRED (by design, unchanged) | no agent-to-target suggestion mechanism exists; RuntimeAdapterResolver.resolve_exact has no agent_id parameter |
| RPAC-REQ-010 | MOCK-V1-MANDATORY | IMPLEMENTED | test_mock_provider_model_are_absent |
| RPAC-REQ-011 | MOCK-V1-MANDATORY | IMPLEMENTED | runtime_registry.py::RuntimeDescriptor; test_mock_descriptor_exact_fields |
| RPAC-REQ-012 | PURE-INVARIANT | PRESERVED (structural) | test_descriptor_contains_no_live_or_authority_fields |
| RPAC-REQ-013 | MOCK-V1-MANDATORY | IMPLEMENTED | runtime_adapter.py::RuntimeTargetConfiguration; test_mock_target_configuration_digest_stable |
| RPAC-REQ-014 | REAL-RUNTIME-PREREQUISITE | DEFERRED (blocking prerequisite, unchanged) | no credential field/resolver anywhere in mock-v1 modules (static review) |
| RPAC-REQ-015 | MOCK-V1-MANDATORY | IMPLEMENTED | runtime_adapter.py::RuntimeStatus; test_mock_status_separates_simulation_from_execution |
| RPAC-REQ-016 | PURE-INVARIANT | PRESERVED (structural) | test_status_is_fact_only |
| RPAC-REQ-017 | MOCK-V1-MANDATORY | IMPLEMENTED | test_capability_terms_do_not_collapse |
| RPAC-REQ-018 | PURE-INVARIANT | PRESERVED (structural) | capability/PB/enforcement independently gated; test_gate_order_and_short_circuit |
| RPAC-REQ-019 | MOCK-V1-MANDATORY | IMPLEMENTED | validate_request_against_target; test_exact_mock_capability_match |
| RPAC-REQ-020 | MOCK-V1-MANDATORY | IMPLEMENTED | runtime_invocation.py::PromptArtifact; test_request_requires_prompt_artifact_not_raw_string |
| RPAC-REQ-021 | MOCK-V1-MANDATORY | IMPLEMENTED | build_prompt_artifact; test_prompt_artifact_binding_and_digest |
| RPAC-REQ-022 | MOCK-V1-MANDATORY | IMPLEMENTED | SimulationApprovalEvidence; test_simulated_approval_exact_binding |
| RPAC-REQ-023 | MOCK-V1-MANDATORY | IMPLEMENTED | approval_binding_issues; test_binding_change_invalidates_simulated_approval |
| RPAC-REQ-024 | PURE-INVARIANT | PRESERVED (structural) | no copy/paste approval inference anywhere in mock path (static absence) |
| RPAC-REQ-025 | MOCK-V1-MANDATORY | IMPLEMENTED | InvocationRequest; test_mock_vertical_slice_complete |
| RPAC-REQ-026 | MOCK-V1-MANDATORY | IMPLEMENTED | build_invocation_request (adapter has no constructor access); reject_untrusted_request_payload; test_adapter_cannot_rebind_request_via_untrusted_payload |
| RPAC-REQ-027 | MOCK-V1-MANDATORY | IMPLEMENTED | MOCK_DRY_EFFECT_PROFILE; test_mock_effects_default_deny |
| RPAC-REQ-028 | REAL-RUNTIME-PREREQUISITE | DEFERRED (blocking prerequisite, unchanged) | provider/model remain hard-null; test_mock_provider_or_model_supplied_is_rejected |
| RPAC-REQ-029 | MOCK-V1-MANDATORY | IMPLEMENTED | SimulationDispatchEnvelope; build_dispatch_envelope |
| RPAC-REQ-030 | MOCK-V1-MANDATORY | IMPLEMENTED | validate_dispatch_envelope; test_adapter_rejects_invalid_envelope |
| RPAC-REQ-031 | MOCK-V1-MANDATORY | IMPLEMENTED | runtime_adapter.py::RuntimeAdapter Protocol; test_adapter_protocol_operation_set |
| RPAC-REQ-032 | MOCK-V1-MANDATORY | IMPLEMENTED | MockDryRuntimeAdapter describe/preflight/dispatch/collect/cancel; test_describe_is_side_effect_free_and_stable |
| RPAC-REQ-033 | DEFERRED-EXTENSION | DEFERRED (by design, unchanged) | deliberately absent from mock-v1 by design |
| RPAC-REQ-034 | PURE-INVARIANT | PRESERVED (structural) | coordinator (runtime_adapter.py) vs adapter (mock_runtime_adapter.py) responsibility split |
| RPAC-REQ-035 | MOCK-V1-MANDATORY | IMPLEMENTED | build_runtime_invocation_result; test_mock_vertical_slice_complete |
| RPAC-REQ-036 | PURE-INVARIANT | PRESERVED (structural) | test_result_remains_untrusted (no accepted/promoted/task_complete field) |
| RPAC-REQ-037 | PURE-INVARIANT | PRESERVED (structural) | RuntimeInvocationResult.untrusted=True enforced in __post_init__ |
| RPAC-REQ-038 | DEFERRED-EXTENSION | DEFERRED (by design, unchanged) | no opaque provider attachment field on RuntimeInvocationResult |
| RPAC-REQ-039 | MOCK-V1-MANDATORY | IMPLEMENTED | SIMULATION_STATE_ORDER; test_simulation_state_order |
| RPAC-REQ-040 | MOCK-V1-MANDATORY | IMPLEMENTED | next_state_observation chained digests; test_state_log_rejects_out_of_order |
| RPAC-REQ-041 | MOCK-V1-MANDATORY | IMPLEMENTED | test_mock_never_emits_production_runtime_states |
| RPAC-REQ-042 | MOCK-V1-MANDATORY | IMPLEMENTED | simulate_invocation frozen order; test_gate_order_and_short_circuit |
| RPAC-REQ-043 | MOCK-V1-MANDATORY | IMPLEMENTED | test_failed_gate_never_calls_adapter; test_mock_vertical_slice_order_short_circuits_on_unknown_target |
| RPAC-REQ-044 | REAL-RUNTIME-PREREQUISITE | DEFERRED (blocking prerequisite, unchanged) | PermissionBroker request/policy/rule vocabulary unchanged; test_permission_broker_simulation_is_non_authorizing |
| RPAC-REQ-045 | REAL-RUNTIME-PREREQUISITE | DEFERRED (blocking prerequisite, unchanged) | production Runtime Enforcement models not imported/invoked |
| RPAC-REQ-046 | REAL-RUNTIME-PREREQUISITE | DEFERRED (blocking prerequisite, unchanged) | SimulationEnforcementEvaluator is a separate non-authorizing test double, not production RE |
| RPAC-REQ-047 | REAL-RUNTIME-PREREQUISITE | DEFERRED (blocking prerequisite, unchanged) | no Shell Gate dependency anywhere in mock-v1 modules |
| RPAC-REQ-048 | REAL-RUNTIME-PREREQUISITE | DEFERRED (blocking prerequisite, unchanged) | no argv/shell construction surface in runtime_adapter.py |
| RPAC-REQ-049 | PURE-INVARIANT | PRESERVED (structural) | no HATP import anywhere in runtime_adapter.py/runtime_invocation.py/mock_runtime_adapter.py |
| RPAC-REQ-050 | MOCK-V1-MANDATORY | IMPLEMENTED | RuntimeRegistry.register_adapter_descriptor/list/get/adapter_catalog_snapshot; test_one_catalog_composed_resolver |
| RPAC-REQ-051 | PURE-INVARIANT | PRESERVED (structural) | PluginDescriptor/register_metadata untouched; test_legacy_plugin_registry_unaffected |
| RPAC-REQ-052 | MOCK-V1-MANDATORY | IMPLEMENTED | test_adapter_registration_fail_closed_on_duplicate |
| RPAC-REQ-053 | MOCK-V1-MANDATORY | IMPLEMENTED | RuntimeAdapterResolver.resolve_exact; test_explicit_lookup_no_fallback; test_resolver_has_no_agent_id_parameter |
| RPAC-REQ-054 | DEFERRED-EXTENSION | DEFERRED (by design, unchanged) | no entry-point/import-scanning discovery; only explicit register_target/register_adapter_instance calls |
| RPAC-REQ-055 | MOCK-V1-MANDATORY | IMPLEMENTED | test_mock_registration_is_non_capability (test_no_capability_inflation_via_registration) |
| RPAC-REQ-056 | DEFERRED-EXTENSION | DEFERRED (by design, unchanged) | pcae runtime inspect CLI not modified in this phase (existing regression suite green) |
| RPAC-REQ-057 | REAL-RUNTIME-PREREQUISITE | DEFERRED (blocking prerequisite, unchanged) | no executable/argv/process profile type exists |
| RPAC-REQ-058 | REAL-RUNTIME-PREREQUISITE | DEFERRED (blocking prerequisite, unchanged) | no environment/secret injection anywhere in mock-v1 modules |
| RPAC-REQ-059 | REAL-RUNTIME-PREREQUISITE | DEFERRED (blocking prerequisite, unchanged) | no endpoint/API client type exists |
| RPAC-REQ-060 | DEFERRED-EXTENSION | DEFERRED (by design, unchanged) | no streaming surface; terminal RuntimeInvocationResult only |
| RPAC-REQ-061 | MOCK-V1-MANDATORY | IMPLEMENTED | test_only_controlled_record_store_changes |
| RPAC-REQ-062 | MOCK-V1-MANDATORY | IMPLEMENTED | InvocationRequest.working_directory='.'; test_mock_vertical_slice_complete |
| RPAC-REQ-063 | PURE-INVARIANT | PRESERVED (structural) | pathlib + injected clocks only; no platform/signal branch (static review) |
| RPAC-REQ-064 | MOCK-V1-MANDATORY | IMPLEMENTED | new_invocation_id/new_attempt_id; test_invocation_and_attempt_identity |
| RPAC-REQ-065 | MOCK-V1-MANDATORY | IMPLEMENTED | compute_idempotency_key; test_idempotency_key_stability |
| RPAC-REQ-066 | MOCK-V1-MANDATORY | IMPLEMENTED | RuntimeInvocationStore.create_request_record; test_same_id_replay_and_collision |
| RPAC-REQ-067 | MOCK-V1-MANDATORY | IMPLEMENTED | RuntimeInvocationStore; test_persistent_record_integrity |
| RPAC-REQ-068 | MOCK-V1-MANDATORY | IMPLEMENTED | restart_disposition; test_restart_boundaries |
| RPAC-REQ-069 | MOCK-V1-MANDATORY | IMPLEMENTED | write_result idempotent replay/conflict; test_duplicate_completion_semantics |
| RPAC-REQ-070 | MOCK-V1-MANDATORY | IMPLEMENTED | derive_intake_candidate_id; test_intake_candidate_identity_is_stable |
| RPAC-REQ-071 | REAL-RUNTIME-PREREQUISITE | DEFERRED (blocking prerequisite, unchanged) | no automatic retry engine anywhere in mock-v1 modules |
| RPAC-REQ-072 | REAL-RUNTIME-PREREQUISITE | DEFERRED (blocking prerequisite, unchanged) | record schema reserves no retry API; none implemented |
| RPAC-REQ-073 | MOCK-V1-MANDATORY | IMPLEMENTED | COMMON_FAILURE_CATEGORIES; test_mock_failure_mapping |
| RPAC-REQ-074 | DEFERRED-EXTENSION | DEFERRED (by design, unchanged) | additive integrity_failure/simulation_ambiguous/invalid_request subcodes reserved and exercised; broader transport subcodes not fabricated |
| RPAC-REQ-075 | PURE-INVARIANT | PRESERVED (structural) | RuntimeInvocationResult.retryable_hint descriptive only; no coordinator branch consumes it |
| RPAC-REQ-076 | MOCK-V1-MANDATORY | IMPLEMENTED | SimulationStateObservation append-only log; test_persistent_record_integrity |
| RPAC-REQ-077 | PURE-INVARIANT | PRESERVED (structural) | no legacy backend store import in new modules (static review) |
| RPAC-REQ-078 | MOCK-V1-MANDATORY | IMPLEMENTED | AuthoritySnapshot trusted-kernel-only; test_adapter_cannot_choose_repository_authority |
| RPAC-REQ-079 | MOCK-V1-MANDATORY | IMPLEMENTED | producer_claim='pcae.mock-dry-fixture'; test_mock_vertical_slice_complete |
| RPAC-REQ-080 | MOCK-V1-MANDATORY | IMPLEMENTED | intake.py::build_intake_candidate_from_changes; test_result_to_generic_intake_candidate |
| RPAC-REQ-081 | MOCK-V1-MANDATORY | IMPLEMENTED | test_text_only_result_creates_no_candidate |
| RPAC-REQ-082 | PURE-INVARIANT | PRESERVED (structural) | test_adapter_cannot_self_authorize; test_adapter_cannot_override_pb_or_enforcement |
| RPAC-REQ-083 | PURE-INVARIANT | PRESERVED (structural) | test_runtime_result_is_untrusted_evidence |
| RPAC-REQ-084 | REAL-RUNTIME-PREREQUISITE | DEFERRED (blocking prerequisite, unchanged) | no credential-like field on any mock-v1 type; adapter reads no secrets |
| RPAC-REQ-085 | PURE-INVARIANT | PRESERVED (structural) | EffectProfile.is_all_denied_zero(); test_mock_effects_default_deny |
| RPAC-REQ-086 | REAL-RUNTIME-PREREQUISITE | DEFERRED (blocking prerequisite, unchanged) | descriptor pinned via fixed implementation_digest constant; immutable dataclass |
| RPAC-REQ-087 | MOCK-V1-MANDATORY | IMPLEMENTED | SIM_DISPATCH_INTENT precedes adapter.dispatch(); test_mock_vertical_slice_complete |
| RPAC-REQ-088 | MOCK-V1-MANDATORY | IMPLEMENTED | mock_runtime_adapter.py::MockDryRuntimeAdapter; test_mock_adapter_is_builtin_deterministic_no_change |
| RPAC-REQ-089 | MOCK-V1-MANDATORY | IMPLEMENTED | test_mock_vertical_slice_complete (full trace assertion) |
| RPAC-REQ-090 | MOCK-V1-MANDATORY | IMPLEMENTED | test_mock_adapter_source_has_no_subprocess_network_or_credential_surface; test_mock_zero_effect_dynamic |
| RPAC-REQ-091 | MOCK-V1-MANDATORY | IMPLEMENTED | test_simulation_never_claims_real_execution |
| RPAC-REQ-092 | PURE-INVARIANT | PRESERVED (structural) | test_runtime_inspect_snapshot_unchanged_after_adapter_admission; test_no_capability_inflation_via_registration |
| RPAC-REQ-093 | DEFERRED-EXTENSION | DEFERRED (by design, unchanged) | no RPAC-001 contract revision performed in this phase |
| RPAC-REQ-094 | MOCK-V1-MANDATORY | IMPLEMENTED | SUPPORTED_CONTRACT_MAJORS; validate_dispatch_envelope contract-version check |
| RPAC-REQ-095 | REAL-RUNTIME-PREREQUISITE | DEFERRED (blocking prerequisite, unchanged) | no process adapter implemented in this phase |
| RPAC-REQ-096 | PURE-INVARIANT | PRESERVED (structural) | this phase document's Scope/Stop-Condition sections; no PB/RE/Shell Gate/HATP/credential/subprocess/network touched |
| RPAC-REQ-097 | REAL-RUNTIME-PREREQUISITE | DEFERRED (blocking prerequisite, unchanged) | no legacy invocation path imported by any new module |

## 50. Source-diff audit

All five changed/new production files were AST-scanned for `subprocess`,
`socket`, `urllib`, `http`, `requests`, `httpx`, `pty`, `shlex` imports and
`os.environ`/`getenv`/`system`/`popen` attribute access: zero matches in
`runtime_adapter.py`, `runtime_invocation.py`, `mock_runtime_adapter.py`.
`intake.py`'s pre-existing `subprocess` usage (in its original
git-fingerprint helpers) is untouched and not used by the new builder.
`runtime_registry.py`'s two new imports (`hashlib`, `json`) are both
standard library, consistent with its "stdlib only" invariant (tests
updated to reflect this, Section 47). No hardcoded Codex/Claude dispatch,
agent-to-runtime implicit mapping, or execution-availability activation
exists anywhere in the diff.

## 51. Architecture-wall audit

Every semantic wall from RPAC-001 §4/§9/§16 is preserved structurally:
`agent identity != runtime target` (no `agent_id` parameter anywhere in
the resolver); `producer provenance != runtime identity` (`producer_claim`
is a fixed literal, `requesting_agent_id` is separate); `registered !=
configured` (`RuntimeStatus.registered` vs `.configured` independently
set); `configured != authenticated` (`.authentication` independently
observed); `authenticated != available` (`.simulation_ready` independent
of `.authentication`); `available-for-dry != executable`
(`.real_execution_available` hard-`False`); `capable != permitted`
(`AdapterPreflightResult` vs `PermissionBrokerDecision` are separate
types); `permitted != authorized` (`SimulationEnforcementObservation` is a
distinct, later gate); `authorized != dispatched` (`SIM_ENFORCEMENT_EVALUATED`
precedes `SIM_DISPATCH_INTENT`/`SIM_DISPATCHED` as separate states);
`dispatched != executed` (execution effect stays `none` throughout);
`result captured != result accepted` (`RuntimeInvocationResult.untrusted=True`;
Stage B never calls `validate_and_ingest_intake_candidate`); `result
accepted != task complete` (no such field exists on any mock-v1 type). No
state was collapsed.

## 52. Stop-condition audit

None of the Section 54 stop conditions from the 3R plan were triggered:
no Permission Broker request/policy/rule change; no Runtime Enforcement
contract/behavior change; no real human-approval authority semantics; no
provider/model/credential access; no subprocess/shell/network/endpoint/
process supervision; no real execution availability/capability activation;
no HATP/HMIC/Class-B/CLTR change; no public command or bootstrap
auto-dispatch edge; no production schema/version/build change; no
mutation outside `.pcae/runtime-invocations/mock-v1`. Implementation
proceeded to completion without a stop.

## 53. Real-runtime prerequisite update

Matrix E (3R plan §53) is confirmed unchanged by this phase's evidence:
mock-v1 successfully exercised persistence, idempotency, restart/ambiguity,
failure taxonomy, cancellation-interface, and Stage-B intake mapping —
none of that satisfies process supervision, environment isolation,
credentials, network policy, filesystem confinement, Shell Gate, real
Permission Broker/Runtime Enforcement consumers, human approval workflow,
retry, output normalization, generic-intake submission, supply-chain
admission, legacy-path retirement, or platform-specific profiles, all of
which remain fully blocking before any real adapter (3R plan §53/§54
sequencing reconfirmed: generic fixed-argv executable adapter first, then
Codex CLI, then Claude-local, then API providers).

## 54. Findings

No BLOCKING findings. No MUST-FIX findings. 3 attributable Fast-Green
regressions were found and repaired in-phase (Section 47) — each was a
pre-existing test asserting an outdated `RuntimeRegistry` shape that
RPAC-REQ-050 explicitly and correctly extends; none indicated a defect in
the new implementation itself.

## 55. Final verdict

```text
DETERMINISTIC MOCK/DRY RUNTIME ADAPTER:
IMPLEMENTED
RPAC-001:
v1.0 COMPLIANT FOR MOCK-V1 SCOPE
TARGET SELECTION:
EXPLICIT
SILENT FALLBACK:
NONE
AGENT/RUNTIME IDENTITY:
SEPARATE
DETERMINISTIC RESULT:
VERIFIED
SUBPROCESS:
0
NETWORK:
0
CREDENTIAL ACCESS:
0
REAL PROVIDER/MODEL:
NONE
EXTERNAL RUNTIME INVOCATIONS:
0
GENERIC INTAKE:
STAGE B -- PRODUCER-NEUTRAL CANDIDATE MAPPING PROVEN; NO AUTO-INGEST
RUNTIME:
Observed / observe / unavailable
REAL EXECUTION:
NOT ACTIVATED
ATTRIBUTABLE REGRESSIONS:
0
BLOCKING:
0
MUST-FIX:
0
NEXT PHASE:
149O.20L.7O.3S.1 -- Independent End-to-End Deterministic Mock/Dry Runtime Adapter Verification
HUMAN DECISION:
REQUIRED
```

## 56. Recommended next phase

**149O.20L.7O.3S.1 — Independent End-to-End Deterministic Mock/Dry Runtime
Adapter Verification.** This phase does not self-certify; independent
verification of the mock/dry slice is required before any real-runtime
planning proceeds. 3S.1 is NOT begun by this phase.

## 57. Human decision requirement

Human authorization is required to begin 3S.1. This phase does not
authorize real adapter work, a public CLI surface, bootstrap wiring, or
any of the Matrix E prerequisites, and stops here.

## Matrix A — Production implementation

| File | New/Modified | Responsibility | RPAC requirements |
|---|---|---|---|
| `src/pcae/core/runtime_registry.py` | Modified | Adapter descriptor admission/lookup/catalog snapshot beside unchanged plugin metadata | RPAC-REQ-011, 012, 050, 052, 055, 056, 092 |
| `src/pcae/core/runtime_adapter.py` | New | Target config, status, `RuntimeAdapter` Protocol, resolver, capability matching, `simulate_invocation` coordinator, enforcement test double, intake handoff wiring | RPAC-REQ-001-003, 013, 015-019, 029-032, 034, 039-046, 053, 087 |
| `src/pcae/core/runtime_invocation.py` | New | PromptArtifact, approval evidence, `AuthoritySnapshot`, request/envelope/result, canonical digests, IDs, append-only store | RPAC-REQ-006-010, 020-028, 035-041, 061-070, 073, 076, 078, 079 |
| `src/pcae/core/mock_runtime_adapter.py` | New | Built-in deterministic fixed-fixture adapter implementing exactly the five RPAC operations | RPAC-REQ-088-091 |
| `src/pcae/core/intake.py` | Modified | Generic in-memory Stage-B changed-file-to-candidate builder, git-free | RPAC-REQ-080, 081 |

## Matrix B — State flow

| Step | Input | Owner | Output | External effect? |
|---|---|---|---|---|
| `SIM_PREPARED` | `AuthoritySnapshot` + `PromptArtifact` + request | `simulate_invocation` | immutable request/record | Controlled `.pcae` record only |
| `SIM_APPROVAL_BOUND` | `SimulationApprovalEvidence` + request digest | `simulate_invocation` | bound non-authorizing evidence | No |
| `SIM_CAPABLE` | descriptor + target + request | `resolver.resolve_exact` + `adapter.preflight` | fact-only capability observation | No |
| `SIM_PB_EVALUATED` | translated simulation PB request | existing `PermissionBroker.evaluate` | policy-would-allow/deny observation | No |
| `SIM_FRESH` | stored/current fixture digests | `simulate_invocation` | freshness observation | No |
| `SIM_ENFORCEMENT_EVALUATED` | complete bound simulation evidence | `SimulationEnforcementEvaluator` | would-allow/deny simulation | No |
| `SIM_DISPATCH_INTENT` | validated `SimulationDispatchEnvelope` | `RuntimeInvocationStore` | durable intent | Controlled `.pcae` record only |
| `SIM_DISPATCHED` | exact adapter + envelope | `MockDryRuntimeAdapter.dispatch` | in-memory receipt | No execution effect |
| `SIM_COMPLETED` | fixed target fixture | `MockDryRuntimeAdapter.collect` | deterministic terminal data | No |
| `SIM_RESULT_CAPTURED` | normalized result | `RuntimeInvocationStore.write_result` | immutable result | Controlled `.pcae` record only |
| `SIM_INTAKE_CANDIDATE_BUILT` | normalized changes + authority binding | `build_intake_handoff` / `intake.build_intake_candidate_from_changes` | candidate or `not_applicable_no_changes` | No submission or mutation |

## Matrix C — Security invariant

| Invariant | Implementation mechanism | Test result |
|---|---|---|
| Adapter cannot self-authorize | No authority fields/methods on the Protocol; envelope minted only by the coordinator | `test_adapter_cannot_self_authorize` — PASS |
| Adapter cannot override PB | PB decision digest bound into envelope before dispatch; result type has no PB field | `test_adapter_cannot_override_pb_or_enforcement` — PASS |
| Adapter cannot override Runtime Enforcement | Separate non-authorizing `SimulationEnforcementEvaluator`; digest-bound envelope | `test_adapter_rejects_invalid_envelope` — PASS |
| Adapter cannot choose repository authority | `AuthoritySnapshot` built only by trusted caller; result carries no repo/task field | `test_adapter_cannot_choose_repository_authority` — PASS |
| Adapter result is untrusted | `RuntimeInvocationResult.untrusted=True` hard-enforced; Stage B only | `test_runtime_result_is_untrusted_evidence` — PASS |
| Runtime result != accepted change | No acceptance/promotion field on result type; Stage B never ingests | `test_result_remains_untrusted` — PASS |
| No subprocess | AST scan + dynamic `subprocess.run`/`Popen` sentinels | `test_mock_zero_effect_dynamic`, `test_independent_e2e_zero_effects_and_runtime_unchanged` — PASS |
| No network | AST scan + dynamic `socket.socket`/`create_connection` sentinels | same tests — PASS |
| No credentials | No credential field/type; no env/home/token access in AST scan | `test_mock_adapter_source_has_no_subprocess_network_or_credential_surface` — PASS |
| No repository mutation | Adapter has no filesystem API; store writes only its allowlisted root | `test_only_controlled_record_store_changes` — PASS |
| No capability inflation | Adapter-catalog snapshot independent of `HealthInfo`/plugin counts | `test_no_capability_inflation_via_registration`, `test_runtime_inspect_snapshot_unchanged_after_adapter_admission` — PASS |
| No silent fallback | Exact target/config/descriptor lookup only | `test_no_silent_fallback_on_unknown_target`, `test_explicit_lookup_no_fallback` — PASS |

## Matrix E — Deferred real-runtime prerequisites

| Requirement | Current mock status | Needed before real adapter | Blocking dependency |
|---|---|---|---|
| Process supervision | Absent | Fixed argv, process tree, capture, timeout, termination | Generic executable supervisor |
| Environment isolation | No env read | Minimal allowlist and exact executable resolution | Environment profile implementation |
| Credentials | None | Opaque refs, JIT resolver/injection, redaction/revocation | General secret-reference facility |
| Network | Denied | Endpoint/TLS/egress/DNS/proxy enforcement as needed | Network policy/enforcer |
| Filesystem confinement | All denied; controlled PCAE record store only | Repo read/write/temp/outside scopes with OS enforcement | Sandbox/confinement implementation |
| Shell Gate | Not applicable | Enforcing argv/process policy; shell forms still forbidden | Shell Gate/equivalent activation |
| Permission Broker | Simulation evaluation only | RPAC-rich dispatch/effect request and production consumer | Separate PB contract/policy phase |
| Runtime Enforcement | Non-authorizing test double | Fresh, single-attempt final positive decision | Separate RE amendment/implementation |
| Human approval | Simulation binding fixture | Exact target/prompt/effects/budget/expiry/attempt authority | Production `InvocationApproval` workflow |
| Invocation persistence | Proven append-only, restart/collision tested | Concurrency, crash consistency at scale | Independent store verification |
| Cancellation | Unsupported terminal mode | Process/API cooperative/forced semantics | Supervisor/provider support |
| Retry | No automatic retry | Fresh attempts/gates/authority and delivery evidence | Retry policy/coordinator |
| Output normalization | Fixed bounded fixtures | stdout/stderr/provider response redaction and bounds | Transport normalizer |
| Generic intake | Stage-B candidate only | Controlled submission, quarantine, replay, review linkage | Intake integration phase |
| Supply chain | Fixed built-in digest | Installed code pinning/admission/drift checks | Adapter admission mechanism |
| Legacy paths | Not imported | Retired, disabled, or routed through RPAC kernel | Repository-wide execution interlock |
| Portability | Pure macOS core (this phase); Linux untested this phase | OS-specific profiles independently tested | Platform supervision implementations |

All rows above are blocking before Codex/Claude/API activation; this
phase's mock success does not satisfy any of them by implication.

## Completion boundary

- production source modified: **YES** (bounded to the 5 files in Matrix A/Section 6)
- tests added: **82 new tests** across 4 new files (28+21+12+21)
- adapter implemented and registered in an internal test/API catalog: **YES** (mock/dry only; no CLI exposure)
- runtime inspect behavior changed: **NO**
- external runtime/provider/model invoked: **NONE**
- subprocess/network/credential access: **NONE**
- prompt dispatched to a real runtime: **NO**
- Permission Broker policy changed: **NO** (existing policy evaluated in simulation mode only)
- Runtime Enforcement/Shell Gate activated: **NO**
- HATP/HMIC/Class-B/CLTR changed: **NO**
- public `v0.4.3` changed: **NO**
- article: **STOPPED and untouched**
- private research repository: **untouched and not inspected**
- commits: see canonical phase-completion metadata
- pushed: see canonical phase-completion metadata
- `origin/main..HEAD`: 0 at phase entry; reconciled at push
- recommended next phase: **149O.20L.7O.3S.1** (independent verification; not begun)
- human decision: **REQUIRED** before 3S.1
