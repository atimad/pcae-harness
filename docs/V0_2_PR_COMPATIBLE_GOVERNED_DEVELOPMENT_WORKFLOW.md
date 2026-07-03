# PCAE v0.2 PR-Compatible Governed Development Workflow

**Frozen by**: Phase 107E | **Status**: design/freeze only — no execution
capability, PR automation, GitHub Actions changes, GitHub API integration,
automatic PR creation, automatic merge, automatic approval, merge queue, or
branch creation automation implemented by this document or this phase.

## Purpose

Design and freeze, in one canonical document, the governed development
workflow PCAE follows in a branch-protected repository — before any
execution capability is implemented (108A onward). This document defines
canonical repository roles, the development flow from task to merge, branch
policy, what AI agents may and may not do, the distinction between Git
approval and execution approval, PR requirements, how existing PCAE
governance commands map onto the workflow, and how future execution
components (Permission Broker, Human Approval Gate, Execution Boundary,
Audit Boundary, Rollback Readiness) will eventually integrate with it. It
does not implement any of those future components, any PR automation, or
any execution capability; it only fixes their shape and where they attach.

This document builds on `docs/V0_2_AUTONOMY_CONTRACT.md` (Phase 107B —
architectural invariants, execution lifecycle, components) and
`docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md` (Phase 107C — the 25 no-go
gates that must block execution). It does not change either. It also does
not change `docs/PHASE_106_REPOSITORY_CONTRIBUTION_SAFETY_BRANCH_PROTECTION.md`'s
live branch protection configuration — it documents the current posture and
designs how the governed lifecycle will need to adapt if that posture ever
tightens.

## 1. Repository Roles

Seven canonical roles are frozen. Each has explicit responsibilities,
authority, and limitations. No role listed below currently has execution
authority — that concept does not exist until Phase 108A onward, and even
then only within the bounds of `docs/V0_2_AUTONOMY_CONTRACT.md`'s
invariants.

### Repository Owner

- **Responsibilities:** Own the repository, set branch protection policy,
  hold ultimate authority over what merges to `main`.
- **Authority:** Can configure and change branch protection rules; can, in
  the current transitional posture (`enforce_admins: false`), push directly
  to `main` via the governed `pcae push` lifecycle.
- **Limitations:** Even the Owner's governed pushes still go through
  `pcae health` / `pcae check` / `pcae doctor task-memory` / `pcae push
  check` before every push (see Governance Mapping). The Owner does not
  have execution authority under `docs/V0_2_AUTONOMY_CONTRACT.md` — that is
  a separate, not-yet-implemented concept (Git approval and execution
  approval are distinct; see §5).

### Maintainer

- **Responsibilities:** Review and approve pull requests; maintain code
  quality and adherence to governance conventions; may be delegated
  repository administration by the Owner.
- **Authority:** Can approve/request-changes on PRs; cannot bypass branch
  protection unless separately granted admin rights by the Owner.
- **Limitations:** Subject to the same required review, conversation
  resolution, and status-check requirements as any other contributor's PR
  once `enforce_admins` is ever set to `true`.

### Contributor

- **Responsibilities:** Propose changes via feature branches and pull
  requests; respond to review feedback; keep task contracts and validation
  evidence current.
- **Authority:** Can open PRs, push to their own feature branches, and
  request review.
- **Limitations:** Cannot push directly to `main` (blocked by branch
  protection regardless of `enforce_admins`, since only the Owner is
  currently exempt); cannot self-merge without required approval; cannot
  bypass conversation resolution or status checks.

### Human Reviewer

- **Responsibilities:** Review proposed changes for correctness, safety,
  and adherence to governance/task-contract scope; explicitly approve or
  request changes.
- **Authority:** Approval is one of the two required PR gates (the other
  being conversation resolution). A Human Reviewer's approval is a **Git
  approval** — see §5 for why this is explicitly not an execution
  approval.
- **Limitations:** Review authority is scoped to the PR's diff and its
  stated task contract; a Human Reviewer does not thereby gain execution
  authority over anything outside version control.

### PCAE

- **Responsibilities:** Provide the governed lifecycle tooling (task
  contracts, commit/push wrappers, health/check/doctor validation, phase
  completion and report trust, notification) that every role above uses to
  keep changes scoped, validated, and auditable.
- **Authority:** PCAE can block a governed commit or push if health/check/
  task-memory/push-check fail. PCAE has no authority over GitHub's actual
  branch protection enforcement — that is GitHub's, configured by the
  Owner.
- **Limitations:** PCAE is advisory/governance tooling, not an execution
  engine (v0.1.0-rc1 is explicitly non-executing by design). PCAE does not
  merge PRs, approve PRs, or bypass branch protection on anyone's behalf.

### AI Coding Agent

- **Responsibilities:** Under a role's direction (typically a Contributor's
  or the Owner's), plan work, generate code, prepare commits, prepare
  documentation, and follow the governed task-contract/commit/push
  lifecycle exactly as any other contributor would.
- **Authority:** None beyond what the directing human explicitly grants for
  a given session. No standing authority to merge, approve, or bypass
  governance. See §4 for the frozen AI Participation Model.
- **Limitations:** May not merge, self-approve, bypass branch protection,
  bypass PCAE governance, bypass a future Permission Broker, authorize
  execution, or authorize itself for anything. These limitations are
  invariant regardless of how capable a future AI Coding Agent becomes.

### Permission Broker (future)

- **Responsibilities (future, not implemented):** Decide, for any proposed
  *execution* action (not a Git operation), whether it is `allow`, `deny`,
  or `human_review`, per `docs/V0_2_AUTONOMY_CONTRACT.md`.
- **Authority (future, not implemented):** Sole authority over execution
  authorization once implemented (Phase 108A). Fail-closed by design
  (INV-004).
- **Limitations:** **Not implemented today.** Has no role in the current
  Git/PR workflow described in this document — the Permission Broker
  governs *execution* approval, not *Git* approval (§5), and today neither
  exists as a real, code-enforced gate.

## 2. Development Flow

The canonical development flow is frozen as:

```
Task
  |
  v
Feature Branch
  |
  v
Implementation
  |
  v
Validation
  |
  v
Review
  |
  v
Approval
  |
  v
Merge
  |
  v
Main
```

| Stage | Description |
|---|---|
| **Task** | A governed task contract is created (`pcae task new`) scoping allowed files, zones, and goal. |
| **Feature Branch** | Work proceeds on a branch, not directly on `main` (Contributors are blocked from pushing to `main` regardless of `enforce_admins`; the Owner currently may push directly under the transitional posture — see §3). |
| **Implementation** | Changes are made within the task contract's scope; every change is committed through the governed `pcae commit implementation` path, never raw `git commit`. |
| **Validation** | `pcae health`, `pcae check`, `pcae doctor task-memory`, and the project's test suite (`python -m pytest -n auto` or scoped equivalents) must pass. |
| **Review** | A Human Reviewer examines the diff against the task contract and validation evidence. |
| **Approval** | An explicit, affirmative Git approval is recorded (PR review approval, or, in the current transitional posture, the Owner's own governed push). This is a **Git approval**, not an execution approval (§5). |
| **Merge** | The approved, validated branch is merged into `main` — conversation resolution and required status checks (once configured) must be satisfied first. |
| **Main** | `main` is the single source of truth; branch protection prevents force-push and deletion regardless of role. |

This document freezes the flow itself. **No implementation of PR
automation, automatic branch creation, automatic merge, or automatic
approval is performed by this phase** — every stage above remains a human-
or governed-tooling-driven action today.

## 3. Branch Policy

### Protected `main`

- Direct push blocked for all roles except the Owner during the current
  transitional posture (`enforce_admins: false`).
- Force-push blocked (`allow_force_pushes: false`) for every role,
  including the Owner.
- Branch deletion blocked (`allow_deletions: false`) for every role,
  including the Owner.
- One required approving PR review (`required_approving_review_count: 1`),
  with stale reviews dismissed automatically on new commits
  (`dismiss_stale_reviews: true`).
- Conversation resolution required before merge.

### Feature Branches

- Unprotected by default; used for all Contributor and Maintainer work, and
  recommended (not yet required) for Owner work outside the transitional
  direct-push posture.
- No naming convention is imposed by this document; a future phase may
  define one if needed.

### Release Branches (future, if applicable)

- Not in use today. If introduced, release branches would inherit at least
  the same protections as `main` (no force-push, no deletion); exact policy
  is deferred to whichever future phase introduces them. **Design-only
  placeholder — no release-branch mechanism exists or is implemented by
  this phase.**

### Owner Workflow (current, transitional)

The Owner may use the governed `pcae push` lifecycle to push directly to
`main` today, because `enforce_admins: false`. Every such push still passes
through `pcae health` / `pcae check` / `pcae doctor task-memory` / `pcae
push check` first — the transitional posture relaxes GitHub-side branch
protection for the Owner, not PCAE's own governance gates. This is
documented, intentional, and unchanged by this phase
(`docs/PHASE_106_REPOSITORY_CONTRIBUTION_SAFETY_BRANCH_PROTECTION.md`).

### Maintainer Workflow

Maintainers work through feature branches and PRs like Contributors, but
may additionally review and approve others' PRs. Maintainers do not have
the Owner's transitional direct-push exemption unless separately granted
admin rights.

### Contributor Workflow

Contributors always work through feature branches and PRs: branch → commit
(governed) → push branch → open PR → validation → review → approval →
merge. Contributors cannot push to `main` under any current configuration.

### Current Transitional Posture (documented, unchanged by this phase)

| Setting | Current value |
|---|---|
| `enforce_admins` | `false` — repository admin (Owner) may bypass PR requirement |
| Required PR review | `1` approving review required (non-admin) |
| Conversation resolution | required before merge |
| Force push | blocked (`allow_force_pushes: false`), all roles |
| Branch deletion | blocked (`allow_deletions: false`), all roles |
| Stale review dismissal | enabled (`dismiss_stale_reviews: true`) |

This phase does not change any of these settings. It documents them as the
baseline this workflow design assumes, and — per `docs/V0_2_AUTONOMY_CONTRACT.md`'s
"PR / Branch Protection Workflow" component — is the design work that must
happen *before* `enforce_admins: true` is ever adopted, not concurrently
with it.

## 4. AI Participation Model

Frozen for what AI Coding Agents may eventually do, once any of this is
implemented (none of it is implemented by this phase):

**May:**

- Plan work.
- Generate code.
- Prepare commits (via the governed `pcae commit implementation` path).
- Prepare documentation.
- Recommend PR text (title, description, summary).
- Recommend reviewers.

**May not:**

- Merge.
- Self-approve.
- Bypass branch protection.
- Bypass PCAE governance (health/check/doctor/push-check).
- Bypass the Permission Broker (once it exists).
- Authorize execution.
- Authorize itself for anything.

**Current implementation status: Not implemented.** No mechanism exists
today that lets an AI Coding Agent merge, approve, or bypass any governance
gate — this section fixes the permanent boundary, not a current capability.
The "may" list describes assistive actions already broadly consistent with
how this repository's governed lifecycle is used in practice (an AI agent
preparing commits under a human-directed task contract); the "may not" list
is an invariant boundary, not a target to be relaxed by a future phase.

## 5. Approval Model

Two distinct governance concepts are frozen as separate and non-substitutable:

### Git Approval

- **What it is:** Approval that a proposed *change to the repository's
  version-controlled content* (code, docs, tests, config) is correct and
  should be merged.
- **Who grants it:** A Human Reviewer (PR review approval) or, in the
  current transitional posture, the Owner via a governed push.
- **What it authorizes:** Merging a diff into `main`. Nothing more.
- **What it does not authorize:** Any runtime action, execution, shell
  command, backend invocation, or mutation outside version control. Git
  approval has no bearing on execution authorization.

### Execution Approval

- **What it is (future, not implemented):** Approval that a specific,
  proposed *execution action* (per `docs/V0_2_AUTONOMY_CONTRACT.md`'s
  lifecycle: `PLANNED -> READY -> AWAITING_HUMAN_APPROVAL -> AUTHORIZED ->
  EXECUTING -> {COMPLETED|FAILED|ABORTED}`) may proceed.
- **Who would grant it (future):** The Human Approval Gate component,
  after a Permission Broker `allow`/`human_review` decision — a distinct
  mechanism from PR review.
- **What it would authorize (future):** A single mediated execution
  action, once the Permission Broker, Execution Boundary, and other
  invariants from `docs/V0_2_AUTONOMY_CONTRACT.md` are implemented.
- **Current status:** **Not implemented.** No execution approval mechanism
  exists in this codebase today. Merging a PR (Git approval) never has
  granted, and does not grant, execution approval.

**These are never interchangeable.** A merged PR is not an authorized
execution. An authorized execution (once the mechanism exists) does not by
itself constitute or require a Git approval — it is a runtime decision
about a specific action, evaluated independently of version-control state.
This separation is INV-008 (`docs/V0_2_AUTONOMY_CONTRACT.md`): "Execution
capability does not imply execution authorization," extended here to state
explicitly that *Git* capability/approval does not imply execution
authorization either.

## 6. PR Requirements

The following are frozen as the requirements a pull request must satisfy
before merge, once this workflow is fully in effect:

- Passing validation (`python -m pytest -n auto`, or the relevant scoped
  test groups for the change).
- Healthy governance (`pcae health` reports `healthy`).
- Clean governance check (`pcae check` passes with no violations).
- Clean task memory (`pcae doctor task-memory` reports no inconsistencies).
- Clean push readiness (`pcae push check` reports ready).
- Review complete (required approving review satisfied).
- Conversations resolved (all PR review threads marked resolved).
- Branch protection satisfied (no force-push, no direct push to `main`
  outside the Owner's transitional exemption, no deletion).

**No automated PR requirement checking is implemented by this phase.**
These requirements are documented as the target checklist; enforcing them
automatically (e.g., via required GitHub status checks wired to `pcae
check`) is explicitly out of scope here (no GitHub Actions changes, no
GitHub API integration — see Non-Goals) and is deferred to a future phase.

## 7. Governance Mapping

Existing PCAE commands map onto the workflow as follows:

| Command | Workflow stage(s) | Role(s) |
|---|---|---|
| `pcae task new` / `pcae task update` | Task | Contributor, Owner, AI Coding Agent (under direction) |
| `pcae commit implementation` | Implementation | Contributor, Owner, AI Coding Agent (under direction) |
| `python -m pytest -n auto` (or scoped groups) | Validation | Contributor, Owner, AI Coding Agent |
| `pcae health` | Validation, PR Requirements | All roles, before every commit/push |
| `pcae check` | Validation, PR Requirements | All roles, before every commit/push |
| `pcae doctor task-memory` | Validation, PR Requirements | All roles, before every commit/push |
| `pcae push check` | PR Requirements, pre-Merge | All roles, before every push |
| `pcae task finish` | Approval-adjacent (task closure) | Contributor, Owner, AI Coding Agent (under direction) |
| `pcae push` | Merge (Owner's transitional direct path) or branch push (Contributor/Maintainer PR path) | Owner (direct), Contributor/Maintainer (branch push, then PR) |
| Phase completion (`pcae phase complete`) | Post-Merge, Main | Owner, AI Coding Agent (under direction) — governance-level phase bookkeeping, not a Git or execution approval |
| Report trust (phase-completion-metadata validation) | Post-Merge, Main | PCAE (automated validation of the phase report's completeness) |

None of these commands grant execution authority. All of them operate
within the existing v0.1.0-rc1 non-executing design.

## 8. Future Integration

How the not-yet-implemented v0.2 execution components will eventually
attach to this workflow — **design only, nothing below is implemented by
this phase**:

### Permission Broker

Will evaluate proposed *execution* actions independently of the Git
workflow above. Attaches after `AWAITING_HUMAN_APPROVAL` is reached in the
execution lifecycle — never substitutes for, and is never substituted by,
PR review. Implementation: Phase 108A (recommended next phase).

### Human Approval Gate

Will require and record an explicit execution approval, distinct from any
Git approval already granted for the same underlying change (§5). A merged
PR does not pre-satisfy this gate. Implementation: Phase 111A per
`docs/V0_2_AUTONOMY_CONTRACT.md`.

### Execution Boundary

Will be the single code path through which any mediated action may run,
enforced independently of whether the code implementing that action has
already been merged to `main` via this workflow. Merging code that
*could* execute something does not, by itself, execute anything
(INV-008). Implementation: not yet scheduled beyond the sequence in
`docs/V0_2_AUTONOMY_CONTRACT.md`.

### Audit Boundary

Will persist execution decisions durably, separately from this workflow's
existing Git history and phase-completion reports (which remain v0.1's
non-execution-track evidence mechanism). Implementation: Phase 112A.

### Rollback Readiness Boundary

Will require a validated rollback plan to exist before an execution action
can be authorized — a precondition evaluated at execution-authorization
time, not at PR-merge time. A merged PR is not a rollback plan.
Implementation: Phase 113A (design).

## 9. Current Status

Every future capability referenced in this document is explicitly marked:

| Capability | Status |
|---|---|
| Permission Broker (real) | Not implemented |
| Human Approval Gate (execution) | Not implemented |
| Execution Boundary | Not implemented |
| Shell/Subprocess/Network Boundary (enforced) | Not implemented |
| Backend Invocation Boundary | Not implemented |
| Adapter Invocation Boundary | Not implemented |
| Audit Boundary (durable) | Not implemented |
| Rollback Readiness Boundary | Not implemented |
| Emergency Stop Boundary | Not implemented |
| Execution Enablement Model | Not implemented |
| PR automation / automatic PR creation | Not implemented |
| Automatic merge | Not implemented |
| Automatic approval | Not implemented |
| Merge queues | Not implemented |
| Branch creation automation | Not implemented |
| GitHub Actions changes for this workflow | Not implemented |
| GitHub API integration for this workflow | Not implemented |

The Git-level workflow described in §1–§3 and §6–§7 (roles, development
flow, branch protection, PR requirements, governance command mapping)
**is already how this repository operates today** for ordinary,
non-execution governed development — this document freezes and documents
that existing practice rather than introducing a new one. Everything
execution-related (§4's future AI capabilities beyond assistive
preparation, §5's Execution Approval, §8 in full) remains **not
implemented**.

## Explicit Non-Goals (This Document and This Phase)

- No runtime enforcement.
- No execution capability.
- No permission broker enforcement.
- No shell mediation.
- No backend invocation.
- No adapter execution.
- No Telegram inbound.
- No audit storage implementation.
- No rollback execution.
- No emergency stop implementation.
- No execution enablement.
- No PR automation.
- No GitHub Actions changes.
- No GitHub API integration.
- No automatic PR creation.
- No automatic merge.
- No automatic approval.
- No merge queues.
- No branch creation automation.

## Recommended Next Phase

**108A — Permission Broker Enforcement Implementation.** Implement the real
Permission Broker described in `docs/V0_2_AUTONOMY_CONTRACT.md` and
referenced throughout this document's Future Integration section — the
first execution-track implementation phase, gated behind everything frozen
in 107B, 107C, and this phase.
