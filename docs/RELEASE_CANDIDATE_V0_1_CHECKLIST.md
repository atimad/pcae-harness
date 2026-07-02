# PCAE v0.1 — Release Candidate Checklist

## Release Candidate Name

**PCAE v0.1 — Governed AI Coding Lifecycle Harness (Release Candidate)**

## Release Candidate Target

`v0.1.0-rc1` (recommended tag; see "Tag Readiness" below). Prepared in
Phase 106E. Tag creation itself is deferred to Phase 106F, after explicit
operator approval — this phase does not create a tag.

## Release Scope Confirmation

Confirmed against `docs/RELEASE_SCOPE_V0_1.md` (106A, frozen): PCAE v0.1 is
non-executing by design — a governed AI coding lifecycle harness. It governs task
scope, commit/push sequencing, and phase-completion report trust for a
human-driven AI coding workflow. It does not execute code, invoke a real AI
backend, mediate a shell, or perform rollback execution. No scope changes
were introduced in 106B, 106C, 106D, or 106E — this phase is
documentation/review/testing only.

## Non-Execution Boundary Confirmation

Confirmed unchanged through 106E:

- No runtime enforcement (permission broker / shell gate remain
  evidence-only classification prototypes; every `*_performed` flag is
  `False`).
- No autonomous execution — no code path runs agent-authored code or
  shell commands without a human driving the CLI.
- No real AI backend invocation.
- No adapter execution.
- Telegram is outbound-only (`sendMessage`/`sendDocument`); no inbound
  handler exists anywhere in `core/notifications.py`.
- All 12 authorization flags remain `False`; all 5 safety flags
  (`simulation_only`, `no_execution`, `evidence_only`, `non_authorizing`,
  `design_only`) remain `True` across the evidence/decision/coordinator
  layers (Phase 104C contract, unchanged).

## Included Capabilities

Unchanged from `docs/RELEASE_SCOPE_V0_1.md`'s "Included v0.1 Capabilities"
list: governed task/phase lifecycle, task contracts with allowed
files/zones, governed commit/push workflow, phase report trust validator
(105A), report-trust CLI (105B), hard-fail trust gates (105D),
task-finish report/notification integration (105C/105C.1), phase report
canonical metadata, canonical no-go registry, shared safety/authorization
contract, Telegram outbound notifications, `health`/`check`/`doctor
task-memory`/`push check`, evidence-only runtime-readiness artifacts,
explicit no-execution posture, fast-green baseline tracking,
`report_notification_tests`/`bootstrap_session_reporting_tests` schema
fields.

## Excluded Capabilities

Unchanged from `docs/RELEASE_SCOPE_V0_1.md`'s "Excluded v0.1 Capabilities"
list: autonomous execution, runtime enforcement, real backend invocation,
adapter execution, shell/subprocess/network mediation beyond existing
lifecycle/test plumbing, shell interception, Telegram inbound/polling/
remote shell/`/run`, automatic apply/patch parsing, rollback execution,
commit/push authorization changes beyond the existing governed lifecycle,
execution enablement flag/toggle, cryptographic signing, remote
attestation, database-backed audit storage, production multi-agent
autonomous orchestration.

## Supported Golden Workflow

Documented and command-verified in `docs/V0_1_GOLDEN_WORKFLOW.md` (106C):
start-of-phase checks → task/phase setup → implementation → pre-
finalization → finalization (report/notify/commit/push) → post-completion
verification. Smoke-tested end-to-end from a genuinely fresh `git clone`
in Phase 106D (`docs/PHASE_106_PACKAGING_INSTALLATION_CLEAN_SMOKE_TEST.md`,
`docs/V0_1_CLEAN_SMOKE_TEST.md`). No divergence found between the
documented workflow and the fresh-clone smoke test.

## Installation / Packaging Status

- Editable install (`pip install -e .`): **succeeded** (106D).
- Non-editable local install (`pip install .`): **succeeded** (106D).
- `python -m build` (sdist + wheel): **succeeded** (106D).
- Two release-critical packaging defects found and fixed in 106D:
  `pcae health`/`pcae check` no longer crash with a raw traceback outside
  a git repository (clean one-line error instead); sdist no longer sweeps
  in local `.claude`/`.pcae` state (scoped via explicit
  `[tool.hatch.build.targets.sdist]` include list, 117 files vs. the prior
  44,399).
- No remaining packaging blockers.

## Test Baseline

| Check | Result |
|---|---|
| Fast-green (`-m fast_green -n auto`) | **4390/4390 — fully green, no known failures** |
| Combined regression (preflight/artifact/trust/contract/readiness/boundary/attempt/no_go/runtime_enforcement/evidence_bundle/decision/coordinator) | 2220/2220 passed |
| Release/lifecycle regression | 459/459 passed |
| `report_notification_tests` | 219/219 passed |
| `bootstrap_session_reporting_tests` | present_in_canonical_metadata |
| Packaging/installation smoke tests | 20/20 passed |
| Focused golden workflow tests | 80/80 passed |
| Release scope tests (106A) | 16/16 passed |
| Release critical triage tests (106B) | 20/20 passed |

## Governance Baseline

| Check | Result |
|---|---|
| `pcae health` | healthy |
| `pcae check` | passed |
| `pcae doctor task-memory` | clean |
| `pcae push check` | clean |

Task-memory is clean and push-check is clean as of this phase's own
validation run (see `docs/PHASE_106_V0_1_RELEASE_CANDIDATE_READINESS.md`
for the exact commands and outputs captured during 106E).

## Notification / Reporting Baseline

- Telegram runtime: loaded, configured, enabled (outbound only).
- `pcae task finish --commit` finalizes and trust-validates the phase
  report, dispatching Telegram only when the report is push-state
  complete (105C.1/105D) — never a partial/pre-final report.
- `pcae phase complete` hard-fails by default on an incomplete/invalid
  report (105D); `--allow-partial-report` is the explicit, logged
  override.
- `.pcae/phase-reports/.last-notified.json` prevents duplicate sends.

## Known Limitations

- `README.md` test-count/phase-count figures were brought current in
  Phase 106J (now cites `v0.1.0-rc1` and the current test count);
  `docs/ROADMAP.md` remains a lower-priority internal planning artifact.
- Two independent, overlapping report-trust schemas exist in this
  codebase (the pre-existing 95M.1 `assess_completeness()` schema and the
  105A/105B `validate_phase_report_trust()` schema) — their combination
  logic is now shared between `task finish --commit` and `phase complete`
  (Phase 106H), but the schemas themselves are not fully unified.
- A trust-gate asymmetry between `task finish --commit` and `phase
  complete` was found post-tag by Phase 106G's audit and repaired in
  Phase 106H, then re-verified via live CLI in Phase 106I — see
  `docs/PHASE_106_RC_AUDIT_FINDINGS_REPAIR.md` and
  `docs/PHASE_106_RC_END_TO_END_VERIFICATION_FULL_PHASE_CHECK.md`.
- `pcae push check`'s phase-report-trust gate deliberately checks report
  *content* completeness only, not push-state fields (105D design
  decision, to avoid deadlocking the normal task-finish-then-push
  sequence).
- Package version is static (`0.1.0` in `pyproject.toml`), not derived
  from git tags — acceptable for a first release, a manual process for
  future ones.
- This phase (and 106D) validated install/build mechanics and CLI
  availability; it did not re-run the full test suite against a
  wheel-installed copy end-to-end (the test suite runs against the source
  checkout via `pythonpath = ["src"]`). Judged low-risk since the wheel's
  package contents are identical to the source tree's `pcae/` package.

## Release Blockers

**None identified.** All items previously tracked as "must document before
v0.1" in `docs/RELEASE_SCOPE_V0_1.md` (install/packaging validation,
golden workflow smoke test, README/ROADMAP staleness review, tag/release
notes) are now addressed as of 106D/106E, or explicitly documented as
accepted known limitations above (none blocking).

## Tag Readiness

- Current `pyproject.toml` version: `0.1.0`.
- Recommended tag: **`v0.1.0-rc1`** (semantic-versioning pre-release
  style; see `docs/PHASE_106_V0_1_RELEASE_CANDIDATE_READINESS.md`
  "Version/Tag Readiness" section for the full rationale).
- No version bump is required before tagging — `0.1.0` is the correct
  base version for a `v0.1.0-rc1` pre-release tag; the `-rc1` suffix lives
  in the tag name, not in `pyproject.toml`'s static version field.
- **Tag created and pushed in Phase 106F.** `v0.1.0-rc1` now exists
  locally and on `origin`, pointing at commit
  `d155dddcf56e7ec17ed558f234d6148799192290`. See
  `docs/RELEASE_HANDOFF_V0_1_RC1.md` and
  `docs/PHASE_106_V0_1_RC_TAG_ARTIFACT_FINALIZATION.md` for full detail.

## Post-Phase Manual Tag Instructions (Completed in 106F)

Phase 106F, after operator approval, completed the following:

1. Confirmed `origin/main..HEAD` was `0` (nothing unpushed) before
   tagging.
2. Created an annotated tag: `git tag -a v0.1.0-rc1 -m "PCAE v0.1.0-rc1"`.
3. Pushed the tag: `git push origin v0.1.0-rc1`.
4. Did **not** publish a GitHub Release or promote the release notes
   draft — that remains an optional operator action (see
   `docs/RELEASE_HANDOFF_V0_1_RC1.md`'s "What to Do Next").

No `v0.1.0` final release tag exists or was created.

## v0.2 Autonomy Boundary

v0.2 remains the autonomy target and is explicitly out of scope for this
release candidate: runtime enforcement, governed real backend invocation,
adapter execution, human-approval-enforced execution, durable audit
persistence, and rollback execution governance are all future-phase work,
not part of v0.1. See `docs/RELEASE_SCOPE_V0_1.md`'s "v0.2 Full-Autonomy
Roadmap Boundary" section (unchanged in 106E).

## Final Go/No-Go Status

**GO — tagged.** `v0.1.0-rc1` was created and pushed in Phase 106F after
operator approval. See
`docs/PHASE_106_V0_1_RELEASE_CANDIDATE_READINESS.md` for the readiness
review and `docs/PHASE_106_V0_1_RC_TAG_ARTIFACT_FINALIZATION.md` for the
tag-creation record.
