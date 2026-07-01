# Phase 106F — v0.1 RC Tag / Release Artifact Finalization

## Purpose

Perform the tag-readiness verification for PCAE v0.1, create the
operator-approved `v0.1.0-rc1` release candidate tag, and document the
final RC handoff — release artifact finalization only, following the
**GO** decision reached in Phase 106E
(`docs/PHASE_106_V0_1_RELEASE_CANDIDATE_READINESS.md`).

## Scope

Pre-tag hard-gate verification, a rebuild of release artifacts (sdist +
wheel) from the tag-ready state, re-running release-candidate validation,
creating and pushing the `v0.1.0-rc1` annotated tag, documenting the RC
handoff (`docs/RELEASE_HANDOFF_V0_1_RC1.md`), updating existing release
docs to reflect the tag, and new tests
(`tests/test_release_artifact_v0_1_rc1.py`). No product/runtime behavior
is implemented or changed in this phase.

## Non-Goals

No runtime enforcement; no autonomous execution; no real backend
invocation; no adapter execution; no subprocess/shell execution beyond
existing lifecycle/test/packaging/tag-verification command behavior; no
network calls outside the existing Telegram outbound path and the
ordinary git remote operations needed to push the approved tag; no shell
interception; no Telegram inbound/polling; no remote shell; no `/run`; no
automatic apply/apply execution/patch parsing; no commit/push
authorization changes beyond the existing governed lifecycle (except the
approved RC tag push, documented below); no real AI backend calls; no
executable artifact-only invocation path; no execution enablement flag or
toggle; no cryptographic signing (no existing signing convention in this
repository, so none is introduced); no remote attestation; no
database-backed audit storage; no shell mediation; no rollback execution,
file mutation rollback, or automatic restore; no git reset/checkout/revert
execution; **no `v0.1.0` final tag created** — only `v0.1.0-rc1`.

## Operator Approval

Confirmed in this phase's brief: "The operator has approved proceeding
from 106E to 106F," with the recommended tag `v0.1.0-rc1` explicitly
named. This phase proceeds on that basis; no additional approval step was
required or invented.

## Pre-Tag Gate Results

All gates verified **before** tag creation:

| Gate | Result |
|---|---|
| Working tree clean before tag | clean |
| `origin/main..HEAD` = 0 before tag | 0 |
| Active/latest phase report trust complete | `"complete": true` (phase_id `106E`, `pcae phase-report trust --json`) |
| `pcae health` | healthy (idle) |
| `pcae check` | passed |
| `pcae doctor task-memory` | clean |
| `pcae push check` | clean (nothing to push) |
| `fast_green` | 4390/4390 fully green |
| `report_notification_tests` | 219/219 passed |
| `bootstrap_session_reporting_tests` | present_in_canonical_metadata |
| `v0.1.0-rc1` exists locally | no (`git tag --list` empty before this phase) |
| `v0.1.0-rc1` exists on origin | no (`git ls-remote --tags origin` empty before this phase) |
| Release candidate checklist present | `docs/RELEASE_CANDIDATE_V0_1_CHECKLIST.md` (106E) |
| Release notes draft present | `docs/RELEASE_NOTES_V0_1_DRAFT.md` (106E) |
| Readiness review present | `docs/PHASE_106_V0_1_RELEASE_CANDIDATE_READINESS.md` (106E) |
| Docs claim autonomous execution/runtime enforcement/Telegram inbound | none found (confirmed in 106E's docs-alignment review; re-confirmed by this phase's own test suite, `tests/test_release_candidate_v0_1.py`) |

**All gates passed. Tag creation is authorized.**

## Tag Selected

`v0.1.0-rc1` — the only tag created or pushed in this phase.

## Tag Existence Check

`git tag --list | sort` and `git ls-remote --tags origin` were both empty
before this phase (verified above) — no prior `v0.1.0-rc1` or any other
release tag exists locally or on origin.

## Package Version / Tag Relationship

`pyproject.toml` version remains `0.1.0` (unchanged, per 106E's review —
no version bump was needed or performed). The `-rc1` pre-release
qualifier lives entirely in the git tag name (`v0.1.0-rc1`), not in the
static package version field. This is an accepted, documented convention
for this repository (a manual, non-tag-derived version scheme, per
106D/106E) — a future improvement to tie version to tags is out of scope
here.

## Build Artifact Result

Rebuilt from the tag-ready state (commit `176e8e27`, HEAD at the time of
the build) in a throwaway virtual environment, output to a scratch
directory outside the repository (not committed, per project convention —
`dist`/`build`/`*.egg-info` are not tracked and none were left in the
working tree):

- **sdist:** `pcae_harness-0.1.0.tar.gz` (~1.05 MB)
- **wheel:** `pcae_harness-0.1.0-py3-none-any.whl` (~1.11 MB)
- **Build result:** succeeded (`python -m build`, hatchling backend)
- **Post-build smoke check:** wheel installed cleanly into a fresh
  throwaway venv; `pcae --help` resolved; `pip show pcae-harness` reported
  `Version: 0.1.0`.
- **Repo cleanliness after build:** `git status --short` showed no
  `dist/`, `build/`, or `*.egg-info` artifacts — the build output was
  written entirely to a scratch directory outside this repository.

## Validation Baseline

Re-run in this phase, before tagging:

| Check | Result |
|---|---|
| Focused release-candidate/packaging/golden-workflow/scope/triage tests | 109/109 passed |
| Release/lifecycle regression | 421/421 passed |
| Combined regression | 2220/2220 passed |
| Fast-green | 4390/4390 fully green |
| `pcae health` | healthy |
| `pcae check` | passed |
| `pcae doctor task-memory` | clean |
| `pcae push check` | clean |
| Telegram runtime | loaded, configured, enabled (outbound only) |

## Docs Alignment Review

`docs/RELEASE_CANDIDATE_V0_1_CHECKLIST.md`, `docs/RELEASE_NOTES_V0_1_DRAFT.md`,
and `docs/PHASE_106_V0_1_RELEASE_CANDIDATE_READINESS.md` (all from 106E)
already named `v0.1.0-rc1` as the recommended tag and described it as
pending operator approval — no content contradicted this phase's tagging
action. Updated in this phase (see "Docs Updated After Tagging" in
`docs/RELEASE_HANDOFF_V0_1_RC1.md` and this phase's own doc-update
commit) to state the tag has now been created and pushed, with the exact
tagged commit. No document was found to claim autonomous execution,
runtime enforcement, or Telegram inbound for v0.1 — confirmed by this
phase's own test suite as well as 106E's.

## Governed Tag Command Gap

No governed PCAE tag or release command exists in this codebase — verified
via `pcae --help` (no `tag`/`release` subcommand) and a source grep across
`commands/push.py`, `commands/commit.py`, `commands/task.py`, and
`cli.py` (no `tag` handling of any kind). Per this phase's operating
rules, this gap is documented here, and the tag/tag-push operations below
use the explicitly-permitted minimal raw `git tag`/`git push origin
<tag>` path — the only raw git operations performed in this phase, scoped
to exactly one tag.

## Tag Creation Result

```
git tag -a v0.1.0-rc1 -m "PCAE v0.1.0-rc1"
```

- **Result:** created.
- **Tagged commit:** `d155dddcf56e7ec17ed558f234d6148799192290` ("Record
  106F pre-tag finalization progress" — confirmed identical to `HEAD` at
  tag-creation time via `git rev-parse v0.1.0-rc1^{commit}` vs. `git
  rev-parse HEAD`). Tag object hash (annotated tag):
  `b47ce1817a697eab6bee8ef158ba50d96e57c3bb`.
- No other tag was created.

## Tag Push Result

```
git push origin v0.1.0-rc1
```

- **Result:** pushed.
- Verified via `git ls-remote --tags origin v0.1.0-rc1` →
  `b47ce1817a697eab6bee8ef158ba50d96e57c3bb refs/tags/v0.1.0-rc1`
  (present on origin after push, matching the local annotated tag object
  hash) and `git rev-list --count origin/main..HEAD` (`0`, unchanged by a
  tag push — tags do not affect branch ahead/behind counts).
- No branch was pushed with raw git in this phase — the `main` branch was
  pushed exclusively via `pcae push --staged-file-aware` (governed);
  `git push origin v0.1.0-rc1` was used only for the tag itself, per this
  phase's operating rules. No force push was used; no other tag was
  pushed.

## Release Artifact Status

- sdist + wheel: built successfully, smoke-installed successfully, not
  committed to the repository (scratch-directory build, per convention).
- Tag: `v0.1.0-rc1`, created and pushed, pointing at the tag-ready commit.
- Release notes draft, checklist, and readiness review: all present,
  reviewed, and updated to reflect the tag.
- No GitHub Release was created (not requested; out of scope for this
  phase per its operating rules).

## Remaining Risks

Unchanged from 106E's readiness review, plus:

1. Release artifacts (sdist/wheel) are not published anywhere (e.g. PyPI,
   GitHub Release assets) — they exist only as this phase's scratch-built,
   verified-buildable evidence. Publishing distribution artifacts is a
   distinct, not-yet-requested action.
2. No GitHub Release object was created for `v0.1.0-rc1` — the tag exists
   on the git remote, but no release notes are attached to it via the
   GitHub Releases UI/API. This is intentionally out of scope per this
   phase's operating rules ("Do not create a GitHub release unless
   explicitly supported and requested").
3. All risks carried from 106E (README/ROADMAP staleness, dual
   report-trust schemas, static package version, no full test-suite run
   against a wheel-installed copy) remain unchanged and non-blocking.

## Post-Phase Operator Actions

1. Optionally publish `v0.1.0-rc1` as a GitHub Release, attaching
   `docs/RELEASE_NOTES_V0_1_DRAFT.md`'s content (promoted from draft) as
   the release description, and optionally the built sdist/wheel as
   release assets. Not performed in this phase.
2. Optionally publish the built sdist/wheel to a package index (e.g.
   PyPI/TestPyPI). Not performed in this phase.
3. Use the RC for external validation/dogfooding before considering a
   final `v0.1.0` tag. No `v0.1.0` tag exists or was created in this
   phase.

## Recommended Next Phase

107A — v0.2 Full Autonomy Roadmap / Execution Capability Gap Analysis.
