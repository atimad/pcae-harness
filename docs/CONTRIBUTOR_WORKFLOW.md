# PCAE Contributor Workflow — Branch Protection Edition

This document is the explicit, checklist-style companion to
`CONTRIBUTING.md`, reflecting the repository state established in Phase
106M (`docs/PHASE_106_REPOSITORY_CONTRIBUTION_SAFETY_BRANCH_PROTECTION.md`).
If anything here conflicts with `CONTRIBUTING.md`, this document is the
more specific, more current source for the branch-protection-era
workflow.

## 1. Branch Protection Is Active on `main`

- **No direct pushes to `main`.** `main` is a GitHub-protected branch.
  Use a feature branch and open a pull request.
- **Use branches and pull requests.** Create a branch, commit your work,
  push the branch, and open a PR against `main`.
- **Pull request reviews are required** — at least one approving review
  before merge. Stale approvals are dismissed automatically when new
  commits are pushed.
- **Review conversations must be resolved** before a PR can merge.
- **Force pushes to `main` are blocked.** Never force-push a protected
  branch. Force-pushing your own feature branch before opening a PR is
  fine.
- **Branch deletion of `main` is blocked.**
- Repository administrators are currently exempt from these rules
  (`enforce_admins: false`) during this transitional period — this does
  not change what is expected of external contributors.

## 2. Run PCAE Checks Before Opening a PR

```bash
pcae health
pcae check
pcae doctor task-memory
pcae push check
python -m pytest -n auto        # or focused suites for the area you changed
```

All of these should be clean/passing before you open a pull request. If
`pcae check` reports scope or zone violations, either narrow your change
or update your task contract's allowed files/zones to match what you
actually touched.

## 3. Never Use `--no-verify` or Force Push to Protected Branches

- Do not pass `--no-verify` to any git operation.
- Do not force-push `main` (GitHub will reject it anyway once branch
  protection is active; do not attempt to work around this).
- Do not use raw `git commit` / `git push` in place of the governed PCAE
  commands (`pcae commit implementation`, `pcae task finish --commit`,
  `pcae push`) for changes inside this repository's own governed
  lifecycle.

## 4. Runtime/Autonomy Boundary Changes Require Explicit Maintainer Approval

PCAE v0.1.0-rc1 is **non-executing by design**. Do not add, in a normal
contribution:

- Runtime enforcement or autonomous execution.
- Real AI backend invocation or adapter execution.
- Telegram inbound handling, polling, or remote command reception
  (Telegram remains outbound-only).
- Shell mediation, shell interception, or remote shell execution.
- An execution enablement flag, execution availability toggle, or any
  other mechanism that would let PCAE cross from evidence-only to
  actually executing code or commands.

Any change that touches these boundaries requires a dedicated phase and
explicit maintainer approval — it is not something a routine PR should
introduce incidentally. v0.2 is the target release for governed autonomy;
none of it exists in v0.1.

## 5. Keep Article/Source-Packet Material Out of the Repository

- Do not commit LinkedIn articles, blog drafts, or other narrative/
  marketing source material to tracked paths.
- `.pcae-local/` is the ignored, local-only location for this kind of
  scratch material (see
  `docs/PHASE_106_PUBLIC_NARRATIVE_ARTIFACT_HYGIENE_REPAIR.md`) and
  **must remain ignored** — do not remove it from `.gitignore` and do
  not commit its contents.

## 6. Release/Publication State (Do Not Assume Otherwise)

- A GitHub Release for `v0.1.0-rc1` **exists**, marked prerelease, with
  the sdist and wheel attached
  (https://github.com/atimad/pcae-harness/releases/tag/v0.1.0-rc1).
- **PyPI is not used yet.** Do not assume `pip install pcae-harness`
  installs from an index — it does not.
- **GitHub Packages is not used yet.**
- Do not create a new tag, a final `v0.1.0` tag, or a new GitHub Release
  as a side effect of an unrelated contribution.

## 7. Pull Request Checklist

Before requesting review, confirm:

- [ ] `pcae health`, `pcae check`, `pcae doctor task-memory`, `pcae push
      check` all pass.
- [ ] Relevant `pytest` suites pass for the area you changed.
- [ ] Documentation updated for any behavior-visible change (see
      `CONTRIBUTING.md` Section 6).
- [ ] `CHANGELOG.md` has a new entry.
- [ ] The PR description answers every question in
      `.github/pull_request_template.md`.
- [ ] No execution/autonomy boundary was crossed without a dedicated
      phase and maintainer approval.
- [ ] No article/source-packet material was committed; `.pcae-local/`
      remains ignored.

## 8. See Also

- `CONTRIBUTING.md` — full contribution workflow and governance
  requirements.
- `docs/V0_1_GOLDEN_WORKFLOW.md` — the governed PCAE command sequence
  for a phase, start to finish.
- `docs/PHASE_106_REPOSITORY_CONTRIBUTION_SAFETY_BRANCH_PROTECTION.md` —
  the full record of this repository's branch protection state, threat
  model, and residual risks.
