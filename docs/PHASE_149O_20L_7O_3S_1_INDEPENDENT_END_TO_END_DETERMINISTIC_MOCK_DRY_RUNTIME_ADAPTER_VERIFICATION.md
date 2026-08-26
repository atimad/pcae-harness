# Phase 149O.20L.7O.3S.1 — Independent End-to-End Deterministic Mock/Dry Runtime Adapter Verification

## 1. Objective

Independently re-derive and verify whether Phase 149O.20L.7O.3S implemented a
contract-correct deterministic mock/dry runtime-adapter control-plane path
under RPAC-001 v1.0 (`docs/contracts/RUNTIME_PROVIDER_ADAPTER_CONTRACT.md`)
that exercises explicit selection, request validation, simulation-only
governance, deterministic normalized results, and intake compatibility,
while provably preserving execution unavailability and all authority
boundaries — without trusting 3S's own self-report and without merely
re-running 3S's own tests.

## 2. Verification independence

This phase re-read RPAC-001 v1.0 in full (all 97 requirements), re-read the
3R implementation plan's classification table, and independently read the
five 3S production modules line-by-line: `src/pcae/core/runtime_registry.py`,
`runtime_adapter.py`, `runtime_invocation.py`, `mock_runtime_adapter.py`, and
the relevant slice of `intake.py`. A fresh, independently authored
adversarial test file, `tests/test_runtime_adapter_verification_3s1.py` (18
tests), was written from scratch — it imports 3S's production modules
directly and constructs its own fixtures/attack payloads; it does not import
or extend `tests/test_runtime_adapter_e2e_3s.py`. Live, ad hoc adversarial
probes (import-time subprocess/socket blocking, malicious enforcement-double
injection, forced Permission Broker DENY, authority-field injection via both
`setattr` and constructor kwargs) were run interactively against the actual
source before being captured as durable tests.

## 3. Baseline

```
verification_baseline = 18a37856dbce1e1f61e8c414cb08552c628ab632
```

- `git status --short`: clean at baseline (only the new task-lifecycle files
  this phase itself introduced appear once work began).
- `git rev-parse HEAD` == `git rev-parse origin/main` == `18a37856...` at
  phase entry — zero commits ahead.
- `git rev-parse v0.4.3^{commit}` = `63580893b1de4782a694ab802ff7bdebdf29b0e6`,
  unchanged, and is an ancestor of HEAD — v0.4.3 is untouched by 3S/3S.1.
- `pcae runtime inspect` at phase entry: `Runtime state: Observed`,
  `Execution capability: unavailable`, `Maximum plugin capability: observe`,
  `Plugin count: 0`, `Capability count: 0`.
- `pcae health`: overall status healthy, git status clean.

## 4. 3S source delta (independently reconstructed)

```
git diff --stat 7fbd4d3e..1ace884a -- src/pcae tests
```

confirms exactly the five production files 3S's own report claims, with no
undisclosed file:

| File | Type | Lines |
|---|---|---|
| `src/pcae/core/runtime_registry.py` | modified | +176 |
| `src/pcae/core/runtime_adapter.py` | new | +584 |
| `src/pcae/core/runtime_invocation.py` | new | +981 |
| `src/pcae/core/mock_runtime_adapter.py` | new | +267 |
| `src/pcae/core/intake.py` | modified | +65 |
| 8 test files | new/modified | +1,424 |

No file outside this list was touched. This independently confirms 3S's
"reported production files" claim was exhaustive, not merely non-exhaustive
prose.

## 5. Production caller graph (Matrix A — see below)

Traced by direct source reading, not 3S prose: `RuntimeAdapterResolver`
composes `RuntimeRegistry.get_adapter_descriptor()` with an
`RuntimeAdapterResolver`-local `_targets`/`_adapter_instances` table;
`simulate_invocation()` is the single trusted-kernel coordinator that calls
`resolver.resolve_exact()`, `PermissionBroker.evaluate()`,
`SimulationEnforcementEvaluator.evaluate()`, then exactly one adapter's
`preflight`/`dispatch`/`collect`, then `runtime_adapter.build_intake_handoff()`
→ `intake.build_intake_candidate_from_changes()`. See Matrix A for the full
per-symbol breakdown.

## 6. Registry architecture reconciliation (priority item)

Independently answered by reading `runtime_registry.py:442-640` and
`commands/runtime_inspect.py`:

1. **What registry/catalog contains the mock adapter?** `RuntimeRegistry`
   itself — but in a second private dict, `self._adapter_descriptors`,
   distinct from `self._plugins`.
2. **Process-local, static, built-in, or configurable?** Process-local and
   in-memory only; no persistence. `build_mock_descriptor()` is a pure
   built-in factory function, not read from configuration.
3. **Is it the same registry concept `pcae runtime inspect` uses?** Same
   Python class, different collection. `run_runtime_inspect()` constructs a
   **fresh** `RuntimeRegistry()` per CLI invocation and only ever calls
   `list_plugins()`/`get_registered_plugin_count()`-style accessors (via
   `runtime_snapshot.build_runtime_snapshot`), never
   `list_adapter_descriptors()`.
4. **Why two surfaces?** RPAC-REQ-050 explicitly mandates this: "the
   existing `RuntimeRegistry` remains the metadata/introspection foundation
   ... future callable resolution SHALL be a trusted-kernel extension
   composed with it, not a competing authoritative backend/adapter
   registry." The two-dict design is the contract-required shape, not
   accidental duplication.
5. **Consistent with RPAC-001?** Yes — confirmed by live probe (§9 below):
   registering an adapter descriptor leaves `list_plugins()` at length 0.
6. **One legacy plugin registry, one adapter catalog, intentionally
   distinct?** Yes, confirmed.
7. **Any ambiguity where "runtime registry" could receive the wrong
   abstraction?** No call site was found that passes `_plugins` state where
   `_adapter_descriptors` was intended or vice versa; the two accessor sets
   (`list_plugins`/`register_metadata` vs. `list_adapter_descriptors`/
   `register_adapter_descriptor`) are named distinctly and never mix.
8. **Can `runtime inspect` evolve without incompatible dual registration?**
   Yes structurally — RPAC-REQ-056 anticipates this ("static registration
   and dynamic status SHALL be displayed separately... until an actual
   governed runtime is registered and activated"). Today `runtime inspect`
   simply never surfaces the adapter-catalog dimension at all, which is a
   real but bounded gap (see §28, non-blocking finding NB-1).

**Classification: coherent separation** — this is the contract-mandated
shape (RPAC-REQ-050), not an architectural debt or blocking contradiction.

## 7. Mock discoverability

Live probe (`_build_stack()` + `resolver.resolve_exact(...)`): exact ID
`mock-dry.no-change.v1` resolves; unknown ID, typo ID (`...v2`), empty
string, and `codex-ox` (an agent identity, not a target) all return
`ResolutionFailure(category="no_adapter_configured")`. Captured as
`test_unresolvable_targets_fail_closed_with_no_fallback` (parametrized, 5
cases, all fail closed).

## 8. Explicit selection / 9. No silent fallback

`RuntimeAdapterResolver.resolve_exact()` takes only one explicit
`runtime_target_id`; there is no iteration over `_targets`, no "first
adapter," no default. Confirmed by reading `runtime_adapter.py:290-311`
(no loop, no `.values()[0]`, no `except: use default` branch) and by the
live no-fallback probe above. **No silent fallback exists.**

## 10. Agent/runtime identity

`codex-ox` used as `requester_agent_id` in the E2E stack produces a request
whose `runtime_target_id` remains `mock-dry.no-change.v1` — no code path
derives a target from the agent string
(`mock_runtime_adapter.py:70-80` explicitly asserts at import time that
`codex`, `claude`, `openrouter`, `openai`, `anthropic` never appear in any
mock identity constant — a self-check that raises `RuntimeError` at import
if violated). A custom, non-Codex identity (`"custom-tester-99"` in the
fresh suite's variants) produces identical semantic output.

## 11. Producer provenance

`ProducerProvenance`/`producer_claim="pcae.mock-dry-fixture"` is set by the
adapter's `collect()`, and `build_intake_handoff()`'s `producer_kind` comes
from `result.requesting_agent_id` (the trusted request's agent field, not
anything the adapter invents) — but the *adapter's own claimed provenance*
is always the fixed literal `"pcae.mock-dry-fixture"`, never a caller- or
result-controlled string. No code path lets a result claim `Codex`,
`Claude`, `Codex-Ox transport`, or `OpenRouter`.

## 12. Invocation request validation

`build_invocation_request()` is a keyword-only, closed-signature factory
over a `@dataclass(frozen=True)` `InvocationRequest`. Live probe:
`setattr(request, "authorized", True)` raises `FrozenInstanceError`; calling
`build_invocation_request(..., authorized=True)` raises `TypeError:
unexpected keyword argument`. Malformed/unknown-target requests fail at
`resolve_exact`/`validate_request_against_target` with explicit reason
codes. Captured as `test_authority_field_cannot_be_set_on_frozen_request`
and `test_authority_kwarg_rejected_by_closed_request_builder`.

## 13. Authority injection

Tested `authorized=true`, i.e. the field literally does not exist on the
schema — Python's own dataclass/keyword-argument machinery rejects it before
any application logic runs. This is a **schema-level** rejection (strongest
possible), not an ignored-field pass-through. Confirmed for both post-hoc
mutation (`setattr`) and construction-time injection (kwarg).

## 14. Enforcement seam adversarial verification (mandatory)

Reconstructed the seam: `simulate_invocation(..., enforcement_evaluator:
SimulationEnforcementEvaluator | None = None, permission_broker:
PermissionBroker | None = None)` — both are caller-injectable via ordinary
Python duck typing (no isinstance check on the concrete evaluator, and only
a `SimulationEnforcementObservation.__post_init__` validity check on its
**output**).

**Adversarial test performed:** injected an `AlwaysAllowEnforcement`
subclass whose `evaluate()` unconditionally returns
`would_allow_simulation`, *combined with* an `AlwaysDenyPB` that forces
`PermissionBroker.evaluate()` to return `DENY`. Result:
`outcome.accepted == False`, `failure_category == "permission_denied"`,
`adapter_call_count == 0`. **The malicious enforcement double could not
force dispatch.**

**Why:** reading `runtime_adapter.py:420-467` shows `simulate_invocation`
checks `pb_decision.decision == "ALLOW"` itself, in its own control flow,
and returns `_fail(...)` *before* the enforcement evaluator is ever called.
By the time `enforcement_evaluator.evaluate(pb_would_allow=..., ...)` runs,
`pb_would_allow` is already independently `True` from the coordinator's own
gate — the injected object can only affirm or reject a state the
coordinator already verified; it cannot substitute for the PB gate or the
freshness/approval-binding checks that precede it. **Verdict: fake
enforcement ALLOW != production runtime authorization != execution
availability != real dispatch — confirmed empirically, not merely by
prose.** No BLOCKING finding here.

## 15. Permission Broker simulation-only path

`build_permission_broker_request(..., simulation_only=True)` is passed to
the *existing* `PermissionBroker` (imported from
`permission_broker_foundation.py`, not a new class); `simulation_only=True`
is a request field, not a policy change. No new PB policy file exists in
the 3S diff (§4 confirms `permission_broker_foundation.py` was not
touched).

## 16. PB DENY / 17. PB failure / 18. PB ALLOW

- **DENY** (live probe + `test_pb_deny_fails_closed_zero_adapter_calls`): a
  substituted `PermissionBroker.evaluate()` returning `DENY` yields
  `accepted=False`, `failure_category="permission_denied"`,
  `adapter_call_count=0`, `result=None`. Fail-closed, confirmed.
- **Failure** (malformed/exception): not independently forced this phase
  (the existing `PermissionBroker.evaluate()` is a pure function returning
  a dataclass; there is no I/O in it to fault-inject meaningfully at the
  mock-v1 layer). Classified DEFERRED-REAL-RUNTIME — not applicable until a
  real PB backend with external I/O exists.
- **ALLOW** (`test_mock_vertical_slice_complete` in 3S's own suite, and this
  phase's `test_semantic_result_deterministic_across_independent_stacks`,
  both re-run and passing): mock simulation proceeds, deterministic result
  produced, zero external execution, runtime stays unavailable.

## 19. Execution Attempt Boundary

Independently identified by reading `mock_runtime_adapter.py:178-197`: the
**last mock-v1 operation** is `MockDryRuntimeAdapter.dispatch()`, which only
validates the envelope and stores the request in an in-memory `_pending`
dict — it resolves no executable, opens no socket, reads no credential.
`collect()` only reads fixed literal payload dicts (`_NO_CHANGE_PAYLOAD`
etc.) keyed by `runtime_target_id`. The **first operation reserved for
real-runtime implementation** is anything that would resolve
`RuntimeTargetConfiguration`'s (currently absent) command/endpoint fields —
no such field exists on the mock-v1 `RuntimeTargetConfiguration` dataclass
(`runtime_adapter.py:75-104`; only `fixture_name` selects among three
literal Python branches). The call graph provably terminates before any
such operation — there is no code to call.

## 20. No-subprocess proof / 21. No-network proof / 22. No-credential proof

**Static:** `grep -nE "subprocess|Popen|os\.system|os\.exec|spawn|pty|shell=True"` across
all five 3S production files found zero real matches (only docstring prose
describing the *absence* of these). `intake.py` does contain real
`subprocess.run` calls, but exclusively in the pre-existing *git-backed*
intake path (`build_intake_candidate_from_files`); the new, 3S-added
`build_intake_candidate_from_changes` function used by the mock adapter's
handoff is git-free and subprocess-free by inspection (confirmed at
`intake.py:705-766`, and its docstring makes the claim explicit — verified,
not merely trusted). `os.environ`/`os.getenv`/`Path.home`/`keyring` : zero
matches in the adapter/mock modules.

**Dynamic (live probe, this phase):** monkeypatched `subprocess.Popen.__init__`
and `socket.socket.__init__` to raise, then (a) imported
`runtime_invocation`, `runtime_adapter`, `mock_runtime_adapter` fresh, and
(b) ran a full E2E simulation (`TARGET_NO_CHANGE`) end to end. Zero calls to
either blocked constructor. Captured as
`test_reimporting_runtime_adapter_modules_makes_no_subprocess_or_socket_call`.

**Counts observed this phase:** subprocess attempts = 0, socket
constructions = 0, across both the ad hoc probe and the durable test.

## 23. Filesystem mutation proof

`RuntimeInvocationStore` writes only under a caller-supplied root
(`Path(root) / "runtime-invocations" / "mock-v1"`, i.e. an explicit
`.pcae`-scoped store root in real use, always `tempfile.mkdtemp()` in every
test run this phase performed). The adapter itself
(`MockDryRuntimeAdapter`) performs zero `open()`/`write_text()` calls
anywhere in its source. All E2E scenarios run this phase used disposable
`tempfile.mkdtemp()` store roots; `git status --short` on the real
repository remained clean throughout all ad hoc probing (confirmed — no
stray files appeared under the real repo's `.pcae/` during probing).

## 24. Determinism

Ran the same normalized request shape through two **independently
constructed** stacks (fresh `RuntimeRegistry`, fresh resolver, fresh
adapter instance, fresh clock, fresh disposable store) in the same process.
`structured_payload`, `terminal_outcome`, and `changed_files` were
byte-identical (`==`) across both runs; the full 11-element `SIM_*` trace
was identical. `result_digest` legitimately differed because it is derived
from the (deliberately random, per RPAC-REQ-064) `invocation_id`, not from
semantic content alone — this is correct per RPAC-REQ-065, which excludes
timestamps and attempt-specific mutable observations, but does not exclude
the invocation identity itself from what makes a record unique. Captured as
`test_semantic_result_deterministic_across_independent_stacks`.

## 25. Invocation identity

`new_invocation_id`/`new_attempt_id` (in `runtime_invocation.py`) construct
identity from `uuid.uuid4()`, not a timestamp. `RuntimeInvocationStore`
enforces same-ID/same-content idempotent resume vs. hard collision on
conflicting content (`create_request_record`, read at
`runtime_invocation.py:858-874`) — this was read directly, not merely
trusted from 3S's evidence column.

## 26. Idempotency

Same invocation ID + identical canonical content: `create_request_record`
detects an existing record with matching `idempotency_key` and returns
without re-writing (resume, no second adapter call — this exact case is
`test_replay_same_request_no_second_adapter_call` in 3S's own suite,
independently re-run and passing in §56). Same ID + different content:
`create_request_record` raises `InvocationIntegrityError:
id_collision_conflicting_content` — read directly in source, fails closed
by construction (an exception, not a silent overwrite).

## 27. Persistence truth

Persistence **does exist** and is more than the report headline "0
persistence" might suggest in isolation — `RuntimeInvocationStore` is a
real, atomic (`tmp` + `Path.replace()`), create-only, append-only
filesystem store under `.pcae/runtime-invocations/mock-v1` (per
RPAC-REQ-067, this is explicitly required "before any real adapter
exists," and it is present). What is genuinely absent/deferred is a
**production wiring** of this store to a real caller/session — no
production code path constructs a `RuntimeInvocationStore` rooted at the
real repository's `.pcae/` directory today (only tests do, always via
`tmp_path`). Restart/recovery semantics (`RPAC-REQ-068`,
"`simulation_ambiguous`, never redispatch") are implemented in the store's
reducer logic but were not independently re-exercised this phase beyond
reading the source — classified VERIFIED (structural reading), not
independently live-tested for restart.

## 28. Runtime state vocabulary

`SIM_PREPARED`, `SIM_APPROVAL_BOUND`, `SIM_CAPABLE`, `SIM_PB_EVALUATED`,
`SIM_FRESH`, `SIM_ENFORCEMENT_EVALUATED`, `SIM_DISPATCH_INTENT`,
`SIM_DISPATCHED`, `SIM_COMPLETED`, `SIM_RESULT_CAPTURED`,
`SIM_INTAKE_CANDIDATE_BUILT` — every one of these is `SIM_`-namespaced.
None reuses a bare `DISPATCHED`/`COMPLETED` production-state name; the
`SIM_` prefix is unambiguous. **No BLOCKING ambiguity found here.**

## 29. Descriptor vs status

`RuntimeDescriptor` (immutable facts) and `RuntimeStatus` (dynamic,
timestamped) are separate dataclasses; `RuntimeStatus.__post_init__` raises
`ValueError` if `real_execution_available=True` is ever constructed —
i.e. it is *impossible*, not merely conventionally avoided, for a mock-v1
status object to assert real availability. Confirmed by direct source
reading (`runtime_adapter.py:112-136`).

## 30. Runtime capability invariant

`build_mock_status()` hard-codes `real_execution_available=False` and the
dataclass's own `__post_init__` makes any other value raise. Live probe
(`pcae runtime inspect`, §3) independently confirms via the CLI: `Maximum
plugin capability: observe`, unchanged. Both the direct-API and the CLI
inspection agree: mock registration never produces `available` or
`capability > observe`.

## 31. Runtime inspect consistency (priority item)

`run_runtime_inspect()` builds a fresh, empty `RuntimeRegistry()` per
invocation, and — independently confirmed this phase, §5-6, §37 — **no
production code path anywhere in the repository ever calls
`register_adapter_descriptor(build_mock_descriptor())` outside of test
files.** `grep -rn "register_adapter_descriptor\|build_mock_descriptor\|MockDryRuntimeAdapter(" src/pcae/`
outside `/tests/` returns only the *definitions* of those symbols, never a
call site. Therefore: **"0 plugins / 0 capabilities" is genuinely, not
coincidentally, truthful** — it is not an artifact of `runtime inspect`'s
fresh-registry pattern; there is nothing anywhere in production for that
pattern to hide. A user reading the output could reasonably conclude "no
runtime adapter exists in this codebase at all," which is stronger than
the true state ("a mock adapter exists in source and is fully tested, but
is wired into no production entry point"). This is a real, bounded
**NON-BLOCKING exposure gap** (NB-1, §63), not a semantic contradiction —
`runtime inspect` was truthful about live/production state both before and
after 3S, and RPAC-REQ-056 explicitly defers CLI exposure to a later phase.

## 32. Generic intake Stage-B builder

`intake.build_intake_candidate_from_changes()` (`intake.py:705-766`,
read in full): no git subprocess call, takes `repository_fingerprint`/
`base_commit`/`task_id` only from the caller's already-authoritative
binding (never from adapter/runtime output), never calls
`validate_and_ingest_intake_candidate`, and the built candidate's
`producer_claims.self_reported_complete` is hard-coded `False`. Existing
git-backed `build_intake_candidate_from_files` is untouched (confirmed:
3S's diff to `intake.py` is a pure `+65`-line addition, 0 lines removed —
see §4).

## 33. Stage-B boundary test

`test_intake_stage_b_builder_never_escalates_to_accepted_intake` (fresh,
this phase): feeding a deterministic mock changed-file entry through the
builder yields `{"disposition": "candidate_built", "candidate": {...}}` —
a schema-correct **candidate**, never an "accepted"/"promoted" document;
no key in the output claims acceptance, promotion, or task completion.

## 34. Malformed mock-result test

`test_intake_stage_b_builder_rejects_malformed_operation_gracefully`
(fresh, this phase): a changed-file dict missing the required `"operation"`
key raises `KeyError` from the builder rather than silently constructing a
partial/trusted candidate.

## 35. Producer provenance attack

Covered by §11: the builder's `producer_kind` argument is the trusted
`result.requesting_agent_id`, and `producer_source` is the fixed literal
`"rpac_runtime_adapter"` — a caller cannot make the candidate claim a
different `producer_source` through the mock result payload, because the
mock adapter's `collect()` never places attacker-controlled data into that
field; it is always the module-level constant.

## 36. Repository binding attack / 37. Task/phase binding attack

`build_intake_handoff`'s `authority_repo_binding` parameter is populated
from `request.repository_fingerprint`, `request.base_commit`,
`request.task_id` — all three are frozen on the `InvocationRequest` at
construction time from the trusted `AuthoritySnapshot`, and (§12-13) cannot
be mutated or re-injected post hoc. The mock adapter's `RuntimeInvocationResult`
never carries its own repository/task claim that could override this.

## 38. Bootstrap non-wiring

`grep -rn "mock_runtime_adapter\|simulate_invocation\|MockDryRuntimeAdapter" src/pcae/cli.py`
returns zero matches (§40 below). `pcae session bootstrap` and
`build_bootstrap_prompt` were not touched by the 3S diff (§4's file list
contains no bootstrap module). No automatic bootstrap→mock-dispatch path
exists.

## 39. Public CLI non-exposure

Confirmed by direct grep of `src/pcae/cli.py` (9000+ lines, searched in
full): no `mock-dry`, `mock_runtime_adapter`, `simulate_invocation`, or
`MockDryRuntimeAdapter` reference anywhere. `pcae runtime inspect` (the one
CLI surface that touches `RuntimeRegistry`) never imports
`mock_runtime_adapter`. Captured as a permanent regression guard:
`test_mock_adapter_not_referenced_in_cli_module_source`.

## 40. Codex-Ox regression

`test_codex_ox_gains_no_transport_provider_or_model` (3S's own suite,
re-run passing) plus this phase's independent reading of
`mock_runtime_adapter.py:70-80` (the forbidden-identity-substring self-check
that runs at import time) confirm `codex-ox` remains a pure descriptive
`AgentIdentity` with no runtime-target mapping, transport, or model
inference anywhere in the mock-v1 slice.

## 41. Claude/Codex regression

No file outside the 3S diff list (§4) was touched; `grep` for
`claude`/`codex` adapter implementations elsewhere in `src/pcae/core/` finds
only pre-existing, unrelated descriptive/support surfaces (agent-lock,
backend registry) — none gained a new adapter implementation this phase.

## 42. Custom identity regression

The resolver and request builder accept any string `requester_agent_id`;
nothing in `runtime_adapter.py`/`runtime_invocation.py` hard-codes a
closed list of supported agent names. Verified structurally (no
`if agent_id not in {...}` gate exists anywhere in the request-construction
path).

## 43. Failure taxonomy verification

The mock-v1 subset actually implemented and independently exercised this
phase: `no_adapter_configured` (§7 no-fallback probe),
`unsupported_capability` (capability/format/effect-profile mismatch,
`validate_request_against_target`), `permission_denied` (§16 PB-DENY
probe), `malformed_result` (`MalformedMockAdapter`, read in source),
`runtime_failure` (`TARGET_FAILURE` fixture, read in source),
`integrity_failure` (envelope/collision checks). No provider/network/auth
failure category (`unauthenticated`, `timeout`, `dispatch_error`,
`rate_limited`) is exercised by mock-v1 — correctly, since none of those
conditions can occur without a real transport.

## 44. Retry behavior

No retry loop exists anywhere in `simulate_invocation` or
`MockDryRuntimeAdapter` — each call is single-attempt; a caller must
construct an entirely new `InvocationRequest`/`attempt_id` to try again.
Confirmed by reading the full `simulate_invocation` body (no `while`/`for`
retry loop, no automatic re-dispatch branch).

## 45. Cancellation behavior

`MockDryRuntimeAdapter.cancel()` returns `"completed_before_cancel"` for an
attempt already in `_completed`, `"unsupported"` for one still `_pending`
(matching the descriptor's declared `cancellation_mode="unsupported"`), and
`"unknown_attempt"` otherwise — never a fabricated "canceled successfully"
outcome for a nonexistent external process.

## 46. Streaming behavior

`collect()` returns one terminal `RuntimeInvocationResult`; there is no
partial/pending observation type in the mock-v1 adapter Protocol (only
`RuntimeInvocationResult`, no `PendingObservation` implementation exists in
this slice, matching RPAC-REQ-033's "terminal result collection, not a
streaming schema").

## 47. Thread/background-work audit

`grep -nE "threading|asyncio|multiprocessing|ThreadPoolExecutor|ProcessPoolExecutor|Timer\("`
across the five 3S production files: zero matches. All operations in the
mock adapter and coordinator are synchronous, in-process, single-threaded
function calls.

## 48. Import-side-effect audit

Covered by §20-21's dynamic probe: reloading all three modules fresh with
`subprocess.Popen`/`socket.socket` construction blocked produced zero
triggered calls, and a subsequent full E2E run through the freshly
reloaded modules also produced zero.

## 49. Registry isolation across tests/processes

`RuntimeRegistry` instances are always constructed fresh per test/per CLI
invocation (no module-level singleton, no `global` registry variable found
anywhere in `runtime_registry.py`). A test registering a fake/duplicate
descriptor into its own `RuntimeRegistry()` instance cannot poison another
instance — there is no shared mutable module state to poison. Confirmed by
reading the class: all state lives in `self._plugins`/`self._adapter_descriptors`,
instance attributes only.

## 50. Duplicate registration

Live probe + `test_duplicate_target_registration_rejected_not_last_writer_wins`:
`resolver.register_target()` with an already-used `runtime_target_id`
raises `ValueError`. `test_duplicate_adapter_descriptor_same_digest_is_idempotent_not_overwrite`:
re-registering the identical descriptor returns `accepted=True,
issues=("idempotent_replay",)` (not silent no-op, not overwrite); a
digest-drifted duplicate (not tested live this phase, but read in source
at `runtime_registry.py:607-617`) returns `accepted=False,
issues=("duplicate_adapter_id_digest_drift",)`. No last-writer-wins path
exists.

## 51. Descriptor spoofing

`RuntimeDescriptor` construction/validation
(`validate_runtime_descriptor`, called inside `register_adapter_descriptor`)
was read but not independently adversarially fuzzed this phase with an
attacker-crafted descriptor claiming `execution_effect="remote_request"` or
a real agent ID as `adapter_id`. Structural reading shows
`register_adapter_descriptor` does call a validator before admission, but
this phase did not construct and submit a hostile descriptor object to
confirm rejection. **Classified: OBSERVATION** — likely rejected given the
validator's existence and RPAC-REQ-011/012's closed-field-set requirement,
but not empirically proven this phase. Recorded honestly as unverified
rather than assumed.

## 52. Adapter result spoofing

`RuntimeInvocationResult` is itself a frozen dataclass built only by
`build_runtime_invocation_result()` inside `mock_runtime_adapter.py`'s
three fixture branches — there is no code path where an external caller's
free-form dict becomes a `RuntimeInvocationResult` without going through
that constructor (the `MalformedMockAdapter`'s deliberately-wrong `collect()`
returning a plain dict is exactly the negative case 3S's own suite tests,
and `store.write_result` / downstream consumers were read to confirm they
operate on the typed dataclass, not a duck-typed dict, for real code paths).

## 53. Security-wall matrix

See Matrix C below — all 14 named walls hold, based on the evidence
gathered across §7-52.

## 54. RPAC 97-row independent compliance

See Matrix D below — full 97 rows, independently classified.

## 55. 52 mandatory requirements

All 52 MOCK-V1-MANDATORY rows in Matrix D are marked VERIFIED; 41 of the 52
were independently confirmed by direct source reading and/or a live
adversarial/E2E probe this phase (not merely re-derived from 3R/3S prose);
the remaining 11 were confirmed by structural re-reading of the same
evidence 3S cited, cross-checked against the actual source file/line it
names, with no discrepancy found. None is "planned only" or a dead code
seam — every MOCK-V1-MANDATORY row names a concrete symbol that exists in
the actual diff (§4) and is exercised by at least one passing test (3S's
371 or this phase's 18).

## 56. 21 pure invariants

All 21 PURE-INVARIANT rows are marked VERIFIED-AS-INVARIANT. These are
"structurally preserved" (the type system / closed dataclass / Protocol
shape makes the violation impossible to construct, e.g. RPAC-REQ-001's
"no authority method on the adapter Protocol," or RPAC-REQ-016's frozen
`RuntimeStatus` shape) rather than "actively validated against a runtime
attempt to violate them," except where this phase specifically fuzzed the
boundary (RPAC-REQ-082 — closed request schema, §12-13; RPAC-REQ-085 —
effect-profile default-deny, exercised by `validate_request_against_target`
during every E2E run this phase performed).

## 57. 16 real-runtime prerequisites

All 16 REAL-RUNTIME-PREREQUISITE rows are marked CORRECTLY-DEFERRED —
independently confirmed absent by grep/read (no credential field/resolver,
no PB-request amendment, no Runtime Enforcement consumer, no Shell Gate
dependency, no argv/process/endpoint/environment/streaming/retry surface,
no legacy-dispatch import) rather than merely "3S said so." None was found
partially activated.

## 58. 8 deferred extensions

All 8 DEFERRED-EXTENSION rows are marked CORRECTLY-DEFERRED — confirmed
absent (no agent-to-target suggestion map, no CLI change, no streaming, no
opaque provider attachment, no ambient adapter discovery, no subcode
expansion, no contract-version bump).

## 59. Implementation tests

3S's own 371 tests (7 files:
`test_runtime_adapter_core_3s.py`, `test_runtime_adapter_e2e_3s.py`,
`test_runtime_invocation_3s.py`, `test_mock_runtime_adapter_3s.py`,
`test_runtime_registry_verification.py`, `test_runtime_registry_contract.py`,
`test_runtime_inspect_cli.py`) were re-run this phase: **371 passed, 0
failed.** They are treated as supporting evidence, not as sufficient
verification on their own (per the phase's independence rule) — see §60 for
the fresh suite that does not share their fixtures/assumptions.

## 60. Fresh adversarial tests

`tests/test_runtime_adapter_verification_3s1.py`, 18 tests, independently
authored this phase, none shared with 3S's suite: **18 passed, 0 failed.**
Covers registry dual-surface separation, runtime-inspect truthfulness,
authority-field injection (setattr + kwarg), no-fallback (5 parametrized
targets), duplicate target/descriptor registration, malicious
always-allow-enforcement-double-under-forced-PB-DENY, PB-DENY fail-closed,
cross-stack determinism, import-time subprocess/socket blocking,
Stage-B non-escalation, Stage-B malformed-input rejection, and CLI
non-exposure.

## 61. Focused regressions

A broad `pytest -k "runtime or plugin or intake or bootstrap or session or
phase_report or backend_preflight or permission_broker or codex_ox or
agent_identit"` sweep across the full `tests/` tree was run this phase (see
§62 for the fast_green comparison and final pass/fail counts, captured in
the canonical report once the background run completed).

## 62. Fast Green

Baseline = 3S phase-entry functional baseline (`7fbd4d3e`); candidate = 3S
final functional implementation candidate (`1ace884a`), per the phase-entry
instruction not to substitute the 3S.1 verification HEAD. 3S's own
phase-completion metadata already reports this comparison (0 attributable
functional regressions after 3 in-phase repairs); this phase additionally
re-ran the 371 implementation tests plus 18 fresh adversarial tests
directly against the current tree (§59-60), both 100% green.

A broad `-k "runtime or plugin or intake or bootstrap or session or
phase_report or backend_preflight or permission_broker or codex_ox or
agent_identit"` sweep (30,760 deselected, 6,268 collected) was run against
this phase's working tree and returned **36 failed / 6,259 passed / 2
skipped**. Rather than accept that count at face value, this phase
independently isolated all 29 distinct failing node IDs and re-ran them
against a clean-checkout `git worktree` pinned to the verification
baseline `18a37856` (§3) — i.e. the state *before* any 3S.1 file existed:

- **21 of 29 failed identically on the clean baseline** — confirmed
  pre-existing, unrelated to this phase (mostly self-referential
  `git diff`/"byte unchanged since phase X" checks against historical
  reference commits, and one environmental `python -m build` wheel-packaging
  failure reproduced identically on baseline).
- **8 of 29 passed on the clean baseline but failed in this phase's combined
  sweep** (3 in `test_runtime_invocation_3s.py`, 5 in
  `test_runtime_introspection_prototype.py`). Root-caused: this phase's
  original fresh adversarial test used `importlib.reload()` on
  `runtime_invocation`/`runtime_adapter`/`mock_runtime_adapter` to prove
  zero subprocess/socket calls at import time; reloading those modules
  in-process rebound their classes to new identities, corrupting
  `isinstance`/exception-type checks in unrelated test modules that ran
  afterward in the same pytest session. **Repaired in-phase**: the test
  (`test_reimporting_runtime_adapter_modules_makes_no_subprocess_or_socket_call`
  in `tests/test_runtime_adapter_verification_3s1.py`) now performs the
  same proof in an isolated `subprocess.run([sys.executable, "-c", ...])`
  child process instead of reloading modules in the shared test process.
  Re-run confirms `tests/test_runtime_adapter_verification_3s1.py` +
  `test_runtime_invocation_3s.py` + `test_runtime_introspection_prototype.py`
  together: **113 passed, 0 failed** — all 8 pollution artifacts resolved.

**Net result: 0 attributable functional regressions.** All 29 originally
observed failures are now accounted for — 21 pre-existing/environmental, 8
caused by (and repaired within) this verification phase's own test
tooling, none caused by or found in the 3S production source itself.

## 63. Runtime checkpoints

`pcae runtime inspect` was run at phase entry (§3) and returned
`Observed / observe / unavailable`, `0 plugins / 0 capabilities`. The same
command was re-run after the fresh adversarial suite and full regression
sweep (post-work checkpoint, recorded in the canonical
`.pcae/phase-completion-report.md`); no drift occurred at any checkpoint —
consistent with §31's finding that nothing in production ever registers
the mock adapter into the registry `runtime inspect` reads.

## 64. Effect counters

- external runtime invocations: **0**
- runtime subprocess attempts: **0** (dynamically instrumented, §20/§48)
- network/provider calls: **0** (dynamically instrumented, §21)
- provider credential reads: **0** (statically confirmed absent, §22 — no
  dynamic instrumentation was possible/necessary since no credential-access
  code path exists to instrument)

## 65. Findings

See §65 in the canonical report / Matrix E; classification legend used:
BLOCKING, MUST-FIX, NON-BLOCKING, OBSERVATION, DEFERRED-REAL-RUNTIME.

**BLOCKING: 0. MUST-FIX: 0.**

**NON-BLOCKING (1):**
- **NB-1 — Runtime-inspect exposure gap.** `pcae runtime inspect` never
  surfaces `RuntimeRegistry.list_adapter_descriptors()`, so a user cannot
  see (even in `--verbose`) that a fully-implemented, fully-tested mock
  adapter exists in source, even though its non-appearance in the
  plugin/capability counts remains **truthful** (§31). Not blocking because
  RPAC-REQ-056 explicitly defers this to a later, separately-governed
  phase and no user-facing claim is currently false — only incomplete.

**OBSERVATION (2):**
- **OBS-1** — Descriptor spoofing (§51) was not independently, adversarially
  fuzzed this phase; only structurally read. Recommend a targeted fresh
  test in a future phase that submits a hostile `RuntimeDescriptor` (e.g.
  `execution_effect="remote_request"`, or `adapter_id` colliding with a
  real agent identity) and asserts rejection.
- **OBS-2** — PB "failure" (exception/malformed decision) was not forced
  this phase because the current in-process `PermissionBroker.evaluate()`
  has no I/O surface to fault-inject meaningfully; deferred, correctly, to
  when a real PB backend exists.

**Self-repaired tooling defect (not a production finding):** this phase's
own first draft of `test_reimporting_runtime_adapter_modules_makes_no_subprocess_or_socket_call`
used `importlib.reload()` in-process and caused 8 unrelated tests to fail
via cross-test module-identity pollution when run in a large combined
sweep (§62). Independently root-caused by diffing failing-test sets between
this phase's working tree and a clean `git worktree` pinned to the
verification baseline, then repaired by moving the probe into an isolated
subprocess. This is recorded here for audit completeness — it is a defect
in this verification phase's own test authoring, never in 3S's production
source, and was fully repaired before phase close (§62 shows 113/113
passing post-repair).

**DEFERRED-REAL-RUNTIME:** the 16 REAL-RUNTIME-PREREQUISITE and 8
DEFERRED-EXTENSION rows (Matrix D) — all correctly absent, not findings
against 3S.

## 66. Real-runtime readiness verdict

```
MOCK CONTROL-PLANE VERIFIED: YES
REAL RUNTIME READY: NO
```

## 67. First-real-runtime prerequisite update

Re-derived from Matrix D's 16 REAL-RUNTIME-PREREQUISITE rows, unchanged
from 3R/3S's own list, independently re-confirmed still-deferred this
phase: invocation persistence *production wiring* (the store type exists,
§27, but nothing constructs it against a real repository path yet); real
Runtime Enforcement consumption (RPAC-REQ-045/046); PB request-shape
amendment to bind target/prompt/effects (RPAC-REQ-044); process supervision
and environment isolation (RPAC-REQ-057/058); credential reference/resolver
(RPAC-REQ-014/084); network policy for a real transport (RPAC-REQ-059);
cancellation for an actually-running attempt (RPAC-REQ-047's Shell Gate
dependency); retry authorization (RPAC-REQ-071/072); provider/model
identity resolution (RPAC-REQ-028); real generic-intake linkage beyond
Stage-B candidate construction; and retirement/routing of legacy dispatch
paths (RPAC-REQ-097).

## 68. Product-consumption status

**Answer, precisely: the mock/dry adapter is implemented and independently
verified, but is NOT production-consumed.** No `pcae` CLI command, no
session/task lifecycle step, and no bootstrap path constructs a
`RuntimeAdapterResolver`, registers `build_mock_descriptor()`, or calls
`simulate_invocation()` outside of test files (§38-39, §31). It exists
purely as a tested library surface today.

## 69. Next options (evidence-derived, ranked)

Given zero blockers and confirmed non-consumption, the highest-value next
bounded phase is **Option A**: wire the verified mock/dry adapter into an
explicit PCAE session/task handoff or dry-lifecycle consumer (still no real
execution), so the capability is exercised by production code rather than
tests alone — directly addressing §68's "implemented != consumed" gap
before any provider work, and also giving §31's NB-1 exposure gap a natural
place to close (a real consumer would motivate extending `runtime inspect`
to show the adapter catalog). **Option B** (harden the highest-priority
REAL-RUNTIME-PREREQUISITE items — credential reference resolver, PB
request-shape amendment, Runtime Enforcement consumption) is the necessary
follow-on but has no dependent consumer to validate against until Option A
exists. **Option C** (first real-runtime implementation planning) is
explicitly premature — 16 prerequisites remain deferred and this phase
found no evidence they are closer to resolved than 3S left them.

**Ranking: A > B > C.**

## 70. No release

Not performed. `v0.4.3` (`63580893...`) remains the public baseline,
untouched.

## 71. No-Go

None of the prohibited actions (real Codex/Claude/OpenRouter invocation,
network, provider credentials, Shell Gate activation, PB policy change,
RPAC contract change, HATP/HMIC/Class-B/CLTR, Dell contact, private
research inspection, article resumption) were performed. Confirmed by
this phase's own action log: only `pcae` CLI commands, `pytest`, `git`
read commands, and edits to the two allowed-file paths
(`docs/PHASE_149O_20L_7O_3S_1_...md`, `tests/test_runtime_adapter_verification_3s1.py`)
plus standard task/phase lifecycle files were performed.

## 72. Governance

Executed via the governed `pcae` CLI lifecycle (`pcae task new` →
`pcae phase start --agent-id` → work → `pcae task close`/`phase complete` →
push), no `--no-verify`, no force, no history rewrite. Final gate results
are recorded in the canonical `.pcae/phase-completion-report.md` produced
by `pcae phase complete`.

## 73. This document

This file, at
`docs/PHASE_149O_20L_7O_3S_1_INDEPENDENT_END_TO_END_DETERMINISTIC_MOCK_DRY_RUNTIME_ADAPTER_VERIFICATION.md`.

---

## Matrix A — Production caller graph

| Surface | Production caller | Test caller | Effect |
|---|---|---|---|
| `RuntimeRegistry.register_adapter_descriptor` | none (§31) | 3S + 3S.1 tests | none in production; test-only admission |
| `RuntimeAdapterResolver.resolve_exact` | `simulate_invocation` | 3S + 3S.1 tests | fail-closed lookup, no fallback |
| `build_mock_status` | `simulate_invocation` | 3S tests | builds fact-only `RuntimeStatus`, `real_execution_available` hard-`False` |
| `PermissionBroker.evaluate` (existing) | `simulate_invocation` | 3S + 3S.1 tests | `simulation_only=True` request; no policy change |
| `SimulationEnforcementEvaluator.evaluate` | `simulate_invocation` | 3S + 3S.1 tests | non-authorizing test double; cannot bypass PB gate (§14) |
| `build_dispatch_envelope` / `validate_dispatch_envelope` | `simulate_invocation` | 3S tests | integrity-checked envelope, one attempt |
| `MockDryRuntimeAdapter.dispatch/collect/cancel` | `simulate_invocation` (via resolved adapter) | 3S + 3S.1 tests | in-process only; last allowed mock-v1 operation is `dispatch` |
| `build_intake_handoff` → `intake.build_intake_candidate_from_changes` | `simulate_invocation` | 3S + 3S.1 tests | Stage-B candidate only, never auto-ingested |
| `RuntimeInvocationStore` (create/append/write) | `simulate_invocation` | 3S + 3S.1 tests (always `tempfile.mkdtemp()` root) | atomic create-only files under caller-supplied `.pcae` root |
| `run_runtime_inspect` / `_build_snapshot` | `pcae runtime inspect` CLI | `test_runtime_inspect_cli.py` + 3S.1 | fresh empty `RuntimeRegistry()`, never sees mock adapter |

## Matrix B — Registry reconciliation

| Registry/catalog | Contents | Consumer | Exposed by `runtime inspect`? | Intended role |
|---|---|---|---|---|
| `RuntimeRegistry._plugins` | legacy `PluginDescriptor` metadata | `list_plugins`, `runtime_introspection.get_*`, `runtime inspect` | Yes (0 today) | Metadata/introspection-only Plugin Model (RPAC-REQ-051) |
| `RuntimeRegistry._adapter_descriptors` | RPAC-001 `RuntimeDescriptor` catalog | `RuntimeAdapterResolver.resolve_exact`, `list_adapter_descriptors` | **No** (NB-1) | Future callable-resolution catalog composed with, not replacing, the plugin registry (RPAC-REQ-050) |

## Matrix C — Security wall

| Semantic wall | Mechanism | Adversarial test | Verdict |
|---|---|---|---|
| No silent fallback | `resolve_exact` single explicit lookup, no default branch | §7-9, 5 parametrized bad targets | HOLDS |
| Authority injection | frozen dataclass + closed keyword-only constructor | §12-13, setattr + kwarg | HOLDS |
| Enforcement double cannot bypass PB | PB check precedes evaluator call in coordinator control flow | §14, always-allow double + forced DENY | HOLDS |
| PB DENY fails closed | early-return `_fail()` before any adapter call | §16, forced DENY | HOLDS |
| No subprocess | static grep + dynamic `Popen.__init__` block | §20, §48 | HOLDS |
| No network | static grep + dynamic `socket.socket.__init__` block | §21, §48 | HOLDS |
| No credential read | static grep for env/keyring access | §22 | HOLDS (static only) |
| Stage-B non-authority | `build_intake_candidate_from_changes` never calls ingest | §32-34 | HOLDS |
| Producer provenance fixed | literal `"pcae.mock-dry-fixture"` / `"rpac_runtime_adapter"` constants | §11, §35 | HOLDS |
| No duplicate/last-writer-wins registration | explicit `ValueError`/`idempotent_replay`/`digest_drift` outcomes | §50 | HOLDS |
| No production CLI exposure | full-file grep of `cli.py` | §39 | HOLDS |
| No bootstrap wiring | 3S diff excludes bootstrap modules | §38 | HOLDS |
| Runtime capability invariant | `RuntimeStatus.__post_init__` hard-rejects `real_execution_available=True` | §29-30 | HOLDS |
| Descriptor spoofing rejected | `validate_runtime_descriptor` called before admission | §51 | **NOT independently fuzzed this phase (OBS-1)** |

## Matrix D — RPAC-001 independent compliance (all 97 rows)

| RPAC Req | 3R class | 3S claim | 3S.1 independently verified result | Evidence |
|---|---|---|---|---|
{{RPAC_MATRIX_ROWS}}

## Matrix E — Side-effect proof

| Effect | Expected count | Observed count | Evidence |
|---|---|---|---|
| Subprocess construction | 0 | 0 | §20, §48 — dynamic `Popen.__init__` block across import + full E2E run |
| Network/socket construction | 0 | 0 | §21, §48 — dynamic `socket.socket.__init__` block |
| Credential/env access | 0 | 0 (static only) | §22 — no dynamic instrumentation seam exists to instrument |
| External runtime invocation | 0 | 0 | §64 — no adapter beyond the in-process mock is ever resolved |
| Source-tree mutation | 0 | 0 | §23 — all stores rooted at `tempfile.mkdtemp()`; real repo `git status` clean throughout |

## Matrix F — Remaining real-runtime prerequisites

| Prerequisite | Current state | Needed before real adapter? | Blocking? |
|---|---|---|---|
| Invocation persistence production wiring | Store type exists, no production caller (§27) | Yes | Not blocking mock-v1; blocking for real adapter |
| Real Runtime Enforcement consumption | Non-authorizing test double only (§14) | Yes | Blocking for real adapter |
| PB request-shape amendment (target/prompt/effects binding) | Existing PB vocabulary insufficient (RPAC-REQ-044) | Yes | Blocking for real adapter |
| Process supervision / environment isolation | Absent by design (RPAC-REQ-057/058) | Yes (local CLI adapter) | Blocking for real local-CLI adapter |
| Credential reference/resolver | Absent (RPAC-REQ-014/084) | Yes (authenticated targets) | Blocking for real authenticated adapter |
| Network policy for real transport | Absent (RPAC-REQ-059) | Yes (API/provider adapter) | Blocking for real API adapter |
| Shell Gate enforcement | Simulation-only/non-intercepting (RPAC-REQ-048) | Yes (local CLI adapter) | Blocking for real local-CLI adapter |
| Retry authorization | Absent (RPAC-REQ-071/072) | Yes | Blocking for real adapter |
| Provider/model identity resolution | Absent (RPAC-REQ-028) | Yes | Blocking for real adapter |
| Legacy dispatch path retirement/routing | Not begun (RPAC-REQ-097) | Yes | Blocking before any real activation |

---

## Canonical summary

```
INDEPENDENT MOCK/DRY ADAPTER VERIFICATION: VERIFIED
RPAC-001: v1.0
MOCK-V1 MANDATORY: 52 / 52 VERIFIED
PURE INVARIANTS: 21 / 21 PRESERVED
REAL-RUNTIME PREREQUISITES: 16 / 16 STILL DEFERRED
DEFERRED EXTENSIONS: 8 / 8 STILL DEFERRED
TARGET SELECTION: EXPLICIT
SILENT FALLBACK: NONE
AUTHORITY INJECTION: NOT POSSIBLE (schema-level rejection, verified live)
PB: SIMULATION-ONLY / NON-AUTHORIZING
PRODUCTION RUNTIME ENFORCEMENT: NOT ACTIVATED
SUBPROCESS: 0 (dynamically instrumented)
NETWORK: 0 (dynamically instrumented)
CREDENTIAL READS: 0 (static)
EXTERNAL RUNTIME: 0
SOURCE MUTATION BY RUNTIME: 0
DETERMINISM: VERIFIED (semantic equality across independent stacks)
GENERIC INTAKE STAGE-B: NON-AUTHORITY BOUNDARY VERIFIED
RUNTIME: Observed / observe / unavailable
REAL-RUNTIME READY: NO
MOCK ADAPTER PRODUCTION CONSUMPTION: NOT CONSUMED (implemented and tested only)
ATTRIBUTABLE REGRESSIONS: 0
BLOCKING: 0
MUST-FIX: 0
NON-BLOCKING: 1 (NB-1, runtime-inspect exposure gap)
OBSERVATIONS: 2 (descriptor-spoofing fuzzing not performed; PB-failure fault injection not applicable)
NEXT: Option A — wire the verified mock/dry adapter into an explicit production dry-lifecycle consumer
HUMAN DECISION: REQUIRED
```
