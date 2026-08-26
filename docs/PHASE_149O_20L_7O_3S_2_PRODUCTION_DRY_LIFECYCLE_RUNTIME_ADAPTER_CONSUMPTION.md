# Phase 149O.20L.7O.3S.2: Production Dry-Lifecycle Runtime Adapter Consumption

## Objective

Close the "implemented, verified, NOT production-consumed" gap identified
by Phase 149O.20L.7O.3S.1 by wiring the verified RPAC-001 v1.0 mock/dry
adapter into exactly one explicit, narrow production consumer, without
enabling real execution. Human-approved: Option A (149O.20L.7O.3K).

## Baseline

- Phase-entry HEAD = `origin/main` = `74a36dd060c60fd2b3c986fe0e682271d865bb8a`
- `v0.4.3` tag = `63580893b1de4782a694ab802ff7bdebdf29b0e6` (unchanged throughout)
- Repository clean, 0 commits ahead of `origin/main` at entry
- `pcae health`/`check`/`status coherence`/`push check`: healthy/passed/coherent/clean
- `pcae runtime inspect`: `Observed` / `observe` / `unavailable`, registry
  empty, 0 plugins, 0 capabilities
- `pcae doctor task-memory`: only pre-existing `tasks/DONE.md` sync
  warnings (historical debt, not attributable to this phase)
- Telegram notification runtime: configured, enabled, ready

## 3S/3S.1 verified state

Phase 3S implemented the RPAC-001 mock-v1 vertical slice
(`src/pcae/core/runtime_registry.py`, `runtime_adapter.py`,
`runtime_invocation.py`, `mock_runtime_adapter.py`, `intake.py`). Phase
3S.1 independently re-verified all 97 RPAC-001 requirements (52
MOCK-V1-MANDATORY, 21 PURE-INVARIANT, 16 REAL-RUNTIME-PREREQUISITE, 8
DEFERRED-EXTENSION) and confirmed the adapter was implemented, verified,
and **not production-consumed** — its only callers were test modules.

## Pre-consumption proof

`grep -rn "simulate_invocation" src/ tests/` at phase entry returned
matches only in `runtime_adapter.py` (the definition/docstring) and two
test modules (`test_runtime_adapter_e2e_3s.py`,
`test_runtime_adapter_verification_3s1.py`).

**PRE-3S.2 PRODUCTION CONSUMERS: 0**

## Consumer selection

Selected: `pcae session bootstrap --compact` — specifically its existing
`build_bootstrap_prompt()` call in
`pcae.commands.session._run_compact_bootstrap`.

Selection criteria satisfied:

- Already has authoritative repository/task/session context
  (`build_context_pack`, `find_latest_active_task`).
- Already produces prompt/instructions (`build_bootstrap_prompt`) — reused
  unmodified as the RPAC `PromptArtifact` content source (RPAC-REQ-020,
  spec Section 9).
- Human can explicitly request dry-runtime behavior via new
  `--dry-runtime --runtime-target <id>` flags; absent both, behavior is
  byte-for-byte unchanged.
- No automatic execution: `--compact` was already read-only/no-lock; the
  dry path adds only a simulation-only RPAC invocation, not any wider
  authority.
- Minimal source change: one new core module
  (`runtime_dry_consumption.py`), two new CLI flags, one new branch in
  `_run_compact_bootstrap`.
- Independently testable: isolated `tmp_path` git fixtures exercise the
  full production construction path without touching the real repository.

## Rejected consumer alternatives

- **Full (non-compact) `session bootstrap --agent-id`**: acquires an
  agent lock and mutates governance state (`agent-locks/latest.json`,
  provenance events) as a side effect of every invocation. Adding a dry
  path here would conflate lock acquisition with simulation intent —
  rejected as a wider, less explicit seam than `--compact`.
- **`pcae phase handoff` / `phase start`**: phase-lifecycle commands
  already have wide side effects (task-lifecycle transitions, report
  writes) unrelated to invoking a runtime; wiring RPAC there would risk
  conflating phase-completion authority with dry-runtime intent.
- **A new standalone `pcae runtime dry-invoke` command**: rejected as
  unnecessary new public surface (spec Section 34 "minimize new public
  surface") when an existing, already-governed prompt-producing seam
  (`--compact`) satisfies every selection criterion.

## Human boundary

`--dry-runtime` and `--runtime-target` are both required together; neither
is inferred from task creation, phase start, or ordinary bootstrap. A
human must type both flags in one explicit invocation for any RPAC request
to be constructed at all.

## Explicit target selection

`runtime_target_id` must exactly match one of the three known mock-v1
fixture IDs (`mock-dry.no-change.v1`, `mock-dry.synthetic-change.v1`,
`mock-dry.failure.v1`, from `KNOWN_MOCK_TARGET_FIXTURES`). No default, no
first-registered-adapter fallback, no environment-derived target. Missing
or unknown target both fail closed with an explicit CLI error and exit
code 1; the ordinary prompt-only path is never silently substituted.

## Agent/runtime separation

`agent_id` (from `--agent-id`, defaulting to the descriptive string
`"unspecified"` when omitted) is carried only as `AgentIdentity`
(`requester_agent_id` on `InvocationRequest`). It never selects a target,
provider, or model. `codex-ox` receives no special-cased handling anywhere
in `runtime_dry_consumption.py`; `provider_id`/`model_id` remain `None`
for every agent identity, verified by
`test_codex_ox_gains_no_provider_or_model_inference` and
`test_custom_agent_identity_same_semantic_output` (byte-identical
`structured_payload`/`payload_digest` across `codex-ox` and an arbitrary
custom identity).

## Prompt source

The compact bootstrap prompt (`build_bootstrap_prompt(pack, profile,
handoff=handoff, audit=audit, prompt=prompt_meta)`) is passed unmodified
as `prompt_content` into `run_production_dry_invocation`, which wraps it
in a `PromptArtifact` via the existing, unmodified
`build_prompt_artifact()`. No new prompt-generation subsystem was added.

## Invocation request

`runtime_dry_consumption.resolve_dry_consumer_context()` derives the
`AuthoritySnapshot` from PCAE-owned state only:

- `base_commit` via the existing `pcae.core.intake.current_head_commit()`
  (the same git-HEAD subprocess PCAE already runs for push-check/intake —
  not a new "runtime dispatch" subprocess surface);
- `repository_fingerprint` via the existing
  `pcae.core.intake.compute_repo_fingerprint()`;
- `task_id` via the existing `pcae.core.tasks.find_latest_active_task()`;
- `task_contract_digest` computed as `sha256(active_task.path.read_text())`.

No field is ever accepted from CLI/user payload except `agent_id`,
`runtime_target_id`, and `prompt_content`. Absence of an active task fails
closed with `UnknownRuntimeTargetError` rather than binding to a
best-effort/partial authority.

## Governance semantics

`run_production_dry_invocation` → `_run_with_context` builds the
`RuntimeAdapterResolver`/`RuntimeRegistry`/`MockDryRuntimeAdapter` stack
exactly as the existing 3S/3S.1 tests do, then calls the existing,
**unmodified** `simulate_invocation()` coordinator with its default
(internal) `PermissionBroker()` and `SimulationEnforcementEvaluator()` —
both already `simulation_only=True`. No PB policy or Runtime Enforcement
model was touched.

## PB simulation-only

Unchanged: `simulate_invocation` builds its PB request with
`simulation_only=True` via `build_permission_broker_request`, exactly as
in 3S/3S.1.

## Runtime Enforcement

Not activated as real authority. `simulate_invocation`'s internal
`SimulationEnforcementEvaluator` remains the only enforcement seam
touched; it is explicitly `non_authorizing=True` and never mints
`AUTHORIZED`.

## Enforcement-injection safety

`run_production_dry_invocation`'s signature is
`(root, agent_id, runtime_target_id, prompt_content)` — no
`enforcement_evaluator` or `permission_broker` parameter exists on the
production-facing function, so no caller (CLI or otherwise) can inject a
permissive double into the production path. Verified structurally by
`test_production_entry_point_accepts_no_injected_authority`. Adversarial
injection is exercised only in test-only code
(`_build_production_shaped_request` + a `PermissionBroker` subclass) that
never executes inside the production entry point.

## Execution Attempt Boundary

- **LAST MOCK/DRY OPERATION**: `MockDryRuntimeAdapter.collect()` (in-process
  fixture normalization; `execution_effect` stays `none`)
- **FIRST REAL-RUNTIME OPERATION** (prohibited, never called): any
  subprocess spawn, socket/HTTP call, or credential read for an actual
  runtime target — none exists in this module or its call graph.

## Production invocation call graph

See Matrix A below. `commands/session.py` calls
`runtime_dry_consumption.run_production_dry_invocation()` only; it never
imports `MockDryRuntimeAdapter`, `simulate_invocation`, or
`RuntimeAdapterResolver` directly (verified by
`test_cli_module_has_no_direct_adapter_business_logic` and grep over
`commands/session.py`).

## Result handling

The CLI renders `outcome.result.terminal_outcome`,
`outcome.result.structured_payload`, `outcome.failure_category`, and
`outcome.trace` — narrow, structured surfacing. No task-completion or
accepted-intake claim is made anywhere in the dry path; the CLI always
labels output "SIMULATION ONLY".

## Generic intake boundary

`simulate_invocation` still builds its existing Stage-B
`intake-handoff.json` evidence document via `build_intake_handoff()`
(unchanged), written under the invocation's own controlled store
directory. Nothing in the CLI/service layer calls
`validate_and_ingest_intake_candidate`; no `.pcae/intake-candidates/`
directory is created by this phase (same invariant 3S's own tests already
established, unchanged here).

## Product-visible output

Text mode prints: requested runtime target, descriptive agent identity,
`Simulation accepted`, `Final state`, terminal outcome labeled
"(SIMULATION ONLY)", structured payload, "External runtime invoked: no",
"Real execution: none (simulation only)", "Execution availability:
unavailable". JSON mode carries the equivalent fields plus
`simulation_only: true`, `external_runtime_invoked: false`,
`execution_availability: "unavailable"`.

## Registry/introspection reconciliation

`pcae runtime inspect` output is **unchanged** by this phase
(`test_runtime_inspect_unchanged_after_dry_consumption`,
`test_run_with_context_zero_subprocess_network`'s stack never touches the
global runtime-inspect code path). `RuntimeRegistry()` is constructed
fresh, in-process, per dry invocation and discarded — no production module
registers the mock descriptor into any registry `pcae runtime inspect`
itself reads. 0 plugins / 0 capabilities remains truthful: production
consumption of the *mock/dry* adapter is orthogonal to the *legacy
plugin/backend registry* `runtime inspect` reports on (RPAC-001 §11 keeps
these namespaces distinct by design). No `runtime inspect` change was
needed or made.

## Failure behavior

- Unknown target → CLI error, exit 1, no fallback, no RPAC construction
  attempted (context/prompt/request never built).
- No active task → `UnknownRuntimeTargetError("no_active_task_authority")`,
  same explicit-failure CLI rendering.
- PB DENY (test-only, via a real `PermissionBroker` subclass exercising
  the production-shaped request) → `simulate_invocation` returns
  `accepted=False`, `failure_category="permission_denied"`,
  `adapter_call_count=0`.
- Malformed/invalid request → `UnknownRuntimeTargetError("invalid_request:...")`.

## No fallback

Confirmed at both layers: the CLI never reverts to the ordinary
prompt-only rendering after a `--dry-runtime` failure
(`test_unknown_runtime_target_fails_closed_no_fallback` asserts the
prompt-only marker string is absent from failure output), and
`RuntimeAdapterResolver.resolve_exact` (unmodified from 3S) has no
priority/provider/model/agent-name fallback.

## Determinism

`test_custom_agent_identity_same_semantic_output` proves byte-identical
`structured_payload`/`payload_digest` across two independently
constructed stacks differing only in `agent_id`. The only wall-clock read
in the new module (`_utc_clock`) feeds solely non-semantic timestamp
fields already excluded from the idempotency/payload digest by
`InvocationRequest.canonical_projection()` and
`RuntimeInvocationResult.payload_digest` (unchanged from 3S).

## Idempotency

Unchanged: `RuntimeInvocationStore.create_request_record` (untouched)
still enforces same-ID/same-content resume vs. hard collision per
RPAC-REQ-066; this phase does not alter that logic.

## Source mutation

0. `MockDryRuntimeAdapter` still performs no filesystem writes of its own;
all persistence remains inside `RuntimeInvocationStore`'s controlled
`.pcae/runtime-invocations/mock-v1/` tree, now added to `.gitignore`
(local evidence store, same pattern as `.pcae/approvals/`). No tracked
source file is ever written by the runtime path.

## No subprocess / No network / No credentials

`test_run_with_context_zero_subprocess_network` monkeypatches
`subprocess.run`/`Popen`/`socket.socket`/`socket.create_connection` to
raise, then runs the full RPAC-consuming phase (`_run_with_context`) with
a manually constructed `DryConsumerContext` — proving the phase that
actually reaches the adapter makes zero such calls, independent of
`resolve_dry_consumer_context`'s separate, legitimate, pre-existing use of
PCAE's own git-HEAD subprocess helper.

## No background execution

No `threading`, `asyncio`, `multiprocessing`, or timer is imported or used
anywhere in `runtime_dry_consumption.py` or the new CLI branch; every call
in the chain is synchronous.

## Normal workflow compatibility

`test_ordinary_compact_bootstrap_unchanged_without_dry_flag` proves
`--compact --json` without `--dry-runtime` produces JSON with no
`dry_runtime` key and creates no store artifact.
`test_dry_runtime_flag_alone_without_compact_is_a_no_op_lock_bootstrap`
proves `--dry-runtime` outside `--compact` has zero effect on the
pre-existing lock-acquiring bootstrap path.

## CLI/API surface

New flags on `pcae session bootstrap`: `--dry-runtime` (store_true),
`--runtime-target RUNTIME_TARGET_ID`. Help text states simulation-only, no
external runtime, no model/provider, no source mutation, execution
availability remains unavailable (see `src/pcae/cli.py`).

## Command-zone architecture

`src/pcae/cli.py` contains only argparse wiring plus target-ID vocabulary
in help strings — no `simulate_invocation(` or `MockDryRuntimeAdapter(`
call. `src/pcae/commands/session.py` calls only
`run_production_dry_invocation()` from the core layer; it never imports
`MockDryRuntimeAdapter`, `RuntimeAdapterResolver`, or
`simulate_invocation` directly. All RPAC construction lives in
`src/pcae/core/runtime_dry_consumption.py`.

## Agent identity regressions

Exercised: `codex`/`codex-ox` (existing 3S/3S.1 suites, unchanged),
`claude-local` is not a runtime-target-selecting identity anywhere in this
module, custom identity (`custom-review-agent-17`) — all produce the same
semantic RPAC outcome; none gains an implicit real runtime.

## Intake regressions

`tests/test_runtime_adapter_e2e_3s.py` and
`tests/test_runtime_adapter_verification_3s1.py` (347 tests across the
full 3S/3S.1/3S.2 runtime-adapter suite set) pass unmodified except the
one intentional, phase-attributable repair below.

## PB regressions

Full `test_permission_broker*.py` + `test_phase_148c7/148c8/148f/148g2*.py`
+ `test_phase_149o_20l_7o_3f*.py` + `test_runtime_enforcement*.py` suite:
1604 passed, 2 pre-existing failures confirmed unrelated by baseline
`git stash` re-run (`test_permission_broker_consumer_scope_inventory`,
`test_actual_git_push_dispatch_site_in_core_agent_remains_unwired` — both
concern `pcae.core.agent`, a file untouched by this phase).

## Runtime Enforcement regressions

Included in the suite run above; 0 attributable failures.

## Runtime/plugin regressions

`test_runtime_plugin_contracts.py`, `test_runtime_registry_contract.py`,
`test_schema_runtime_registry.py`, `test_runtime_registry_verification.py`,
`test_runtime_registry_prototype.py`, `test_runtime_inspect_cli.py`: all
pass.

## Bootstrap/session regressions

`test_bootstrap_todo_consistency.py`,
`test_phase_136ax_lifecycle_bootstrap_reporting_repair.py`,
`test_phase_136ay_lifecycle_bootstrap_independent_verification.py`,
`test_hatp_bootstrap_foundation.py`: pass except 4 pre-existing
`test_bootstrap_todo_consistency.py` failures confirmed unrelated by
baseline re-run (stale `tasks/TODO.md` vs. `PROJECT_STATUS.md`, a
pre-existing condition visible in every bootstrap run this session, not
caused by this phase).

## Task/phase regressions

`pcae health`/`pcae check` pass throughout; task-lifecycle transitions
(close idle → new task → task update) behaved per established convention.

## Successful dry E2E

`test_successful_production_dry_e2e` and the CLI-level
`test_successful_dry_runtime_json_output_is_unambiguous` /
`test_successful_dry_runtime_text_output_states_simulation_only`: full
chain from real git-backed fixture repo through `simulate_invocation` to
product-visible output, `adapter_call_count == 1`, evidence confined to
the controlled store tree.

## PB DENY E2E

`test_pb_deny_e2e_fails_closed_zero_adapter_calls`: production-shaped
request (built via the same construction path as `_run_with_context`)
plus a real `PermissionBroker` subclass forcing `DECISION_DENY` →
`accepted=False`, `failure_category="permission_denied"`,
`adapter_call_count=0`, `SIM_DISPATCH_INTENT` never reached.

## Unknown-target E2E

`test_unknown_target_fails_closed_no_context_derivation` (core) +
`test_unknown_runtime_target_fails_closed_no_fallback` (CLI): explicit
failure, no fallback, no context derivation attempted.

## Authority-spoof E2E

`test_authority_spoofing_fields_rejected_by_existing_guard`: forged
payload with `authorized`/`permission`/`execution_allowed`/`approved`
keys is rejected by the existing, unmodified
`reject_untrusted_request_payload` guard (4/4 rejected).

## Custom-identity E2E

`test_custom_agent_identity_same_semantic_output` (see Agent/runtime
separation above).

## Codex-Ox E2E

`test_codex_ox_gains_no_provider_or_model_inference` +
`test_successful_dry_runtime_json_output_is_unambiguous` (CLI,
`--agent-id codex-ox`): dry simulation succeeds, `provider_id`/`model_id`
remain `None`, no `openrouter` string anywhere in the adapter identity or
JSON output.

## Fast Green

Baseline = phase-entry SHA `74a36dd060c60fd2b3c986fe0e682271d865bb8a`.
Candidate = final functional implementation commit (recorded in the
canonical phase-completion report). `pcae phase fast-green-attribution
--phase-id 149O.20L.7O.3S.2` result and attributable regression count are
recorded in the canonical report's `test_results.fast_green` field.

## Findings

**BLOCKING: 0. MUST-FIX: 0.**

NON-BLOCKING: one phase-attributable, bounded repair to a 3S.1 test
(`test_mock_adapter_not_referenced_in_cli_module_source` →
`test_cli_module_has_no_direct_adapter_business_logic`) whose premise
("mock adapter not yet CLI-exposed") this phase's human-approved
objective intentionally supersedes; the replacement test preserves the
underlying invariant that actually matters (command-zone architecture:
CLI has no adapter business logic) rather than weakening it.

## Real-runtime readiness

**NO.** This phase adds a production *consumer* of the simulation-only
mock adapter; it does not touch any of the 16 REAL-RUNTIME-PREREQUISITE
RPAC-001 requirements.

## Remaining prerequisites (post-3S.2 reassessment)

With production dry-lifecycle consumption now proven end-to-end, the
highest-value next prerequisite is evidence that the *same* consumption
seam's gate ordering survives an actual Runtime Enforcement positive
decision — i.e., replacing `SimulationEnforcementEvaluator` with a real,
bound Runtime Enforcement consumer remains the largest single gap before
any real adapter could be considered, ahead of credential resolution,
process supervision, or Shell Gate activation (all of which still lack an
authorized consumer entirely). See Matrix E.

## Next options

- **Option A (recommended)**: 149O.20L.7O.3S.2.1 — Independent
  End-to-End Production Dry-Lifecycle Runtime Adapter Consumption
  Verification.
- **Option B**: Real-runtime prerequisite contract/hardening (only after
  independent verification).
- **Option C**: First real adapter planning (only if prerequisite
  analysis unexpectedly proves ready — not the case here).

## Final verdict

```text
PRODUCTION DRY-LIFECYCLE CONSUMPTION: IMPLEMENTED
MOCK/DRY ADAPTER: IMPLEMENTED / VERIFIED / PRODUCTION-CONSUMED
PRODUCTION ENTRY POINT: pcae session bootstrap --compact --dry-runtime --runtime-target <id>
TARGET SELECTION: EXPLICIT
NORMAL EXISTING WORKFLOW: UNCHANGED
PB: SIMULATION-ONLY
RUNTIME ENFORCEMENT: NOT ACTIVATED AS REAL AUTHORITY
GENERIC INTAKE: Stage-B evidence handoff only, never submitted/ingested
SUBPROCESS: 0 (RPAC-consuming phase)
NETWORK: 0
CREDENTIAL READS: 0
EXTERNAL RUNTIME: 0
SOURCE MUTATION BY RUNTIME: 0
RUNTIME: Observed / observe / unavailable
REAL-RUNTIME READY: NO
ATTRIBUTABLE REGRESSIONS: 0
BLOCKING: 0
MUST-FIX: 0
NEXT PHASE: 149O.20L.7O.3S.2.1 — Independent End-to-End Production Dry-Lifecycle Runtime Adapter Consumption Verification
HUMAN DECISION: REQUIRED
```

## Human decision required

Whether to authorize 149O.20L.7O.3S.2.1 (independent verification) next.
No further phase begins automatically.

---

## Matrix A — Production consumer call graph

| Entry point | Core/service | RPAC surface | Adapter | Result consumer |
|---|---|---|---|---|
| `pcae session bootstrap --compact --dry-runtime --runtime-target <id>` (`cli.py` → `commands/session.py::_run_compact_bootstrap_dry`) | `core/runtime_dry_consumption.py::run_production_dry_invocation` → `_run_with_context` | `core/runtime_adapter.py::simulate_invocation` (unmodified) via `RuntimeAdapterResolver` | `core/mock_runtime_adapter.py::MockDryRuntimeAdapter` (unmodified) | `commands/session.py` renders `SimulationOutcome` (text/JSON); Stage-B intake-handoff evidence written by `simulate_invocation` itself, never ingested |

## Matrix B — Lifecycle state flow

| Step | Owner | Input | Output | Authority change? | External effect? |
|---|---|---|---|---|---|
| Context derivation | `runtime_dry_consumption.resolve_dry_consumer_context` | real repo/task state | `DryConsumerContext` | No | git HEAD read (existing PCAE subprocess, not runtime dispatch) |
| Prompt/approval/request build | `runtime_dry_consumption._run_with_context` | context, agent_id, target, prompt | `InvocationRequest` | No | none |
| Gate sequence | `simulate_invocation` (unmodified) | request | `SimulationOutcome` | No (simulation-only) | writes to `.pcae/runtime-invocations/mock-v1/` only |
| Adapter dispatch/collect | `MockDryRuntimeAdapter` (unmodified) | `SimulationDispatchEnvelope` | `RuntimeInvocationResult` | No | none (in-process fixture) |
| Rendering | `commands/session.py` | `SimulationOutcome` | text/JSON | No | stdout only |

## Matrix C — Security invariants

| Invariant | Mechanism | E2E result |
|---|---|---|
| No fallback on unknown target | `runtime_target_id not in KNOWN_MOCK_TARGET_FIXTURES` check before any construction | PASS (explicit error, no context derivation) |
| No authority injection | `run_production_dry_invocation` signature has no evaluator/broker parameter; `reject_untrusted_request_payload` unchanged | PASS |
| PB DENY fails closed | real `PermissionBroker` subclass forcing DENY on production-shaped request | PASS (0 adapter calls) |
| Zero subprocess/network in RPAC phase | monkeypatched `subprocess`/`socket` around `_run_with_context` | PASS |
| Source mutation = 0 | evidence confined to `.pcae/runtime-invocations/`, gitignored | PASS |
| Determinism | identical payload/digest across independent stacks with different agent identity | PASS |

## Matrix D — Registry/introspection truth

| Surface | What it reports | What actually exists | Truthful? | Follow-up |
|---|---|---|---|---|
| `pcae runtime inspect` | 0 plugins, 0 capabilities, Observed/observe/unavailable | A production-consumed *simulation-only* mock/dry adapter exists in a separate RPAC catalog namespace, orthogonal to the legacy plugin/backend registry | Yes — the two namespaces are contractually distinct (RPAC-001 §11); `runtime inspect` was never claiming anything about RPAC adapters | None required this phase |

**RUNTIME INSPECT: TRUTHFUL.**

## Matrix E — Remaining real-runtime prerequisites

| RPAC prerequisite | Current state after 3S.2 | Needed before real runtime | Priority |
|---|---|---|---|
| Real Runtime Enforcement consumer | Still evidence-only, zero-consumer; `SimulationEnforcementEvaluator` remains the only seam exercised | Yes | Highest |
| PB dispatch semantics (RPAC-REQ-044 gap) | Unchanged | Yes | High |
| Invocation persistence/recovery under restart | Store exists; restart/ambiguous-outcome handling not exercised by this phase | Yes | Medium |
| Process supervision | Not started | Yes | Medium |
| Environment isolation | Not started | Yes | Medium |
| Shell Gate relationship | Simulation-only, non-intercepting (unchanged) | Yes | Medium |
| Credentials | No general credential-reference/resolution implementation (unchanged) | Yes | Medium |
| Network | Default-denied (unchanged) | Yes | Low (until an API adapter is planned) |
| Cancellation | Descriptor-declared `unsupported` for mock-v1 (unchanged) | Yes | Low |
| Provider/model identity | Absent by design for mock-v1 (unchanged) | Yes | Low (until first real adapter) |
| Real result capture | Not started | Yes | Low (until first real adapter) |
