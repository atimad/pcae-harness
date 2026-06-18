# PCAE Architecture Overview

For step-by-step setup instructions, see [docs/INSTALLATION.md](INSTALLATION.md).

## Motivation

AI coding agents can produce real changes to real repositories — commits, pushes, file rewrites — with no approval gate, no audit trail, and no rollback plan. A single unconstrained invocation can leave a codebase in an inconsistent state with no recorded path back to a known-good one.

PCAE exists to put a governed, evidence-producing boundary around that process: every step from "a human approved this prompt" to "this content was written to root" to "this write was reversed" is a structured, append-only artifact, not an unrecorded side effect. The system does not make AI execution safe by trusting the agent; it makes it governable by recording what was authorized, what was attempted, what changed, who reviewed it, and what was actually written or reverted — and by refusing to proceed when that evidence is missing.

## Governance Principles

- **Human approval is authoritative.** No prompt is invoked, no content is promoted to root, and no promotion is rolled back without an explicit human decision recorded in an artifact.
- **Evidence before action.** Every stage in the chain is gated on the prior stage's artifact existing and being in an eligible state. A missing or ineligible artifact blocks outright; it is never inferred or assumed.
- **Failure is never silent.** Where a post-execution step (such as evidence capture) can fail, the failure itself is recorded as a stored, inspectable artifact rather than discarded.
- **Mutation is the exception, not the default.** Of PCAE's entire command surface, exactly two commands mutate the root repository — `pcae promote` and `pcae rollback` — and both require prior human-reviewed evidence (an EPR or a PER) before they will act.
- **Idempotency over retry magic.** Promotion and rollback are safe to re-run against the same evidence: already-applied or already-reverted paths are skipped and recorded as such, never re-written, with no separate `--resume` flag.
- **Divergence blocks, it does not guess.** If root has changed since the evidence was captured, the entire promotion or rollback attempt is aborted before any file is touched. There is no automatic conflict resolution.
- **Approval, activation, commit, and push are distinct decisions.** Implementing a capability does not make it active; activating a phase does not authorize a commit; authorizing a commit does not authorize a push. Each is a separate human decision (see [Current Limitations](#current-limitations)).
- **No silent roadmap advancement.** The roadmap's authoritative phase registry (`_CRI_KNOWN_PHASES`) requires exactly one active phase at all times; this is enforced as a blocking `pcae check` condition, not a convention.

## Artifact Model

PCAE's execution governance is a chain of structured artifacts. Each one gates the next; none of them invoke an AI runtime or write to root except where stated.

| Artifact | Name | Phase | Store | Role |
|---|---|---|---|---|
| **APA** | Approved Prompt Artifact | 69B | `.pcae/approvals/` | Records that a specific prompt + agent combination has been explicitly human-approved before any invocation is considered. |
| **ARA** | Authorization Record | 69E | `.pcae/authorizations/` | Records that an approved, contract-validated invocation has been explicitly authorized to proceed. |
| **EAR** | Execution Audit Record | 69F | `.pcae/audit/` | Append-only audit trail entry created for every invocation attempt, regardless of outcome. |
| **ESA** | Execution Snapshot Artifact | 69J | `.pcae/execution-snapshots/` | Captures git working-tree state at a point in time, used as the before/after reference for change detection. |
| **ERR** | Execution Result Record | 69G | `.pcae/results/` | The structured outcome of an invocation attempt (technical status, captured output), classified by `pcae execution-result-governance`. |
| **ECR** | Execution Change Record | 69J | `.pcae/execution-changes/` | The set of file-level changes detected between two ESAs, classified by severity and rollback-candidacy. Captures which paths changed, not their content. |
| **ECP** | Execution Change Package | 69M | `.pcae/execution-packages/` | Full evidentiary capture of sandbox-produced content: per-file diffs, before/after content, and SHA-256 hashes, captured immediately before the sandbox is destroyed. Closes the gap left by ECR capturing paths but not content. |
| **EPR** | Execution Promotion Review | 69M | `.pcae/promotion-reviews/` | A human's explicit content-level review of a specific ECP, with partial-path approval support and a separate `promotion_authorized` flag. |
| **PER** | Promotion Execution Record | 69N | `.pcae/promotion-executions/` | Durable record of an actual write to the root repository, created before the first file write and persisted after every file. The first artifact where root mutation actually occurs. |
| **RER** | Rollback Execution Record | 69O | `.pcae/rollback-executions/` | Durable record of an actual reversal of a PER's writes, using the originating ECP's before-content and hashes as evidence. The first artifact whose subject is reversing a root mutation. |

The canonical chain, in the order evidence is produced for a single governed invocation:

```
APA -> ARA -> EAR -> ESA -> ERR/ECR -> ECP -> EPR -> PER -> RER
```

A companion artifact, **ERRA** (Execution Result Review Artifact, Phase 69I, `.pcae/result-reviews/`), records a human's disposition on an ERR's outcome (e.g. `acceptable_for_context`, `needs_follow_up`). It is distinct from EPR: ERRA reviews whether an execution's outcome was acceptable; EPR reviews whether specific captured content should be promoted to root. Neither ERRA's review nor any disposition on it authorizes execution, retry, rollback, commit, or push — those boundaries are stated explicitly in `_ERRA_GOVERNANCE_BOUNDARIES`.

## Execution Lifecycle

The path from an approved prompt to a classified result, run inside an isolated workspace:

1. **Approval** (69B) — a human approves a specific prompt/agent pair, producing an APA.
2. **Contract and pathway validation** (69C–69D) — invocation contracts and runtime contracts for the selected agent are validated; all required gates are evaluated together into a single `authorization_status`.
3. **Authorization** (69E) — an ARA is recorded for the specific invocation.
4. **Audit** (69F) — an EAR is created for the attempt before it proceeds.
5. **Activation** (69G) — `pcae execution-activation invoke` runs the invocation inside a sandboxed workspace (Phase 69L: a `git worktree` + `rsync` overlay, not the root checkout), producing an ERR.
6. **Result governance** (69H) — the ERR is classified along technical status, governance attention, and severity axes.
7. **Snapshot and change detection** (69J–69K) — ESAs taken before and after the attempt are diffed into an ECR, with automatic snapshot integration removing the need for a manual snapshot step.
8. **Result review** (69I) — a human records a disposition on the ERR as an ERRA.

At every one of these steps, `execution_allowed` is hard-coded `False`. No command in this lifecycle invokes a real AI runtime against the live root checkout, and none of them write to root.

## Promotion Lifecycle

Promotion is what turns sandboxed, reviewed content into a root-repository write:

1. **Change capture** (69M) — immediately before the sandbox is destroyed, an ECP captures every changed file's diff, before/after content, and hashes. Hard exclusions (`.git/`, `.pcae/`, external symlink escapes) can never be overridden; default exclusions (toolchain artifacts, gitignored files, oversized binaries) can be reviewed per-path.
2. **Promotion review** (69M) — a human reviews the ECP and records an EPR: a disposition (`approved`/`rejected`/`deferred`/`escalated`/`cancelled`), optionally a partial set of `approved_paths`, and a separate `promotion_authorized` flag that nothing before 69N consumes.
3. **Promotion execution** (69N) — `pcae promote --epr-id <id>` is the first command in PCAE's history that mutates root. It is gated strictly on `EPR.promotion_authorized=True`, never on an ECP alone. For each eligible path it performs a three-way divergence check against the current root content (`pending` / `already_applied` / `conflict`); any conflict aborts the entire attempt before any file is touched. A PER is created with `status="in_progress"` before the first write and persisted after every file, so an interrupted promotion is always a stored, inspectable record, and a second `pcae promote` against the same EPR resumes safely (`already_applied` paths are skipped, not re-written).

`execution_allowed` remains `False` through promotion. `pcae promote` does not invoke a runtime; it writes content that a human already reviewed and authorized in the EPR.

## Rollback Lifecycle

Rollback is the mirror image of promotion, reversing a specific promotion's writes using evidence captured during that promotion — never user-specified paths, never a range of PERs:

1. **Eligibility gate** — `pcae rollback --per-id <id>` is refused outright unless the target PER has `status` in `{completed, partial}` and `rollback_payload_available=True`. No RER is created on refusal.
2. **Plan derivation** — the rollback's file plan is derived strictly from `PER.file_results` where `outcome="success"`; `already_applied` entries from the original promotion are excluded, since those paths were never written by the PER being rolled back.
3. **Divergence check (inverted from promotion)** — a path whose current root hash matches the PER's `after_hash` is `pending` (still promoted, needs reverting); a path matching `before_hash` is `already_reverted` and is skipped without error; a path matching neither is a `conflict` that aborts the entire attempt before any file is touched.
4. **Restore** — for each file actually reverted, `before_exists=True` restores the original `before_content`; `before_exists=False` removes the file. An RER is created with `status="in_progress"` before the first restore and persisted after every file.
5. **Resumability, not retry** — re-running `pcae rollback` against the same PER resumes a partial rollback via the `already_reverted` skip; there is no `--resume` flag. `pcae rollback-execution mark-interrupted` transitions an interrupted RER from `in_progress` to `partial` as pure bookkeeping — it never writes a file.

There is no mechanism to target an RER for reversal: the rollback build function accepts only a `per_id`, never an `rer_id`. Rollback-of-rollback is forbidden by construction, not by a runtime check that could be bypassed.

## Strategic Lineage Philosophy

PCAE distinguishes three kinds of record that are easy to conflate:

- **Roadmap state** (`_CRI_KNOWN_PHASES` in `src/pcae/core/agent.py`) — which phase is active, completed, or superseded. Mutable in the sense that statuses advance, but only one phase may be active at a time, enforced as a blocking check.
- **Activation evidence** (provenance events) — a timestamped record that a phase was activated.
- **Strategic decision lineage** (`.pcae/strategic-lineage.json`, Phase 65J) — an append-only record of *why* a human made a given strategic decision: the rationale, the alternatives considered and deferred, and the Strategic Lineage Record (SLR) entries documenting accepted scope. This file is authoritative only for human strategic decisions and their rationale. It does not own roadmap state, does not own activation evidence, and a later phase's lineage record superseding an earlier one (`supersedes_lineage_id`) never mutates or deletes the earlier record — supersession is reference-derived, not a status flip.

Sitting alongside lineage is the **Independent Review Governance (IRG) Challenge** (Phases 66E–68D): an automated, advisory-only mechanism that surfaces assumptions, blind spots, counterfactuals, and uncertainty about a strategic decision for human attention. It is deliberately *not* an approval authority — it never recommends approval or rejection, never prescribes implementation, and never gates a command's outcome. Its findings are surfaced at session bootstrap, phase handoff, and phase completion, with full detail available on demand (`pcae irg-challenge`).

The underlying principle, stated explicitly in this project's accepted decisions: **implementation approval does not imply activation approval, commit approval, or push approval.** A capability can be fully coded and tested and still not be the thing a human has authorized as "the current active phase," let alone authorized to commit or push. PCAE's own roadmap registry has carried this distinction since Phase 65I/65J, and it applies recursively to PCAE's own development process, not just to the code it governs.

## Current Limitations

- **No real AI runtime invocation.** `execution_allowed=False` everywhere, including inside the sandboxed execution lifecycle and through `pcae promote`/`pcae rollback`. Promotion and rollback write content a human already authorized; they do not invoke an agent.
- **Workspace isolation is not OS-level containment.** The Phase 69L sandbox is a `git worktree` + `rsync` overlay with the subprocess `cwd` pointed at the sandbox directory — it isolates *relative* working-tree changes, not absolute-path filesystem access, process isolation, or network isolation. `production_containment_ready=False` is asserted explicitly and cannot be auto-asserted true.
- **The sandbox shares git's object store with root.** A git commit made inside the sandbox lands in the same object database as the root checkout (Phase 69L, SLR-69L-006).
- **No commit or push automation anywhere.** Every governed write path stops at a file-level write or reversal; `git commit` and `git push` remain exclusively human actions.
- **Phase Activation Governance is unresolved roadmap debt.** PCAE has no first-class mechanism that separates "implementation approved" from "activation approved" from "commit approved" from "push approved" as distinct, independently-recorded human decisions — today this distinction is enforced by convention and by the single-active-phase invariant, not by a dedicated artifact.
- **Single active phase, no designated successor for 69O.** The roadmap registry's "exactly one active phase" invariant means a phase cannot be marked `completed` without a successor phase taking over `active` status. As of this writing, Phase 69O is BR-005's last implemented phase and remains the formally active phase pending a future, explicitly human-approved phase activation decision — even though the BR-005 capability set described above is fully implemented end to end (see [PROJECT_STATUS.md](../PROJECT_STATUS.md)).

## Deferred Capabilities

Explicitly out of scope for the BR-005 execution governance chain as implemented through Phase 69O:

- Automatic promotion or automatic rollback — both require an explicit human-invoked command every time.
- Rollback-of-rollback — no entry point accepts an `rer_id` as a rollback target.
- Multi-PER batch rollback — `pcae rollback` takes exactly one `--per-id`.
- Divergence override consumption — EPR's `override_divergence` field is recorded but not consumed by `pcae promote`; a conflict always aborts the attempt.
- Container-based or OS-level sandbox providers — `docker_dependency_forbidden=True` and `sandbox_exec_dependency_forbidden=True` are explicit constraints; only `git worktree` workspace isolation exists.
- Forensic retention of sandbox directories — sandbox directories are ephemeral and destroyed after evidence capture; no separate forensic copy is retained.
- Atomic, staged-rename file writes for promotion — promotion and rollback write sequentially per file with incremental PER/RER persistence, not as a single atomic transaction.
- Any git commit or push step inside the governed write/rollback chain.

## Lifecycle Review Gate Design (Phase 70Q)

### Problem

PCAE has two distinct review domains:

1. **Execution review (69-series)** — governs AI runtime invocations. Artifacts: ERRA (ExecutionResultReviewArtifact), EPR (ExecutionPromotionReview). These review sandbox outputs before promotion to root. Stored in `.pcae/` artifact stores.

2. **Lifecycle review (70-series)** — governs developer task implementation. No review artifacts exist today. `pcae task finish` enforces health/check/acceptance but has no concept of "reviewed."

These are fundamentally different: execution review asks "should this AI output be promoted?" while lifecycle review asks "has this implementation been reviewed before closure?"

### Lifecycle Review Record (LRR) — Proposed Design

A Lifecycle Review Record captures evidence that implementation changes were reviewed before task closure.

#### Artifact Shape

```
.pcae/lifecycle-reviews/{task_id}-{timestamp}.json
```

```json
{
  "lrr_id": "lrr-{task_id}-{timestamp}",
  "task_id": "20260618-2129-70p-acceptance-criteria-vs-executable-checks",
  "reviewer": "human",
  "disposition": "approved",
  "commit_range": "e9bf3a2..d4484f90",
  "reviewed_files": ["src/pcae/core/tasks.py", "src/pcae/commands/task.py"],
  "notes": "Acceptance criteria/checks separation looks correct.",
  "created_at": "2026-06-18T21:30:00+02:00"
}
```

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `lrr_id` | string | Unique identifier |
| `task_id` | string | Active task at review time |
| `reviewer` | string | Who reviewed (default: "human") |
| `disposition` | enum | `approved`, `changes_requested`, `informational` |
| `commit_range` | string | Git commit range reviewed |
| `reviewed_files` | list | Files explicitly reviewed |
| `notes` | string | Free-text review notes |
| `created_at` | ISO timestamp | When the review was recorded |

#### Dispositions

- **approved** — implementation is reviewed and acceptable
- **changes_requested** — reviewer identified issues; task should not close
- **informational** — review is recorded but does not gate closure

### Proposed Command Shape

```bash
# Record a lifecycle review
pcae review lifecycle --disposition approved --notes "Looks good"
pcae review lifecycle --disposition approved --json

# Show reviews for the current task
pcae review lifecycle show
pcae review lifecycle list --task-id <id>
```

### Integration Points

| Command | Current behavior | With lifecycle review |
|---------|-----------------|---------------------|
| `pcae task finish` | Runs health + check + acceptance checks | Additionally checks for LRR if `require_approved` policy is enabled |
| `pcae task finish --commit` | Same as above + commit | Same gate before commit |
| `pcae push check` | Checks health/check/doctor/git | Reports review status; blocks when `require_approved = true` and review is not approved |
| `pcae push` | Runs push check + push | Refuses push when policy-required review fails |
| `pcae health` | Reports overall health | Could include review coverage as informational |
| `pcae check` | Validates scope/zones/docs | No change — check is about source validity, not review |

### Policy Configuration

```toml
[lifecycle_review]
require_approved = false  # advisory-first default
```

When `false` (default): LRR is informational. `pcae push check` shows review status but does not gate on it.
When `true`: `pcae push check` requires review status `approved` or `not_applicable` to pass. Statuses `missing`, `changes_requested`, `informational_only`, `mixed`, and `unknown` block push readiness.

JSON output includes `lifecycle_review_required`, `lifecycle_review_passed`, and `lifecycle_review_reason` fields.

### Rollout Recommendation: Advisory-First

1. **Phase 1 (advisory, 70R)**: Add `pcae review lifecycle` command. Record reviews optionally. `pcae push check` reports review coverage.

2. **Phase 2 (visibility, 70S)**: `pcae push check` shows lifecycle review status in human and JSON output.

3. **Phase 3 (enforcement, 70T)**: Policy option `require_approved = true` makes review a blocker for `pcae push check` and `pcae push`.

### What This Does NOT Change

- 69-series execution review (ERRA, EPR) is unchanged
- `pcae promote` and `pcae rollback` gate on execution review, not lifecycle review
- `pcae task complete` remains a bare primitive with no gates
- `--skip-checks` continues to bypass all gates including lifecycle review
- No automatic review approval — review requires explicit human action

## Governed Multi-Phase Runner Design (Phase 70Z)

### Problem

PCAE supports governed lifecycle automation: task creation, commit, finish, push, handoff, and phase queue planning. An agent can execute these one phase at a time with human supervision. Direct autonomous multi-phase execution without governance would risk undetected scope drift, cascading failures, silent state corruption, and ungoverned mutations.

### Why Autonomous Multi-Phase Execution is Risky

1. **Cascading failures**: a broken commit in phase N poisons phases N+1 through N+K before detection.
2. **Scope drift**: without per-phase human review, implementation can silently expand beyond the phase spec.
3. **Silent state corruption**: governance artifacts (provenance, session, agent lock) can become inconsistent if a phase fails mid-mutation.
4. **Ungoverned mutations**: push, commit, and task-finish are root mutations — unattended execution removes the human gate.
5. **Test blindness**: tests verify code correctness, not feature correctness — a passing test suite does not guarantee the right thing was built.
6. **Review bypass**: lifecycle review enforcement exists precisely to gate push readiness — autonomous execution without review defeats the purpose.

### Proposed Design: Governed One-Phase-at-a-Time Execution

The multi-phase runner should execute exactly one phase per iteration, validate governance between phases, and stop on any anomaly. It does not batch, parallelize, or skip governance gates.

#### Command Shape

```
pcae phase run-queue [--max-phases N] [--stop-on-warning] [--dry-run] [--json]
```

- `--max-phases N`: execute at most N phases from the queue (default: 1).
- `--stop-on-warning`: stop on warnings, not just errors.
- `--dry-run`: validate the queue and report what would execute without running anything.
- Default behavior: execute one phase, validate, stop.

#### Execution Loop (per phase)

1. Read next entry from `.pcae/phase-queue.json`.
2. Create task contract via `pcae task new`.
3. Agent implements the phase (external agent or PCAE-native).
4. Run `pcae check`, `python -m pytest -n auto`.
5. Commit implementation.
6. Run `pcae task finish --commit`.
7. Run `pcae push`.
8. Run `pcae phase handoff`.
9. Validate stop conditions.
10. If clean, remove completed entry from queue, continue to next.
11. If stop condition triggered, halt and report.

#### Mandatory Stop Conditions

| Condition | Severity | Action |
|-----------|----------|--------|
| Test failure (`pytest` exit != 0) | error | halt immediately |
| `pcae health` unhealthy | error | halt immediately |
| `pcae check` failed | error | halt immediately |
| Dirty working tree after commit | error | halt immediately |
| `pcae push check` not ready | error | halt immediately |
| Lifecycle review required but not approved | error | halt immediately |
| `pcae doctor task-memory` has errors | error | halt immediately |
| Files changed outside task scope | error | halt immediately |
| `pcae push` fails | error | halt immediately |
| `pcae doctor task-memory` has warnings | warning | halt if `--stop-on-warning` |
| Unexpected untracked files | warning | halt if `--stop-on-warning` |

#### Audit Artifact

Each phase execution produces an audit artifact at `.pcae/phase-runs/<run-id>.json`:

```json
{
  "run_id": "run-20260619T010000-70W",
  "phase_description": "70W — Handoff Bootstrap Consumption",
  "started_at": "2026-06-19T01:00:00+00:00",
  "completed_at": "2026-06-19T01:05:00+00:00",
  "status": "completed | failed | stopped",
  "stop_reason": null,
  "task_id": "20260619-0100-handoff-bootstrap-consumption",
  "commit_hash": "abc123",
  "push_result": "success | failed | skipped",
  "health_passed": true,
  "check_passed": true,
  "tests_passed": true,
  "doctor_clean": true,
  "files_changed": ["src/pcae/commands/session.py", "tests/test_session.py"],
  "test_count": 5907,
  "duration_seconds": 300
}
```

#### External-Agent-Driven vs PCAE-Native

The runner should be **external-agent-driven**, not PCAE-native:

- **External-agent-driven**: an AI agent (Claude, Codex) reads the queue, implements each phase, and calls PCAE governance commands. PCAE validates but does not drive implementation. The agent is the executor; PCAE is the governance layer.
- **PCAE-native**: PCAE itself drives implementation by invoking an agent runtime. This couples execution to governance, which violates separation of concerns and requires PCAE to manage agent sessions, prompts, and context windows.

The external-agent-driven model preserves PCAE's role as a governance harness. The runner command (`pcae phase run-queue`) would orchestrate the governance loop (create task, validate, finish, push, handoff) while delegating implementation to the agent.

#### What This Design Does NOT Include

- No implementation in Phase 70Z — design only.
- No automatic review approval — lifecycle review still requires explicit human action.
- No parallel phase execution — one phase at a time.
- No retry on failure — failed phases require human investigation.
- No branch/remote management — uses current branch.
- No prompt generation — phase descriptions are human-authored in the queue.
