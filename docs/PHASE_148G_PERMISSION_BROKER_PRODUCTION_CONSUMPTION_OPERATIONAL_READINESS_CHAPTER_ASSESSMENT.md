# Phase 148G — Permission Broker Production Consumption Operational Readiness / Chapter 148 Assessment

**Status:** completed (assessment-only; zero `src/pcae/**` or `docs/contracts/**` modification)
**Phase type:** operational-readiness assessment + Chapter 148 closure decision
**Predecessor:** Phase 148F — Permission Broker Production Consumption Independent Implementation Verification (VERIFIED WITH NON-BLOCKING FINDINGS)

---

## 1. Initial Inspection (verbatim results)

```
git status --short                          → (empty; clean)
git status --branch --short                  → ## main...origin/main
git rev-list --count origin/main..HEAD       → 0
pcae health                                  → Overall status: healthy
pcae check                                   → PCAE check passed.
pcae status coherence                        → Status: coherent
pcae doctor task-memory                      → Task memory: clean
pcae push check                              → Mode: nothing_to_push
pcae runtime inspect                         → Observed / observe / unavailable
pcae notify status                           → Telegram configured, enabled, ready
pcae phase-report show --latest              → 148F, completed, complete, VERIFIED WITH NON-BLOCKING FINDINGS
pcae phase-report reconcile --phase-id 148F  → reconciled, mutation: none (inspection only)
```

Confirmed: repository clean; `origin/main..HEAD = 0`; 148F complete; PBPC-001 remains v1.2; PBPA-001 remains v1.0; 148C-B-1 remains CLOSED; production wiring present; runtime Observed/observe/unavailable.

---

## 2. Chapter 148 Objective Reconstruction

Reconstructed independently from `docs/architecture/PHASE_148A_NEXT_STRATEGIC_CAPABILITY_ARCHITECTURE.md` and PROJECT_STATUS.md's 148A entry, not from later-phase summaries: three independent 148A research passes converged on one finding — the Permission Broker Foundation (`POL-001..012`, frozen 108A-C) and the Runtime Enforcement Decision Engine were contract-frozen and implemented but had **zero real call sites** outside their own CLI/test modules, while `pcae commit`/`pcae push` already performed real, production-wired git mutation through bespoke, broker-independent readiness logic. Chapter 148 selected **`pcae push` alone** (gating only the existing `HARD_BLOCK_REGISTRY` conditions) as the **Minimum Safe MVP** — the first real, non-bypassable Permission Broker enforcement point in PCAE.

**pcae push MVP** (in scope) is explicitly distinguished from **repository-wide universal mutation governance** (out of scope): PBPC-REQ-004/005 state the contract applies to exactly one production consumer, `pcae push`'s two dispatch paths, and explicitly SHALL NOT apply to `pcae commit`, arbitrary git commands, shell execution, or generic command dispatch. This phase does not retrospectively expand that scope.

---

## 3. Chapter 148 Lineage (148A–148F)

Reconstructed from primary phase documents / PROJECT_STATUS.md entries, not solely from prose summaries.

| Phase | Objective | Result | Blocking findings | Closure/repair | Remaining debt |
|---|---|---|---|---|---|
| 148A | Select next strategic capability | Selected Chapter 148 (PBPC MVP) | none | n/a (architecture) | none |
| 148B | Freeze PBPC-001 v1.0 | Frozen | none | n/a | — |
| 148C | Independently verify PBPC-001 v1.0 | NOT VERIFIED | **B-1**: `POL-004` universally active, `approval_present` fixed `False` → every conformant push request → `HUMAN_REVIEW`, never `ALLOW` | opened 148C.1 | B-1 open |
| 148C.1 | Clarify/repair B-1 | Category C (Foundation scoping gap); PBPC-001 → v1.1 | B-1 remains OPEN | opened 148C.2 (applicability design) | B-1 open |
| 148C.2 | Design policy-applicability model | Hybrid declarative-metadata design selected | none (design only) | — | B-1 still open |
| 148C.3 | Freeze PBPA-001 v1.0 | Frozen | none | — | B-1 still open (contract, not yet implemented) |
| 148C.4 | Independently verify PBPA-001 v1.0 | VERIFIED WITH NON-BLOCKING FINDINGS | none | — | B-1 still open |
| 148C.5 | Implementation plan for PBPA-001 | Planning complete, zero blocking | none | — | B-1 still open |
| 148C.6 | Implement PBPA-001 in Foundation | Implemented (`permission_broker_foundation.py` only) | none | — | B-1 formally still open pending verification |
| 148C.7 | Independently verify PBPA-001 implementation | VERIFIED WITH NON-BLOCKING FINDINGS (7 V-findings) | none | — | B-1 formally still open pending PBPC re-evaluation |
| 148C.8 | Re-evaluate B-1 against live Foundation | **B-1 CLOSED** (canonical push request → `ALLOW`) | none | closed | PBPC-001 v1.1 text not yet reconciled |
| 148C.9 | Reconcile PBPC-001 text to v1.2, ratify B-1 closure | PBPC-001 → v1.2, SATISFIABLE AND TEXTUALLY RECONCILED | none | — | independent verification of v1.2 recommended |
| 148C.10 | Independently verify PBPC-001 v1.2 | VERIFIED — READY FOR IMPLEMENTATION PLANNING | none | — | none |
| 148D | Implementation plan for PBPC-001 v1.2 in `push.py` | Planning complete, zero blocking | none | — | none |
| 148E | Implement PBPC-001 v1.2 production consumption | Implemented (`push.py` only, +166/-0) | none | — | none claimed |
| 148F | Independently verify 148E's implementation | VERIFIED WITH NON-BLOCKING FINDINGS | none | — | **F-148F-1** (construction-failure diagnostics), **F-148F-2** (scope observation), **F-148F-3** (Section 17 not implemented) |

This phase (148G) is the first to adjudicate whether F-148F-1/F-148F-2/F-148F-3 are acceptable retained debt or require repair before certification.

---

## 4. Contract State Verification

- **PBPC-001**: v1.2, unamended since 148C.9 (`docs/contracts/PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md` — `git diff --name-only <pre-148G>..HEAD -- docs/contracts/` = empty).
- **PBPA-001**: v1.0, unamended since 148C.3 freeze (single commit `234fce06` since freeze, re-confirmed unchanged through 148C.10/148D/148E/148F and now 148G).
- No conflict found between the two contracts; PBPC-REQ-003A's PBPA-001 dependency remains satisfied.

## 5. B-1 Closure Re-Confirmation

Live re-execution of the canonical PBPC push request during this phase (not cited from 148F):

```
action_type=push, execution_class=mutation, requested_component=COMP-001,
requested_capability=pcae_push, approval_present=False, simulation_only=True
→ decision: ALLOW
→ non_applicable_policy_ids: ('POL-004',)
```

`POL-004` non-applicability under `EXECUTION_CLASS_MUTATION` holds; **148C-B-1 remains CLOSED.** Not re-litigated beyond this confirmatory re-execution, per phase scope.

## 6. Production Core Invariant Re-Confirmation

Independent re-derivation (not reuse of 148F's inventory), via `Explore` agent AST-level search of `src/pcae/**` for every `subprocess` invocation whose argv contains `git`+`push`:

**Confirmed: exactly 5 real `git push` dispatch sites in the entire `src/pcae` tree.**

| # | Site | Reachable via `pcae push`? | Broker-gated? |
|---|---|---|---|
| 1 | `push.py:591` (`run_push`) | Yes | Yes (`_evaluate_push_permission`, lines ~560-571) |
| 2 | `push.py:772` (`_run_push_staged_file_aware`) | Yes | Yes (`_evaluate_push_permission`, lines ~748-765) |
| 3 | `core/agent.py:4732` (`_run_git_push`, via `push_file_changes`) | No — only `pcae agent`/remote-job push | No |
| 4 | `commands/phase.py:19566` (`_build_backend_created_output_adoption_push_execution`) | No — only `pcae phase ...` subcommand | No |
| 5 | `commands/phase.py:20295` (`_build_final_verification_tooling_push_decision`) | No — only `pcae phase ...` subcommand | No |

Both `pcae push` dispatch paths cross the broker with `ALLOW` required to proceed; `DENY`/`HUMAN_REVIEW`/broker-`evaluate()`-failure all abort with zero dispatch (independently re-confirmed by re-running `tests/test_phase_148f_permission_broker_production_consumption_independent_verification.py` and `tests/test_permission_broker_push_production_consumption.py`, 31/31 passed).

`HARD_BLOCK_REGISTRY` independently recounted: **12 entries** (unchanged).

---

## 7. F-148F-2 — Scope of Other Git-Push Sites

Per PBPC-REQ-004/005 (Section 3, read directly): this contract "SHALL apply to exactly one production consumer: `pcae push`," and "SHALL NOT apply to ... arbitrary Git commands ... generic command dispatch. Those become consumers only through separately governed future phases." This is textually unambiguous.

**Classification of the three non-`push.py` sites: `OUTSIDE_148_MVP`** (all three).

- Sites 3-5 are not reachable through the `pcae push` CLI verb under any argument combination — they are wired to distinct CLI verbs (`pcae agent`, two `pcae phase ...` subcommands) with their own, separate authorization surfaces (site 3's remote-push job model; sites 4-5's phase-execution approval flags).
- None of the three existed as, or were ever claimed to be, part of Chapter 148's Minimum Safe MVP (148A §31 scopes the MVP to `pcae push` alone).
- **Chapter-claim precision requirement (mandatory, per this phase's brief):** any future Chapter 148 closure language MUST say *"the `pcae push` production mutation path is Permission-Broker governed,"* and MUST NOT say *"all git push operations in PCAE are Permission-Broker governed"* — that broader statement is false today and this phase does not make it.
- **Disposition:** not Chapter-148 repair debt. Recorded as a **future strategic observation** — "Repository-Wide Mutation Permission Coverage" (Section 14 below) — for post-Chapter-148 strategic reassessment, not Chapter 148 scope expansion.

---

## 8. F-148F-1 — Broker Construction Failure Handling

### 8.1 Independent reproduction

Re-ran (unmodified) `tests/test_phase_148f_permission_broker_production_consumption_independent_verification.py::test_ordinary_path_broker_construction_failure_does_not_dispatch` and its staged-path counterpart. Both monkeypatch `PermissionBroker.__init__` to raise `RuntimeError`, then call `main(["push"])` directly (not via subprocess) and assert `pytest.raises(RuntimeError, ...)`. Confirmed live: the exception propagates through `_evaluate_push_permission` → `run_push` → `args.handler(args)` → `pcae.cli.main()` itself, uncaught.

### 8.2 Source-level confirmation

`src/pcae/commands/push.py:450-459`:

```python
broker_instance = broker if broker is not None else permission_broker_foundation.PermissionBroker()
try:
    decision = broker_instance.evaluate(request)
except Exception as error:
    ...
```

`PermissionBroker()` construction sits **outside** the `try:` block; only `.evaluate()` is wrapped.

`src/pcae/cli.py:10923-10943` (`main()`'s only exception handler) catches exclusively `subprocess.CalledProcessError` for `git`-prefixed commands (added Phase 106D for a distinct "not a git repo" case). No general `except Exception` exists anywhere between `run_push`/`_run_push_staged_file_aware` and the console-script entry point (`pcae = "pcae.cli:main"`, `pyproject.toml`). A construction failure therefore terminates the process with a raw Python traceback via Python's default top-level exception handling, not a controlled diagnostic.

### 8.3 Failure-surface precedent search

`src/pcae/core/command_path_observation.py:70-84` — the pre-existing (Phase 109B) observation-only broker touchpoint — wraps **both** `build_permission_broker_request(...)` construction and `PermissionBroker().evaluate(...)` in a single `try/except Exception: return None`. This is the one other place in the codebase that constructs a fresh `PermissionBroker()` inline, and it already treats construction and evaluation failure identically (both fail closed to `None`). The PBPC production-consumption adapter in `push.py` deviates from this established local precedent by narrowing its `try:` to `evaluate()` only.

**Repair, if undertaken, is a one-line change at the command/CLI boundary already established by this existing sibling integration** (widen `_evaluate_push_permission`'s `try:` to include the `PermissionBroker()` construction line) — no new abstraction, no adapter-level redesign needed.

### 8.4 Assessed dimensions

- **Security:** fail-closed. The process terminates before reaching either `git push` dispatch line; zero dispatch occurs either way (confirmed by `dispatch_calls["count"] == 0` in both reproduction tests).
- **User experience:** poor. A raw Python traceback (file paths, internal frame references) replaces the polished `"Push blocked: Permission Broker evaluation failed (...)"` message the sibling `evaluate()`-failure path produces. No secrets or credentials appear in the traceback (`PermissionBroker.__init__` constructs only a `PolicyRegistry` from a fixed in-memory tuple — no I/O, no external config).
- **Lifecycle integrity:** no corruption risk. The exception fires strictly before any git mutation and before `_reconcile_post_push`/`_finalize_report_and_notify` are reached — no partial state write occurs on this path.
- **Notification/reporting:** no important terminal bookkeeping is bypassed beyond what a `DENY` already bypasses (no push happened either way, so no post-push reconciliation was ever due).
- **Retry behavior:** safe. Nothing was mutated; a retry is a fresh, independent attempt with no stale state.
- **Realistic likelihood:** very low under current production conditions — `PolicyRegistry()`'s constructor validates a fixed, versioned-by-code-review tuple (`DEFAULT_POLICY_RULES`) with no I/O or external dependency; a construction failure today would require either a code regression in the registry itself or a caller-supplied malformed `registry=` argument, neither of which the CLI path exercises.

### 8.5 Classification

**F-148F-1: `REPAIR_RECOMMENDED_POST_CLOSURE`.** Not closure-blocking: the security invariant (no dispatch without `ALLOW`) is fully preserved, the failure mode is not lifecycle-corrupting, and the realistic likelihood is very low given the constructor's fixed, I/O-free nature. It is retained as an operational-quality gap, not a security or correctness gap, and is trivially and cheaply fixable by aligning with the existing `command_path_observation.py` precedent — a narrow, low-risk, one-line follow-up appropriate for a future bounded hardening phase rather than a Chapter 148 closure blocker.

---

## 9. F-148F-3 — Final Pre-Dispatch Validation (PBPC-REQ-059/060/061)

### 9.1 Requirement re-derivation (direct contract read, Section 17)

- **PBPC-REQ-059**: "Immediately before each dispatch site (Section 12), a future implementation SHALL re-observe: local HEAD revision, local branch, unpushed-commit count, and active task ID."
- **PBPC-REQ-060**: a mismatch between any re-observed field and the value bound into the evaluated request constitutes a **material mismatch**.
- **PBPC-REQ-061**: on material mismatch, the existing `ALLOW` decision SHALL be treated as invalid; no dispatch SHALL occur using it; a fresh request/evaluation cycle SHALL be required. "This contract does NOT authorize silently updating the bound operation underneath an existing decision."

This is normative `SHALL` language, not aspirational prose. Section 12's own control-flow diagram (PBPC-REQ-040) places "final pre-dispatch validation (Section 17)" as a mandatory step between `ALLOW` and the `git push` dispatch call. PBPC-REQ-090/091 (Section 27) list Section 17 conformance as a **required implementation-acceptance precondition** and require a built implementation to **demonstrate** "stale/mismatched decisions cannot authorize a changed operation (Section 17)" before it is accepted as conformant.

### 9.2 Implementation gap — traced directly, both paths

**Ordinary path** (`run_push`, `push.py:556-596`): between the `permission_result.authorized` check (line 562) and `subprocess.run(["git", "push"], ...)` (line 590), the only intervening statement (when authorized) is an `if not args.json: print(...)` banner (lines 582-587) — no re-observation of HEAD, branch, unpushed-commit count, or task ID.

**Staged-file-aware path** (`_run_push_staged_file_aware`, `push.py:747-772`): between the `permission_result.authorized` check (line 753) and `subprocess.run(["git", "push", "origin", "main"], ...)` (line 771) there is no intervening statement at all — the dispatch call is the immediate next executable line.

Confirmed by direct read of both call sites: **zero re-observation code exists on either path.** No equivalent mechanism was found elsewhere (searched for a pre-dispatch helper, git-state assertion, lock-validation call, preflight function, or snapshot comparison between decision and dispatch on both paths — none exists).

### 9.3 TOCTOU threat model

Realistic mutation sources between decision and dispatch, assessed individually:

| Source | In scope of PBPC-REQ-055's carve-out? | Realistic within the synchronous gap? |
|---|---|---|
| Concurrent PCAE process (another agent) | Yes — explicitly excluded by PBPC-REQ-055 ("concurrent process activity ... out of scope ... unchanged from today's single-agent-lock model") | Blocked by the agent lock (see 9.4) |
| Another PCAE process bypassing the lock | Same carve-out | Not possible while lock held |
| External `git` process (manual operator command in a second terminal) | **Not excluded** — REQ-055 only names "concurrent process activity" generically but the single-agent-lock model it references governs PCAE-issued commands, not arbitrary shell use | Possible in principle; the gap is a handful of synchronous, I/O-free statements, so the window is extremely narrow but not zero |
| Git hooks | Not excluded | No hook fires between decision and dispatch in the current code (no I/O in the gap to trigger one) |
| Filesystem watcher | Not excluded | Same — no I/O in the gap for a watcher to react to |
| User/manual git command (branch switch, reset, new commit) | Not excluded | Same narrow-window caveat as "external git process" above |
| Branch/HEAD mutation | Not excluded | Same |
| Task state mutation (task contract changed mid-flight) | Not excluded | Same |

**Conclusion:** the current implementation has no intervening I/O in the gap, so *today's specific code path* has essentially no realistic exploit window. But PBPC-REQ-055's out-of-scope carve-out is narrower than what Section 17 is written to catch — REQ-055 excludes **concurrent-process** races under the single-agent-lock model; Section 17 is written to catch **any** local drift immediately before dispatch, regardless of source, including a human operator's own manual git activity in a second terminal, which the lock does not and cannot prevent (see 9.4). REQ-055 does not logically excuse REQ-059-061.

### 9.4 Single-agent-lock boundary

Traced `acquire_agent_lock`/`release_agent_lock` (`src/pcae/core/agent.py:265-330`): the lock is a cooperative JSON file (`.pcae/agent-lock.json`) created with exclusive (`"x"`) mode, checked and enforced only by PCAE's own governed-command code paths. It is **not** an OS-level file lock (`flock`/`fcntl`), has no kernel enforcement, and is invisible to any process that doesn't itself call PCAE's lock-acquisition code.

**Exact boundary: the lock protects against another PCAE-governed agent invoking governed commands concurrently. It provides zero protection against**: a human operator running raw `git` commands in another terminal, a git hook, a filesystem watcher, external CI/automation, or any process that mutates the repository without going through PCAE's own tooling. This is the narrower of the two boundaries the phase brief asked to distinguish, confirmed directly from the lock's implementation.

### 9.5 Normative conformance vs. exploitability

Per this phase's own instruction (Section 15 of the governing brief): exploitability and normative conformance are separate questions. Here:

- **Exploitability today:** very low — no I/O exists in the gap on either path, and the lock (while not a general mutation guarantee) does block the one multi-agent scenario PCAE itself creates.
- **Normative conformance:** **unmet.** PBPC-REQ-059/060/061 use unconditional `SHALL` language, are structurally required by the contract's own control-flow diagram (Section 12), and are listed as a mandatory implementation-acceptance demonstration (PBPC-REQ-091) that 148F's own inspection found **entirely absent** — not weakly implemented, not partially covered by an equivalent mechanism, but simply not present in any form on either dispatch path.

A MUST-level contract requirement with zero implementation and no equivalent substitute is a conformance gap independent of whether an exploit has been (or can currently be) constructed. Low exploitability under today's narrow, I/O-free gap does not retroactively satisfy a structural requirement that exists precisely to remain sound as the code evolves — e.g., a future refactor that inserts any I/O (a log write, a notification call, a config read) between decision and dispatch would silently reopen exactly the window Section 17 exists to close, with no test or contract check currently positioned to catch it.

### 9.6 Classification

**F-148F-3: `REPAIR_REQUIRED_BEFORE_CLOSURE`.** This revises 148F's Non-Blocking classification. The revision is justified by evidence, not re-litigation: 148F correctly found the implementation gap and correctly found no live exploit, but assessed severity primarily through an exploitability lens (148F's own text: "low practical severity ... no exploit constructed"). This phase's operational-readiness mandate requires assessing normative conformance independently of exploitability (per this phase's Section 15 instruction), and under that lens PBPC-REQ-059-061 is a clearly normative, currently and completely unimplemented `SHALL` requirement that PBPC-REQ-090/091 explicitly gate implementation-acceptance on. No contract-provided equivalent exists. The requirement's own purpose — remaining sound as the surrounding code evolves, not just today — is not satisfied by "the current gap happens to be exploit-free."

This is **not** a `CONTRACT_CLARIFICATION_REQUIRED` case: PBPC-REQ-059-061's text is unambiguous about what must be re-observed, when, and what happens on mismatch. It is a bounded, well-specified implementation gap, not an interpretive one.

---

## 10. Requirement-Level Completion Review (compact traceability)

| Section | Requirement group | Status |
|---|---|---|
| §3-11 (scope, terminology, consolidation, ownership) | Architectural/contract-level | VERIFIED (148C.10, unchanged) |
| §12 (Decision Consumption Point positioning) | PBPC-REQ-040/041 | IMPLEMENTED, VERIFIED (148F) |
| §13 (canonical push identity) | PBPC-REQ-042-044 | IMPLEMENTED, VERIFIED (148F) |
| §14 (request construction) | PBPC-REQ-045-050 | IMPLEMENTED, VERIFIED (148F, and re-confirmed §5 above) |
| §15 (decision semantics) | PBPC-REQ-051-054 | IMPLEMENTED, VERIFIED (148F) |
| §16 (TOCTOU analysis) | PBPC-REQ-055-058 | ANALYZED, non-normative (analysis section, not an implementation mandate) — accurate as re-confirmed §9.3-9.4 above |
| **§17 (final pre-dispatch validation)** | **PBPC-REQ-059-061** | **NOT_IMPLEMENTED** — see Section 9 |
| §18 (failure ownership) | PBPC-REQ-062-063 | IMPLEMENTED for every listed row except the unlisted "broker construction failure" case (contract silence — see §11.1 below); VERIFIED for listed rows (148F) |
| §19 (diagnostics) | PBPC-REQ-064-066 | IMPLEMENTED, VERIFIED for `DENY`/`HUMAN_REVIEW`/`evaluate()`-failure; NOT satisfied for construction failure (F-148F-1) |
| §20 (replay/restart) | PBPC-REQ-067-068 | IMPLEMENTED, VERIFIED (148F) |
| §21-26 (IWC/AESIC/runtime/compatibility independence) | Boundary preservation | VERIFIED, unchanged (re-confirmed §12-13 below) |
| §28 (security threat model) | PBPC-REQ-092 | Bypass/identity/replay items VERIFIED; TOCTOU items correctly flagged as "addressed with explicit limitation" / "deferred for true multi-process concurrency" — accurate text, but the local-drift half of the TOCTOU item (Section 17) is unimplemented, not merely "addressed with limitation" |
| §29 (non-goals) | PBPC-REQ-093 | Preserved — no non-goal violated |

No requirement outside §17/§18/§19 (construction-failure row) was found unimplemented or unverified.

---

## 11. PBPA-001 Completion Review

No new PBPA-specific work performed or required this phase. Re-confirmed: PBPA-001 v1.0 unchanged since freeze; 148C.7 verified its implementation with zero Blocking findings; no remaining PBPA-specific Blocking debt. Not re-litigated further (out of this phase's scope; 148F already re-confirmed it independently).

### 11.1 Section 18 contract-silence note

The Section 18 failure-ownership table (PBPC-001 §18) contains no explicit row for "Permission Broker construction failure" — only "Broker evaluation failure (rule raises)." PBPC-REQ-063 asserts the table's ownership scheme is exhaustive ("No failure category above SHALL be owned by more than one component"), but construction failure is a genuinely distinct failure category from evaluation failure and the contract text does not visibly anticipate it. This is a minor **contract-text gap**, not an implementation gap — recorded here as an observation for whichever future phase repairs F-148F-1, since that repair should also add the missing table row (an additive, non-semantic PBPC-001 text change, out of this assessment phase's own authorization to make).

---

## 12. Findings Inventory (full Chapter 148, including historical)

| Finding | Origin | Status | Severity | Closure evidence | Chapter-148-blocking? |
|---|---|---|---|---|---|
| B-1 (`POL-004` universal applicability) | 148C | **CLOSED** (148C.8, ratified 148C.9) | was Blocking | Live re-execution → `ALLOW`, `POL-004` non-applicable (re-confirmed 148D/E/F/G) | No (closed) |
| F-148C.4 (empty-applicable-set textual gap) | 148C.4 | Non-Blocking, unreachable under current matrix | Low | — | No |
| F-148C.4 ("mutation" terminology collision) | 148C.4 | Non-Blocking, disambiguated by later contract text | Low | PBPC-001 §4/§8.1 | No |
| F-148C.8-1 (`simulation_only=False` → `POL-005` DENY) | 148C.8 | Observation, corroborating not defective | n/a | Ratified as EXPECTED_CONTRACT_BEHAVIOR (148C.9) | No |
| V-1..V-7 (148C.7 misc observations) | 148C.7 | Non-Blocking/Observation | Low | Recorded in 148C.7 doc | No |
| F-148F-1 (broker construction failure ungraceful) | 148F | **RETAIN_AS_NON_BLOCKING / TRACK_POST_CHAPTER** (this phase) | Low-Medium (operational, not security) | §8 above | No — see §13 |
| F-148F-2 (other git-push sites out of scope) | 148F | **CLOSE (as Chapter-148 debt); TRACK_POST_CHAPTER (as future capability observation)** | Observation | §7 above | No |
| F-148F-3 (Section 17 not implemented) | 148F | **REPAIR_BEFORE_CERTIFICATION** (revised this phase) | Medium (normative conformance, low current exploitability) | §9 above | **Yes** |
| §11.1 (Section 18 table silence on construction failure) | 148G (new, this phase) | Observation, bundle with F-148F-1's future repair | Low | §11.1 above | No |
| Stale 148C.10 push.py-import invariant test | 148G (new, this phase, incidental) | `TRACK_POST_CHAPTER`, bundle with 148G.1 (test-only, zero-risk) | Low | §17A above | No |
| `tasks/TODO.md` roadmap-staleness (stuck at 137T) | 148G (new, this phase, incidental) | `TRACK_POST_CHAPTER`, unrelated to Chapter 148 | Low | §17A above | No |

No finding was deleted from the chapter narrative; all historical findings are preserved above with their original and (where applicable) revised disposition.

---

## 13. Operational Readiness Matrix

| Area | Status | Evidence | Closure Blocking? |
|---|---|---|---|
| PBPC contract | Frozen v1.2, unamended, VERIFIED (148C.10) | §4 | No |
| PBPA contract | Frozen v1.0, unamended, VERIFIED (148C.7) | §4, §11 | No |
| B-1 | CLOSED, live-re-confirmed this phase | §5 | No |
| Ordinary push gating | Both dispatch sites broker-gated, `ALLOW` required | §6, 31/31 tests passed | No |
| Staged push gating | Broker-gated, `ALLOW` required | §6, 31/31 tests passed | No |
| Non-`ALLOW` fail-closed | `DENY`/`HUMAN_REVIEW`/`evaluate()`-failure all abort, zero dispatch | §6, 148F tests re-run | No |
| Broker construction failure | Uncaught exception, fail-closed but ungraceful diagnostics | §8 | **No** (repair recommended post-closure, not blocking) |
| Final pre-dispatch validation (§17) | **Not implemented on either path** | §9 | **Yes** |
| Mechanical checks (force-push, phase-report trust/identity) | Intact, unaffected by this phase | Re-run 31/31 push/148F suite | No |
| Scope precision (F-148F-2) | 5 dispatch sites total, only 2 in `pcae push` scope, both gated | §6, §7 | No |
| Runtime boundary | Observed/observe/unavailable, unchanged | §1 | No |

---

## 14. Runtime, IWC, AESIC, Runtime Enforcement Boundaries — Reconfirmed

- **Runtime:** `pcae runtime inspect` → `Observed / observe / unavailable`, unchanged before and after this phase. This chapter governs an existing command mutation path; it does not enable autonomous runtime execution.
- **IWC independence:** no Chapter 148 change (including this phase) has turned Confirmation into Approval. `IWC-REQ-029` untouched.
- **AESIC independence:** no Authority Evaluation dependency has become permission-bearing. AESIC remains disclosure-only.
- **Runtime Enforcement independence:** `pcae push` PBPC consumption remains separate from the Runtime Enforcement Decision Engine/Coordinator — no wiring between them exists or was introduced.
- **No durable decision artifact:** still none required or created; PBPC-001 §24's "no durable artifact" assessment stands. In-process result consumption only remains acceptable for this MVP's operational posture — the absence of a durable audit artifact is a pre-existing, disclosed, unchanged design decision, not new debt introduced by this assessment.

## 15. Deferred / Future Strategic Observations (not started this phase)

1. **Prompt Generation / Prompt Creation (Phase 45F)** — remains `partially_ready`: design/data-model exists, live prompt-generation pipeline, prompt dispatch, and agent invocation all inactive. Preserved as **DEFERRED STRATEGIC OBSERVATION**. Not implemented or redesigned this phase. `generated ≠ approved ≠ dispatched ≠ executed` preserved.
2. **Repository-Wide Mutation Permission Coverage** (new, this phase, from F-148F-2 §7) — three pre-existing `git push` dispatch sites (`pcae agent`, two `pcae phase ...` subcommands) sit entirely outside any Permission Broker gate. Recorded as a candidate future strategic capability, not Chapter 148 debt.

Both are recorded without starting either; the next strategic reassessment should choose among them (and any other roadmap gap) rather than either winning by default.

---

## 16. Diagnostics / Exit-Code / Recovery Readiness (F-148F-1-specific)

| Outcome | Diagnostic | Exit code | Retry-safe? |
|---|---|---|---|
| `DENY` | `"Push blocked: permission denied (<reason>)."` + causing policy IDs | 1 | Yes — no mutation occurred |
| `HUMAN_REVIEW` | `"Push blocked: human review required (<reason>)."` | 1 | Yes |
| Broker `evaluate()` failure | `"Push blocked: Permission Broker evaluation failed (<reason>)."` | 1 | Yes |
| Broker construction failure | Raw uncaught Python traceback (via Python's default top-level exception handling under the `pcae = "pcae.cli:main"` console-script entry point) | 1 (Python's standard uncaught-exception exit status) | Yes — nothing was mutated before the exception fires |

Exit code is coincidentally already `1` in all four cases (uncaught exceptions exit `1` under the standard console-script wrapper), so no *exit-code* readiness gap exists — only a *diagnostic-quality* gap (F-148F-1, §8). No stale decision state persists across any of the four outcomes; a retry after any of them is a fresh, independent attempt.

---

## 17. Validation Performed This Phase

```
pcae health / pcae check / pcae status coherence / pcae doctor task-memory /
pcae push check / pcae runtime inspect / pcae notify status   → all clean (§1)
pcae phase-report show --latest / reconcile --phase-id 148F   → reconciled, read-only

python -m pytest tests/test_phase_148f_permission_broker_production_consumption_independent_verification.py \
                  tests/test_permission_broker_push_production_consumption.py -q
  → 31 passed

Live canonical-request re-execution (§5)                       → ALLOW, POL-004 non-applicable

Independent AST-level dispatch-site re-derivation (Explore agent, §6)
  → 5 sites confirmed, 2 in-scope + gated, 3 out-of-scope + ungated

fast_green (python -m pytest -n auto -q -m "not slow")         → run this phase; see Test Results
```

No production or contract file was modified to reach any of the above conclusions. `git diff --name-only <pre-148G-baseline>..HEAD -- src/pcae/` and `-- docs/contracts/` both empty for the duration of this phase's inspection work.

---

## 17A. Incidental Discovery — Test-Suite Hygiene Debt Outside `fast_green`

In addition to the curated `fast_green` gate (§17, 4391/4391 passed, unchanged from the 148D/E/F baseline), this phase also ran a broader, non-curated sweep (`python -m pytest -n auto -q -m "not slow"`, 26,617 additional tests) as part of validating this phase's own conclusions. That sweep is **not** this repository's regression gate and its results do not affect the Chapter 148 verdict, but it surfaced 34 failures worth recording honestly rather than discarding.

Sampled and root-caused (not exhaustively, proportionate to this bounded assessment phase):

- **`tests/test_gate_dry_run_context.py` + `tests/test_project_state.py`** (7 of the 34 failures): re-ran both files in isolation — **all pass** (104/104 combined with the TODO suite below, minus the 3 genuine TODO failures). These are `-n auto` parallel-execution pollution artifacts of the broad sweep, not real defects.
- **`tests/test_bootstrap_todo_consistency.py`** (3 failures — `test_real_todo_no_longer_marks_90_series_as_next`, `test_real_todo_current_roadmap_lists_recommended_phase_as_next`, `test_real_todo_not_flagged_stale_against_real_project_status`): re-ran in isolation — **genuinely fail**, confirmed pre-existing. `tasks/TODO.md`'s "Current Roadmap" table's only `🔜 Next` marker still points at **Phase 137T**, unrelated to and far older than the entire 148-series arc — `tasks/TODO.md` has evidently not been kept in sync with `PROJECT_STATUS.md`'s recommended-next-phase field since at least Phase 138. Not caused by this phase (confirmed via `git log -- tasks/TODO.md` predating 148A), and this phase's own task contract does not authorize touching `tasks/TODO.md`'s roadmap table (out of allowed-files scope) — recorded, not repaired.
- **`tests/test_phase_148c10_pbpc_v12_independent_verification.py::test_push_module_does_not_import_permission_broker`** (1 failure): re-ran in isolation — **genuinely fails**, confirmed pre-existing since Phase 148E. This test was authored in 148C.10 (`git log` shows a single commit, `fe9912bc`, predating 148D/148E) asserting `push.py` never imports `PermissionBroker`/`permission_broker_foundation` — an invariant Chapter 148's own MVP (148E) *deliberately* violated by design. The test was never updated after 148E's intentional wiring, and — because it carries no `fast_green` marker and none of 148D/E/F's own curated "push regression" file lists happened to include it — this contradiction has been silently latent since 148E and undetected by three subsequent phases (148E, 148F, and nearly 148G).
- Remaining ~23 failures (`test_shell_gate.py`, `test_cltr_migration_135p_verification.py`, `test_cltr_135o_integration.py`, `test_phase_137i1_finalization_ordering_deadlock.py`) not individually isolated by this phase — the confirmed pattern above (parallel-sweep pollution for two files, genuine pre-existing staleness for the other two) makes both explanations plausible for the remainder; resolving which is which is disproportionate to this bounded assessment and unrelated to Permission Broker/`pcae push` in any case.

**Disposition:** recorded as a new Observation, **`REPOSITORY_TEST_HYGIENE_DEBT — TRACK_POST_CHAPTER`**, not Chapter-148-blocking (production code is unaffected — `git diff --name-only <pre-148G>..HEAD -- src/pcae/` remains empty throughout — and the actual regression gate, `fast_green`, is unaffected and unchanged). The one item genuinely caused by Chapter 148 itself (the stale 148C.10 invariant test) is a natural companion to the 148G.1 repair phase already recommended for F-148F-1/F-148F-3 — updating or retiring that assertion is a test-only, zero-risk change appropriate to bundle there. The `tasks/TODO.md` roadmap-staleness item is unrelated to Chapter 148 and is recorded purely as an incidental discovery for whoever next maintains `tasks/TODO.md`'s roadmap table.

## 18. Chapter Readiness Verdict

**NOT READY — BOUNDED REPAIR REQUIRED BEFORE CHAPTER 148 CERTIFICATION.**

Driven specifically by F-148F-3 (§9): PBPC-REQ-059-061 is a clear, unambiguous, currently and completely unimplemented `SHALL` requirement that the contract itself (PBPC-REQ-090/091) gates implementation-acceptance on. F-148F-1 (§8) and F-148F-2 (§7) are **not**, independently, closure-blocking — both are RETAIN_AS_NON_BLOCKING / TRACK_POST_CHAPTER.

### Finding-specific disposition

| Finding | Disposition |
|---|---|
| F-148F-1 | `RETAIN_AS_NON_BLOCKING` — recommended for the same narrow future hardening phase as F-148F-3's repair (cheap, low-risk, same file), but does not itself block certification |
| F-148F-2 | `CLOSE` as Chapter-148 debt (correctly out of MVP scope, per PBPC-REQ-004/005); `TRACK_POST_CHAPTER` as the "Repository-Wide Mutation Permission Coverage" future strategic observation |
| F-148F-3 | `REPAIR_BEFORE_CERTIFICATION` |
| §11.1 (Section 18 table silence) | `TRACK_POST_CHAPTER` — bundle into the same repair phase as F-148F-1 (additive contract-text row, not a behavior change) |

### Recommended next phase

**148G.1 — Permission Broker Production Consumption Operational Hardening** (bounded repair phase), scoped to exactly:

1. Implement PBPC-REQ-059/060/061: immediately before each of `push.py`'s two `git push` dispatch calls, re-observe local HEAD revision, local branch, unpushed-commit count, and active task ID; on any mismatch against the values bound into the evaluated request, treat the `ALLOW` decision as invalid and abort with zero dispatch (no silent re-authorization).
2. Widen `_evaluate_push_permission`'s `try:` block to also cover `PermissionBroker()` construction (matching the existing `command_path_observation.py:70-84` precedent), producing the same clean `"Push blocked: Permission Broker ... failed (...)"` diagnostic family as the `evaluate()`-failure path, rather than an uncaught traceback (F-148F-1).
3. Add the missing "Permission Broker construction failure" row to PBPC-001 §18's failure-ownership table (additive, non-semantic contract-text repair, §11.1).
4. Update or retire `tests/test_phase_148c10_pbpc_v12_independent_verification.py::test_push_module_does_not_import_permission_broker`, which has asserted the opposite of Chapter 148's own intended design since Phase 148E (§17A) — test-only, zero-risk.

Do not combine with unrelated future repository-wide mutation-governance work (§15, item 2) — that remains a separate, not-yet-started strategic candidate.

After 148G.1 completes and is independently verified, a dedicated **148H — Permission Broker Production Consumption Chapter Certification** phase (or repository-conventional equivalent) should formally certify Chapter 148 against the criteria in §19 below.

## 19. Chapter Certification Criteria (for the next certification phase, not certified here)

1. PBPC-001 v1.2 verified (already true — 148C.10)
2. PBPA-001 v1.0 verified (already true — 148C.7)
3. B-1 closed (already true — 148C.8/148C.9, re-confirmed 148D/E/F/G)
4. Production wiring verified (already true — 148F)
5. Both `pcae push` paths non-bypassably gated (already true — 148E/148F/148G)
6. **PBPC-REQ-059-061 implemented and independently verified** (pending — 148G.1 + its own verification phase)
7. F-148F-1 repaired (pending — 148G.1)
8. No unresolved Blocking findings (pending — contingent on 6-7)
9. Retained findings (F-148F-2, §11.1) explicitly accepted and recorded (already done — this phase)
10. Scope claims accurately stated (`pcae push` path governed; repository-wide git-push is not) (already done — this phase, §7)
11. Runtime unchanged (already true, re-confirmed every phase including this one)

---

## Explicit Confirmations

- PBPC-001 v1.2 remains unchanged.
- PBPA-001 v1.0 remains unchanged.
- 148C-B-1 remains CLOSED (independently re-confirmed, not re-discovered).
- Phase 148G modified no production code (`git diff --name-only <pre-148G>..HEAD -- src/pcae/` empty).
- The two real `git push` dispatch paths reachable through `pcae push` remain Permission-Broker gated.
- No Chapter-148 scope claim is made over the unrelated `pcae agent` or `pcae phase ...` git-push paths.
- No new push policy was introduced.
- No approval was fabricated.
- No `POL-001..012` meaning was changed.
- Interactive Workflow Confirmation remains independent.
- Authority Evaluation / AESIC remains disclosure-only.
- No Runtime Enforcement behavior was changed.
- Prompt Generation remains design-only / `partially_ready` and DEFERRED.
- No Prompt Generation, Prompt Dispatch, or agent invocation capability was implemented.
- Runtime remains Observed, maximum capability remains observe, execution availability remains unavailable.
