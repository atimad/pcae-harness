# Phase 89B — Dry-Run Blocking Simulation Design

```
phase_name    = phase_89b_dry_run_blocking_simulation_design
phase_version = 1.0
phase_status  = completed
implementation_status = design_only
recommended_next_phase = 89c_dry_run_blocking_simulation_prototype
```

## 1. Purpose

Define PCAE's dry-run blocking simulation layer — the bridge between advisory mode (Stage 1: "would block") and blocking enforcement (Stage 3: "is blocked"). Dry-run blocking simulation shows exactly what PCAE would block, allow, require review for, or require evidence for — but never actually enforces, intercepts, wraps, or executes anything.

This is a **design document**. No implementation is performed in 89B.

## 2. Scope

In scope (design only):

- Definition of dry-run blocking simulation and its boundaries
- Relationship to advisory mode, permission broker, shell gate, and gate dry-run
- Simulation decision vocabulary, severity model, and recommendation model
- JSON and human-readable output models
- Hard-block, human-review, missing-evidence, read-only-allow, and secret-redaction simulation behavior
- Accepted-risk and human-approval boundaries
- Safety invariants, failure modes, and known limitations
- Future test matrix and implementation roadmap
- Command namespace recommendation

Out of scope:

- Implementing dry-run blocking simulation
- Implementing real blocking or enforcement
- Shell interception, wrappers, or shell configuration modification
- Executing command text, invoking backends, sending prompts, capturing outputs
- Granting authorization
- Changing shell-gate, permission-broker, or advisory behavior
- Persistent state, cache, or audit logging
- Phase 89C task contract or any phase beyond 89B

## 3. Non-Goals

89B must not and does not:

- Implement dry-run blocking simulation or any CLI command
- Implement real blocking or enforcement
- Implement shell interception or wrappers
- Modify shell configuration
- Execute requested command text
- Invoke backends, send prompts, capture outputs, or perform intake/adoption
- Grant real authorization
- Change shell-gate classification behavior
- Change permission-broker behavior
- Change advisory mode behavior
- Persist simulation state or add cache

## 4. Starting Point from Advisory Mode

### 4.1 Advisory Mode (Stage 1)

Current advisory mode (88X, 88Y, 88Z, 89A) provides:

```
pcae advisory check --command "<cmd>" [--json]
pcae advisory explain --decision <decision> [--json]
pcae advisory status [--json]
```

Advisory mode:
- Evaluates commands through shell gate + broker → advisory decision
- Reports "would block" / "would require" / "would allow" decisions
- Never executes, intercepts, blocks, or authorizes
- Uses "advisory only" language throughout
- 292 tests, all authorization/performed flags false

### 4.2 Advisory mode is informational only

The operator must manually:
1. Read the advisory output
2. Understand the decision
3. Decide what to do
4. Act (use governed command, run directly, or resolve block)

There is no simulation of "what blocking would feel like" — the operator never experiences a PCAE-governed execution path where blocking is simulated interactively.

### 4.3 What's missing

The gap between advisory mode and enforcement:

| Layer | Exists? | What it does |
|-------|---------|-------------|
| Advisory mode | ✅ 88X | Tells operator "would block" / "would allow" |
| **Dry-run blocking simulation** | ❌ | Shows operator what the blocking experience would be like, with structured simulation output |
| Real blocking gate | ❌ | Actually blocks commands in governed context |

89B designs the middle layer.

### 4.4 Enforcement Staging (88V)

Per the 88V enforcement staging model:

| Stage | Name | Status |
|-------|------|--------|
| 0 | Read-Only Classification | ✅ Implemented (shell gate + broker) |
| 1 | Advisory | ✅ Implemented (pcae advisory check/explain/status) |
| 2 | Advisory With Warnings | 🔜 Future |
| 3 | Blocking Gate (Dry-Run) | 📋 Designed here |
| 4 | Execution Gate With Human Approval | 🔜 Future |
| 5 | Enforcement With Accepted Risk | 🔜 Future |
| 6 | Full Enforcement | 🔜 Future |

## 5. Definition of Dry-Run Blocking Simulation

### 5.1 Core Definition

Dry-run blocking simulation is a **read-only, non-authorizing, non-intercepting** simulation layer that evaluates a proposed shell command and produces a structured simulation result showing exactly what PCAE would decide if enforcement were active — including whether the command would be blocked, require review, require evidence, or be allowed — while never actually blocking, intercepting, executing, or authorizing anything.

### 5.2 Key Properties

1. **Simulation-only.** Every output explicitly states that this is a simulation. No enforcement occurred. No command was executed.

2. **Uses the same evidence chain as enforcement would.** Shell gate → broker → simulation decision. The classification is identical to what enforcement would use.

3. **Shows the same decision as enforcement would.** If enforcement would block, simulation returns `would_block_by_*`. If enforcement would require review, simulation returns `would_require_human_review`.

4. **Adds simulation-specific metadata.** Unlike advisory mode, simulation output includes simulation-specific fields: `simulation_mode`, `simulation_severity`, `simulation_id`, `enforcement_would_apply`.

5. **Designed for interactive and CI/CD use.** Human-readable output for operator interaction; JSON output for CI/CD pipelines and automated governance checks.

### 5.3 What Simulation Adds Beyond Advisory Mode

| Feature | Advisory Mode | Dry-Run Simulation |
|---------|--------------|-------------------|
| Decision language | "would block" (advisory) | "SIMULATED: would block" (closer to enforcement feel) |
| Operator posture | "You may still run this" | "If enforcement were active, this is what you would see" |
| CI/CD integration | JSON parsing | JSON + exit codes + severity filtering |
| Enforcement readiness | Informs operator | Prepares operator for enforcement experience |
| Blocking preview | Conceptual | Experiential — operator sees blocking output format |

## 6. What Simulation Is Not

### 6.1 Not Enforcement

Simulation never blocks, denies, or prevents any command. The operator can always run the command directly in their shell. Simulation is informational.

### 6.2 Not Authorization

Simulation does not grant `execution_authorized = true` or `authorization_granted = true`. It does not approve, bless, or sanction any command.

### 6.3 Not Shell Interception

Simulation does not wrap `bash`, `zsh`, or any shell. It does not intercept commands typed at a prompt. It is explicitly invoked: `pcae dry-run check --command "..."`.

### 6.4 Not a Bypass

Simulation does not provide a way to bypass or work around governance. Hard blocks remain hard blocks in simulation output. Simulation does not suggest workarounds.

### 6.5 Not a Replacement for Advisory Mode

Advisory mode and simulation mode serve different purposes:
- **Advisory mode**: "What would PCAE decide?" — Quick, informational, operator-learning tool
- **Simulation mode**: "What would the blocking experience be like?" — Closer to enforcement, structured output, CI/CD-ready

Both should coexist. Advisory mode for quick checks; simulation mode for enforcement readiness.

## 7. Operator Personas

Same five personas as defined in 88Z §5, with additional simulation-specific needs:

| Persona | Simulation-Specific Need |
|---------|-------------------------|
| **Task Developer** | Preview what enforcement would block before committing |
| **Reviewer** | Verify simulation decisions match expected enforcement behavior |
| **Release Operator** | Pre-flight push simulation; verify no blocking surprises |
| **Oncall/Diagnostician** | Debug why simulation blocks a command that advisory mode allows |
| **CI/CD Pipeline** | Consume simulation JSON with stable exit codes for automated gating |

Additional simulation-specific persona:

| Persona | Role | Primary Simulation Use |
|---------|------|----------------------|
| **Enforcement Evaluator** | Operator preparing for PCAE enforcement rollout | Run simulation against typical workflows; identify false positives before enforcement goes live; build confidence in enforcement rules |

## 8. Operator Workflow

### 8.1 Primary Workflow: Pre-Enforcement Simulation

```
┌─────────────────────────────────────────────────────────┐
│ 1. OPERATOR HAS A COMMAND THEY PLAN TO RUN              │
│    Under future enforcement, this would be checked.     │
├─────────────────────────────────────────────────────────┤
│ 2. OPERATOR RUNS DRY-RUN SIMULATION                     │
│    pcae dry-run check --command "git push origin main"   │
├─────────────────────────────────────────────────────────┤
│ 3. SIMULATION EVALUATES (read-only, no execution)        │
│    - Shell gate classifies the command                  │
│    - Broker aggregates evidence and decides             │
│    - Simulation layer wraps the result                  │
├─────────────────────────────────────────────────────────┤
│ 4. SIMULATION OUTPUT IS PRINTED                         │
│    Shows what enforcement would show:                   │
│    - Decision with SIMULATED prefix                     │
│    - Severity with visual indicator                     │
│    - Block/require/allow status                         │
│    - Hard block detail if present                       │
│    - Recommended governed alternative                   │
│    - What would happen under real enforcement           │
├─────────────────────────────────────────────────────────┤
│ 5. OPERATOR READS SIMULATION OUTPUT                     │
│    Understands what enforcement would do.               │
│    Identifies any unexpected blocks.                    │
├─────────────────────────────────────────────────────────┤
│ 6. OPERATOR ACTS                                        │
│    Path A: Use governed alternative                     │
│    Path B: Report unexpected block (potential FP)       │
│    Path C: Satisfy requirements and re-simulate         │
│    Path D: Understand enforcement and proceed           │
├─────────────────────────────────────────────────────────┤
│ 7. SIMULATION EXITS. NO ENFORCEMENT OCCURRED.           │
│    No command was executed. No shell intercepted.       │
│    No authorization granted. This was a simulation.     │
└─────────────────────────────────────────────────────────┘
```

### 8.2 Enforcement Rollout Workflow

```
For each typical workflow command:
  1. pcae dry-run check --command "<cmd>"
  2. Review simulation decision
  3. If unexpected block → investigate, report potential FP
  4. If expected behavior → note for enforcement transition
  5. Repeat for all workflow commands
  6. Build confidence in enforcement behavior
```

## 9. Relationship to Advisory Mode

### 9.1 Shared Infrastructure

Both advisory mode and dry-run simulation use the same evidence chain:
```
command_text → shell_gate.classify → broker.decide → decision
```

The classification and decision logic is identical. The difference is in presentation and operator framing.

### 9.2 Key Differences

| Aspect | Advisory Mode | Dry-Run Simulation |
|--------|--------------|-------------------|
| **Framing** | "PCAE Advisory Mode — Non-Authorizing" | "PCAE Dry-Run Simulation — SIMULATED BLOCK" |
| **Decision prefix** | `would_*` (advisory decisions) | Same `would_*` values, but presented as simulation results |
| **Operator message** | "Advisory mode does not enforce this block. You may still run this command." | "This is a simulation. Under real enforcement, this command would be blocked. No enforcement occurred." |
| **Exit codes** | Always 0 (advisory is informational) | Differentiated: 0=allow, 1=blocked/deny, 2=error |
| **Footer** | "⚠️ Advisory mode is non-authorizing" | "⚠️ Dry-run simulation complete. No enforcement occurred." |
| **Primary use** | Learning, quick checks | Enforcement readiness, CI/CD gating |

### 9.3 Coexistence

Both commands should exist side by side:
```
pcae advisory check --command "..."   # Quick "what would happen?"
pcae dry-run check --command "..."    # "Show me the enforcement experience"
```

Operators can choose based on their need: quick information (advisory) or enforcement preview (simulation).

## 10. Relationship to Permission Broker

### 10.1 Evidence Chain

The simulation layer is a **consumer** of broker output, just as advisory mode is:

```
shell_gate._classify_command()
  → broker._broker_decide()
    → simulation.build_simulation()
```

The simulation layer does not modify broker decisions, reclassify commands, or override broker logic. It wraps the broker output in a simulation envelope.

### 10.2 Broker Decision Preservation

Every broker decision maps to the same simulation decision. The mapping from 88X advisory mode is reused:

| Broker Decision | Simulation Decision |
|----------------|---------------------|
| `allow_preflight_only` | `would_allow_governed_preflight_only` |
| `requires_human_review` | `would_require_human_review` |
| `blocked_by_*` | `would_block_by_*` |
| `deny` | `would_deny` |
| `unknown` | `unknown` |

### 10.3 Hard-Block Preservation

The 18 `BPE_HARD_BLOCK_DECISIONS` are preserved in simulation. No hard block is softened, demoted, or converted to a warning. Simulation output for hard blocks includes:
- `hard_block_present: true`
- `hard_block_reason` (which block)
- `hard_block_source` (shell_gate / broker / scope)
- `would_block: true`
- `enforcement_would_apply: true`

## 11. Relationship to Shell Gate

### 11.1 Classification Chain

Simulation uses the same `_classify_command()` function as advisory mode and the broker. The simulation layer:
1. Calls shell gate classification (via broker's internal call)
2. Receives shell gate category, decision, and detected flags
3. Presents them in simulation output

### 11.2 Shell Gate Evidence in Simulation Output

Simulation output includes shell gate evidence:
- `shell_gate_category` — the command category
- `shell_gate_decision` — the raw shell gate decision
- Shell gate reason codes
- Shell gate detected flags (relevant ones)

This gives operators visibility into the full classification chain.

## 12. Relationship to Gate Dry-Run

### 12.1 Different Purposes

| System | Purpose |
|--------|---------|
| **Gate Dry-Run** (`build_gate_dry_run()`) | Evaluate ALL gates (15 gates) against repository state for audit/evidence |
| **Dry-Run Simulation** | Evaluate a SINGLE proposed command through shell gate + broker for operator preview |

### 12.2 Shared Context

Both use `GateDryRunContext` (88Y.3) for shared evidence. Dry-run simulation can optionally accept a pre-built context to avoid redundant computation.

### 12.3 Execution Model

Gate dry-run is a batch operation: evaluate all gates, produce full envelope. Dry-run simulation is a single-command operation: evaluate one command, produce simulation result. The simulation is lighter-weight and designed for interactive use.

## 13. Relationship to Future Enforcement

### 13.1 Enforcement Pathway

Dry-run simulation is the last stop before real enforcement:

```
Advisory (Stage 1) → Simulation (Stage 3 design) → Enforcement (Stage 3+)
```

When enforcement is implemented:
- The same shell gate + broker chain runs
- Instead of "SIMULATED: would block", the command IS blocked
- The simulation output format becomes the enforcement output format
- Exit codes, JSON schema, and decision vocabulary remain stable

### 13.2 Transition Path

| Now (89B) | Future (89C+) |
|-----------|---------------|
| `pcae dry-run check` | `pcae enforce check` or `pcae gate check` |
| SIMULATED block | REAL block |
| Operator can bypass | Operator cannot bypass (in governed context) |
| Simulation footer | Enforcement footer |

### 13.3 Schema Stability

The JSON output model designed for simulation should be forward-compatible with enforcement. The same fields, same decision vocabulary, same severity model. Enforcement adds:
- `simulation_mode: false` → `enforcement_mode: true`
- `command_blocked: false` → `command_blocked: true` (when applicable)
- `bypass_attempted: false` → tracked

## 14. Command Namespace Recommendation

### 14.1 Evaluated Options

| Name | Pros | Cons |
|------|------|------|
| `pcae dry-run check` | Consistent with "gate dry-run" naming; clear it's a dry-run; short | May be confused with gate dry-run |
| `pcae dry-run-block check` | Very explicit | Long; awkward |
| `pcae blocking-sim check` | Emphasizes simulation | "blocking-sim" is jargon |
| `pcae enforcement-sim check` | Forward-looking to enforcement | Implies enforcement exists now |
| `pcae simulate check` | Short, clear | Too generic |
| `pcae dry-run check` | ✅ **Recommended** | Best balance of clarity, brevity, consistency |

### 14.2 Recommendation

**`pcae dry-run check`** is the recommended canonical name.

Rationale:
- Consistent with existing `pcae gate-dry-run` naming convention
- "dry-run" clearly signals no enforcement, no execution
- "check" mirrors `pcae advisory check` for discoverability
- Short enough for frequent interactive use
- Namespaces well: `pcae dry-run check`, `pcae dry-run explain`, `pcae dry-run status`

### 14.3 Command Surface

```
pcae dry-run check --command "<cmd>" [--json] [--severity <level>]
    [--health-passed] [--check-passed]
    [--human-review-present] [--human-approval-present]
    [--accepted-risk-present]

pcae dry-run explain --decision <decision> [--json]

pcae dry-run status [--json]
```

## 15. Simulation Decision Vocabulary

### 15.1 Decision Values

The simulation uses the same 19 decision values as advisory mode:

```python
SIMULATION_DECISIONS = (
    "would_allow_read_only",
    "would_allow_governed_preflight_only",
    "would_require_active_task",
    "would_require_preflight",
    "would_require_human_review",
    "would_require_more_evidence",
    "would_block_by_scope",
    "would_block_by_task_contract",
    "would_block_by_raw_git_push",
    "would_block_by_force_push",
    "would_block_by_shell_gate",
    "would_block_by_test_run_lock",
    "would_block_by_failed_health",
    "would_block_by_failed_check",
    "would_block_by_failed_doctor",
    "would_block_by_push_check",
    "would_block_by_conflicting_evidence",
    "would_deny",
    "unknown",
)
```

### 15.2 Decision Grouping for UX

Same grouping as 88Z:

| UX Category | Decisions | Visual |
|-------------|-----------|--------|
| **Would Allow** | `would_allow_read_only`, `would_allow_governed_preflight_only` | Green |
| **Would Require** | `would_require_active_task`, `would_require_preflight`, `would_require_human_review`, `would_require_more_evidence` | Yellow/Orange |
| **Would Block** | All `would_block_by_*` | Red |
| **Would Deny** | `would_deny` | Red (strongest) |
| **Unknown** | `unknown` | Gray |

### 15.3 Decision Priority

Most restrictive decision wins. Priority order:
1. `would_deny` (strongest)
2. `would_block_by_*` (hard blocks)
3. `would_require_human_review`
4. `would_require_preflight` / `would_require_active_task` / `would_require_more_evidence`
5. `would_allow_*` (weakest)
6. `unknown`

## 16. Severity Model

### 16.1 Severity Levels

Same five levels from 88Z §9, with simulation-specific labels:

| Severity | Label | Visual | Simulation Framing |
|----------|-------|--------|-------------------|
| `info` | ℹ️ INFO | Neutral | "Under enforcement, this would be allowed (read-only or governed)." |
| `caution` | ⚠️ CAUTION | Yellow | "Under enforcement, this would require additional steps." |
| `review_required` | 👁️ REVIEW REQUIRED | Orange | "Under enforcement, this would require human review." |
| `blocked` | 🚫 SIMULATED BLOCK | Red | "Under enforcement, this command WOULD BE BLOCKED." |
| `unknown` | ❓ UNKNOWN | Gray | "Enforcement decision could not be determined." |

### 16.2 Severity Assignment

Same mapping as advisory mode:
- `would_allow_*` → `info`
- `would_require_*` → `caution` (task/preflight/evidence) or `review_required` (human review)
- `would_block_by_*` → `blocked`
- `would_deny` → `blocked`
- `unknown` → `unknown`

## 17. Recommendation Model

### 17.1 Operator Actions

Same 15 actions from 88Z §10, with simulation-specific framing:

| Action | Simulation Framing |
|--------|-------------------|
| `proceed_at_discretion` | "Under enforcement, this would be allowed. No PCAE concerns." |
| `use_governed_alternative` | "Use the PCAE-governed alternative to avoid enforcement blocking." |
| `resolve_blocking_condition` | "Resolve the blocking condition before enforcement is active." |
| `request_human_review` | "Obtain human review. Under enforcement, this would be gated." |
| `do_not_execute` | "Do not execute. Under enforcement, this would be permanently denied." |
| `escalate_false_positive` | "If you believe this block is incorrect, report it before enforcement goes live." |

### 17.2 Enforcement Readiness Guidance

Simulation adds enforcement-readiness guidance:

| Simulation Decision | Enforcement Readiness |
|---------------------|----------------------|
| `would_allow_read_only` | "Ready for enforcement. No changes needed." |
| `would_allow_governed_preflight_only` | "Ready for enforcement. Preflight-only path confirmed." |
| `would_block_by_raw_git_push` | "Use `pcae push` instead. Enforcement will block raw git push." |
| `would_block_by_force_push` | "Force push will be permanently blocked under enforcement." |
| `would_require_human_review` | "Under enforcement, human review will be required before proceeding." |

## 18. JSON Output Model

### 18.1 JSON Envelope

```json
{
  "schema_version": "0.1",
  "generated_at": "<ISO 8601>",
  "repository_root": "<path>",
  "simulation_id": "<unique-id>",

  "simulation_mode": true,
  "simulation_version": "0.1",
  "enforcement_stage": "dry_run_simulation",

  "requested_action": "<action>",
  "requested_command": "<command or redacted sentinel>",
  "requested_command_redacted": false,
  "requested_files": ["<file>", "..."],

  "broker_decision": "<BPE_DECISIONS>",
  "shell_gate_decision": "<SGP_DECISIONS>",
  "shell_gate_category": "<SGP_CATEGORIES>",
  "simulation_decision": "<would_*>",

  "simulation_severity": "info|caution|review_required|blocked|unknown",
  "simulation_recommendation": "<human-readable>",
  "enforcement_would_apply": true,

  "would_allow_read_only": false,
  "would_allow_governed_preflight_only": false,
  "would_require_active_task": false,
  "would_require_preflight": false,
  "would_require_human_review": false,
  "would_require_more_evidence": false,
  "would_block": false,
  "would_deny": false,

  "hard_block_present": false,
  "hard_block_reason": null,
  "hard_block_source": null,
  "human_approval_relevant": false,
  "human_approval_would_change_outcome": false,
  "accepted_risk_relevant": false,
  "human_approval_cannot_override_hard_block": true,

  "redaction_applied": false,
  "redaction_reason": null,
  "safe_to_display": true,

  "operator_message": "<contextual guidance>",
  "next_required_action": "<recommended step>",
  "governed_alternative": "<pcae command or null>",
  "enforcement_readiness": "<guidance>",

  "authorization_granted": false,
  "execution_authorized": false,
  "command_executed": false,
  "enforcement_applied": false,
  "shell_intercepted": false,
  "wrapper_installed": false,
  "backend_invoked": false,
  "prompt_sent": false,
  "output_captured": false,
  "intake_performed": false,
  "adoption_performed": false,

  "safety_invariants": {
    "simulation_only": true,
    "no_execution": true,
    "no_authorization": true,
    "no_enforcement": true,
    "no_interception": true,
    "no_wrappers": true,
    "no_backend": true,
    "no_persistent_state": true,
    "hard_blocks_preserved": true,
    "secrets_redacted": true
  },

  "evidence_sources": ["<source>", "..."],
  "missing_evidence": ["<item>", "..."],
  "warnings": ["<warning>", "..."],
  "errors": [],
  "known_limitations": [
    "Simulation only — no enforcement occurred",
    "Operator can still run command directly in shell",
    "No shell interception or wrapping active"
  ]
}
```

### 18.2 Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `simulation_mode` | bool | Always `true` for simulation output |
| `simulation_id` | string | Unique ID for this simulation run (allows CI/CD traceability) |
| `enforcement_stage` | string | `"dry_run_simulation"` — which enforcement stage this represents |
| `enforcement_would_apply` | bool | Whether enforcement would apply to this command (true for blocks, false for allows) |
| `enforcement_readiness` | string | Guidance for enforcement transition |
| `governed_alternative` | string\|null | PCAE-governed command that achieves the same goal |
| `safety_invariants` | object | All safety invariants as explicit boolean fields |
| `known_limitations` | array | Explicit list of simulation limitations |

### 18.3 Invariant Fields (Always False)

These fields are unconditionally `false` in every simulation output:

```
authorization_granted, execution_authorized, command_executed,
enforcement_applied, shell_intercepted, wrapper_installed,
backend_invoked, prompt_sent, output_captured,
intake_performed, adoption_performed
```

## 19. Human-Readable Output Model

### 19.1 Design Principles

- Scannable in <10 seconds
- Self-explanatory decision with SIMULATED prefix
- Severity-indicated with clear visual hierarchy
- Always includes governed alternative when applicable
- Always ends with simulation footer

### 19.2 Recommended Layout (Allow)

```
╔══════════════════════════════════════════════════════════════╗
║  PCAE Dry-Run Simulation — ℹ️ INFO                           ║
║  Simulation only. No enforcement occurred.                   ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Command:     git status                                     ║
║                                                              ║
║  Shell Gate   read_only_inspection → allow_read_only         ║
║  Broker       allow_preflight_only                           ║
║                                                              ║
║  Simulation:  would_allow_read_only                          ║
║  This command is read-only. Under enforcement, it would      ║
║  be allowed without restrictions.                            ║
║                                                              ║
║  Would block: no   Hard block: none   Redaction: none        ║
║                                                              ║
║  Enforcement readiness: Ready. No changes needed.            ║
║                                                              ║
║  Next: Proceed at your discretion.                           ║
║                                                              ║
║  Authorization: not granted  Execution: not authorized       ║
║  Enforcement:   not applied   Interception: not applied      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
────────────────────────────────────────────────────────────
⚠️  Dry-run simulation complete. No enforcement occurred.
    No command was executed. Operator retains full authority.
────────────────────────────────────────────────────────────
```

### 19.3 Recommended Layout (Blocked)

```
╔══════════════════════════════════════════════════════════════╗
║  PCAE Dry-Run Simulation — 🚫 SIMULATED BLOCK                ║
║  Simulation only. No enforcement occurred.                   ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Command:     git push origin main                           ║
║                                                              ║
║  Shell Gate   raw_git_push → blocked_by_raw_git_push         ║
║  Broker       blocked_by_raw_git_push                        ║
║                                                              ║
║  ┌─ SIMULATED BLOCK ────────────────────────────────────┐    ║
║  │                                                       │    ║
║  │  SIMULATED: would_block_by_raw_git_push               │    ║
║  │                                                       │    ║
║  │  HARD BLOCK. Cannot be overridden.                    │    ║
║  │                                                       │    ║
║  │  Under real enforcement, this command WOULD BE        │    ║
║  │  BLOCKED. No enforcement occurred in this simulation. │    ║
║  │                                                       │    ║
║  │  Governed alternative: pcae push                      │    ║
║  │                                                       │    ║
║  └───────────────────────────────────────────────────┘    ║
║                                                              ║
║  Enforcement readiness: Use pcae push instead.              ║
║  Raw git push will be blocked under enforcement.            ║
║                                                              ║
║  Authorization: not granted  Execution: not authorized       ║
║  Enforcement:   not applied   Interception: not applied      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
────────────────────────────────────────────────────────────
⚠️  Dry-run simulation complete. No enforcement occurred.
    No command was executed. Operator retains full authority.
────────────────────────────────────────────────────────────
```

### 19.4 Simulation Footer (Mandatory)

Every human-readable simulation output must end with:

```
────────────────────────────────────────────────────────────
⚠️  Dry-run simulation complete. No enforcement occurred.

    • No command was executed.
    • No shell was intercepted.
    • No authorization was granted.
    • No enforcement was applied.

    This was a simulation of what PCAE enforcement would
    decide. The operator retains full authority.

    When enforcement is active, blocked commands will be
    prevented from executing in governed contexts.
────────────────────────────────────────────────────────────
```

## 20. Hard-Block Simulation Behavior

### 20.1 Simulation Rules

1. **Hard blocks are presented as SIMULATED BLOCK.** Not "recommend against", not "consider avoiding."
2. **Hard blocks state they cannot be overridden.** "HARD BLOCK. Cannot be overridden by human approval or accepted risk."
3. **Hard blocks explain why.** Policy rationale in plain language.
4. **Hard blocks suggest the governed alternative.** PCAE-governed command shown prominently.
5. **Hard blocks do not suggest workarounds.** "You may run directly in your shell" is informational framing, not a recommendation.

### 20.2 Hard-Block Wording Template

```
┌─ SIMULATED BLOCK ────────────────────────────────────────┐
│                                                           │
│  SIMULATED: <would_block_decision>                        │
│                                                           │
│  HARD BLOCK. Cannot be overridden by human approval       │
│  or accepted risk.                                        │
│                                                           │
│  Why: <policy rationale>                                  │
│                                                           │
│  Governed alternative: pcae <command>                     │
│                                                           │
│  Under real enforcement, this command WOULD BE BLOCKED.   │
│  This simulation did not enforce any block.               │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

## 21. Human-Review Simulation Behavior

### 21.1 Simulation Rules

1. **Human review is presented as a gate, not a block.** "REVIEW REQUIRED" not "BLOCKED."
2. **Human review states it is not authorization.** "Human review is a required step, not authorization to execute."
3. **Human review shows it would change the outcome.** "Human review would change outcome: yes."
4. **Human review cannot override hard blocks.** If a hard block is also present, the hard block takes precedence.

### 21.2 Human-Review Wording Template

```
┌─ REVIEW REQUIRED ────────────────────────────────────────┐
│                                                           │
│  SIMULATED: would_require_human_review                    │
│                                                           │
│  Under enforcement, this command would require human      │
│  review before proceeding.                                │
│                                                           │
│  Human review would change outcome: yes                   │
│                                                           │
│  To proceed (in simulation): re-evaluate with             │
│    pcae dry-run check --command "..." \                   │
│      --human-review-present                               │
│                                                           │
│  Note: Human review is not authorization. The operator    │
│  retains full responsibility for the command.             │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

## 22. Missing-Evidence Simulation Behavior

### 22.1 Simulation Rules

1. **Name the missing items.** Not "missing evidence" — "Missing: active_task_contract."
2. **Explain how to provide each item.** Link to the PCAE command that provides it.
3. **Distinguish blocking from non-blocking gaps.** Health failure blocks; missing preflight gates.

### 22.2 Missing-Evidence Wording Template

```
┌─ MISSING EVIDENCE ───────────────────────────────────────┐
│                                                           │
│  SIMULATED: would_require_more_evidence                   │
│                                                           │
│  Under enforcement, this command would require:           │
│                                                           │
│  • active_task_contract — No active task found.           │
│    Provide: pcae task new "<title>"                       │
│                                                           │
│  • scope_preflight — Scope not verified.                  │
│    Provide: pcae preflight scope <files>                  │
│                                                           │
│  Until evidence is provided, enforcement would gate       │
│  this command.                                            │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

## 23. Read-Only Allow Simulation Behavior

### 23.1 Simulation Rules

1. **Read-only commands show INFO severity.** Green/neutral presentation.
2. **Clear that no enforcement applies.** "Under enforcement, this command would be allowed without restrictions."
3. **Still no execution authorization.** Even for allowed commands, `execution_authorized` is `false`.

### 23.2 Read-Only Allow Wording

```
SIMULATED: would_allow_read_only

This command is read-only inspection. Under enforcement, it
would be allowed without restrictions.

Enforcement readiness: Ready. No changes needed for enforcement.

Note: Advisory/simulation mode never authorizes execution.
```

## 24. Accepted-Risk Boundary

### 24.1 Simulation Rules

1. **Accepted risk is relevant for review-required and caution paths.** If a command requires human review, accepted risk may be considered in future enforcement stages.
2. **Accepted risk must never override hard blocks.** This is a permanent invariant (88V §16).
3. **Accepted risk handling is reserved for Stage 5+.** In simulation (Stage 3), `accepted_risk_relevant` is informational only.

### 24.2 Accepted-Risk Field

```json
{
  "accepted_risk_relevant": false,
  "accepted_risk_would_change_outcome": false,
  "accepted_risk_note": "Accepted risk handling is reserved for enforcement Stage 5+. In simulation, accepted risk is informational only."
}
```

## 25. Human-Approval Boundary

### 25.1 Simulation Rules

1. **Human approval is distinct from human review.** Review = a human looked at it. Approval = a human explicitly approves it.
2. **Human approval can change outcomes for non-hard-blocks.** If `requires_human_review`, providing approval advances the decision.
3. **Human approval cannot override hard blocks.** This is a permanent invariant.
4. **Human approval simulation** — the `--human-approval-present` flag simulates approval for testing.

### 25.2 Human-Approval Field

```json
{
  "human_approval_relevant": true,
  "human_approval_would_change_outcome": true,
  "human_approval_cannot_override_hard_block": true,
  "human_approval_note": "Human approval can change outcomes for non-hard-block decisions. Hard blocks are never overridable."
}
```

## 26. Secret-Redaction Requirements

### 26.1 Redaction Rules

All 88V.1 and 89A redaction rules apply to simulation output:

1. **Secret VAR=val prefixes** → redacted
2. **env/printenv** → redacted (env with secret-like vars)
3. **Secret file access** → redacted
4. **Secret access programs** → redacted
5. **`requested_command` field** → `<redacted_secret_access_command>` sentinel
6. **JSON output** → never contains raw secret text
7. **Human-readable output** → never contains raw secret text
8. **Simulation ID and logs** → never contain raw secret text

### 26.2 Redaction in Simulation Context

Simulation adds:
- `redaction_applied: true` in simulation envelope
- `redaction_reason: "secret_access_detected"` 
- `safe_to_display: true` (always true after redaction)
- Redacted commands show `<redacted_secret_access_command>` sentinel in all output fields

## 27. Audit/Evidence Model

### 27.1 Simulation Is Stateless (Initial Prototype)

In the initial prototype (89C), simulation is stateless:
- No audit records written
- No logs persisted
- No command history stored
- Each invocation is independent

### 27.2 Future Audit Logging (Post-89C)

When audit logging is added:
- Simulation evaluations **may** be logged to `.pcae/simulations/`
- Logs **must** store only redacted command text
- Logs **must** record simulation decision, timestamp, repository state
- Logs **must not** store raw secret-access command text
- Logs **must not** store execution results (nothing was executed)

### 27.3 Evidence Sources

Simulation output includes `evidence_sources` array documenting what was consulted:
- Shell gate classifier (internal)
- Permission broker (internal)
- Scope preflight (if applicable)
- Health/check/doctor/push evidence (if provided)
- Task contract (if detected)

## 28. Safety Invariants

### 28.1 Permanent Invariants

These invariants must hold for all simulation output, in all formats:

| # | Invariant | Verification |
|---|-----------|-------------|
| **SI-1** | `command_executed` is always `false` | Assert in every test |
| **SI-2** | `shell_intercepted` is always `false` | Assert in every test |
| **SI-3** | `wrapper_installed` is always `false` | Assert in every test |
| **SI-4** | `authorization_granted` is always `false` | Assert in every test |
| **SI-5** | `execution_authorized` is always `false` | Assert in every test |
| **SI-6** | `enforcement_applied` is always `false` | Assert in every test |
| **SI-7** | `backend_invoked` is always `false` | Assert in every test |
| **SI-8** | `prompt_sent` is always `false` | Assert in every test |
| **SI-9** | Redacted commands never appear in any output field | Assert in redaction tests |
| **SI-10** | Simulation footer present in every human-readable output | Assert in human-readable tests |
| **SI-11** | JSON output contains all required schema fields | Assert schema validation |
| **SI-12** | Hard blocks are never presented as overridable | Assert `can_override: false` for all hard blocks |
| **SI-13** | Simulation never calls subprocess with user command text | Code invariant |
| **SI-14** | Simulation never writes files outside `.pcae/` | Code invariant |
| **SI-15** | `simulation_mode` is always `true` | Assert in every test |
| **SI-16** | `safety_invariants.simulation_only` is always `true` | Assert in every test |

### 28.2 Simulation-Specific Invariants

| # | Invariant | Rationale |
|---|-----------|-----------|
| **SSI-1** | `simulation_id` is unique per invocation | Traceability |
| **SSI-2** | `enforcement_stage` is `"dry_run_simulation"` | Explicit stage identification |
| **SSI-3** | `known_limitations` includes simulation-only disclaimer | Transparency |
| **SSI-4** | Exit codes are differentiated: 0=allow, 1=blocked, 2=error | CI/CD integration |

## 29. Failure Modes

### 29.1 Simulation Failures (Internal Errors)

| Failure | Behavior | Operator Message |
|---------|----------|-----------------|
| Broker raises exception | Return `unknown` decision, log error | "Simulation encountered an internal error. The decision could not be determined." |
| Shell gate raises exception | Return `unknown` decision, log error | "Command classification failed. The simulation could not complete." |
| Invalid command text (empty, null) | Return `unknown` with reason | "No command text provided for simulation." |
| Schema version mismatch | Warning in output, continue | "Schema version mismatch detected. Results may be inconsistent." |

### 29.2 Operator Errors

| Error | Behavior |
|-------|----------|
| Missing `--command` flag | CLI error, exit 2 |
| Unparseable JSON in `--json` mode | CLI error, exit 2 |
| Invalid `--severity` filter value | CLI error, exit 2 |

### 29.3 Simulation Must Not

- Crash on adversarial command text (Unicode, ANSI escapes, very long strings)
- Leak secrets in error messages
- Execute command text even on internal error
- Grant authorization even on internal error
- Write files outside `.pcae/` even on internal error

## 30. Known Limitations

1. **Simulation is not enforcement.** Commands are never actually blocked. The operator can always bypass simulation and run commands directly.

2. **No shell integration.** Simulation is explicitly invoked via `pcae dry-run check`. It does not wrap or monitor shell sessions.

3. **Stateless.** No history, no audit trail, no persistent records in initial prototype.

4. **Same evidence as advisory mode.** Simulation uses the same shell gate + broker chain. It does not add new classification capabilities.

5. **No real-time feedback.** Simulation is a CLI command, not a daemon. It evaluates one command at a time, on demand.

6. **Single-command evaluation.** Simulation evaluates one command per invocation. Multi-command workflows (script files, Makefiles) are not simulated.

7. **No contextual learning.** Each simulation is independent. Past simulation results are not considered.

8. **Exit codes are advisory.** Exit code 1 (blocked) is informational. The operator can still proceed.

## 31. Known Full-Suite Baseline Issue

### 31.1 Issue Description

As of 89A, the full test suite has 3 known pre-existing failures:

| Test | File | Type |
|------|------|------|
| `test_88m_requires_human_review[backend]` | `test_preflight_integration_verification.py` | Pre-existing |
| `test_88m_requires_human_review[mutation]` | `test_preflight_integration_verification.py` | Pre-existing |
| `test_project_state_no_repository_files_created` | `test_project_state.py` | Flaky (passes in isolation) |

### 31.2 Verification

These failures were verified on clean HEAD commit 5230a325 (88Z completion + fix), confirming they are not caused by 89A changes.

### 31.3 Impact on 89B

None. 89B is a design-only phase. No source or test files are changed. Fast-green (3,001 tests) passes cleanly. These failures should be addressed in a future baseline repair phase before enforcement implementation begins.

### 31.4 Recommendation

A pre-enforcement baseline repair phase should investigate and fix these failures before Stage 3 (blocking gate) implementation.

## 32. Test Matrix for Future Implementation

### 32.1 Unit Tests (89C)

| Test Category | Tests | Description |
|--------------|-------|-------------|
| Simulation envelope | ~15 | JSON schema validation, required fields, invariant fields |
| Decision mapping | ~25 | Every broker decision → simulation decision |
| Would-* flags | ~10 | Exactly one would-* flag true per evaluation |
| Authorization invariants | ~20 | All auth/enforcement/interception fields always false |
| Safety invariants | ~10 | All safety_invariants fields correct |
| Hard-block preservation | ~18 | All 18 BPE_HARD_BLOCK_DECISIONS produce blocked severity |
| Secret redaction | ~15 | All 88V.1/89A redaction rules applied |
| Exit codes | ~6 | 0=allow, 1=blocked, 2=error |
| Simulation ID | ~3 | Unique per invocation |
| Known limitations | ~3 | Present in every output |

### 32.2 Integration Tests (89C)

| Test Category | Tests | Description |
|--------------|-------|-------------|
| CLI JSON stability | ~10 | `--json` produces valid, complete JSON |
| CLI human-readable | ~8 | Output contains required sections and footer |
| CLI exit codes | ~8 | Correct exit codes for allow/block/error |
| `--severity` filter | ~5 | Correct filtering behavior |
| Multi-command consistency | ~5 | Same command → same simulation decision |

### 32.3 Command Matrix Tests (89C)

| Category | Tests | Commands |
|----------|-------|---------|
| Read-only | 12 | git status, ls, cat, grep, diff, echo, pwd, whoami, date, head, wc |
| Governed PCAE | 4 | pcae health, check, doctor task-memory, doctor test-run |
| Git hard blocks | 7 | git push, git push --force, git commit, git rebase |
| Dangerous fs | 5 | rm -rf variants, git reset --hard, git clean -fd |
| Policy forbidden | 5 | echo > README.md, tee README.md |
| Review-required | 9 | pip install, brew install, curl, wget, ssh, scp |
| Secret/redaction | 35+ | VAR=val, env, printenv, cat ~/.ssh, security |
| Compound/compact | 10 | &&, \|\|, ; , pipe chains, compact operators |
| Shell commands | 8 | bash, sh -c, bash -lc, zsh |
| Unknown | 4 | unknown-tool |

### 32.4 Total Estimated Tests

~250 simulation-specific tests for 89C prototype.

## 33. Implementation Roadmap

### 33.1 Phase Sequencing

| Phase | Name | Type | Description |
|-------|------|------|-------------|
| **89C** | Dry-Run Blocking Simulation Prototype | Implementation | Implement `pcae dry-run check/explain/status` CLI; simulation envelope; ~250 tests |
| **89D** | Simulation Output Hardening | Implementation | Implement human-readable layout from 89B §19; severity banners; footer; exit codes |
| **89E** | Simulation CI/CD Integration | Implementation | JSON schema versioning; `--severity` filter; CI/CD consumer docs; stable exit codes |
| **89F** | Pre-Enforcement Baseline Repair | Implementation | Fix 3 known full-suite failures; verify clean baseline |
| **89G+** | Enforcement Stage 3+ | Implementation | Real blocking gate per 88V staging model |

### 33.2 Dependencies

```
89B (design)
  → 89C (prototype)
    → 89D (output hardening)
      → 89E (CI/CD integration)
        → 89F (baseline repair)
          → 89G+ (enforcement)
```

## 34. Open Questions

| # | Question | Deferred To |
|---|----------|------------|
| Q1 | Should simulation output include a diff from advisory output? | 89C |
| Q2 | Should `pcae dry-run status` show recent simulation history? | 89D |
| Q3 | Should there be a `--diff` flag showing advisory vs simulation comparison? | 89D |
| Q4 | Should simulation support `--output-format html` for dashboards? | 89E |
| Q5 | Should simulation exit codes be configurable? | 89E |
| Q6 | How should simulation handle multi-line commands? | 89C |
| Q7 | Should there be a batch simulation mode (simulate N commands at once)? | 89E |
| Q8 | What `schema_version` should simulation start with? | 89C (recommend: "0.1") |
| Q9 | Should simulation output be color-coded in the terminal? | 89D |
| Q10 | Should there be a `--quiet` mode that only prints the decision? | 89D |

## 35. Recommended Next Phase

**89C — Dry-Run Blocking Simulation Prototype**

Implement the dry-run blocking simulation as designed in this document:

- `pcae dry-run check --command "<cmd>" [--json]`
- `pcae dry-run explain --decision <decision> [--json]`
- `pcae dry-run status [--json]`
- Simulation JSON envelope with all invariant fields
- Human-readable output with SIMULATED prefix and footer
- ~250 fast-green tests
- Differentiated exit codes (0=allow, 1=blocked, 2=error)
- No enforcement, no shell interception, no authorization

## 36. Summary

Phase 89B defines PCAE's dry-run blocking simulation layer. Key outcomes:

1. **Simulation defined** as read-only, non-authorizing, non-intercepting enforcement preview.
2. **Relationship to advisory mode** defined — simulation adds enforcement framing, differentiated exit codes, and CI/CD readiness.
3. **Relationship to broker and shell gate** defined — simulation consumes their output without modification.
4. **Command namespace** recommended: `pcae dry-run check/explain/status`.
5. **19-value decision vocabulary** defined (same as advisory mode for consistency).
6. **JSON output model** designed with 50+ fields, safety invariants, and known limitations.
7. **Human-readable output model** designed with severity banners, SIMULATED prefix, and mandatory footer.
8. **Hard-block simulation** defined — presented as SIMULATED BLOCK, not suggestion.
9. **Human-review simulation** defined — review as gate, not authorization.
10. **Accepted-risk/human-approval boundaries** defined — cannot override hard blocks.
11. **Secret-redaction requirements** defined — all 88V.1/89A rules preserved.
12. **16 safety invariants** defined with verification strategy.
13. **Failure modes** documented for internal errors and operator errors.
14. **Future test matrix** defined — ~250 tests for 89C prototype.
15. **Implementation roadmap** sequenced through 89C→89G+.
16. **Known full-suite baseline issue** documented (3 pre-existing failures).
17. **10 open questions** deferred to implementation phases.
18. **Recommended next phase: 89C** — Dry-Run Blocking Simulation Prototype.
