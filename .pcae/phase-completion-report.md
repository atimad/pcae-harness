# Phase 149O.20L.7O.3R Complete — Deterministic Mock/Dry Runtime Adapter Implementation Plan

**Status: completed. Completeness: complete. Human decision required.**

Phase-entry commit:
`7318230feb619b161c08caa2d5256a5d2a41edf6`. Substantive planning commit:
`197c0c7bc391d5fbac82bfceb62b77fc18cdfca3`. Canonical evidence and task
lifecycle commits: `b4c74b2432aba7f2c5c6ab8d993a4d051595c716` and
`9a803701e946fc90f604ce5ed6f561f95c089914`. All are pushed to `origin/main`.

## Baseline and scope result

- Phase ID: `149O.20L.7O.3R`.
- Phase status/completeness: `completed / complete`.
- Latest public release: `v0.4.3`, still resolving to
  `63580893b1de4782a694ab802ff7bdebdf29b0e6`; unchanged.
- Contract baseline: **RPAC-001 v1.0**.
- Runtime: `not_implemented / Observed / unavailable / observe`.
- Runtime Registry current truth: 0 plugins / 0 capabilities.
- Production source modified: **NO**.
- Adapter implementation: **NOT STARTED**.
- Execution activated: **NO**.
- External runtime/provider invocation: **NONE**.
- Pushed: pushed.
- origin/main..HEAD: 0.

## RPAC-001 classification

All 97 normative requirements were re-read and classified exactly once:

| Classification | Count |
|---|---:|
| MOCK-V1-MANDATORY | 52 |
| REAL-RUNTIME-PREREQUISITE | 16 |
| DEFERRED-EXTENSION | 8 |
| PURE-INVARIANT | 21 |
| **Total** | **97** |

Every MOCK-V1-MANDATORY row identifies an expected module and symbol, named
test seam, and fail-closed behavior. The full mapping is Matrix A in the phase
document. The plan explicitly avoids converting all 97 requirements into the
first implementation.

## Proposed implementation footprint

Production files proposed for the separately authorized 3S phase:

| File | Action | Responsibility |
|---|---|---|
| `src/pcae/core/runtime_registry.py` | Modify | Add inert adapter-descriptor cataloging without changing plugin counts/capabilities |
| `src/pcae/core/runtime_adapter.py` | New | Target config, status, Protocol, exact resolver, and simulation coordinator |
| `src/pcae/core/runtime_invocation.py` | New | Immutable prompt/authority/request/envelope/result types, IDs, digests, states, append-only store |
| `src/pcae/core/mock_runtime_adapter.py` | New | Built-in fixed-fixture, deterministic, in-process mock/dry adapter |
| `src/pcae/core/intake.py` | Modify | Pure normalized-change to producer-neutral intake-candidate mapping |

Proposed tests:

- `tests/test_runtime_adapter_core_3s.py`
- `tests/test_runtime_invocation_3s.py`
- `tests/test_mock_runtime_adapter_3s.py`
- `tests/test_runtime_adapter_registry_3s.py`
- `tests/test_runtime_adapter_intake_3s.py`
- `tests/test_runtime_adapter_e2e_3s.py`

No proposed production or test file was created or modified in 3R.

## Registry, descriptor, and status plan

The one existing `RuntimeRegistry` remains the declarative catalog. It gains
inert adapter descriptor metadata only; the callable resolver is a separate,
trusted component composed with that catalog. Mock-v1 uses trusted built-in,
internal/test registration only—no ambient plugin discovery and no CLI
auto-registration.

- Adapter ID: `pcae.mock-dry`.
- Explicit targets: `mock-dry.no-change.v1`,
  `mock-dry.synthetic-change.v1`, and `mock-dry.failure.v1`.
- Unknown or ambiguous target: fail `no_adapter_configured`; never fallback.
- Static descriptor: RPAC version, immutable adapter identity/version/digest,
  class `mock_dry`, transport `in_process_fixture`,
  `simulation.dry_dispatch`, result format, `effect=none`, local/portable,
  no network, no subprocess, cancellation unsupported, simulation-only.
- Dynamic status: registered/installed/configured/auth-not-required,
  `simulation_ready=true`, `real_execution_available=false`, health and
  observed simulation capability. It contains no permission or authorization.

Mock registration does not change legacy plugin count/capability aggregation,
maximum real capability, or global execution availability. Runtime inspect is
unchanged in 3S; a later additive view may show adapter count and simulation
readiness separately while retaining 0 plugin capabilities and real execution
unavailable.

## Invocation request and identity plan

The minimum immutable request binds RPAC version; PCAE-created logical
invocation/attempt identities; idempotency key; trusted repository fingerprint,
root, base commit, active task and phase/session; descriptive agent identity;
explicit target/adapter/descriptor/config digests; typed prompt artifact and
separate simulation-approval evidence; requested simulation capability/result
format; repo-relative cwd `.`; all-none effect profiles; finite timeout; and
zero paid budget. Provider, model, credential, network, write, and outside-repo
fields are absent or explicitly none/denied.

The request cannot contain PB ALLOW, Runtime Enforcement ALLOW, permission, or
authorization claims. PCAE creates UUID4 invocation and attempt IDs. A SHA-256
digest of canonical semantic request content supplies stable idempotency;
timestamps and attempt observations are excluded.

Identity separation is directly tested. This is valid:

```text
agent_id       = codex-ox
runtime_target = mock-dry.no-change.v1
adapter_id     = pcae.mock-dry
producer       = pcae.mock-dry-fixture
provider/model = absent
```

`codex-ox` is an agent/session identity only. It implies no Codex target,
OpenRouter, Ox model, credential, configuration, capability, or execution. A
custom agent ID must work with the same explicit mock target.

## Prompt and bootstrap decisions

Mock-v1 consumes a lightweight immutable `PromptArtifact`, not a raw string or
a heavyweight workflow artifact. It binds exact content/hash, repository/task/
phase, generator version, provenance/human-edit markers, and an injected clock.
The existing deterministic bootstrap prompt may populate it.

Choose **Option B: adapter/request primitives first**. There is no live
`session bootstrap -> dispatch` connection and no user-facing dispatch CLI in
3S. The independent E2E may construct the existing bootstrap prompt from a
fixed trusted context fixture; lifecycle wiring waits until the primitives are
independently verified.

## Result, determinism, and provenance plan

The normalized result binds invocation/attempt/idempotency; target, adapter,
descriptor/config digests; simulation namespace and terminal observation;
bounded deterministic payload; normalized change list; error category;
untrusted marker; and separate producer provenance. Provider/model/principal
remain absent.

Given identical normalized semantic input and fixture version, descriptor,
payload/change bytes, result digest, status/error, and provenance are identical.
UUIDs and injected envelope timestamps may vary but never enter the deterministic
payload digest. Host paths, ambient environment, unordered mappings, and wall
clock do not influence it.

Fixed harmless fixtures are:

- explicit no-change result;
- one in-memory synthetic creation of `mock-output.txt`, never written by the
  adapter;
- deterministic simulated runtime failure;
- malformed output supplied only by a test fake.

Agent identity, runtime target, adapter identity, and producer
`pcae.mock-dry-fixture` remain separate. Runtime output cannot select or alter
repository/task authority.

## Governance-gate decisions

Mock-v1 is a dry control-plane simulation, not a governed execution attempt.
It emits `SIM_*` observations only—never production `APPROVED`, `PERMITTED`,
`AUTHORIZED`, `DISPATCHED`, or `COMPLETED` states.

- Permission Broker: call the existing broker with `simulation_only=true`.
  Persist an ALLOW result only as `PB_POLICY_WOULD_ALLOW`; it does not establish
  `PERMITTED`. Policy is unchanged.
- Runtime Enforcement: the current evidence-only/negative-only facility is not
  a positive authority. Use an injected, digest-bound, explicitly
  non-authorizing simulation test double that can produce
  `would_allow_simulation` or deny. It never establishes `AUTHORIZED`.
- Request/approval/capability/PB/simulated-enforcement evidence remains
  structurally separate, and a failed gate leaves the adapter call count zero.

Execution Attempt Boundary:

- Last mock-v1 operation allowed: after durable `SIM_DISPATCH_INTENT`, call
  `MockDryRuntimeAdapter.dispatch` in-process with an immutable
  `simulation_only=true`, `effect=none` envelope.
- First operation reserved for a real-runtime phase: executable/process launch,
  provider/client/network request, child-environment or credential resolution,
  source-worktree mutation, or emission of real `DISPATCHED` state.

Crossing that line is a hard test failure and implementation STOP condition.

## Persistence, intake, idempotency, and failure plan

Persistence is required in mock-v1 because replay and restart semantics should
be proven before effects exist. PCAE—not the adapter—writes immutable,
create-only request/event/result/handoff artifacts under:

```text
.pcae/runtime-invocations/mock-v1/<invocation_id>/
```

Events are digest-chained. Identical ID/content resumes without redispatch;
same ID/conflicting content fails `integrity_failure`; duplicate identical
completion is idempotent; conflicting completion is quarantined; persisted
intent without terminal result becomes `simulation_ambiguous` and never
redispatches automatically. Retry lineage is reserved, but retry APIs and
automatic retry are deferred.

Generic intake decision: **Stage B**. A pure provider-neutral helper converts
normalized in-memory changes to the existing candidate shape and stable
invocation/attempt/result-digest identity. It does not call live intake,
Evidence Collection Pipeline, acceptance, review, promotion, or filesystem/git
binding helpers. No-change returns `not_applicable_no_changes` rather than a
fabricated candidate. Result and candidate remain untrusted evidence.

Mock-v1 failure subset:

- no adapter configured / invalid explicit target;
- invalid request or integrity collision;
- unsupported simulation capability/effect;
- deterministic simulated runtime failure;
- malformed normalized result;
- result-to-intake mapping failure;
- simulation ambiguity on restart.

Authentication, provider/network, delivery timeout, and real process failures
remain representable contract vocabulary but unexercised prerequisites.
Cancellation returns deterministic unsupported/already-complete semantics;
streaming is deferred and terminal results only are planned.

## Security and zero-effect proof design

Static AST/import guards and dynamic sentinels jointly prove:

| Invariant | Evidence design |
|---|---|
| No subprocess | Reject `subprocess`, `os.system`, `exec*`, `spawn*`, shell helpers; patched sentinels must remain at zero calls |
| No network | Reject HTTP/socket/provider clients; patched socket/client constructors must remain at zero calls |
| No credentials | Reject environment/auth/keyring/token/secret reads and credential-like fields; patched env/open/keyring sentinels remain untouched |
| Controlled filesystem only | Hash repo outside the invocation-record root before/after; adapter write attempt fails; only PCAE record artifacts may differ |
| Adapter cannot self-authorize | Protocol/result schemas contain no authority methods or fields; forged fields fail closed |
| PB/RE cannot be overridden | Coordinator owns separate immutable evidence; adapter sees only final simulation envelope |
| Repo authority cannot be chosen by adapter | Trusted `AuthoritySnapshot` is kernel-supplied and output claims cannot rebind it |
| Result is not accepted change | `untrusted=true`; Stage-B mapping only; no acceptance/promotion/task-success path |

The independent E2E uses a fixed trusted repository/task/session context,
builds the existing deterministic bootstrap prompt, constructs the typed
artifact/request, explicitly selects `mock-dry.synthetic-change.v1`, evaluates
the simulation-only PB and non-authorizing enforcement double, records
`SIM_DISPATCH_INTENT`, calls the in-process fixture, persists the normalized
result, and produces a generic intake-compatible candidate. It asserts zero
process, network, credential, and runtime source-write calls; no source diff;
and unchanged `Observed / observe / unavailable` with plugin registry 0/0.

Core common types use `pathlib`, repo-relative logical paths, canonical JSON,
injected clocks, and no shell/signal/OS branch. macOS and Linux CI exercise the
same mock logic. Dell is not involved.

## Implementation and commit sequence

Separately authorized 3S order:

1. immutable IDs/types/digests and validation;
2. descriptor/status plus inert catalog extension and exact resolver;
3. deterministic fixed-fixture adapter;
4. append-only simulation store and replay reducer;
5. simulation coordinator with PB and non-authorizing enforcement seams;
6. normalized result and pure intake-candidate mapping;
7. unit, integration, zero-effect, identity, restart, and E2E tests;
8. independent verification before any public CLI/bootstrap/inspect exposure.

Recommended logical commits: core invocation types; registry/resolver;
deterministic adapter; persistence/coordinator; intake mapping/integration;
security/E2E verification. Do not over-fragment and do not add CLI exposure.

Implementation must stop if it requires PB policy or Runtime Enforcement
contract change, credentials, network, subprocess, real execution activation,
Shell Gate/HATP/Class-B changes, or new authority semantics.

## First-real-runtime prerequisites and sequencing

Before any real adapter: positive attempt-bound human authority; RPAC-rich PB
dispatch/effect permission; production Runtime Enforcement authorization;
durable invocation/attempt persistence; process supervision/confinement and
Shell Gate/equivalent for local execution; sanitized environment and secret
reference resolver; explicit network policy; filesystem scope enforcement;
timeouts/cancellation; ambiguity-safe retry/recovery; bounded/redacted output
normalization; generic-intake linkage; supply-chain admission; and macOS/Linux
verification.

After mock implementation and independent verification, first build a generic
fixed-argv external-executable adapter against a non-AI fixture to validate the
process boundary. The first named AI target should then be an explicitly
configured **Codex CLI RuntimeTarget**, followed by Claude-local. API providers
come later because secrets, network, cost, and delivery ambiguity add more
unproven dependencies. This sequencing creates no mapping from `codex-ox`.

## Verification and no-go record

- Planning static verifier: 58/58 sections, matrices A-E, 97/97 sequential
  RPAC rows, exact 52/16/8/21 totals, and every mandatory mapping; 0 failed.
- Source-reuse inspection: current registry, runtime, identity, prompt, PB,
  enforcement, legacy backend, persistence, and intake surfaces; 0 unresolved
  contradictions.
- `git diff --check`: passed.
- Full Fast Green: not run under the planning-only testing rule; no production,
  test, contract, schema, version, or build file changed; 0 attributable
  failures.
- Required PCAE governance/runtime checks: passed, with only established
  historical task-memory warnings.

No production source file was modified. No test file was modified. No contract
or schema was modified. No adapter was implemented or registered. No runtime
inspect behavior or identity was changed. No prompt was dispatched. No runtime,
subprocess, network, provider/model, or credential operation occurred. No PB,
Runtime Enforcement, Shell Gate, HATP, HMIC, Class-B, or CLTR behavior changed.
No Dell system was contacted. The private research repository was untouched and
uninspected. The article remains stopped, unread, unmodified, and unpublished.
No release was cut.

## Final verdict

```text
DETERMINISTIC MOCK/DRY ADAPTER IMPLEMENTATION PLAN:
COMPLETE
RPAC-001:
v1.0
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
STAGE B PURE CANDIDATE MAPPING; NO SUBMISSION
RUNTIME REGISTRY:
ONE INERT CATALOG; INTERNAL EXPLICIT MOCK REGISTRATION; NO FALLBACK
EXECUTION AVAILABILITY:
UNCHANGED BY MOCK ADAPTER
IMPLEMENTATION:
NOT STARTED
NEXT PHASE:
149O.20L.7O.3S — DETERMINISTIC MOCK/DRY RUNTIME ADAPTER IMPLEMENTATION
HUMAN DECISION:
REQUIRED
```

No release occurs in 3R. A future runtime chapter may justify `v0.5.0`, but no
version is frozen.

## Exact next phase

**149O.20L.7O.3S — Deterministic Mock/Dry Runtime Adapter Implementation.**

It is not started. A new explicit human decision is required. Stop after 3R.
