# Phase 149O.20L.7O.3N.1: Mature Capability Consumer-Edge Investigation

**Status:** COMPLETE — read-only investigation. No `src/pcae` modification.

## 1. Objective

Determine whether any of three areas flagged by Phase 149O.20L.7O.3N as
"UNVERIFIED" contain a real, bounded, currently missing
production-consumption or automatic-orchestration edge connectable
without a new contract, new authority semantics, or execution
activation:

1. audit/explainability lifecycle surfacing
2. Advisory Governance Framework production consumption
3. Repository Decision / Explainability production consumption

No implementation was performed. This phase classifies and ranks; it
does not build.

## 2. v0.4.2 Baseline

Confirmed at phase entry and reconfirmed at phase exit:

- Working tree: clean
- `origin/main..HEAD`: 0 commits
- `HEAD` = `origin/main` = `aa60c33352a8e1c07d2e06b2148efc6d425f497a`
- `v0.4.2` tag = `bc7935f4bb86ea7f6ade823a4e63ed9c9cc0a0c4`, unchanged
- Runtime: `Observed` / `observe` / `unavailable`, unchanged
- `pcae health`: healthy; `pcae check`: passed; `pcae status coherence`:
  coherent; `pcae push check`: clean (nothing to push)

## 3. Unreleased 3M Delta

```
git diff --name-status v0.4.2..HEAD -- src/pcae
M   src/pcae/commands/agent.py     (+13/-0)
M   src/pcae/core/agent.py         (+23/-0)
```

Confirmed: this is exactly and only Phase 149O.20L.7O.3M's rollback
evidence visibility change (already independently verified in 3M.1).
No other unreleased product behavior exists. This investigation did not
touch, extend, or depend on this delta.

## 4. Audit/Explainability Subsystem Inventory

The codebase contains **no single "audit subsystem."** Independent
fresh grep/read across `src/pcae` found roughly ten deliberately-siloed
audit/evidence/explainability subsystems, each frozen by its own phase
contract, each scoped not to share code or authority with the others:

| # | Subsystem | Core module(s) | Own CLI reader? |
|---|---|---|---|
| 1 | Shell Gate Audit | `core/shell_gate.py` (1,719 ln) | Yes — `pcae shell-gate audit show/list/verify` |
| 2 | Enforcement Audit | `core/enforcement_audit.py` (669 ln) | No — simulation-only schema, no persistence, no runtime; awaits a not-yet-built (and explicitly out-of-scope, No-Go §37) enforcement runtime |
| 3 | Phase Audit | `commands/phase.py` (audit section) | Yes — `pcae phase audit [--save]`, `phase audit-show` |
| 4 | Multi-Runtime Audit Chain | `core/agent.py` (`build_multi_runtime_audit_chain`) | Yes — `pcae ... multi-runtime-audit-chain` (meta report over the other subsystems) |
| 5 | Interactive Workflow Audit (Decision Session) | `interactive_workflow/audit/{models,recorder}.py` | Consumed internally by `orchestration/coordinator.py`, `application/session_service.py`, `session/coordinator.py`; no dedicated raw-audit-event CLI (by design — publication/CHGR is a separately gated later phase) |
| 6 | Interactive Workflow Evidence | `interactive_workflow/evidence/{models,coordinator}.py` | Yes — `pcae decision-session evidence` |
| 7 | Governance Publication / CHGR | `governance/{inspection,verification,publication/*}.py` | Yes — `pcae governance-record inspect/verify/publish` |
| 8 | Rollback Approval Evidence + HATP Signed/Store Evidence | `core/rollback_approval_evidence.py`, `core/hatp_evidence_store.py`, `core/hatp_signed_evidence.py` | Consumed within HATP/rollback flows |
| 9 | Permission Broker reason chain | `core/permission_broker_foundation.py`, `core/permission_broker.py` | Returned synchronously per-call (`PermissionBrokerDecision.reason_chain`); also a static reason-code lookup via `pcae permission-broker explain --reason-code` — **not durably persisted anywhere** |
| 10 | Decision Log | `core/decision_log.py` | Yes — `pcae decision-log` (derived from git history, not a live-recorded trail) |
| 11 | Repository Decision Evaluation (115E/F) | `core/decision_evaluation.py`, `core/repository_transition_validator.py` | **No** — see §7 |

Each subsystem, on its own, is internally coherent (has a writer and at
least one reader for its own narrow purpose) or is an intentionally
frozen, not-yet-activated schema (Enforcement Audit — tied to Runtime
Enforcement, a No-Go item). The one subsystem whose computed output has
**zero reader anywhere** is #11, detailed below.

## 5. Audit Writers

Writers are per-subsystem and automatic within their own scope:
`persist_audit_record` (Shell Gate, gated by `PCAE_SHELL_GATE_AUDIT`),
`_save_audit_artifact` (Phase Audit, via `--save`), `AuditRecorder.append`
/ `EvidenceCoordinator.register` (Interactive Workflow, automatic within
a Decision Session), `PublicationCoordinator.authorize/.execute`
(Governance/CHGR), `_compute_content_digest` binding constructors
(Rollback Approval Evidence), in-memory `PermissionBrokerDecision`
construction (Permission Broker — no persistence), and
`_build_explanation` in `repository_transition_validator.py` (Decision
Evaluation — automatic on every `pcae phase complete` / `pcae task
finish --commit` invocation, per that module's own docstring).

## 6. Audit Readers/Consumers

See table in §4. Notably: Permission Broker's `reason_chain` is
consumed only by the immediate caller of that single evaluation call
(never durably logged); Decision Evaluation's `TransitionResult.explanation`
has **zero readers of any kind** — not CLI, not lifecycle, not
report/finalization, not test-asserted-and-discarded. Independently
confirmed via `grep -rn "\.explanation\b" src/pcae`: the only production
hits are the module's own construction/serialization code
(`decision_evaluation.py:94`, `evidence.py:301`) and the *unrelated*
Permission Broker `hb.explanation` field (a different attribute on a
different type, already surfaced via `pcae permission-broker explain`).
No hit exists in `commands/task.py`, `commands/phase.py`,
`commands/phase_reports.py`, `repository_transition_integration.py`, or
any notification code.

## 7. Audit Lifecycle Surfacing Analysis

**Finding:** `repository_transition_validator.py`'s own docstring states
plainly (verbatim, confirmed by direct read):

> "`repository_transition_integration.py` is the live adapter that calls
> `validate_transition` from `pcae phase complete` and `pcae task
> finish --commit`... so the explanation enrichment added here is
> automatically available through that real path too, without any
> change to those lifecycle commands or their printed output (neither
> reads `TransitionResult.explanation`)."

This is a real, bounded, exactly-identified gap: on every governed
phase-complete/task-finish-commit invocation, a deterministic,
template-generated `EvaluationResult` (six invariant checks: phase
identity, push state, metadata, report completeness,
runtime-execution-unavailable, canonical-promotion-eligibility) is
computed and attached to `TransitionResult.explanation`, then
discarded. No command prints it. No phase report renders it. No
notification carries it.

**But:** per the governing caution (surfacing existing evidence ≠
consumption, established directly by 3M/3M.1's own precedent), this is
classified strictly as a **VISIBILITY / SURFACING GAP**, not a TRUE
CONSUMPTION GAP. The verdict (`TransitionVerdict`) that actually gates
the phase-complete/task-finish path is computed independently by this
same module's own hardcoded invariant checks and is wholly unaffected
by whether `.explanation` is ever read. Printing `.explanation`
would change nothing about what is permitted, blocked, or gated — it
would only give a human operator a readable "why" alongside a verdict
they already receive. This is the same shape of change as 3M itself.

## 8. Audit Authority Boundary

Preserved by construction: `decision_evaluation.py`'s own docstring
states "Evidence never decides. Evaluation is deterministic," and
`repository_transition_validator.py`'s docstring states the enrichment
"never influences, overrides, or is consulted by the verdict logic
itself... Same decisions, better explanations." Any future surfacing of
`.explanation` remains strictly informational under the existing
contract; no authority-model change is implied or required.

## 9. Advisory Governance Framework Inventory

**Finding: zero code footprint.** The Advisory Governance Framework /
Pilot / operational certification / operational adoption strategy
(docs `PHASE_138A`–`PHASE_141G`, governed by contracts GLP-001,
GAC-001, PGP-001, PPA-001, AGOC-001) is a purely
documentary/procedural governance chapter about how PCAE's human
authority process would evaluate a hypothetical governance-*pattern*
pilot. It is not software.

Confirmed by exhaustive grep: `grep -rl "GLP-001\|GAC-001\|PGP-001"
src/pcae --include="*.py"` → **zero matches**. No
`src/pcae/advisory_governance` directory or equivalent exists. Every
phase in the chapter states explicitly, in its own completion text,
that no file under `src/pcae/` was created, modified, or deleted (e.g.
138D: "Production code (`src/pcae/**`) was not modified by this
phase"; 141D: "no file under `src/pcae/` is created, modified, or
deleted by this phase").

Modules that share vocabulary but are unrelated, confirmed by content
inspection, not name matching alone: `src/pcae/core/advisory.py`,
`advisory_context_package.py`, `advisory_repository_skills.py`,
`advisory_runtime.py`, `current_acting_model_advisory_provider.py`
(a different concept: contextual advice/repository-skill info for the
acting model, tracks 88X/113C/115P-Z/122+); `core/hatp_mandatory_certification.py`
(HMIC-001, track 149O.19.5A/B); `core/notification_certification.py`
(Phase 114B notification-dispatch eligibility).

## 10. Advisory Governance Reachability

Not applicable — there is no code to reach. This supersedes any prior
framing that treated 140B "operational certification" / 141A
"operational adoption strategy" as release-engineering artifacts for a
shipped feature; they are governance-process artifacts about
GLP-001/GAC-001, evaluated and retrospected entirely at the documentation
layer. The chapter's own closing retrospective (141G) already discloses
its own central gap without concealment: the pilot-technical half
(139F onward) reached "one stage out of four," never advanced across
seven subsequent phases (140A–141F); overall assurance is "not yet
evidenced" for the pilot's technical value, only "high" for the
framework's internal documentary consistency.

## 11. Advisory Governance Consumer Analysis

No production service exists that any lifecycle code could be "already
calling but is not." There is no missing edge to name, because there is
no production service.

**Classification: NO MEANINGFUL GAP** (not a software consumption
question — there is nothing to consume).

## 12. Repository Decision/Explainability Inventory

Phase 115A itself ("Decision & Explainability Framework Architecture")
is architecture/contract only, no runtime code. Its runtime descendants,
independently confirmed by direct file read:

| Module | Lines | Role |
|---|---|---|
| `core/evidence.py` | 406 | `Evidence`/`EvidenceCollection` data model (115C) |
| `core/evidence_providers.py` | 778 | `EvidenceProvider` ABC + Git/Runtime/Report/Metadata providers (115D) |
| `core/decision_evaluation.py` | 593 | `evaluate()`, six deterministic invariant checks, `EvaluationResult` (115E) |
| `core/repository_transition_validator.py` | 497 | `validate_transition()` — attaches `.explanation` (115F) |
| `core/repository_skills.py` | 438 | `RepositorySkill` ABC + registry (115H/J) |
| `core/repository_skills_integration.py` | 174 | glue between Repository Skills and Decision Evaluation (115M) |
| `core/advisory_repository_skills.py` | 498 | `AdvisoryProvider` ABC, `MockAdvisoryProvider` (115P/Q/R) |
| `core/current_acting_model_advisory_provider.py` | 115 | concrete `AdvisoryProvider` for the acting model (115S) |
| `core/advisory_context_package.py` | 623 | frozen `AdvisoryContextPackage` contract (115W/X) |

## 13. Repository Decision Consumers

Independently confirmed via grep across all of `src/pcae`:

- **`evidence.py` / `decision_evaluation.py`:** production-reachable
  *only* transitively through `repository_transition_validator.py`,
  which is called from the real `pcae phase complete` / `pcae task
  finish --commit` path via `repository_transition_integration.py`.
  Output (`.explanation`) is computed but never read (§7 above) —
  "wired but inert."
- **`evidence_providers.py`, `repository_skills.py`,
  `repository_skills_integration.py`, `advisory_repository_skills.py`,
  `current_acting_model_advisory_provider.py`,
  `advisory_context_package.py`:** zero non-test callers anywhere in
  `src/pcae`. Confirmed dead/prototype, consistent with the codebase's
  own `PHASE_115Z_ADVISORY_SUBSYSTEM_HARDENING.md`, which froze them as
  a stable-but-intentionally-disconnected subsystem, and with
  `PROJECT_STATUS.md`'s Phase 149O.20L.7O.3K finding: "the
  `AdvisoryProvider`/`AdvisoryContextPackage` framework (115P-115Z)
  remains fully mock-only and disconnected from production."
- **No cross-import found** with Permission Broker, mutation paths, or
  finalization/canonical-engineering-evidence (`finalization_transaction.py`
  imports a different, unrelated `evidence_extraction` module — a
  naming collision only, confirmed by content read).
- **Advisory** (`core/advisory.py`, the real `pcae advisory check`
  engine) imports none of these nine modules. It was instead wired
  (Phase 149O.20L.7O.3J) to the separate Repository Intelligence
  advisory-context bridge (`src/pcae/advisory/context/advisory_context_builder.py`,
  track 122+), which explicitly documents itself as distinct from and
  non-integrating with the 115W `AdvisoryContextPackage`.

## 14. Repository Explainability Consumers

Generation and consumption are separate, confirmed: `.explanation` is
generated automatically on every transition (§7) but is retrievable by
**no** command — there is no `pcae decision explain` or equivalent.
`AdvisoryRepositorySkill` / `CurrentActingModelAdvisoryProvider` /
`AdvisoryContextPackage` "explanations" have no runtime entry point at
all (not CLI, not automatic, not manual query) — exercised only inside
the test suite (`test_decision_evaluation.py`, `test_evidence*.py`,
`test_phase_115*.py`, ~26 test files total).

## 15. Contract Readiness

| Area | New contract? | New schema? | New authority semantics? | Execution activation? |
|---|---|---|---|---|
| Decision-Evaluation `.explanation` surfacing | No | No | No | No |
| Advisory Governance Framework | N/A (no code) | N/A | N/A | N/A |
| Repository-Skills / AdvisoryProvider family (6 dead modules) | **Yes** — no frozen contract governs wiring `AdvisoryProvider` output into `core/advisory.py`'s real path (consistent with 3K's finding) | Likely yes | Possibly (would touch advisory decision content) | No |

## 16. Package/Release Maturity

All nine Repository Decision/Explainability modules and all eleven
audit subsystems live under `src/pcae` and are included in the shipped
wheel/sdist — packaging is not the blocker for any of them. Test
coverage exists for `decision_evaluation.py`/`evidence.py`/
`repository_transition_validator.py` (`test_decision_evaluation.py`,
`test_evidence*.py`, `test_phase_115*.py`) and confirms current,
correct behavior of the *verdict* path; no test exercises `.explanation`
being read by any CLI or lifecycle consumer, because none exists.
`AdvisoryProvider`/`AdvisoryContextPackage` family: packaged but
mock-only, zero non-test callers, no public API/CLI availability
(re-confirms 3K).

## 17. Unified Consumer Graph

```
[Shell Gate check]         -> shell-gate-audit store       -> pcae shell-gate audit show/list/verify   [ALREADY CONSUMED]
[Phase Audit --save]       -> .pcae/phase-audits/           -> pcae phase audit-show                    [ALREADY CONSUMED]
[Decision Session ops]     -> AuditRecorder / Evidence       -> orchestration/session_service/           [ALREADY CONSUMED]
                              Coordinator                      pcae decision-session evidence
[Governance publish]       -> CHGR record store              -> pcae governance-record inspect/verify   [ALREADY CONSUMED]
[Rollback/HATP evidence]   -> rollback_approval_evidence /   -> HATP/rollback flows                      [ALREADY CONSUMED]
                              hatp_evidence_store
[Permission Broker eval]   -> in-memory reason_chain         -> immediate caller only; static            [ALREADY CONSUMED
                                                                  "explain --reason-code" lookup           (not persisted, by design)]
[decision_log build]       -> derived from git log           -> pcae decision-log                        [ALREADY CONSUMED]
[Enforcement Audit schema] -> (no persistence)                -> (no reader; awaits Runtime Enforcement)  [TRUST/AUTHORITY BLOCK]
--------------------------------------------------------------------------------------------------------
[pcae phase complete /     -> decision_evaluation.evaluate() -> TransitionResult.explanation            [VISIBILITY/SURFACING GAP
 task finish --commit]        (6 invariants, automatic)          -> **NO READER** anywhere                — the one real finding]
--------------------------------------------------------------------------------------------------------
[core/advisory.py real     -> (never calls)                  -> AdvisoryProvider / RepositorySkill /    [CONTRACT GAP
 path]                                                            AdvisoryContextPackage family (6 dead     — effort L, unchanged
                                                                   modules, zero production callers)         from 3K]
--------------------------------------------------------------------------------------------------------
(no code)                  -> (no code)                       -> (no code)                               [Advisory Governance
                                                                                                              Framework: NO
                                                                                                              MEANINGFUL GAP]
```

## 18. Dead/Prototype Classification

`evidence_providers.py`, `repository_skills.py`,
`repository_skills_integration.py`, `advisory_repository_skills.py`,
`current_acting_model_advisory_provider.py`,
`advisory_context_package.py` are **intentionally disconnected by
design**, not accidentally missing a caller: Phase 115Z's own
"hardening" phase froze them explicitly as a stable-but-disconnected
subsystem pending a future integration phase; subsequent architecture
(116A+, then 119+ Repository Intelligence) pursued a different
direction entirely. `Enforcement Audit` is a frozen schema awaiting a
runtime that is explicitly out of scope (No-Go §37: do not enable
Runtime Enforcement). None of this is "genuinely missing a caller" in
the sense the governing brief is probing for — each is either
by-design-frozen or blocked by an explicit No-Go.

## 19. Gap-Type Classification (Summary)

| Area | Classification |
|---|---|
| Audit/explainability lifecycle surfacing | **VISIBILITY / SURFACING GAP** (one concrete instance: Decision-Evaluation `.explanation`); all other audit subsystems ALREADY CONSUMED within their own scope, or TRUST/AUTHORITY BLOCK (Enforcement Audit) |
| Advisory Governance Framework | **NO MEANINGFUL GAP** (no code exists) |
| Repository Decision/Explainability | **VISIBILITY / SURFACING GAP** for the wired-but-inert Decision-Evaluation core (same finding as above — this is the shared boundary between areas 1 and 3); **CONTRACT GAP**, effort L, for the six dead AdvisoryProvider-family modules (unchanged from 3K) |

## 20. Effort/Risk

| Candidate | Effort | Authority Risk |
|---|---|---|
| Surface `TransitionResult.explanation` in `pcae phase complete` / `task finish --commit` output (and/or phase report) | **S** | **LOW** — purely informational, verdict computation provably unaffected |
| Wire `AdvisoryProvider`/`AdvisoryContextPackage` family into `core/advisory.py`'s real path | **L** | MODERATE — would require a new contract governing how advisory decision content changes; unchanged from 3K |

## 21. User-Value Analysis

**Decision-Evaluation surfacing:** today an operator sees only the
`TransitionVerdict` outcome (pass/fail/blocked) from `pcae phase
complete`/`task finish --commit`; they must independently reason about
*why* — no automated "why" is available anywhere. Connecting `.explanation`
would let PCAE automatically show the six-invariant deterministic
breakdown alongside the verdict the operator already receives, at zero
change to what is authorized. This is a real (if modest) reduction in
manual reasoning, not cosmetic duplication — no other surface currently
renders this content in any form. It is, however, materially the same
*kind* and *scale* of improvement as 3M, which this program already
rated LOW release-worthiness.

**AdvisoryProvider family:** current user gets no value from these six
modules today (zero runtime entry point). Wiring them would be a new
capability, not a "connect existing consumer" quick win — rejected from
S/M consideration, consistent with 3K.

## 22. E2E Verification Design (Decision-Evaluation surfacing, informational only — not implemented)

- Entry point: `pcae phase complete` / `pcae task finish --commit`
  (existing, no new CLI surface required)
- Automatic invocation: yes, already automatic — no new trigger
- Data passed: existing `RepositoryState` → existing
  `EvaluationResult` (six invariant results) — no new inputs
- Output consumed: printed/rendered in existing terminal output and/or
  phase-report artifact (design choice for whoever implements)
- Human boundary: informational only; verdict/authorization untouched
- Failure: `.explanation` build already best-effort (per 115F
  docstring) — a failure to build it must not affect the verdict path;
  any surfacing code must preserve that same fail-soft guarantee
- Restart/retry, idempotency: unaffected — `.explanation` is
  recomputed fresh each call, not persisted, no new state
- Authority assertions: independent test must assert
  `TransitionVerdict` output is byte-identical whether or not
  `.explanation` is printed, across pass/fail/blocked scenarios
- No-bypass: N/A — no gate is added or removed

## 23. Consumption Maturity Matrix

| Capability | Implemented | Verified | Packaged | Exposed | Production-consumed | Auto-orchestrated | Gap type | Candidate |
|---|---|---|---|---|---|---|---|---|
| Shell Gate Audit | Yes | Yes | Yes | Yes (CLI) | Yes | Yes (write-side) | ALREADY CONSUMED | No |
| Phase Audit | Yes | Yes | Yes | Yes (CLI) | Yes | Partial (`--save` manual) | ALREADY CONSUMED | No |
| Interactive Workflow Audit/Evidence | Yes | Yes | Yes | Yes (CLI) | Yes | Yes | ALREADY CONSUMED | No |
| Governance Publication/CHGR | Yes | Yes | Yes | Yes (CLI) | Yes | Partial (`publish` manual) | ALREADY CONSUMED | No |
| Rollback/HATP Evidence | Yes | Yes | Yes | Partial | Yes | Yes | ALREADY CONSUMED | No |
| Permission Broker reason chain | Yes | Yes | Yes | Partial (static explain only) | Yes (per-call) | Yes | ALREADY CONSUMED | No |
| Decision Log | Yes | Yes | Yes | Yes (CLI) | Yes | Yes (derived) | ALREADY CONSUMED | No |
| Enforcement Audit | Schema only | N/A | Yes | No | No | No | TRUST/AUTHORITY BLOCK | No |
| Decision Evaluation core (`evidence.py`/`decision_evaluation.py`/`repository_transition_validator.py`) | Yes | Yes | Yes | No | **No (computed, discarded)** | Yes (write-side only) | VISIBILITY/SURFACING GAP | **Yes — S effort** |
| AdvisoryProvider/AdvisoryContextPackage family (6 modules) | Yes (mock) | Yes (tests) | Yes | No | No | No | CONTRACT GAP | No (effort L) |
| Advisory Governance Framework | No (no code) | N/A | N/A | N/A | N/A | N/A | NO MEANINGFUL GAP | No |

## 24. Consumer-Edge Matrix

| Capability | Production owner | Current consumers | Expected consumer | Missing edge | Contract ready? | Effort | Risk |
|---|---|---|---|---|---|---|---|
| Decision Evaluation `.explanation` | `core/decision_evaluation.py` + `core/repository_transition_validator.py` | none | `pcae phase complete` / `task finish --commit` printed output or phase report | print/render existing field | Yes (no new contract needed) | S | LOW |
| AdvisoryProvider family | `core/advisory_repository_skills.py` + siblings | tests only | `core/advisory.py` real path | new wiring + new contract | No | L | MODERATE |
| Advisory Governance Framework | none (no code) | none | — | — | — | — | — |

## 25. Candidate Ranking

Only one candidate survives to ranking: **Decision Evaluation
`.explanation` surfacing.** It is not ranked against the AdvisoryProvider
family (effort L, contract-blocked, excluded from S/M scope) or Advisory
Governance Framework (no code exists).

Per the governing brief's own explicit caution (§7 of this document; the
taxonomy's separation of VISIBILITY/SURFACING GAP from TRUE CONSUMPTION
GAP; and 3M's own established precedent that a visibility-only patch of
this shape and scale rates LOW release-worthiness) — **this candidate
does not qualify as a genuine S/M production-consumption gap** under the
Outcome A bar. It is a real, exactly-identified, zero-risk surfacing
improvement, but it is the same *kind* of change 3M already shipped, not
a new consumption edge. It is documented here as a legitimate small
finding, not manufactured to continue the phase chain, and not put
forward as a Plan A/B/C candidate.

## 26. Mature-Program Exhaustion Verdict

```
MATURE CAPABILITY CONSUMPTION PROGRAM:
CURRENTLY EXHAUSTED AT S/M SCOPE
```

No TRUE CONSUMPTION GAP or AUTOMATIC ORCHESTRATION GAP was found in any
of the three investigated areas. The one real finding (Decision
Evaluation `.explanation` discard) is a VISIBILITY/SURFACING GAP,
already-shipped-precedent-scale, not a new consumption edge.

## 27. 3M Release Decision (Reconfirmed)

3N recommended BUNDLE. This investigation reconfirms that
recommendation is **no longer clearly optimal**: the "wire existing
capabilities" loop is now exhausted at S/M scope, and the only next
strategic work available (architecture/contract/trust/runtime-scale
chapters, or the L-effort AdvisoryProvider contract work) is
categorically larger and slower than 3M's own visibility patch. Holding
3M pending an unspecified future bundle risks indefinite delay of an
already-verified, zero-risk improvement.

**Recommendation: RELEASE NOW** (ship `v0.4.3`) is now favored over
BUNDLE, though BUNDLE remains defensible if a next chapter is selected
and begun imminently. This is a recommendation only — **human decision
required**, no release action taken this phase.

## 28. Fast Green Infrastructure Debt

Carried forward unrepaired, per instruction: caller-supplied mutable
`--pushed-status`/push-state attribution instability. **NON-BLOCKING
INFRASTRUCTURE DEBT**, confirmed unrelated to any of the three
candidate areas investigated this phase (no shared module, no shared
test file).

**`rg` environment finding:** confirmed this is a genuine **developer
prerequisite**, not an optional Python dependency and not a packaging
gap. Two tests (`tests/test_phase_149o_20l_7o_3m_1_independent_rollback_readiness_evidence_consumption_verification.py`)
invoke the external `rg` (ripgrep) binary directly via
`subprocess.run(["rg", ...])`. In this investigation's shell
environment, `rg` resolves only to a Claude-Code-provided zsh shell
function (not a real binary on `PATH`) — a shell function is not
inherited by a Python subprocess, so any Python-invoked `subprocess.run(["rg", ...])`
in an environment lacking the real `ripgrep` binary on `PATH` fails
exactly as 3N observed. Confirmed unrelated to any of the three
investigated areas. Not fixed this phase (no-go).

## 29. Recommendation

1. Do not open another "wire existing capability" phase against these
   three areas — they are exhausted at S/M scope.
2. If a small, zero-risk surfacing improvement is ever wanted, the
   Decision-Evaluation `.explanation` finding (§7, §22) is fully
   specified and ready for an S-effort implementation phase, bundled
   with a release rather than pursued as a standalone chapter.
3. Reassess `v0.4.3` release timing per §27 — RELEASE NOW is now
   favored over BUNDLE.
4. Next strategic work should shift to one of: new architecture,
   contract evolution (e.g., an AdvisoryProvider-family contract, if
   ever prioritized — effort L), trust-activation preparation, or
   provider/runtime work — not another mature-capability-consumption
   sweep.

## 30. Human Decision Requirement

`HUMAN PRIORITY/RELEASE SELECTION REQUIRED.` No next phase begun. No
implementation performed. No release action taken.
