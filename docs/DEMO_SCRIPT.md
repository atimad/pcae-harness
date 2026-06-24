# PCAE Demo Script

A guided walkthrough of PCAE's governance capabilities. All commands are read-only
or dry-run. Nothing in this demo invokes agents, modifies files, commits, or pushes.

## Prerequisites

```bash
pip install -e .
cd <your-pcae-repo>
```

## 1. Repository Health

```bash
pcae health          # Overall governance health
pcae check           # Validate changes against governance policy
pcae doctor task-memory  # Check task/session consistency
pcae push check      # Push readiness without pushing
```

## 2. Task and Lifecycle Status

```bash
pcae lifecycle backend-output-adoption summary --json
# Shows: current_state=closed, execution_authorized=false
```

## 3. Read-Only Project Intelligence

These commands answer governance questions from committed evidence:

```bash
# What governance artifacts exist?
pcae artifact-index --json

# What phase are we in? What's the lifecycle state?
pcae memory-snapshot --json

# What happened and when?
pcae governance-timeline --json

# What was decided?
pcae decision-log --json

# What risks are active, accepted, or deferred?
pcae risk-register --json

# Complete project state answer surface
pcae project-state --json
```

All output is JSON to stdout. No files written. No storage created.

## 4. Gate Dry-Run Evaluation

Evaluate hypothetical actions without performing them:

```bash
# Default: evaluate all 15 gates
pcae gate-dry-run --json

# Scope: is this file in scope for this task?
pcae gate-dry-run --json --requested-action source_mutation \
  --requested-file src/pcae/core/gate_dry_run.py

# Scope: is README in scope? (likely blocked)
pcae gate-dry-run --json --requested-action source_mutation \
  --requested-file README.md

# Backend: could we invoke Claude? (requires human review)
pcae gate-dry-run --json --requested-action backend_invocation \
  --requested-backend claude --prompt-present

# Adoption: could we adopt this file? (requires human review)
pcae gate-dry-run --json --requested-action adoption \
  --requested-file src/example.py --adoption-artifact-present

# Commit: could we commit? (requires human review)
pcae gate-dry-run --json --requested-action commit \
  --commit-message-present --human-approved

# Push: could we push? (requires human review)
pcae gate-dry-run --json --requested-action push \
  --push-target origin/main --human-approved
```

## 5. What the Demo Shows

**Every gate reports:**
- `authorization_granted: false`
- `enforcement_performed: false`
- No gate produces `allow`

**Key safety properties:**
- Read-only intelligence does not authorize action
- Gate dry-run does not enforce decisions
- Scope match does not authorize mutation
- Human approval flag does not execute mutation
- Backend name does not invoke backend
- Commit message does not create commit
- Push target does not perform push

## 6. What Is NOT Demonstrated

- No agent is invoked (Claude, DeepSeek, Codex, etc.)
- No file is modified by any command
- No commit is created
- No push is performed
- No storage or cache is created
- Permission broker is architecture-only (not implemented)
- Shell gate is architecture-only (not implemented)
- Enforced preflight gates are not yet implemented

## 7. Architecture Layers

```
Implemented:
  pcae artifact-index    → evidence layer
  pcae memory-snapshot   → state layer
  pcae governance-timeline → history layer
  pcae decision-log      → decision layer
  pcae risk-register     → risk layer
  pcae project-state     → integrated answer
  pcae gate-dry-run      → dry-run gate evaluation

Designed (not implemented):
  Permission broker      → policy mediation
  Shell gate             → command enforcement

Future:
  Enforced preflight     → narrow scope/commit/push blocking
  Governed execution     → controlled agent action
```

## 8. Running the Full Test Suite

```bash
python -m pytest -n auto
# Expected: 7278+ tests passed, 0 failures
```
