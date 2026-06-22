# PCAE Roadmap

## Current Milestone

PCAE has completed its first full governed backend-created output adoption lifecycle (phases 77J through 77V.1).

The completed chain:

```
backend mutation detected
  -> mutation intake
  -> quarantine review
  -> adoption preflight
  -> adoption review
  -> adoption approval
  -> adoption execution preflight
  -> adoption execution / staging
  -> commit approval
  -> commit execution
  -> hook-bypass reconciliation
  -> push approval
  -> push execution
  -> final verification
  -> tooling closure
```

This milestone proves that PCAE can:

- capture backend-created output,
- detect unsafe repo mutation,
- quarantine and review the output,
- approve adoption explicitly,
- stage exactly one approved file,
- approve and execute a commit,
- reconcile hook-bypass exceptions,
- approve and execute a governed push,
- verify final local and remote state,
- close the lifecycle.

## Roadmap Principles

PCAE prioritizes governed autonomy over raw autonomy.

Core principles:

- Task contracts before execution.
- Explicit approvals before adoption, commit, and push.
- Artifact-backed auditability.
- No silent backend execution.
- No hidden output application.
- No force push.
- No raw push normalization.
- Staged-file-aware governance.
- Repeatability before multi-agent scale.

## Near-Term Roadmap

### 78 — Stabilize the Completed Lifecycle

**Purpose:** Turn the 77J-77V.1 lifecycle from a one-off success into a reusable governed path.

Candidate phases:

- 78A — PCAE Roadmap Documentation
- 78B — Backend Output Lifecycle Retrospective
- 78C — Lifecycle Command Consolidation Plan
- 78D — Adoption Lifecycle Summary Artifact
- 78E — Lifecycle Regression Suite

**Expected outcome:** PCAE has a clear post-adoption roadmap and a documented lifecycle summary.

### 79 — Fix Known Lifecycle Friction

**Purpose:** Address the pain points discovered during the first real backend-created output adoption.

Known issues:

- Staged-file-aware commits.
- Staged-file-aware task finish.
- Staged-file-aware push.
- Hook-bypass policy.
- Artifact metadata consistency.
- Stale task memory.
- Approval refresh after implementation commits.

Candidate phases:

- 79A — Staged-File-Aware Implementation Commit Mode
- 79B — Staged-File-Aware pcae task finish
- 79C — Staged-File-Aware pcae push
- 79D — Hook-Bypass Policy Formalization
- 79E — Artifact Metadata Consistency Validator
- 79F — Task Memory Auto-Reconciliation

**Expected outcome:** The next real lifecycle should not require direct push exceptions, accidental commit resets, or manual task-memory cleanup.

### 80 — Package Lifecycle Orchestration

**Purpose:** Move from many isolated phase commands to a governed lifecycle state machine.

Candidate commands:

```
pcae lifecycle backend-output-adoption status
pcae lifecycle backend-output-adoption next
pcae lifecycle backend-output-adoption run-gate --gate review
pcae lifecycle backend-output-adoption summary
```

Candidate phases:

- 80A — Lifecycle State Machine Design
- 80B — Lifecycle Status Command
- 80C — Lifecycle Next-Step Recommendation
- 80D — Lifecycle Gate Runner Dry-Run
- 80E — Lifecycle Gate Runner With Human Approval
- 80F — Lifecycle Final Summary Command

**Expected outcome:** PCAE can identify where it is in a lifecycle and recommend the next legal governed action.

### 81 — Run a Second Real Captured Task

**Purpose:** Validate repeatability after the first lifecycle and after friction fixes.

Candidate phases:

- 81A — Second Real Captured Task Selection
- 81B — Second Real Captured Task Contract
- 81C — Second Backend Capture Preflight
- 81D — Second Backend Capture
- 81E — Second Output Intake
- 81F — Second Adoption Lifecycle Using Consolidated Gates
- 81G — Second Lifecycle Final Verification

Success criteria:

- No raw git push.
- No accidental staged file inclusion.
- No uncommitted tooling leftovers.
- No ungoverned hook bypass.
- Fewer manual phases than 77J-77V.1.

### 82 — Agent Capability Discovery

**Purpose:** Introduce multiple agents safely without letting them modify the repository.

Candidate phases:

- 82A — Agent Capability Registry Design
- 82B — Agent Identity / Backend Capability Probe
- 82C — Subagent Discovery Contract
- 82D — Subagent Safety Profile
- 82E — Agent Routing Dry-Run
- 82F — Multi-Agent Task Split Dry-Run

**Expected outcome:** PCAE can discover and classify what each backend/agent can safely do before assigning work.

### 83 — Governed Multi-Agent Orchestration

**Purpose:** Move from single-agent capture to multi-agent task splitting, review, and merge governance.

Candidate phases:

- 83A — Multi-Agent Task Contract
- 83B — Agent Assignment Approval
- 83C — Parallel Prompt Package Dry-Run
- 83D — Multi-Agent Capture
- 83E — Multi-Agent Output Intake
- 83F — Conflict Detection
- 83G — Merge Review
- 83H — Single Approved Adoption Path

**Important rule:** Even with multiple agents, only one governed adoption path should modify the repository at a time.

### 84 — Persistent Memory and Project Intelligence

**Purpose:** Improve PCAE's ability to explain project state, risks, decisions, and next safe actions.

Candidate phases:

- 84A — Persistent Lifecycle Memory Model
- 84B — Artifact Index
- 84C — Governance Event Timeline
- 84D — Decision Log Integration
- 84E — Risk Register
- 84F — Project State Snapshot

**Expected outcome:** PCAE can answer:

- What phase are we in?
- What was approved?
- What is blocked?
- What can be safely done next?
- What must never be repeated?

### 85 — Productization and Documentation

**Purpose:** Prepare PCAE for explanation, demonstration, and external communication.

Candidate phases:

- 85A — Architecture Overview Refresh
- 85B — Installation / Usage Update
- 85C — Demo Script
- 85D — Governance Lifecycle Diagram
- 85E — README Reframe
- 85F — LinkedIn Article Draft

**Expected outcome:** PCAE can be presented as a governance harness for AI-assisted software engineering, not as a finished production system.

## Immediate Recommended Sequence

1. **78A** — PCAE Roadmap Documentation
2. **78B** — Backend Output Lifecycle Retrospective
3. **79A** — Staged-File-Aware Implementation Commit Mode
4. **79B** — Staged-File-Aware pcae task finish
5. **79C** — Staged-File-Aware pcae push
6. **80A** — Lifecycle State Machine Design
7. **81A** — Second Real Captured Task Selection

**Short summary:**

- Now: make the lifecycle repeatable.
- Next: automate safe next-step orchestration.
- Then: run a second real task.
- Then: add multi-agent discovery.
- Then: multi-agent orchestration.
- Finally: document and productize PCAE.
