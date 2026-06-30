# Phase 96A — Execution-Adjacent Boundary Design

```
phase_name = phase_96a_execution_adjacent_design | phase_status = completed | implementation_status = design_only
recommended_next_phase = 96B — Execution-Adjacent Plan Model
```

## 1. Executive Boundary Decision

Design-only. No implementation, no execution.

| Decision | Value |
|----------|-------|
| `execution_adjacent_design_ready` | **true** |
| `artifact_only_execution_ready` | **false** |
| `real_backend_execution_ready` | **false** |
| `subprocess_mediation_ready` | **false** |
| `shell_interception_ready` | **false** |
| `auto_apply_ready` | **false** |
| `telegram_inbound_ready` | **false** |

## 2. Definition of Execution-Adjacent

"Execution-adjacent" is the design space immediately before process execution. PCAE may model and validate executable intent, command identity, arguments, path, digest, environment, timeout policy, output quarantine, audit record, operator approval, broker/shell-gate decisions, rollback linkage, post-run containment, and failure classification — but must never spawn a process, call subprocess, invoke a shell, invoke a real backend adapter, connect to network, inspect live runtime, run an AI backend, mutate repo files from output, parse/apply patches, authorize commit/push, or accept Telegram commands.

### Allowed (Model/Validate Only)
- Executable intent record
- Command identity/path/digest
- Command arguments
- Environment declaration (key names, never values)
- Timeout/kill policy
- Output quarantine contract
- Audit record contract
- Approval artifact reference
- Broker/shell-gate decision references
- Rollback linkage plan
- Post-run review contract
- Failure classification taxonomy

### Prohibited (Must Not)
- Spawn process
- Call subprocess
- Invoke shell
- Invoke real backend adapter
- Open network connection
- Inspect live runtime
- Run AI backend
- Mutate repo files from output
- Parse/apply patches automatically
- Authorize commit/push
- Accept Telegram inbound commands

## 3. Prohibited-Action Taxonomy

| Category | Why Prohibited | Trigger Risk | Required Guardrail |
|----------|---------------|-------------|-------------------|
| Process execution | Real invocation boundary | CLI with subprocess=True | Shell-gate hard-block |
| Shell execution | Arbitrary command risk | os.system/subprocess | No shell=True ever |
| Backend invocation | AI execution risk | Adapter invoke() | Broker hard-block |
| Network interaction | Credential/API leakage | urllib/requests/socket | No network code in execution path |
| Live runtime inspection | Bypass detection risk | PATH lookup, which, ps | Stat-only evidence only |
| Command discovery | Auto-execution risk | shutil.which, glob | Explicit configured paths only |
| Output application | Repo mutation risk | Patch parsing, file write | Output always quarantined |
| Repository mutation | Unauthorized change | Write to non-.pcae paths | Task scope enforcement |
| Commit/push auth | Autonomous change risk | git commit/push bypass | Governed commit/push only |
| Remote control | Remote execution risk | SSH, /run, webhooks | Explicit command mediation |
| Telegram inbound | Remote command risk | getUpdates, webhooks | Outbound-only |
| Bypass abuse | Safety override risk | Accepted risk without evidence | Hard-blocks non-overridable |
| Audit mutation | Tampering risk | Direct file write to audit | Append-only, digest-chained |

## 4. Boundary Layers (Future, Not Implemented)

| Layer | Purpose | Status |
|-------|---------|--------|
| Execution-adjacent plan model | Captures execution intent without executing | 96B |
| Broker pre-decision | Broker evaluates before any subprocess | 96C |
| Shell-gate pre-decision | Shell-gate classifies before any subprocess | 96C |
| Execution intent record | Immutable record of what was intended | 96B |
| Command identity record | Exact command path, hash, arguments | 96B |
| Timeout/kill policy | Hard timeout, SIGKILL after grace | 96D |
| Output quarantine contract | Output capture, redaction, quarantine rules | 96D |
| Audit immutability contract | Append-only, digest-chained records | 96D |
| Rollback linkage contract | Pre-execution snapshot, affected files | 96D |
| Operator approval semantics | Artifacted, hash-bound, expiring | 96B |
| Post-run review contract | Human reviews output before adoption | 96D |
| Final no-execution dry-run | All checks pass, still no subprocess | 96C |

## 5. Approval Semantics

- Human approval is necessary but not sufficient
- Accepted risk cannot override hard blocks
- Broker hard-blocks are non-overridable
- Shell-gate hard-blocks are non-overridable
- Execution may only be considered when every required evidence record is present and consistent
- Telegram approval/inbound commands remain out of scope
- Approval must be artifacted, not conversational only
- Approval binds to: backend_id, adapter_id, command_hash, plan_hash
- Approval expires by default (1 hour for mutations)

## 6. Fail-Closed Behavior

All of the following must hard-block before any execution-adjacent prototype:

Missing runtime evidence, stale runtime evidence, tampered digests, command path mismatch, command digest mismatch, missing broker decision, broker deny, missing shell-gate decision, shell-gate deny, missing timeout policy, missing output quarantine, missing audit path, missing rollback linkage, missing approval artifact, missing operator identity, dirty repo, unpushed commits, task scope mismatch, unknown adapter, unknown backend, Telegram inbound attempted.

## 7. Output Quarantine Design Boundary

Future output quarantine must: capture raw output, capture redacted output, preserve original output, avoid parsing patches automatically, avoid applying patches automatically, classify output type, classify secrets, link output to invocation intent, link output to approval artifact, link output to audit, support manual review only until explicitly changed by future phases.

## 8. Audit and Immutability Boundary

Future audit must: use append-only records, stable digests, record chain, actor identity, backend/adapter/task/phase/approval/decision/command/output/rollback identity, tamper detection.

## 9. Rollback Linkage Boundary

Rollback readiness required before execution-adjacent prototype. Rollback record must identify affected files/artifacts, cannot rely on model memory, must link to task contract and approval, must be available before any output application considered.

## 10. Execution-Adjacent Readiness Criteria (Go/No-Go)

All must pass before 96B model phase: Phase 95 complete, command boundary ready, orchestration dry-run ready, no-execution invariants tested, finalization gate active, report attribution stable, broker/shell-gate stable, output quarantine contract drafted, audit contract drafted, rollback contract drafted, approval semantics drafted, no subprocess/shell/network/backend invocation, Telegram inbound disabled.

## 11. Recommended Next Phase

**96B — Execution-Adjacent Plan Model**. Implement non-executing model for execution-adjacent intent, command identity, timeout policy, output quarantine reference, audit reference, rollback linkage, and approval reference. No execution.

## 12. 96B Test Strategy (~20 tests)

Valid plan validates as dry-run-only, missing command identity hard-blocks, missing command digest hard-blocks, missing timeout policy hard-blocks, missing output quarantine hard-blocks, missing audit record hard-blocks, missing rollback linkage hard-blocks, missing approval artifact hard-blocks, broker deny hard-blocks, shell-gate deny hard-blocks, execution_allowed=True hard-blocks, subprocess_allowed=True hard-blocks, network_allowed=True hard-blocks, auto_apply_allowed=True hard-blocks, digest stable/changes/excludes record_digest, no subprocess/shell/network/backend invocation, no CLI execution path.

## 13. No-Go

No real backend invocation. No adapter execution. No subprocess. No shell. No network. No execute. 96B not started.
