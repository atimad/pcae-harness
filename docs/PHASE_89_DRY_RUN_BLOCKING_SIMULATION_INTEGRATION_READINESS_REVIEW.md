# Phase 89F — Dry-Run Blocking Simulation Integration Readiness Review

```
phase_name    = phase_89f_dry_run_simulation_integration_readiness_review
phase_version = 1.0
phase_status  = completed
implementation_status = review_only
recommended_next_phase = 89g_enforcement_readiness_threat_model
```

## 1. Purpose

Assess whether the dry-run blocking simulation layer (89B–89E) is ready to become a guarded integration point in PCAE. Define exactly what remains before any real blocking/enforcement path can be designed or implemented. Produce a clear ready/not-ready assessment with required guardrails.

This is a **review document**. No implementation is performed in 89F.

## 2. Scope

In scope (review only):

- Review dry-run architecture from 89B–89E
- Review CLI command coverage and stability
- Review JSON contract stability
- Review human-readable UX readiness
- Review integration touchpoints with advisory mode, permission broker, shell gate
- Define "ready" vs "not ready" criteria for each integration point
- Define required guardrails before any enforcement phase
- Define required tests, audit model, and rollback plan before enforcement
- Define operator workflow today
- Identify remaining risks and deferred defects

Out of scope:

- Implementing enforcement, blocking, shell interception
- Changing source or test behavior
- Creating Phase 89G task contract

## 3. Non-Goals

89F must not and does not implement enforcement, blocking, shell interception, wrappers, backend invocation, authorization, or any source/test changes.

## 4. Starting Point from 89B–89E

Five phases built the dry-run simulation layer:

| Phase | Name | Type | Deliverable |
|-------|------|------|-------------|
| 89B | Design | Design | 36-section design document |
| 89C | Prototype | Implementation | `pcae dry-run check/explain/status`, 74 tests |
| 89D | Test Matrix | Tests | 244 tests, 24 CLI tests, 8 categories |
| 89E | UX Refinement | UX | Structured output, 7 helper sections, fixed wording |

**Current test baseline:** 9,311 passed, zero failures, 19:39 full suite.

## 5. Current Dry-Run Capabilities

### 5.1 Commands

| Command | Purpose | Status |
|---------|---------|--------|
| `pcae dry-run check --command "<cmd>"` | Simulate enforcement evaluation | ✅ Stable |
| `pcae dry-run check --command "<cmd>" --json` | Machine-readable simulation | ✅ Stable, 50+ fields |
| `pcae dry-run explain --decision <d>` | Explain a simulation decision | ✅ Stable, 19 decisions |
| `pcae dry-run explain --decision <d> --json` | Machine-readable explanation | ✅ Stable |
| `pcae dry-run status` | Report simulation invariants | ✅ Stable |
| `pcae dry-run status --json` | Machine-readable status | ✅ Stable |

### 5.2 Decision Vocabulary (19 values, stable)

```
would_allow_read_only
would_allow_governed_preflight_only
would_require_active_task
would_require_preflight
would_require_human_review
would_require_more_evidence
would_block_by_scope
would_block_by_task_contract
would_block_by_raw_git_push
would_block_by_force_push
would_block_by_shell_gate
would_block_by_test_run_lock
would_block_by_failed_health
would_block_by_failed_check
would_block_by_failed_doctor
would_block_by_push_check
would_block_by_conflicting_evidence
would_deny
unknown
```

### 5.3 Classification Categories

- 10 command category coverage (read-only, git hard blocks, dangerous fs, secret, etc.)
- Shell embedded commands via -c/-lc
- Compact operator splitting (|, &&, ||, ; without spaces)
- Env prefix inspection with secret detection

### 5.4 Test Coverage

| Category | Tests |
|----------|-------|
| Envelope structure | 3 |
| Invariant false fields | 33 |
| Safety invariants object | 2 |
| Simulation ID uniqueness | 2 |
| Decision mapping | 7 |
| Severity model | 4 |
| Enforcement readiness | 2 |
| Hard-block preservation | 7 |
| Secret redaction | 8 |
| Explain coverage | 21 |
| Status coverage | 2 |
| JSON stability | 22 |
| Read-only paths | 14 |
| Shell embedded | 8 |
| Env-prefix | 5 |
| Compact operators | 8 |
| Compound commands | 3 |
| Safety cross-check | 15 |
| CLI exit codes | 8 |
| CLI JSON stability | 7 |
| CLI human-readable | 6 |
| **Total** | **244 + 24 CLI** |

## 6. Current Safety Invariants

### 6.1 Permanent Invariants (All Verified)

| # | Invariant | Status |
|---|-----------|--------|
| SI-1 | `command_executed` is always `false` | ✅ 244 tests |
| SI-2 | `shell_intercepted` is always `false` | ✅ |
| SI-3 | `wrapper_installed` is always `false` | ✅ |
| SI-4 | `authorization_granted` is always `false` | ✅ |
| SI-5 | `execution_authorized` is always `false` | ✅ |
| SI-6 | `enforcement_applied` is always `false` | ✅ |
| SI-7 | `backend_invoked` is always `false` | ✅ |
| SI-8 | `prompt_sent` is always `false` | ✅ |
| SI-9 | Redacted commands never appear in output | ✅ |
| SI-10 | Simulation footer present in every output | ✅ |
| SI-11 | JSON contains all required schema fields | ✅ |
| SI-12 | Hard blocks are non-overridable | ✅ |
| SI-13 | `simulation_mode` is always `true` | ✅ |
| SI-14 | `safety_invariants.simulation_only` is always `true` | ✅ |

## 7. CLI Readiness Review

### Assessment: READY for operator use

| Criterion | Status | Notes |
|-----------|--------|-------|
| Commands discoverable | ✅ | `pcae dry-run --help` works |
| Subcommands clear | ✅ | check/explain/status |
| Required flags handled | ✅ | --command required for check |
| Exit codes differentiated | ✅ | 0=allow, 1=blocked, ≠0=error |
| Error messages helpful | ✅ | Missing --command gives argparse error |
| JSON mode stable | ✅ | --json flag on all three commands |
| Human-readable complete | ✅ | Structured sections per 89E |
| No shell modification | ✅ | Purely CLI invocation |

**Gap:** No shell completion or autocomplete support (deferred).

## 8. JSON Contract Readiness Review

### Assessment: READY for machine consumption

| Criterion | Status | Notes |
|-----------|--------|-------|
| Schema version declared | ✅ | `"0.1"` |
| All required fields present | ✅ | 26 verified across 7 command types |
| Field types stable | ✅ | Booleans, strings, arrays consistent |
| Decision values stable | ✅ | 19 values, same as advisory |
| Safety invariants explicit | ✅ | 10-field object, all true |
| Known limitations explicit | ✅ | Array of strings |
| Redaction contract stable | ✅ | `redaction_applied` + `redaction_reason` |
| Simulation ID format stable | ✅ | `sim-` + 12 hex chars |
| Enforcement stage explicit | ✅ | `"dry_run_simulation"` |

**Gap:** No schema versioning policy defined for future breaking changes.

## 9. Human-Readable UX Readiness Review

### Assessment: READY for operator use

| Criterion | Status | Notes |
|-----------|--------|-------|
| Severity banner | ✅ | 5 levels with emoji |
| Decision clearly stated | ✅ | Simulation: would_* |
| Blocked reasoning clear | ✅ | Type + Override + Governed alternative |
| Allowed includes non-auth note | ✅ | "Allow does NOT mean PCAE authorizes" |
| Review includes gate distinction | ✅ | "GATE (not a block)" |
| Redaction warning in review | ✅ | When secrets detected |
| Footer explicit | ✅ | Active "PCAE did NOT" checklist |
| Next action actionable | ✅ | Dry-run explain, not advisory |

**Gaps:** No `--no-color` / `--plain` mode. Unicode emoji may not render on all terminals. No `--verbose` mode.

## 10. Advisory Integration Readiness

### Assessment: READY — stable consumer relationship

| Criterion | Status |
|-----------|--------|
| Delegates to advisory via `build_advisory()` | ✅ |
| Advisory's broker→advisory mapping reused | ✅ |
| Advisory's operator messages consumed | ✅ |
| Advisory's redaction rules inherited | ✅ |
| Advisory's performed flags preserved false | ✅ |
| Does not modify advisory behavior | ✅ |

**Relationship:** Dry-run simulation is a **consumer** of advisory output. It wraps advisory results in a simulation envelope without modifying the advisory decision. If advisory behavior changes, simulation inherits those changes automatically — this is correct and desirable.

## 11. Permission Broker Integration Readiness

### Assessment: READY — indirect consumer (via advisory)

| Criterion | Status |
|-----------|--------|
| Broker called internally via advisory | ✅ |
| Broker decisions preserved in simulation | ✅ |
| Broker hard blocks not softened | ✅ |
| Broker evidence sources propagated | ✅ |
| Does not modify broker behavior | ✅ |

**Relationship:** Dry-run simulation consumes broker output indirectly through advisory mode. The broker remains the single source of truth for governance decisions. Simulation adds presentation metadata (severity, enforcement readiness, governed alternatives) without changing the underlying decision.

## 12. Shell Gate Integration Readiness

### Assessment: READY — indirect consumer (via broker→advisory)

| Criterion | Status |
|-----------|--------|
| Shell gate called internally via broker→advisory | ✅ |
| Shell gate classification preserved | ✅ |
| Shell gate hard blocks propagated | ✅ |
| Shell gate secret detection propagated | ✅ |
| 89A classification fixes inherited | ✅ |
| Does not modify shell gate behavior | ✅ |

**Relationship:** Dry-run simulation is two layers removed from shell gate (via broker, via advisory). Shell gate improvements (89A) flow through automatically. No direct dependency on shell gate internals.

## 13. Future Enforcement Integration Readiness

### Assessment: NOT READY — requires explicit design phase

| Criterion | Status | Gap |
|-----------|--------|-----|
| Decision vocabulary forward-compatible | ✅ | Same values advisory uses |
| Severity model forward-compatible | ✅ | Already maps to enforcement stages |
| JSON schema forward-compatible | ✅ | `simulation_mode: false` → `enforcement_mode: true` |
| Hard blocks non-overridable design | ✅ | Invariant documented |
| **Enforcement design document** | ❌ | Does not exist |
| **Enforcement task contract** | ❌ | Does not exist |
| **No-enforcement-to-enforcement migration** | ❌ | Not designed |
| **Audit trail design** | ❌ | Not designed |
| **Rollback plan** | ❌ | Not designed |
| **Operator approval model** | ❌ | Not designed |
| **Bypass detection** | ❌ | Not designed |
| **Failure-mode tests** | ❌ | Not designed |
| **Threat model** | ❌ | Not designed |

**Gap summary:** The simulation layer produces the right decisions, but the infrastructure to turn those decisions into real enforcement (audit, rollback, approval, bypass detection, threat model) does not exist and has not been designed.

## 14. Ready/Not-Ready Assessment

### Ready (can be used today)

| Capability | Readiness | Rationale |
|-----------|-----------|-----------|
| Operator dry-run command checking | ✅ Ready | CLI stable, UX refined, exit codes clear |
| JSON machine consumption | ✅ Ready | Schema stable, all fields present |
| Hard-block preview | ✅ Ready | Non-overridable, governed alternatives |
| Redaction preview | ✅ Ready | All secret classes detected and redacted |
| Decision explanation | ✅ Ready | All 19 decisions explainable |
| CI/CD integration (informational) | ✅ Ready | Stable exit codes and JSON |
| Integration with advisory/broker/shell-gate | ✅ Ready | Clean consumer relationship |

### Not Ready (must not be used yet — requires design/implementation)

| Capability | Readiness | What's Missing |
|-----------|-----------|----------------|
| Real blocking | ❌ Not Ready | Enforcement design, audit, rollback, bypass detection |
| Shell interception | ❌ Not Ready | Shell wrapper design, configuration management, disable mechanism |
| Backend execution gate | ❌ Not Ready | Backend invocation interception, prompt capture prevention |
| Automatic command denial | ❌ Not Ready | Deny mechanism, override workflow, emergency disable |
| Persistent authorization state | ❌ Not Ready | State storage design, expiration, revocation |
| Accepted-risk override workflow | ❌ Not Ready | Risk acceptance model, approval chain, audit trail |
| Human-approval override workflow | ❌ Not Ready | Approval model, multi-party approval, timeout/expiry |

## 15. Required Guardrails Before Enforcement

### 15.1 Design Guardrails

| # | Guardrail | Description |
|---|-----------|-------------|
| G1 | Enforcement design document | Separate phase (89G+) defining how simulation decisions become real blocks |
| G2 | Enforcement task contract | Explicit task scope, allowed files, forbidden zones |
| G3 | No-enforcement-to-enforcement migration checklist | Documented steps from simulation to blocking |
| G4 | Operator approval model | Who can approve, how approval is recorded, expiry |
| G5 | Bypass detection design | How to detect and log operator bypass of enforcement |
| G6 | Emergency disable mechanism | How to disable enforcement in an emergency |

### 15.2 Test Guardrails

| # | Guardrail | Description |
|---|-----------|-------------|
| G7 | Failure-mode tests | What happens when enforcement fails mid-operation |
| G8 | Cross-platform shell tests | Verify enforcement on bash, zsh, sh |
| G9 | Command parsing threat model | Adversarial inputs, obfuscation, encoding attacks |
| G10 | Safety invariant tests | Prove enforcement cannot be bypassed through classification gaps |
| G11 | Performance regression tests | Enforcement must not slow governed operations |

### 15.3 Infrastructure Guardrails

| # | Guardrail | Description |
|---|-----------|-------------|
| G12 | Audit trail design | Every enforcement action logged, immutable, redacted |
| G13 | Rollback plan | How to revert from enforcement to simulation-only |
| G14 | JSON schema versioning policy | How breaking changes to the schema are managed |
| G15 | CLI compatibility policy | How breaking changes to CLI flags are managed |
| G16 | State storage design | Where enforcement state lives, how it's cleaned up |

## 16. Required Tests Before Enforcement

### 16.1 Minimum Test Suite

| Category | Minimum Tests | Description |
|----------|--------------|-------------|
| Enforcement decision equivalence | 50 | Enforcement decisions match simulation decisions |
| Block enforcement verification | 30 | Blocked commands are actually blocked |
| Allow enforcement verification | 20 | Allowed commands are actually allowed (no false blocks) |
| Bypass detection | 15 | Direct shell execution is detected and logged |
| Emergency disable | 10 | Disable mechanism works and restores normal shell |
| Audit trail integrity | 15 | Every enforcement action produces correct audit record |
| Rollback verification | 10 | Rollback from enforcement to simulation works |
| Cross-platform (bash/zsh/sh) | 20 | Enforcement works on all supported shells |
| Performance | 10 | Enforcement overhead within acceptable bounds |
| Threat model adversarial | 20 | Obfuscated commands, encoding tricks, injection attempts |
| **Total minimum** | **~200** | |

### 16.2 Existing Tests That Apply

The existing 244 simulation tests + 24 CLI tests provide coverage for:
- Decision correctness (all 19 values)
- Invariant preservation (12 invariants)
- Hard-block behavior
- Redaction behavior
- JSON stability
- CLI behavior

These tests validate the decision-making path. Enforcement tests would add the blocking-enforcement path on top of the same decisions.

## 17. Required Audit/Rollback Model Before Enforcement

### 17.1 Audit Requirements

| Requirement | Status |
|-------------|--------|
| Immutable audit log of enforcement actions | Not designed |
| Redacted command text in audit records | Design exists (88V.1/89A redaction) |
| Timestamp, operator, decision, outcome per action | Not designed |
| Audit log in `.pcae/enforcement/` | Not designed |
| No raw secrets in audit logs | Guarantee must be proven |

### 17.2 Rollback Requirements

| Requirement | Status |
|-------------|--------|
| `pcae enforcement disable` command | Not designed |
| Rollback removes enforcement hooks/wrappers | Not designed |
| Rollback preserves audit history | Not designed |
| Rollback tested before enforcement goes live | Not designed |
| Operator can always disable enforcement | Design principle |

## 18. Operator Workflow Today

### 18.1 Current Workflow (Simulation-Only)

```
1. Operator has a command they want to run
   Example: git push origin main

2. Operator runs dry-run simulation (optional, informational)
   pcae dry-run check --command "git push origin main"

3. Simulation shows what enforcement would decide
   🚫 SIMULATED BLOCK — would_block_by_raw_git_push
   Governed alternative: pcae push

4. Operator reads simulation output
   Understands: raw git push would be blocked
   Learns: pcae push is the governed alternative

5. Operator decides what to do
   Option A: Use governed alternative (pcae push)
   Option B: Run command directly (at own risk)
   Option C: Investigate further (pcae dry-run explain)

6. PCAE never executed, intercepted, or blocked anything
   The operator retained full authority throughout.
```

### 18.2 Workflow Properties

- **Optional:** Operator chooses whether to use simulation
- **Informational:** Simulation provides information, not permission
- **Educational:** Operator learns PCAE governance through simulation
- **Non-blocking:** Operator can always ignore simulation and run commands directly
- **Stateless:** Each simulation is independent

## 19. Risks and Deferred Defects

### 19.1 Known Risks

| # | Risk | Severity | Mitigation |
|---|------|----------|------------|
| R1 | Operator ignores simulation and runs blocked commands | Low (by design) | Simulation is informational; enforcement will address this |
| R2 | Classification false positives cause unnecessary SIMULATED BLOCK | Low | 89A fixed known FPs; remaining FPs documented |
| R3 | Classification false negatives miss dangerous commands | Medium | Documented FN (echo $VAR, cat .env, sudo prefix) |
| R4 | Operator confusion between simulation and enforcement | Low | Clear "simulation only" messaging everywhere |
| R5 | Shell expansion before simulation evaluation | Low | Simulation evaluates command text, not expanded result |

### 19.2 Deferred Defects

| # | Defect | Deferred To |
|---|--------|------------|
| D1 | `echo $OPENAI_API_KEY` not redacted | Shell expansion detection (future) |
| D2 | `cat .env` not redacted | Secret file prefix expansion (future) |
| D3 | `sudo rm -rf /` not classified | Sudo prefix handling (future) |
| D4 | No `--no-color` / `--plain` output mode | UX polish phase |
| D5 | No `--verbose` mode for evidence chain | UX polish phase |
| D6 | No shell completion support | CLI polish phase |
| D7 | No schema versioning policy | Before first breaking JSON change |
| D8 | No CLI compatibility policy | Before first breaking CLI change |

## 20. Recommended Next Phase

### Recommendation: 89G — Enforcement Readiness Threat Model and Safety Case

**Rationale:** Before any enforcement implementation begins, PCAE needs a threat model and safety case that defines:

1. **Threat model:** What attacks could bypass enforcement? How would an adversary try to execute blocked commands? What classification gaps could be exploited?

2. **Safety case:** Why is it safe to let PCAE block commands? What invariants must hold? What happens if enforcement fails? How is the operator protected from PCAE misclassifying their commands?

3. **Enforcement staging:** Per the 88V enforcement model, Stage 3 (Blocking Gate Dry-Run) is the next stage after Stage 1 (Advisory) and Stage 2 (Simulation). The threat model should define the exact transition criteria.

4. **Operator consent model:** How does an operator opt into enforcement? Can they opt out? Is enforcement per-repository, per-shell, or per-session?

This is the logical next step before the enforcement implementation phase (89H+).

### Alternative Considered

**89G — Enforcement Implementation Prototype:** Skipping the threat model and going straight to implementation. **Rejected** — the gaps identified in §13–§17 are too significant to skip. Building enforcement without a threat model risks implementing blocking behavior that can be bypassed or that blocks legitimate operator workflows.

### Summary of Phase 89 Series

| Phase | Type | Status | Key Outcome |
|-------|------|--------|-------------|
| 89B | Design | ✅ | 36-section simulation design |
| 89C | Implementation | ✅ | `pcae dry-run check/explain/status` |
| 89D | Test Matrix | ✅ | 268 tests, 8 categories |
| 89E | UX Refinement | ✅ | Structured output, explicit non-auth |
| 89F | Readiness Review | ✅ | Ready for simulation, not for enforcement |
| 89G | Threat Model | 🔜 | Safety case before enforcement |
