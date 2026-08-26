# Phase 149O.20L.7O.3S Complete — Deterministic Mock/Dry Runtime Adapter Implementation

**Status: completed. Completeness: complete. Human decision required for next phase.**

Phase-entry commit: `7fbd4d3ed958ba827d3f7525ba706f6bb77aaf8b`. Implementation
commits: `58717e58` (adapter core types and catalog metadata),
`a0e5d9e2` (deterministic mock adapter and invocation lifecycle types),
`ac512ced` (generic intake handoff and independent E2E/security tests),
`1ace884a` (canonical implementation evidence and task-lifecycle transition),
`94639f37` / `2c1d78c9` (pre-push metadata sync). All are pushed to
`origin/main`.

## Baseline and scope result

- Phase ID: `149O.20L.7O.3S`.
- Phase status/completeness: `completed / complete`.
- Latest public release: `v0.4.3`, still resolving to
  `63580893b1de4782a694ab802ff7bdebdf29b0e6`; unchanged.
- Contract baseline: **RPAC-001 v1.0**.
- Runtime: `not_implemented / Observed / unavailable / observe`.
- Runtime Registry current truth: 0 plugins / 0 legacy-plugin capabilities;
  1 adapter descriptor registered inside an internal test/API catalog only.
- Production source modified: **YES** (bounded to 5 files; see below).
- Adapter implementation: **IMPLEMENTED (mock/dry, internal test/API only)**.
- Execution activated: **NO**.
- External runtime/provider invocation: **NONE**.
- Pushed: pushed.
- origin/main..HEAD: 0.

## RPAC-001 compliance

All 97 normative requirements were re-verified post-implementation:

| Classification | Count | 3S status |
|---|---:|---|
| MOCK-V1-MANDATORY | 52 | IMPLEMENTED |
| PURE-INVARIANT | 21 | PRESERVED (structural) |
| REAL-RUNTIME-PREREQUISITE | 16 | DEFERRED (blocking, unchanged) |
| DEFERRED-EXTENSION | 8 | DEFERRED (by design, unchanged) |
| **Total** | **97** | |

Full 97-row Matrix D is in
`docs/PHASE_149O_20L_7O_3S_DETERMINISTIC_MOCK_DRY_RUNTIME_ADAPTER_IMPLEMENTATION.md`.
No requirement's classification changed from the 3R plan.

## Production implementation footprint

| File | Action | Responsibility |
|---|---|---|
| `src/pcae/core/runtime_registry.py` | Modified | Adapter-descriptor catalog admission/lookup/snapshot beside unchanged plugin metadata |
| `src/pcae/core/runtime_adapter.py` | New | Target config, status, `RuntimeAdapter` Protocol, exact resolver, simulation coordinator |
| `src/pcae/core/runtime_invocation.py` | New | Immutable prompt/authority/request/envelope/result types, IDs, digests, states, append-only store |
| `src/pcae/core/mock_runtime_adapter.py` | New | Built-in fixed-fixture, deterministic, in-process mock/dry adapter |
| `src/pcae/core/intake.py` | Modified | Pure normalized-change to producer-neutral intake-candidate mapping (git-free) |

Tests added (82 new tests, 4 files):

- `tests/test_runtime_adapter_core_3s.py` (28)
- `tests/test_runtime_invocation_3s.py` (21)
- `tests/test_mock_runtime_adapter_3s.py` (12)
- `tests/test_runtime_adapter_e2e_3s.py` (21)

3 pre-existing test files repaired for RPAC-REQ-050 registry-shape
compatibility: `tests/test_runtime_registry_verification.py`,
`tests/test_runtime_registry_prototype.py`, `tests/test_runtime_inspect_cli.py`.

## Registry, descriptor, and status result

The one existing `RuntimeRegistry` remains the declarative catalog. It gained
an independent, inert adapter-descriptor metadata collection
(`_adapter_descriptors`); the existing `_plugins` collection and its API are
byte-compatible and unaffected. The callable resolver
(`RuntimeAdapterResolver`) is a separate, trusted component composed with
that catalog. Mock-v1 uses trusted internal/test registration only — no
ambient plugin discovery and no CLI auto-registration.

- Adapter ID: `pcae.mock-dry`.
- Explicit targets exercised: `mock-dry.no-change.v1`,
  `mock-dry.synthetic-change.v1`, `mock-dry.failure.v1`.
- Unknown target: fails `no_adapter_configured` with adapter call count `0`;
  no fallback anywhere in the resolver.
- Static descriptor: RPAC version, immutable adapter identity/version/digest,
  class `mock_dry`, transport `in_process_fixture`,
  `simulation.dry_dispatch`, result format, `effect=none`, local/portable,
  no network, no subprocess, cancellation unsupported, simulation-only.
- Dynamic status: registered/installed/configured/auth-not-required,
  `simulation_ready=true`, `real_execution_available=false` (hard-enforced
  by `__post_init__`), health and observed simulation capability.

Mock registration does not change legacy plugin count/capability
aggregation, maximum real capability, or global execution availability —
`test_no_capability_inflation_via_registration` and
`test_runtime_inspect_snapshot_unchanged_after_adapter_admission` confirm
this dynamically. `pcae runtime inspect` is unchanged in 3S.

## Invocation request and identity result

The immutable `InvocationRequest` binds RPAC version; PCAE-created UUID4
logical invocation/attempt identities; a SHA-256 idempotency key over
canonical semantic content; trusted repository fingerprint/base-commit/
task/phase binding; descriptive agent identity; explicit target/adapter/
descriptor/config digests; typed `PromptArtifact` and separate simulation
approval evidence; requested simulation capability/result format;
repo-relative cwd `.`; all-none effect profile; finite timeout; and zero
paid budget. Provider/model fields are hard-rejected if supplied.

`reject_untrusted_request_payload` fail-closes any authority-shaped key
(`permission`, `authorized`, `pb_allow`, `execution_allowed`,
`authorization`, `approved`).

Identity separation directly tested and confirmed:

```text
agent_id       = codex-ox
runtime_target = mock-dry.no-change.v1
adapter_id     = pcae.mock-dry
producer       = pcae.mock-dry-fixture
provider/model = absent
```

`codex-ox` remains an agent/session identity only; it implies no Codex
target, OpenRouter, Ox model, credential, configuration, capability, or
execution (`test_codex_ox_gains_no_transport_provider_or_model`). A custom
agent ID (`custom-review-agent-17`) produces identical semantic output with
the same explicit mock target.

## Result, determinism, and provenance result

The normalized `RuntimeInvocationResult` binds invocation/attempt/
idempotency; target, adapter, descriptor/config digests; simulation
namespace and terminal observation; bounded deterministic payload;
normalized change list; error category; `untrusted=True` (hard-enforced);
and separate producer provenance (`pcae.mock-dry-fixture`). Provider/model/
principal remain absent.

Determinism proven dynamically: two independently constructed
`MockDryRuntimeAdapter` instances produce byte-identical `payload_digest`,
`structured_payload`, and `terminal_outcome` for the same target fixture
(`test_mock_adapter_is_builtin_deterministic_no_change`).

## Governance-gate result

Mock-v1 is a dry control-plane simulation, not a governed execution
attempt. It emits `SIM_*` observations only — never production `APPROVED`,
`PERMITTED`, `AUTHORIZED`, `DISPATCHED`, or `COMPLETED` states
(`test_mock_never_emits_production_runtime_states`).

- Permission Broker: the existing, unmodified `PermissionBroker.evaluate`
  is called with `simulation_only=true`; policy/rule vocabulary unchanged
  (`POLICY_IDS == POLICY_IDS_CANONICAL`).
- Runtime Enforcement: production models are not imported or invoked. A
  separately injected, digest-bound, explicitly non-authorizing
  `SimulationEnforcementEvaluator` produces `would_allow_simulation` or
  `deny_simulation`; it never establishes `AUTHORIZED`.
- Every pre-dispatch gate failure leaves the adapter call counter at `0`
  (`test_failed_gate_never_calls_adapter`).

Execution Attempt Boundary — proven, not merely asserted:

- Last mock-v1 operation allowed: after durable `SIM_DISPATCH_INTENT`, call
  `MockDryRuntimeAdapter.dispatch` in-process with a `simulation_only=true`,
  `effect=none` envelope.
- First operation reserved for a real-runtime phase: executable/process
  launch, provider/client/network request, credential resolution,
  source-worktree mutation, or emission of real `DISPATCHED` state.
- Dynamic sentinel tests (`test_mock_zero_effect_dynamic`,
  `test_independent_e2e_zero_effects_and_runtime_unchanged`) monkeypatch
  `subprocess.run`/`Popen`/`socket.socket`/`create_connection` to raise
  across the entire path and confirm zero calls.

## Persistence, intake, idempotency, and failure result

`RuntimeInvocationStore` writes immutable, create-only request/event/
result/handoff artifacts only under
`.pcae/runtime-invocations/mock-v1/<invocation_id>/`
(`test_only_controlled_record_store_changes`). Events are digest-chained.
Identical ID/content resumes without redispatch; conflicting content fails
`InvocationIntegrityError`; duplicate identical completion is idempotent;
conflicting completion is quarantined; a persisted intent without a
terminal result reports `simulation_ambiguous` on restart and never
auto-redispatches (`test_restart_boundaries`).

Generic intake: **Stage B implemented**. `intake.build_intake_candidate_from_changes`
converts normalized in-memory changes to the existing candidate shape with
stable invocation/attempt/result-digest identity
(`derive_intake_candidate_id`). It never calls
`validate_and_ingest_intake_candidate`. A no-change result returns
`not_applicable_no_changes` rather than a fabricated candidate.

Mock-v1 failure subset exercised: `no_adapter_configured`,
`unsupported_capability`, `permission_denied` (structurally),
`enforcement_denied` (structurally), `runtime_failure`, `malformed_result`,
`integrity_failure`, `simulation_ambiguous`, `invalid_request`.

## Security and zero-effect proof result

| Invariant | Evidence |
|---|---|
| No subprocess | AST scan + dynamic `subprocess.run`/`Popen` sentinels: 0 calls |
| No network | AST scan + dynamic `socket.socket`/`create_connection` sentinels: 0 calls |
| No credentials | AST scan rejects env/auth/keyring/token access; no credential field on any type |
| Controlled filesystem only | Byte-manifest outside the invocation-record root unchanged; adapter itself performs zero writes |
| Adapter cannot self-authorize | Protocol has no authority methods/fields; forged results fail closed |
| PB/RE cannot be overridden | Coordinator owns separate immutable evidence; adapter sees only the final envelope |
| Repo authority cannot be chosen by adapter | `AuthoritySnapshot` is kernel-supplied only; result carries no repo/task claim field |
| Result is not accepted change | `untrusted=True` hard-enforced; Stage B mapping only, no acceptance/promotion path |

The independent E2E test (`test_independent_e2e_zero_effects_and_runtime_unchanged`)
constructs a fixed fixture context, explicitly selects
`mock-dry.synthetic-change.v1`, runs the full simulation to
`SIM_INTAKE_CANDIDATE_BUILT`, and asserts zero process/network calls, a
byte-manifest confined to the controlled store root, and unchanged
`Observed / observe / unavailable` runtime posture with plugin registry 0/0
before and after.

## Verification and no-go record

- Unit tests: 61 passed (core/invocation/mock-adapter files), 0 failed.
- Integration/E2E/security/identity tests: 21 passed
  (`test_runtime_adapter_e2e_3s.py`), 0 failed.
- Targeted regression sweep (runtime/plugin/intake/bootstrap/session/
  phase-report, 5208 collected): 5181 passed / 2 skipped / 0 attributable
  failed, after in-phase repair of 3 pre-existing registry-shape
  assertions.
- Full `-m fast_green` tier (9171 tests), baseline-vs-candidate via
  git-stash replay: 0 attributable failed (18 apparent new failures were
  working-tree-dirty sentinels resolved by commit; 1 xdist-parallel flake
  independently confirmed to pass in isolation).
- `pcae health` / `pcae check` / `pcae status coherence`: healthy / passed
  / coherent throughout.
- `pcae runtime inspect`: `not_implemented / Observed / unavailable /
  observe`, 0 plugins / 0 capabilities — identical at phase entry, after
  implementation, after the full test suite, and at close.

No production source file was modified outside the 5 files named above. No
contract, schema, version, or build file was modified. No real runtime,
subprocess, network, provider/model, or credential operation occurred. No
Permission Broker policy, Runtime Enforcement production behavior, or Shell
Gate was activated. No HATP, HMIC, Class-B, or CLTR behavior changed. No
Dell system was contacted. The private research repository was untouched
and uninspected. The article remains stopped, unread, unmodified, and
unpublished. No release was cut and `v0.4.3` was not changed.

## Final verdict

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
149O.20L.7O.3S.1 -- INDEPENDENT END-TO-END DETERMINISTIC MOCK/DRY RUNTIME ADAPTER VERIFICATION
HUMAN DECISION:
REQUIRED
```

No release occurs in 3S. `v0.4.3` remains current. A future runtime chapter
may eventually justify a new minor version, but none is frozen here.

## Exact next phase

**149O.20L.7O.3S.1 — Independent End-to-End Deterministic Mock/Dry Runtime
Adapter Verification.**

It is not started. A new explicit human decision is required. Stop after
3S.
