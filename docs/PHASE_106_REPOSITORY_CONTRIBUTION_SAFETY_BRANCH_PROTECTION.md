# Phase 106M — Repository Contribution Safety / Branch Protection Readiness

## Purpose

Reduce the risk that `main` can be ruined by an accidental or unauthorized
direct push, force push, or branch deletion, and establish a PR-first
contribution workflow — by applying GitHub-level repository authority
controls (branch protection) that sit outside and above PCAE's own
internal governance.

## Scope

Applying (and documenting) GitHub branch protection for `main`; creating
contributor-facing documentation (`CONTRIBUTING.md` updates,
`docs/CONTRIBUTOR_WORKFLOW.md`); adding a pull request template
(`.github/pull_request_template.md`) and a minimal `CODEOWNERS` file;
documenting how the existing PCAE governed lifecycle (`pcae commit`,
`pcae task finish`, `pcae push`) continues to operate once branch
protection is active. New tests
(`tests/test_repository_contribution_safety_branch_protection.py`). No
product/runtime behavior is implemented or changed in this phase.

## Non-Goals

No runtime enforcement; no autonomous execution; no real backend
invocation; no adapter execution; no subprocess/shell execution beyond
existing lifecycle/test/docs/GitHub-protection command behavior; no
network calls outside the existing Telegram outbound path, ordinary git
remote verification, and the explicit GitHub branch-protection API calls
performed in this phase; no shell interception; no Telegram inbound/
polling; no remote shell; no `/run`; no automatic apply/apply execution/
patch parsing; no commit/push authorization changes beyond documenting
the PR-protected workflow and applying GitHub branch protection itself;
no real AI backend calls; no executable artifact-only invocation path; no
execution enablement flag or toggle; no cryptographic signing; no remote
attestation; no database-backed audit storage; no shell mediation; no
rollback execution, file mutation rollback, or automatic restore; no git
reset/checkout/revert execution. **No new git tag was created.** No
final `v0.1.0` tag. No new GitHub Release. No PyPI publication. No
GitHub Packages publication. No v0.2 work started.

## Current Repo Safety State (Before This Phase)

- Repository visibility: **public** (`atimad/pcae-harness`).
- Branch protection on `main`: **none** — `gh api
  repos/atimad/pcae-harness/branches/main/protection` returned `404
  Branch not protected` before this phase.
- Ruleset check: `gh ruleset check main` returned "0 rules apply to
  branch main" before this phase.
- Any collaborator with push access (or the repo owner via direct `git
  push`) could push directly to `main`, force-push, or delete the
  branch, with no GitHub-level guard rail — only PCAE's own internal
  advisory governance (task scope, health/check) stood between an
  in-repo agent and a direct write to `main`. PCAE governance does not
  operate at the GitHub repository-authority layer at all; it has no
  ability to prevent a `git push --force` run outside its own governed
  commands.
- An existing CI workflow, `.github/workflows/pcae-governance.yml`
  ("PCAE Governance"), already runs `pcae health --json`, `pcae check
  --json`, and `pcae analytics risk --json` on every `pull_request` and
  every `push` to `main`. It has run successfully on every push across
  this project's recent phase history (confirmed via `gh run list
  --workflow=pcae-governance.yml`) — a real, stable, existing check
  named `governance` (confirmed via `gh api
  repos/atimad/pcae-harness/commits/HEAD/check-runs`), not yet enforced
  as a required status check.

## GitHub Release State Inherited From 106L

- `v0.1.0-rc1` tag: exists locally and on origin (unchanged by this
  phase).
- GitHub Release for `v0.1.0-rc1`: published, marked **prerelease**,
  with `pcae_harness-0.1.0.tar.gz` and `pcae_harness-0.1.0-py3-none-any.whl`
  attached (checksums previously verified in 106L). Unchanged by this
  phase — no new release was created, and the existing release was not
  modified.
- No PyPI publication. No GitHub Packages publication. No final `v0.1.0`
  tag.
- `.pcae-local/` remains ignored (unchanged by this phase); no LinkedIn
  article or source-packet material was committed.

## Why PCAE Internal Governance Is Not Enough By Itself

PCAE's task/phase governance (`pcae check`, `pcae health`, task-contract
scope enforcement) is **advisory infrastructure that only applies when
someone chooses to go through the governed PCAE commands** (`pcae commit
implementation`, `pcae task finish --commit`, `pcae push`). Nothing in
PCAE itself prevents:

- A raw `git push origin main` (bypassing every PCAE check entirely).
- A raw `git push --force origin main` (rewriting or destroying history).
- Deleting the `main` branch outright (`git push origin --delete main`).
- Merging a pull request without any human review, if the repository has
  no GitHub-level review requirement.
- An external contributor with write access pushing directly to `main`
  without ever running `pcae check`.

These are **repository-authority** concerns that live at the GitHub
platform layer, not the application layer PCAE governs. GitHub branch
protection is the correct, standard control for this — it enforces rules
at the git-server level, before PCAE (or any other in-repo tooling) ever
runs. PCAE protects the *workflow* an agent follows once it is already
working in the repo; GitHub branch protection protects the *repository
itself* from writes that don't go through that workflow at all.

## Threat Model for Contributors

| Threat | Without branch protection | With this phase's protection |
|---|---|---|
| Accidental `git push` to `main` from a feature branch | Succeeds silently | Blocked — must open a PR |
| Force-push rewriting `main` history | Succeeds silently | Blocked (`allow_force_pushes: false`) |
| Deleting `main` | Succeeds (if permissions allow) | Blocked (`allow_deletions: false`) |
| Merging an unreviewed change | Allowed | Requires 1 approving review |
| Stale approval surviving further pushes | Approval stays valid after new commits | Dismissed automatically (`dismiss_stale_reviews: true`) |
| Unresolved review conversations at merge | Allowed | Blocked (`required_conversation_resolution: true`) |
| Repo owner/admin bypassing protection during this transitional period | N/A | Still possible (`enforce_admins: false`, intentional — see below) |
| Malicious/broken CI-required merge | N/A (no required checks existed) | Not yet enforced — no stable required status check is configured yet (see CI/status-check readiness below) |

## Recommended GitHub Branch Protection

Per this phase's operating rules, transitional protection was applied
first (not the strictest possible configuration):

- Require pull request reviews before merging (1 approval).
- Dismiss stale approvals when new commits are pushed.
- Do not require code-owner reviews yet (no team structure beyond a
  single maintainer).
- Do not require "last push approval" yet (single-maintainer repo; would
  make solo-maintainer merges impossible without a second approver).
- Block force pushes.
- Block branch deletion.
- Require conversation resolution before merging.
- Do not enforce against admins yet (transitional — see below).
- Do not require status checks yet (no stable, intentionally-required
  check has been established as a merge gate; see CI/status-check
  readiness below).

## Actual Branch Protection Before/After State

**Before this phase:**

```
$ gh api repos/atimad/pcae-harness/branches/main/protection
{"message":"Branch not protected","documentation_url":"...","status":"404"}

$ gh ruleset check main
0 rules apply to branch main in repo atimad/pcae-harness
```

**Applied in this phase** (via `gh api --method PUT
repos/atimad/pcae-harness/branches/main/protection --input
<payload.json>`, payload below):

```json
{
  "required_status_checks": null,
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "require_last_push_approval": false
  },
  "restrictions": null,
  "required_linear_history": false,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_conversation_resolution": true,
  "lock_branch": false,
  "allow_fork_syncing": true
}
```

**After this phase** — verified via `gh api
repos/atimad/pcae-harness/branches/main/protection`:

| Setting | Applied value |
|---|---|
| `required_pull_request_reviews.required_approving_review_count` | `1` |
| `required_pull_request_reviews.dismiss_stale_reviews` | `true` |
| `required_pull_request_reviews.require_code_owner_reviews` | `false` |
| `required_pull_request_reviews.require_last_push_approval` | `false` |
| `enforce_admins.enabled` | `false` |
| `required_linear_history.enabled` | `false` |
| `allow_force_pushes.enabled` | `false` |
| `allow_deletions.enabled` | `false` |
| `block_creations.enabled` | `false` |
| `required_conversation_resolution.enabled` | `true` |
| `lock_branch.enabled` | `false` |
| `allow_fork_syncing.enabled` | `false` (GitHub returned `false` despite the requested `true`; this field only affects forks pulling from this upstream and does not weaken protection on `main` itself — noted as a minor, non-security deviation) |
| `required_status_checks` | not present in the response (null/unset — no status checks required yet) |
| `required_signatures.enabled` | `false` (not requested; GitHub default) |

**Result: branch protection was successfully applied, not merely
documented.**

## Admin Enforcement Mode

`enforce_admins` is `false` — repository administrators (currently only
the repo owner, `atimad`) are **exempt** from these protection rules
during this transitional period, per this phase's explicit operating
instruction ("do not enforce against admins yet unless operator
explicitly approves strict mode"). Practical consequence: the existing
governed PCAE workflow (`pcae push --staged-file-aware`, run by the
repo-owning operator) continues to push directly to `main` exactly as it
has in every prior phase — this phase does not break that workflow.
External, non-admin contributors are subject to the full protection
(PR + 1 review + no force-push + no deletion + conversation resolution).
Enabling `enforce_admins: true` (strict mode) is a distinct, future,
explicitly-operator-approved decision — not performed here.

## PR-First Workflow Impact

- Any contributor without admin/owner status must now open a pull
  request and obtain at least one approving review to merge into `main`.
  Direct pushes and force-pushes from non-admins to `main` are rejected
  by GitHub itself.
- Pull requests must have all review conversations marked resolved
  before merge.
- Stale approvals (an approval given before new commits were pushed) are
  automatically dismissed, so a review always reflects the latest diff.
- The repo owner (admin) is not yet blocked by these rules — this is
  intentional transitional behavior, not a bug.

## PCAE Workflow Changes After Branch Protection

**None of the governed PCAE lifecycle commands change.** `pcae task new`,
`pcae commit implementation`, `pcae task finish --commit`, `pcae push`,
`pcae phase complete`, and `pcae skill invoke phase-finalization` all
continue to operate exactly as documented in
`docs/V0_1_GOLDEN_WORKFLOW.md`. For the repo-owning operator (an admin,
exempt under `enforce_admins: false`), `pcae push` continues to push
directly to `main` as before. For an external contributor without admin
status, the same governed commands still apply *locally* (running
`pcae health`/`pcae check`/tests before committing), but the final
"submit" step changes from "push directly" to "push to a feature branch,
then open a pull request" — this is now documented explicitly in
`docs/CONTRIBUTOR_WORKFLOW.md` and the updated `CONTRIBUTING.md`.

## CI/Status-Check Readiness

`.github/workflows/pcae-governance.yml` ("PCAE Governance") already runs
on every `pull_request` and every `push` to `main`, executing `pcae
health --json`, `pcae check --json`, and `pcae analytics risk --json`.
It has completed successfully on every one of the last 10+ pushes to
`main` (verified via `gh run list --workflow=pcae-governance.yml`), and
its check-run name is confirmed as `governance` (verified via `gh api
repos/atimad/pcae-harness/commits/HEAD/check-runs`).

**This is a real, stable candidate required status check** — but it was
**not** added to `required_status_checks` in this phase, per the
explicit operating instruction to leave `required_status_checks: null`
and document candidates rather than invent or immediately enforce new
required checks. Recommendation for a future phase: once there is
confidence the `governance` check is stable across PR-triggered runs
(not just direct pushes to `main`), add it as a required status check
via a follow-up `gh api` call updating
`required_status_checks.contexts` to include `"governance"`.

## Contributor Documentation Updates

- `CONTRIBUTING.md`: added a "Branch Protection & Pull Request Workflow"
  section (Section 3, before the existing contribution-workflow steps)
  stating no direct pushes to `main`, no force pushes, no `--no-verify`,
  and pointing to `docs/CONTRIBUTOR_WORKFLOW.md` for the full checklist.
- `docs/CONTRIBUTOR_WORKFLOW.md` (new): the complete, explicit
  contributor checklist — branch protection state, required PCAE
  commands before opening a PR, the PR-first workflow, the non-executing
  v0.1 boundary, the article/source-packet exclusion, and PyPI/GitHub
  Packages status.
- `.github/pull_request_template.md` (new): a PR template asking about
  task/phase scope, files changed/not changed, tests run, `pcae
  check`/`pcae push check` results, and whether the change touches
  execution/autonomy boundaries or any of the no-go domains.
- `.github/CODEOWNERS` (new): minimal, `@atimad` as owner of the entire
  repository (`*`).

## Residual Risks

1. `enforce_admins: false` means the repo owner/admin can still bypass
   all of these protections via direct push — intentional for this
   transitional phase, but a residual risk until (and unless) strict
   mode is explicitly approved.
2. No required status checks are configured yet, so a PR can be merged
   even if the existing `governance` CI check is failing on that PR
   (GitHub will show the check result, but won't block the merge on it).
3. `require_code_owner_reviews` is `false` — the `CODEOWNERS` file
   documents ownership but does not yet gate merges on owner review.
4. Branch protection is currently scoped to `main` only; no rulesets or
   protection exist for tags (e.g. protecting `v0.1.0-rc1` and future
   release tags from deletion/overwrite) — out of scope for this phase.
5. `allow_fork_syncing` was requested as `true` but GitHub returned
   `false`; this is a fork-sync convenience setting, not a protection
   weakening, and does not require follow-up for security purposes.

## Recommended Next Step

107A — v0.2 Full Autonomy Roadmap / Execution Capability Gap Analysis
(roadmap/gap analysis only, not implementation).
