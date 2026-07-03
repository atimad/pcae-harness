# Phase 107E — PR-Compatible Governed Development Workflow Design

## Purpose

Design and freeze the governed development workflow PCAE follows in a
branch-protected repository — seven canonical roles, the Task → Feature
Branch → Implementation → Validation → Review → Approval → Merge → Main
development flow, branch policy (including the current transitional
posture), the AI participation model, the Git-approval-vs-execution-approval
distinction, PR requirements, a mapping of existing governance commands
onto the workflow, and how future execution components will eventually
attach — before any enforcement or execution implementation begins in
Phase 108A.

## Scope

Design/freeze only. Produces `docs/V0_2_PR_COMPATIBLE_GOVERNED_DEVELOPMENT_WORKFLOW.md`
(the frozen workflow document) and `tests/test_v0_2_pr_compatible_governed_workflow.py`.
Builds on `docs/V0_2_AUTONOMY_CONTRACT.md` (Phase 107B — invariants,
lifecycle, components, including the "PR / Branch Protection Workflow"
component this phase now formally designs) and
`docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md` (Phase 107C). No product/
runtime behavior is implemented or changed in this phase, and no change is
made to live GitHub branch protection configuration
(`docs/PHASE_106_REPOSITORY_CONTRIBUTION_SAFETY_BRANCH_PROTECTION.md`
remains authoritative and unchanged).

## Non-Goals

No runtime enforcement; no execution capability; no permission broker
enforcement; no shell mediation; no backend invocation; no adapter
execution; no Telegram inbound; no audit storage implementation; no
rollback execution; no emergency stop implementation; no execution
enablement; no PR automation; no GitHub Actions changes; no GitHub API
integration; no automatic PR creation; no automatic merge; no automatic
approval; no merge queues; no branch creation automation. `v0.1.0-rc1`
remains non-executing by design; v0.2 remains the autonomy target. No
change to `v0.1.0-rc1`, its GitHub Release, or branch protection on `main`.
No new tag. No new release. No package publication.

## What Was Frozen

`docs/V0_2_PR_COMPATIBLE_GOVERNED_DEVELOPMENT_WORKFLOW.md` freezes:

- **Seven repository roles** (Repository Owner, Maintainer, Contributor,
  Human Reviewer, PCAE, AI Coding Agent, Permission Broker (future)), each
  with explicit responsibilities, authority, and limitations.
- **The canonical development flow**: Task → Feature Branch →
  Implementation → Validation → Review → Approval → Merge → Main.
- **Branch policy**: protected `main` (force-push/deletion blocked for all
  roles, 1 required approving review, stale-review dismissal,
  conversation resolution required, admin enforcement currently off
  transitionally), feature branches, a design-only release-branch
  placeholder, and per-role (Owner/Maintainer/Contributor) workflow
  descriptions.
- **The AI Participation Model**: a frozen "may" list (plan, generate code,
  prepare commits, prepare documentation, recommend PR text, recommend
  reviewers) and a frozen "may not" list (merge, self-approve, bypass
  protection, bypass governance, bypass the permission broker, authorize
  execution, authorize itself) — current implementation status "not
  implemented" beyond assistive preparation already broadly practiced.
- **The Approval Model**: an explicit, permanent distinction between **Git
  Approval** (authorizes merging a diff to `main`; grantable today via PR
  review or the Owner's transitional governed push) and **Execution
  Approval** (would authorize a single mediated execution action per
  `docs/V0_2_AUTONOMY_CONTRACT.md`'s lifecycle; not implemented; never
  substitutable for Git approval or vice versa — extends INV-008).
- **PR requirements**: passing validation, healthy governance, clean check,
  clean task memory, clean push readiness, completed review, resolved
  conversations, satisfied branch protection.
- **A governance mapping table** connecting existing `pcae` commands
  (`task new`, `commit implementation`, `health`, `check`, `doctor
  task-memory`, `push check`, `push`, `task finish`, `phase complete`,
  report trust) to the workflow stages and roles that use them.
- **A future-integration design** for the Permission Broker, Human Approval
  Gate, Execution Boundary, Audit Boundary, and Rollback Readiness Boundary
  — how each will eventually attach to this workflow, with no
  implementation performed.
- **A current-status table** marking every future execution/automation
  capability referenced in the document as "Not implemented," while making
  clear that the Git-level workflow itself (roles, flow, branch policy, PR
  requirements, governance mapping) already describes how this repository
  operates today for ordinary governed development.

## Relationship to 107A/107B/107C/107D

107A produced the v0.2 roadmap and execution-capability gap analysis. 107B
froze the autonomy contract (target level, invariants, lifecycle,
components — including a "PR / Branch Protection Workflow" component
explicitly deferred to this phase). 107C froze the 25 execution-readiness
no-go gates built on top of 107B. 107D hardened the validation
infrastructure itself (pytest-xdist compatibility) so that 107C's test
suite, and the suites this phase adds, run reliably in parallel. 107E takes
the next necessary step before any execution implementation begins:
designing and freezing the *Git-level* governed development workflow —
roles, flow, branch policy, PR requirements — and explicitly drawing the
line between that workflow's Git approval and the still-unimplemented
concept of execution approval, so that Phase 108A (Permission Broker
Enforcement Implementation) has an unambiguous, already-frozen boundary to
build against.

## Validation

`tests/test_v0_2_pr_compatible_governed_workflow.py` (new) verifies: the
workflow document and this phase document both exist; all seven repository
roles are defined; the eight-stage development workflow is defined in
order; branch policy (protected main, feature branches, current
transitional posture fields) is defined; the AI participation model's
"may"/"may not" lists are both present; the approval model explicitly
distinguishes Git Approval from Execution Approval; PR requirements are
defined; the governance mapping table exists and references real `pcae`
commands; the future integration section covers all five named future
components; every future capability is marked "Not implemented"; the
document does not claim execution capability, automated PR handling, or
merge automation exist; and the document recommends **108A — Permission
Broker Enforcement Implementation** as the next phase.

All test groups were run with `-n auto`, continuing Phase 107D's hardened
parallel-validation posture. No group required a sequential fallback in
this phase; no new xdist collision was introduced or observed. See the
final phase report for exact pass counts across the focused, documentation/
release, release/lifecycle regression, and fast-green groups.

## No-Go Confirmations

No runtime enforcement. No execution capability. No permission broker
enforcement. No shell mediation. No backend invocation. No adapter
execution. No Telegram inbound. No audit storage implementation. No
rollback execution. No emergency stop implementation. No execution
enablement. No PR automation. No GitHub Actions changes. No GitHub API
integration. No automatic PR creation. No automatic merge. No automatic
approval. No merge queues. No branch creation automation. No no-go gate
runtime enforcement. No commit/push authorization changes beyond the
existing governed lifecycle. No real AI backend calls. `v0.1.0-rc1` remains
non-executing by design. v0.2 remains the autonomy target (Level 3, not
Level 4/5). GitHub Release for `v0.1.0-rc1` and branch protection on `main`
are unchanged. No new tag. No new GitHub Release. No PyPI/GitHub Packages
publication.

## Recommended Next Phase

**108A — Permission Broker Enforcement Implementation.**
