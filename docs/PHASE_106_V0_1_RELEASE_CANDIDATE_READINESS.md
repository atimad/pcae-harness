# Phase 106E — v0.1 Release Candidate Readiness Review

## Purpose

Decide whether PCAE is ready for a v0.1 release candidate tag, by
reviewing release scope, documentation consistency, validation baseline,
and the non-execution boundary as a single point-in-time gate — after
106A (scope freeze), 106B (fast-green triage), 106C (golden workflow),
and 106D (packaging/install smoke test) are all complete.

## Scope

Release-candidate preparation and readiness review only:
`docs/RELEASE_CANDIDATE_V0_1_CHECKLIST.md`,
`docs/RELEASE_NOTES_V0_1_DRAFT.md`, this readiness review, a
release-claim consistency pass over existing docs, a version/tag
readiness assessment, and new tests
(`tests/test_release_candidate_v0_1.py`). No product/runtime behavior is
implemented or changed in this phase.

## Non-Goals

- No runtime enforcement.
- No autonomous execution.
- No real backend invocation.
- No adapter execution.
- No subprocess execution beyond existing lifecycle/test/packaging
  command behavior.
- No shell execution beyond existing lifecycle/test/packaging command
  behavior.
- No network calls outside the existing Telegram outbound notification
  path.
- No shell interception.
- No Telegram inbound or polling.
- No remote shell, `/run`, automatic apply, apply execution, or patch
  parsing.
- No commit/push authorization changes beyond the existing governed
  lifecycle.
- No real AI backend calls.
- No executable artifact-only invocation path.
- No execution enablement flag or toggle.
- No cryptographic signing or remote attestation.
- No database-backed audit storage.
- No shell mediation.
- No rollback execution, file mutation rollback, or automatic restore.
- No git reset/checkout/revert execution.
- **No git tag is created in this phase.**

## Release Evidence From 106A Through 106D

| Phase | Evidence |
|---|---|
| 106A | `docs/RELEASE_SCOPE_V0_1.md` — v0.1 scope frozen in writing: included/excluded capabilities, golden workflow, safety claims, forbidden claims, release blockers, v0.2 boundary. 16 tests. |
| 106B | `docs/PHASE_106_RELEASE_CRITICAL_WARNING_FAST_GREEN_TRIAGE.md` — root-caused and fixed the 3 known fast-green failures (a name collision in `core/backend_invocations.py`, and a test isolation issue). Fast-green: 4390/4390. 22 tests. |
| 106C | `docs/V0_1_GOLDEN_WORKFLOW.md` — concrete, command-verified operator workflow, every command checked against live `--help`. 32 tests. |
| 106D | `docs/PHASE_106_PACKAGING_INSTALLATION_CLEAN_SMOKE_TEST.md`, `docs/V0_1_CLEAN_SMOKE_TEST.md` — editable/non-editable install and sdist/wheel build all verified in throwaway venvs; 2 release-critical packaging defects found and fixed (git-repo crash, sdist scope bloat); fresh-clone golden workflow smoke test passed. 20 tests. |

Cumulative: 90 tests added across 106A–106D specific to release
preparation, on top of the pre-existing fast-green/regression baseline.

## Current Validation Baseline

Captured live during Phase 106E (see "Validation" section of this
phase's completion report for exact commands/output):

| Check | Result |
|---|---|
| Fast-green (`-m fast_green -n auto`) | 4390/4390 — fully green |
| Combined regression | 2220/2220 passed |
| Release/lifecycle regression | 459/459 passed |
| Focused release-candidate tests (106A/106B/106D + new 106E tests) | all passed — see completion report for exact counts |
| `report_notification_tests` | 219/219 passed |
| `bootstrap_session_reporting_tests` | present_in_canonical_metadata |
| `pcae health` | healthy |
| `pcae check` | passed |
| `pcae doctor task-memory` | clean |
| `pcae push check` | clean |
| Telegram runtime | loaded, configured, enabled (outbound only) |

## Install/Build/Smoke Status

Unchanged since 106D, re-confirmed by document review in 106E (no new
install/build run was needed — 106D's evidence stands and no packaging
files were altered except the version-readiness review below):

- Editable install: succeeded.
- Non-editable install: succeeded.
- `python -m build` (sdist + wheel): succeeded, sdist correctly scoped
  (117 files).
- Fresh-clone golden workflow smoke test: succeeded.
- `pcae health`/`pcae check` fail cleanly (not with a crash) outside a
  git repository.

## Docs Alignment Review

Reviewed for release-claim consistency in this phase:

| Document | Finding |
|---|---|
| `README.md` | States PCAE is "not production ready," does not claim to "solve autonomous coding," and describes autonomous execution only as a *future* architecture diagram ("Future Autonomous Flow — target autonomous engineering loop (future state)") and explicitly states "Non-dry-run gate execution is not implemented." No claim of v0.1 autonomous execution found. Headline test/phase counts (7,278 tests / 87 phases) are stale relative to current state — a documentation-currency issue, not a safety-claim violation; retained as a known limitation (see checklist) rather than rewritten in this phase, since correcting it is a content-accuracy pass outside 106E's documentation/review/testing scope and does not affect the non-execution boundary. |
| `docs/RELEASE_SCOPE_V0_1.md` | Consistent: non-executing by design, v0.2 is the autonomy target, forbidden-claims list matches this review's non-goals. Validation baseline table already reflects fast-green 4390/4390, clean task-memory/push-check. |
| `docs/V0_1_GOLDEN_WORKFLOW.md` | Consistent with `docs/RELEASE_SCOPE_V0_1.md`: same command set, same no-execution boundary section, same Telegram outbound-only description. Golden workflow and install docs agree — both point to `docs/V0_1_CLEAN_SMOKE_TEST.md` for install validation. |
| `docs/INSTALLATION.md` | Contains a "v0.1 notes" section (added 106D) pointing to `docs/V0_1_GOLDEN_WORKFLOW.md` and `docs/V0_1_CLEAN_SMOKE_TEST.md`; no separate `docs/INSTALLATION_V0_1.md` file exists — the v0.1-specific content is appended in place, which this review finds sufficient (no fork of the installation doc is warranted). |
| `docs/V0_1_CLEAN_SMOKE_TEST.md` | Consistent: Telegram confirmed optional/skippable, no execution features available, report-trust CLI confirmed present. |

No docs were found to imply v0.1 can execute autonomously. No content
changes to these five documents were required beyond what 106A–106D
already established; this review's job was to confirm consistency, which
it does.

## CLI/Support Status

Unchanged since 106D: the full golden-workflow command set
(`health`/`check`/`doctor task-memory`/`push check`/`phase-report trust`
and `show --trust`/`notify status`/`task new/show/update/finish`/`commit
implementation`/`skill invoke phase-finalization`) is present, documented,
and command-verified. Experimental/internal command families
(`permission-broker`, `shell-gate`, `orchestration`, etc.) remain
evidence-only and outside the v0.1 supported surface, per
`docs/RELEASE_SCOPE_V0_1.md`.

## Safety/No-Go Review

Confirmed via this phase's own governance run and the canonical no-go
confirmation text carried in every recent phase's
`.pcae/phase-completion-metadata.json`/`.pcae/phase-completion-report.md`
(105D through 106D): Telegram outbound-only, execution unavailable, all
authorization flags `False`, all safety flags `True`
(`simulation_only`, `no_execution`, `evidence_only`, `non_authorizing`,
`design_only`). No change to this contract was made or needed in 106E.

## Remaining Risks

1. **README/ROADMAP staleness** — cosmetic/documentation-currency risk,
   not a safety or functional risk; recommended for a future
   documentation-accuracy phase, not a release blocker.
2. **Two overlapping report-trust schemas** (legacy 95M.1,
   105A/105B) — internal complexity, not user-visible; documented across
   105B/105C.1/105D/106A.
3. **Static package version** — acceptable for a first release; a
   future improvement to tie version to tags is out of scope here.
4. **No full test-suite run against a wheel-installed copy** — judged
   low-risk in 106D since wheel contents are identical to the source
   tree's `pcae/` package; not re-validated in 106E (no packaging files
   changed).

None of these are classified as release blockers.

## Go/No-Go Decision

**Ready to tag v0.1.0-rc1 after operator approval.**

Rationale: release scope is frozen and internally consistent (106A);
fast-green is fully green with zero known failures (106B); the golden
workflow is documented, command-verified, and smoke-tested end-to-end
from a fresh clone (106C/106D); packaging/install is validated with all
found defects fixed (106D); documentation reviewed for release-claim
consistency in this phase with no non-execution-boundary violations
found; all governance checks (`health`/`check`/`doctor task-memory`/`push
check`) are green; `report_notification_tests` and
`bootstrap_session_reporting_tests` remain present in canonical metadata;
no remaining item is classified as a release blocker.

## Recommended Next Action

Operator reviews `docs/RELEASE_CANDIDATE_V0_1_CHECKLIST.md`,
`docs/RELEASE_NOTES_V0_1_DRAFT.md`, and this readiness review. If
approved, proceed to **Phase 106F — v0.1 RC Tag / Release Artifact
Finalization**, which creates the approved `v0.1.0-rc1` tag and finalizes
release artifacts. No tag is created in 106E.

**Update (106F):** the operator approved proceeding, and Phase 106F
created and pushed the `v0.1.0-rc1` tag (commit
`d155dddcf56e7ec17ed558f234d6148799192290`). See
`docs/RELEASE_HANDOFF_V0_1_RC1.md` and
`docs/PHASE_106_V0_1_RC_TAG_ARTIFACT_FINALIZATION.md` for the full
tag-creation record. No `v0.1.0` final release tag exists.
