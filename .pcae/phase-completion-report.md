# Phase 149O.20L.7O.3P Complete — Post-Consumption Runtime / Provider / Trust-Boundary Architecture Reassessment

**Status: completed. Completeness: complete. Human decision required.**

Phase-entry commit:
`83af9b3b1b1485fa3acdf4d6eebcef95f692113e`. Substantive phase commit:
`8b351ebe18277de4963f9b5611b5bc0ea1a0069d`, pushed to `origin/main`.

## Baseline and invariant state

- Public state: `v0.4.3` remains current and resolves to
  `63580893b1de4782a694ab802ff7bdebdf29b0e6`; no publication action.
- Runtime: `not_implemented / Observed / unavailable / observe`.
- Runtime Registry: in-memory metadata only; fresh per inspect command;
  state `empty`; 0 plugins; 0 capabilities; no loader, live resolver, or
  executable target.
- Current executable runtimes: **none in the canonical Runtime Registry**.
  Legacy public CLI paths nevertheless contain real subprocess invocation,
  outside one canonical Runtime/PB/Runtime-Enforcement boundary.
- Execution activation: **NO**.
- Production source modified: **NO**.

## Current identities and Codex-Ox

Current agent identities are available `claude-local`, `codex-local`,
`codex-ox`, `pcae-native`, `kimi-local`, and declared `deepseek-local`,
`gemini-local`, `grok-local`, `perplexity-local`. These are descriptive
session/workload identities, not authenticated runtime authority.

Agent/session identity, producer provenance, runtime/backend identity,
provider identity, model identity, and OS execution principal remain distinct.
Core and backend locks are coordination artifacts and use inconsistent backend
vocabularies; neither authenticates a provider/model/principal.

Codex-Ox classification: first-class available PCAE session/agent identity and
generic producer-intake identity; Codex CLI hint only; no runtime-execution
capability claim, canonical runtime entry, OpenRouter transport, provider/model
authentication, or real target mapping.

## Bootstrap prompt and missing handoff edge

Current production path:

```text
session bootstrap --compact
  -> ContextPack + handoff/audit/prompt metadata + profile
  -> build_bootstrap_prompt(...)
  -> deterministic text on stdout
  -> human copy/paste and external target choice
```

The prompt is not persisted as an immutable approved artifact and the builder is
vendor-neutral. The human copy/paste step currently combines implicit content
approval, target selection, and dispatch. Missing edge: bound prompt artifact ->
explicit approval/target -> capability/auth preflight -> PB permission -> final
Runtime Enforcement -> supervised bridge -> normalized result -> generic intake.

## Current abstractions and gate results

- Backend/provider abstractions: static agent/config/backend registries,
  descriptive locks, backend preflight, legacy backend/adapter contracts,
  deterministic mock, advisory provider, and several separate legacy real
  subprocess command paths. No authenticated canonical provider transport.
- Backend preflight: production and reusable for backend/action/task/prompt/hash/
  file-scope facts; descriptive only, name vocabulary incomplete, no live
  capability/auth/network/invocation semantics, never authorization.
- Plugin model: applicable as metadata/discovery vocabulary only. Runtime
  Registry must not become an arbitrary in-process plugin executor.
- Permission Broker: existing `backend_invocation` and `adapter_invocation`
  vocabulary can express dispatch, and provider/network calls are permission-
  relevant effects. Current request binding and positive execution consumer are
  insufficient; PB governs permission, not capability.
- Runtime Enforcement: designed for execution-attempt evidence and the natural
  future final consumer, but current contracts are design-only, negative-only,
  non-authorizing, and have no production dispatch consumer. It remains dormant.
- Execution Attempt Boundary: today proves refusal; backend/adapter/subprocess/
  shell/network requests are denial reasons. Future order is human approval ->
  capability/config/auth facts -> PB effect permission -> Runtime Enforcement
  final conjunction -> atomic dispatch. Capability is not authority.
- Human approval: explicit prompt-content and selected-target approval is
  required initially. Current copy/paste is an implicit, non-durable boundary.
- Dispatch permission: separately required through PCAE governance; human
  content approval does not grant it.

## Runtime, process, trust, and return requirements

- Secrets/network: opaque credential references, environment allowlist,
  authenticated account/endpoint/model binding, redaction, explicit network
  permission and egress allowlist. None exists end-to-end today.
- Process supervision: fixed argv/cwd, process-group/tree ownership, signals,
  graceful/forced cancellation, timeout, stream framing/caps, exit/crash/
  detached-child handling, durable restart reconciliation.
- Sandbox/confinement: existing git worktree is workspace isolation only;
  `network_isolation=false`, `process_isolation=false`, shared git objects,
  and `production_containment_ready=false`. OS filesystem/process/network
  confinement is required for real local CLI execution.
- Output/result: normalized envelope binding invocation/attempt, target/runtime/
  adapter/provider/model, prompt/task/repo/base commit, time/status, bounded
  output refs/hashes, patch/files, usage/cost, sandbox/network profiles,
  provenance, partial/ambiguous state, and intake reference.
- Generic intake: reusable producer-neutral return path. Runtime output is
  untrusted; successful completion is not intake acceptance, and accepted intake
  is not promotion.
- Retry/idempotency: stable logical key and new attempt IDs; bounded attempts/
  cost/time; no automatic replay after dispatch may have occurred; restart
  reconciles records rather than blindly re-invoking.
- Invocation record: required, append-only, secret-free, and bound to prompt,
  task/repo, target, approval, PB/enforcement, policy profiles, attempts,
  provider/process IDs, results, usage, and intake.
- Audit/explainability: must link prepared prompt, approval, selection,
  capability/preflight, PB, enforcement, dispatch, result, and intake and answer
  why/what/who/which-policy/what-happened questions without hiding ambiguity.

## Closed-loop architecture

```text
PCAE task/session
  -> governed context + immutable prompt
  -> explicit human approval + target
  -> capability/config/auth preflight
  -> Permission Broker + Runtime Enforcement
  -> trusted atomic invocation boundary + durable record
  -> replaceable external runtime bridge
  -> quarantined normalized result
  -> generic producer-neutral intake
  -> existing review/governance/promotion
```

Recommended responsibility split: trusted PCAE kernel owns identity/bindings,
selection, permission, final enforcement, state, audit, quarantine, and intake
linkage. A runtime target is declarative. A bridge owns only fixed CLI/API
transport, provider-specific authentication injection, streaming/cancellation
mapping, and result normalization; it cannot approve itself or promote output.

## Trust-gap matrix

| Threat/Concern | Existing PCAE control | Missing control | Required before real execution? |
|---|---|---|---|
| Prompt injection | Deterministic prompt, task scope, human view | Immutable approval and least-privilege context | Yes |
| Malicious output | Generic intake and separate promotion | Quarantine plus invocation-result binding | Yes |
| Filesystem mutation | Scope/worktree/post-hoc diff | OS confinement/pre-effect control | Yes |
| Shell escape | Fixed argv in some paths; classifier | Common argv/process policy; enforcing boundary for shell adapters | Yes for CLI |
| Network exfiltration | Classification only | Enforced egress/endpoints and network permission | Yes |
| Secrets exposure | Redaction and env-key metadata | Secret refs, injection allowlist, account binding | Yes |
| Detached process | Some parent timeouts | Process-tree ownership/cleanup | Yes for CLI |
| Result tampering | Hash/intake evidence idioms | Durable invocation/result ledger | Yes |
| Identity spoofing | Descriptive locks | Authenticated runtime/provider/model/principal | Yes |
| Replay | Intake idempotency, isolated guards | Canonical invocation/attempt lineage | Yes |
| Cost abuse | Some timeouts/output caps | Token/money/concurrency/retry budget | Yes |
| Authority bypass | PB/enforcement designs | Universal boundary; fence legacy paths | **Yes, critical** |

## Existing-component reuse matrix

| Future need | Existing PCAE capability | Reusable? | Gap |
|---|---|---|---|
| Prompt generation | ContextPack/bootstrap builder | Yes | Persist/hash/approval/target binding |
| Task/repo context | Task contract, session, repo/base binding | Yes | Atomic dispatch binding |
| Agent identity | Registry and lock | Partly | Descriptive only |
| Permission Broker | Invocation actions/reason chains | Partly | Request binding and consumer |
| Runtime Enforcement | Attempt/evidence/decision/coordinator | Partly | Positive contract and production boundary |
| Runtime Registry | Metadata/lifecycle vocabulary | Partly | Persistence/live facts/resolution |
| Backend preflight | Prompt/task/scope facts | Partly | Live target/auth/config and naming |
| Generic intake | Producer-neutral validation | Yes | Result-to-candidate link |
| Audit/human/session | Existing evidence and governance idioms | Partly | Unified invocation ledger and explicit approval |

## Missing-edge matrix

| Edge | Current state | Missing abstraction | Contract needed? | Authority risk |
|---|---|---|---|---|
| Prompt -> runtime | Human copy/paste | Bound selection/dispatch | Yes | Critical |
| Runtime -> result | Bespoke stdout/files | Normalized envelope | Yes | High |
| Result -> intake | Manual/path-specific | Generic converter | Yes | High |
| Agent -> target | Hints/inconsistent maps | Explicit advisory mapping | Yes | High |
| Permission -> dispatch | Vocabulary, no consumer | Atomic PB-bound boundary | Yes | Critical |
| Capability -> attempt | Static/caller metadata | Live bound facts | Yes | High |
| Availability -> legacy paths | No relationship | Reconcile/fence every path | **Yes, first** | **Critical** |
| Dispatch -> supervision | Bespoke blocking calls | Process/request supervisor | Yes | Critical |

## Semantic-state matrix

| State | Meaning | Authority? | Persisted? | Existing/New |
|---|---|---|---|---|
| PREPARED | Exact prompt/bindings materialized | No | Not for bootstrap | Existing generation/new state |
| APPROVED | Human accepts content/target/attempt bounds | Human only | Not for bootstrap | Implicit/new explicit |
| DISPATCH-PERMITTED | Policy permits external effects | Permission, not capability | Simulation only today | Contract evolution |
| RUNTIME-CAPABLE | Live target facts satisfy request | No | No | New |
| DISPATCHED | External effect initiated | No new authority | Path-specific only | New canonical |
| ACCEPTED-BY-RUNTIME | Runtime acknowledged | No | No canonical state | New |
| EXECUTING | Work in progress | No | No canonical state | New |
| COMPLETED | Technical terminal outcome | No acceptance | Legacy/path-specific | New canonical |
| RESULT-INGESTED | Generic validation accepted evidence | Evidence only | Yes | Existing path/new link |

## Runtime-class comparison

| Criterion | Local CLI | API Provider | Mock/Dry Adapter |
|---|---|---|---|
| Complexity/trust | High: OS/files/env/process/network | High: secrets/network/remote/cost | Low |
| Portability | Binary/flags/signals/platform-specific | Protocol portable; auth/policy varies | High |
| Supervision | Process group/tree/signals/streams | Request/session/stream/cancel | Deterministic state |
| Secrets/network | CLI login/inherited env; often implicit egress | Explicit token/OAuth and endpoint | None |
| E2E value | Real local behavior | Real provider behavior | High control-plane value; no containment evidence |
| First suitability | No | No | **Yes** |

## Threat-model finding

The dominant risk is semantic/authority confusion: descriptive identity,
registry presence, approval, PB ALLOW, capability, exit zero, or intake
acceptance being treated as another boundary's authority. Legacy subprocess
paths make bypass risk concrete. Prompt/provider hostility, filesystem/process/
network escape, inherited credentials, tampering/replay, and unbounded cost are
also unresolved. Real execution is blocked until critical controls are closed.

## Architecture options and decision

- Option A — executable adapters inside the existing plugin registry: high
  taxonomy reuse, medium/high effort, high kernel trust risk, not recommended.
- Option B — outer runtime-neutral adapter/service: high extensibility and
  possible isolation, but medium/high effort and risk of a duplicate control
  plane.
- Option C — trusted PCAE kernel plus replaceable external runtime bridges:
  strongest authority separation and semantic reuse, highest initial
  reconciliation effort, best long-term extensibility. **Recommended.**

Recommended first adapter: deterministic mock/dry bridge. It validates
selection, bindings, permission/enforcement edges, records, normalized results,
retry/idempotency, audit, and generic intake with no provider/network/process/
secret/cost effect. It provides no evidence for real containment or provider
authentication.

Mac/Linux result: keep the contract platform-neutral and make bridge/sandbox
implementations declare OS/architecture, executable/version/flags, path/cwd,
signals/process groups, and enforcement capabilities. macOS success never
implies Ubuntu/Dell readiness. Dell was not contacted.

## Phased roadmap and exact next phase

1. `149O.20L.7O.3Q — Runtime Surface Reconciliation and Runtime / Provider
   Adapter Contract Freeze` (contract-only): reconcile/fence legacy surfaces and
   freeze identities, target/bridge, records, states, gates, results, and intake.
2. Independent contract verification.
3. Trusted-kernel skeleton plus deterministic mock bridge, no subprocess/network.
4. Independent mock E2E/adversarial verification.
5. One local-CLI bridge contract and non-executing capability probe.
6. Separately human-authorized, controlled real-runtime pilot.
7. Independent verification and separate activation decision.

3Q was not begun. Human decision is required.

## Governance, tests, publication, and no-go

Checks run at baseline and closeout: `git status`, branch/log/ahead/commit/tag
queries, `pcae health`, `pcae check`, `pcae status coherence`, `pcae doctor
task-memory`, `pcae push check`, `pcae runtime inspect`, `pcae notify status`,
and latest phase-report inspection. Health/check/coherence passed; task-memory
warnings are pre-existing historical sync debt; push completed; runtime stayed
unchanged. No full Fast Green was required because no production/test/contract/
schema/version/build file changed. Tests added/updated: 0. Tests run: 0.

No runtime/provider was invoked. No external provider API or OpenRouter was
used. No credentials were accessed or added. No network was enabled for runtime
dispatch. No Permission Broker policy, Runtime Enforcement, Shell Gate, HATP,
HMIC, Class-B, or CLTR behavior changed. No Dell mutation. No private research
inspection. Publication not performed. The article remains STOPPED and was not
read, modified, resumed, or published.

## Final status block

```text
PHASE ID: 149O.20L.7O.3P
STATUS: COMPLETED
COMPLETENESS: COMPLETE
PHASE-ENTRY COMMIT: 83af9b3b1b1485fa3acdf4d6eebcef95f692113e
PHASE COMMIT: 8b351ebe18277de4963f9b5611b5bc0ea1a0069d
PUSHED: pushed
ORIGIN/MAIN..HEAD: 0
V0.4.3 PUBLIC STATE: CURRENT, UNCHANGED
RUNTIME: Observed / observe / unavailable
CANONICAL EXECUTABLE RUNTIMES: 0
RECOMMENDED ARCHITECTURE: TRUSTED PCAE KERNEL + EXTERNAL RUNTIME BRIDGES
RECOMMENDED FIRST ADAPTER: DETERMINISTIC MOCK/DRY
EXACT NEXT PHASE: 149O.20L.7O.3Q — RUNTIME SURFACE RECONCILIATION AND
RUNTIME / PROVIDER ADAPTER CONTRACT FREEZE
EXECUTION ACTIVATION: NO
MATURE S/M CAPABILITY CONSUMPTION PROGRAM: EXHAUSTED
PRODUCTION SOURCE MODIFIED: NO
PUBLICATION PERFORMED: NO
ARTICLE: STOPPED
HUMAN DECISION: REQUIRED
```
