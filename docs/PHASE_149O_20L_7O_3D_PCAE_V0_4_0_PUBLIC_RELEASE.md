# Phase 149O.20L.7O.3D — PCAE v0.4.0 Public Release

## 1. Objective

Publish PCAE v0.4.0 from the exact frozen release candidate prepared and
verified at Phase 149O.20L.7O.3C.4, under explicit human publication
authorization, without engineering any product changes in this phase.

## 2. Human publication authorization

Explicit authorization for **PCAE v0.4.0** publication was given by the
user in the active session via an explicit yes/no prompt ("Yes, publish
v0.4.0"), relayed to the executing agent by the session coordinator.
Prior v0.3.1 authorization did not carry forward and was not relied upon.
The phase halted at the Section 27 checkpoint (`PUBLICATION READY /
HUMAN PUBLICATION AUTHORIZATION: REQUIRED`) until this authorization was
received.

## 3. Release candidate identity

- `release_candidate_commit` = `ea3f731ef50ea16985fd4a0562f0c091bb8109b2`
  (the Phase 3C.4 phase-owning commit; confirmed via `pcae phase-report
  show --latest` and `git log`).
- `tagged_commit` = `ea3f731ef50ea16985fd4a0562f0c091bb8109b2` (verified
  identical before push — see §7).
- 3D lifecycle/reporting commits are later, additive-only commits on top
  (this document, task lifecycle, `.pcae/` metadata, `PROJECT_STATUS.md`
  / `CHANGELOG.md`) — none touch `src/pcae/**` or `pyproject.toml`.

## 4. Pre-publication verification (Sections 1–26)

Full independent verification pass performed before authorization was
requested:

- Baseline: working tree clean, `HEAD == origin/main`,
  `origin/main..HEAD = 0`, `v0.3.1` unchanged at
  `5d7edef9c34ee266a9c5b51940ee4f1848375d22`, no local/remote `v0.4.0`
  tag existed yet. `pcae health`/`check`/`status coherence` clean;
  `pcae doctor task-memory` showed only pre-existing `tasks/DONE.md`
  backfill warnings (accepted debt, unrelated); `pcae push check` =
  `nothing_to_push`; `pcae runtime inspect` = `Observed / observe /
  unavailable`.
- Candidate integrity: `git diff
  ea3f731ef50ea16985fd4a0562f0c091bb8109b2..HEAD` touched only
  `.pcae/phase-completion-{metadata.json,report.md}`, `CHANGELOG.md`,
  `tasks/DONE.md`, and task-lifecycle files — zero drift in `src/pcae`
  or `pyproject.toml`.
- Version: confirmed `0.4.0` in both `pyproject.toml` and
  `src/pcae/__init__.py`.
- v0.3.1 isolation: GitHub Release `v0.3.1` confirmed not draft, not
  prerelease, `publishedAt` predates this session; tag unchanged.
- **Fast Green count investigation (Section 5) — see §5 below for full
  finding.**
- Build provenance: `[build-system].requires = ["hatchling==1.32.0"]`;
  `[tool.hatch.build.targets.sdist].include` root-anchored (`/src/pcae`,
  `/README.md`, `/LICENSE`, `/pyproject.toml`) — both confirmed by direct
  inspection of `pyproject.toml`, not by trusting the 3C.4 summary.
- Artifact recovery: no frozen 3C.4 artifacts survived on disk; performed
  an independent clean-clone rebuild pinned to the candidate commit.
  Resulting hashes matched the canonical 3C.4 record exactly (see §6).
- Contamination: wheel and sdist inspected; no `.git`, no
  `.claude/worktrees`, no secrets/`.env`/credentials/caches. Apparent
  "credential" grep hits were legitimate product source files
  (`hatp_hardware_credential_admin.py`, `hatp_hardware_credentials.py`);
  the only non-source sdist addition was a harmless `.gitignore`.
- Wheel/sdist smoke: fresh disposable venvs, both installed cleanly, both
  report version `0.4.0`, no editable source dependency, CLI functional,
  golden path (`init` → `session bootstrap` → `task new` → `intake
  from-files` → `intake list`) exercised successfully.
- Installed Plan B+ / corrupt-store / Permission Broker behavior: the
  3C.3 and 3C.3.2 independent-verification test files (51 tests total,
  which exercise `auto_publish_confirmed_session`,
  `publish_with_permission_gate`, `mutation_permission.
  evaluate_publication_permission`, and the corrupt-store fail-closed
  path directly and for real) were copied and run against the installed
  wheel's `site-packages` import (not the source checkout). Result: 43
  passed, 8 failed. All 8 failures are AST/source-scan tests that
  `read_text()` a `src/pcae/...` path relative to a repo checkout — they
  are structurally inapplicable when only the wheel is installed with no
  repo tree present, not behavioral regressions. All 43 real behavioral
  tests (including the corrupt-store fail-closed case, the historical
  BLOCKING-defect regression test, and the permission-gate no-bypass
  test) passed.
- Repository Intelligence / runtime / authority: `pcae
  repository-intelligence --help`, `pcae runtime inspect`, `pcae
  authority inspect <path>` all functional from the installed wheel;
  runtime remained `Observed / observe / unavailable`; authority inspect
  returned an explicit non-authoritative disclosure and did not execute
  or cut over anything.
- Release notes: `docs/RELEASE_NOTES_V0_4_0.md` read in full and checked
  against source evidence and the Section 24 semantic-wall list (`auto
  routing != auto approval`, `human confirmation != permission`, `CHGR !=
  general authorization`, `Permission Broker ALLOW != execution
  capability`, `publication ownership != arbitrary execution`,
  `Observed != executable`) — all present verbatim in the notes. No
  substantive false claim found; no edit made to product-facing release
  docs during this phase.
- Final source-tree sanity: clean, `HEAD == origin/main`, candidate diff
  to `src/pcae`/`pyproject.toml` still empty.

**BLOCKING = 0, MUST-FIX = 0** at the authorization checkpoint.

## 5. Fast Green count discrepancy — resolved

The 3C.4 report's prose ("344 HATP/HMIC/Class-B/HBDC-bound-contract-
identity + 2 packaging-related + 1 head-equals-origin-main = 347") did
not match its own stated total of **345** deselected nodeids, and its
categorization understated the true breadth of the deselected set.

Independent investigation: `pytest -m fast_green -q -n auto` was run
twice, in full, at the current `HEAD` (== candidate state for
`src/pcae`/`pyproject.toml`, per the empty diff in §4). Results: **335
failed / 8692 passed / 5 skipped / 9 errors** (run 1) and **336 failed /
8691 passed / 5 skipped / 9 errors** (run 2) — a ±1 flake between runs,
consistent with the project's own previously-documented
`test_head_equals_origin_main`-style timing sensitivity
(`docs/FINDING_BOOTSTRAP_READINESS_STALE_TASK_SELF_COMPARISON.md`).

Full FAILED/ERROR nodeid lists were captured and categorized directly
(not from prose). The actual composition is broader than the 3C.4
report stated: alongside the HATP/HMIC/Class-B/HBDC-bound-contract-
identity cluster (295 of 344 nodeids in the 336-failure run) and the
CHGR/packaging count-drift tests (3 nodeids), there is a substantial
additional cluster (~46 nodeids) of self-referential "no authority-
bearing drift since *this historical phase's own* candidate SHA" tests
spanning many unrelated legacy phases —
`test_phase_149o_20l_7h_deploymentbinding_producer_contract_*`,
`test_phase_149o_20l_7n_*_dell_redeployment_*`,
`test_phase_149o_20l_7o_2a_*_repositoryidentity_*`,
`test_phase_149o_17_hmrc_implementation_plan_completeness.py`, and
`test_shell_gate.py::TestAuditPersistence::test_audit_verify_cli`. Every
one of these compares current `HEAD` against *its own* phase's
historical frozen candidate SHA and fails whenever *any* later commit
lands, regardless of relevance — the same systemic pattern already
documented for `test_head_equals_origin_main`, just not previously
enumerated at this breadth.

Critically: **none of the failing/erroring nodeids reference
`governance_auto_publication`, `publication_permission_gate`,
`mutation_permission`, `phase_complete`, or `phase.py`'s new
auto-publish call site** (confirmed by direct grep of the full failure
list). The three CHGR-adjacent failures found (`test_exactly_five_
historical_chgrs_plus_this_phases_one_exist`,
`test_exactly_four_historical_chgrs_plus_this_phases_one_exist`,
`test_no_authority_bearing_drift_between_candidate_and_head`) are the
same self-referential "exact historical CHGR count" pattern, not
evidence of a Plan B+ defect — they break whenever any later phase
publishes a new CHGR, which is expected, ongoing repository behavior
unrelated to this release.

**Corrected finding: attributable regressions = 0**, independently
confirmed by direct nodeid inspection and by the fact that the failing
set is identical whether measured at the candidate commit or at current
`HEAD` (empty product diff between them). This is broader, more
rigorous evidence than the 3C.4 report's own categorization, though the
3C.4 report's bottom-line conclusion (0 attributable regressions) was
correct. This document does not edit the 3C.4 report retroactively.

## 6. Build provenance and artifact re-verification

- Build frontend: `python -m build` (PEP 517).
- Build backend: `hatchling`, pinned `==1.32.0` in
  `[build-system].requires`.
- Python: 3.14 (build/verification host).
- Clean-clone method: `git clone` from the local `origin`-tracked repo,
  `git checkout ea3f731ef50ea16985fd4a0562f0c091bb8109b2` in a fresh
  temp directory, fresh venv per build, `python -m build` in build
  isolation mode.
- Independent rebuild (pre-authorization verification pass) and a second
  independent rebuild (immediately before upload, post-authorization)
  both reproduced:
  - **Wheel:** `pcae_harness-0.4.0-py3-none-any.whl`, 2,349,213 bytes,
    `sha256:8125d21dc5093892d7303ccbd416cfed91429798ad2d3f17e1512d24b2c3ea00`
  - **Sdist:** `pcae_harness-0.4.0.tar.gz`, 2,051,181 bytes,
    `sha256:13492127f261e0460ba943598dca010881c672e2c2602348697050f763960f61`

  Both exactly match the canonical 3C.4 frozen hashes. Reproducibility:
  **PASS** (now demonstrated across 4 independent clean-clone builds
  total, counting the two from 3C.4).

## 7. Tag creation and verification

- Annotated tag `v0.4.0` created bound explicitly to
  `ea3f731ef50ea16985fd4a0562f0c091bb8109b2` (not current `HEAD`, which
  was `ac56986f...` at tag-creation time — the two differ only in
  lifecycle/reporting commits per §3).
- Local verification before push: `git rev-parse v0.4.0^{commit}` →
  `ea3f731ef50ea16985fd4a0562f0c091bb8109b2`. Match confirmed.
- Pushed to `origin` with no force. Remote verification:
  `git ls-remote --tags origin 'refs/tags/v0.4.0' 'refs/tags/v0.4.0^{}'`
  → peeled commit `ea3f731ef50ea16985fd4a0562f0c091bb8109b2`.
- **`local tag == remote tag == release_candidate_commit ==
  tagged_commit`: confirmed.**

## 8. GitHub Release

- Created via `gh release create v0.4.0 --title "PCAE v0.4.0" --notes-file
  docs/RELEASE_NOTES_V0_4_0.md --target
  ea3f731ef50ea16985fd4a0562f0c091bb8109b2 --latest`.
- URL: `https://github.com/atimad/pcae-harness/releases/tag/v0.4.0`
- State: not draft, not prerelease, `targetCommitish =
  ea3f731ef50ea16985fd4a0562f0c091bb8109b2`, marked Latest.
- Assets uploaded: `pcae_harness-0.4.0-py3-none-any.whl` and
  `pcae_harness-0.4.0.tar.gz`, both freshly rebuilt from the candidate
  commit immediately before upload and hash-verified against the
  canonical 3C.4/§6 values before uploading (no rebuild between
  verification and upload).
- GitHub-reported asset digests matched the frozen values exactly:
  - wheel `sha256:8125d21dc5093892d7303ccbd416cfed91429798ad2d3f17e1512d24b2c3ea00`
  - sdist `sha256:13492127f261e0460ba943598dca010881c672e2c2602348697050f763960f61`
- **Independent download-and-rehash of both public assets** (`gh release
  download v0.4.0`) reproduced the identical SHA-256 values and byte
  sizes. Public bytes == release-of-record bytes: **confirmed**.

## 9. Post-publication verification (public artifacts only)

- Fresh disposable venvs, no local source, installing only the
  downloaded public release assets.
- Public wheel: version `0.4.0`, no editable dependency, CLI functional,
  golden path (`init` → `session bootstrap` → `task new`) exercised
  successfully in a disposable git repo; `pcae runtime inspect` =
  `Observed / observe / unavailable`.
- Public wheel Plan B+ / corrupt-store / Permission Broker smoke: same
  51-test method as §4's pre-publication pass, re-run against the public
  wheel's installed code. Identical result — 43 passed, 8 failed (same
  repo-checkout-dependent AST/source-scan tests, not behavioral).
- Public sdist: installed cleanly in a separate disposable venv, version
  `0.4.0`, CLI functional.
- PyPI: `curl https://pypi.org/pypi/pcae-harness/json` → `404`; `pip
  index versions pcae-harness` → no matching distribution. **NOT
  PUBLISHED**, confirmed directly, not assumed.

## 10. Boundaries preserved

- Runtime: `Observed / observe / unavailable`, confirmed unchanged
  before and after publication (installed and public-artifact checks).
- Article (`~/repos/pcae-deepseek-research`): not read, not modified, not
  published. Remains **STOPPED**.
- Repository Intelligence: exposure confirmed available; internal
  consumption not claimed or implemented.
- No PyPI credentials created or used.
- No force-push, no `--no-verify`, no history rewrite, at any step.
- No product engineering performed in this phase — the one substantive
  finding (§5's broader Fast Green categorization) is investigative/
  reporting-only; the underlying 3C.4 report and product source were not
  modified.

## 11. Post-publication governance re-check

`pcae health` / `check` / `status coherence`: all healthy/passed/
coherent. `pcae doctor task-memory`: same pre-existing, unrelated
`tasks/DONE.md` backfill warnings as before this phase (accepted debt,
unchanged in kind — task-file count grows over time as a matter of
project history, not something this phase introduced). `pcae push
check`: `nothing_to_push` (repository working tree is independent of the
tag/release, which are separate Git ref/GitHub objects). `pcae runtime
inspect`: unchanged. Telegram notify: configured and enabled.

## 12. Blocker table

| Category | Count/Items |
|---|---|
| BLOCKING | 0 |
| MUST-FIX | 0 |
| ACCEPTED-DEBT | pre-existing `tasks/DONE.md` backfill sync warnings (repository-maintainer-only, unrelated); pre-existing broad self-referential "no drift since my own historical candidate" Fast Green cluster (see §5), now more fully characterized than in the 3C.4 report |
| DEFERRED | Repository Intelligence internal consumption; Runtime Enforcement consumption; rollback integration; shell-gate enforcement/audit surfacing; broad Advisory wiring; HATP/HMIC/Class-B authority activation; CLTR cutover; runtime execution; Telegram inbound; backend/model execution |

## 13. Final verdict

```text
PCAE v0.4.0:
PUBLICLY RELEASED

RELEASE THEME:
CONNECTED GOVERNANCE CAPABILITY CONSUMPTION

RELEASE-CANDIDATE COMMIT:
VERIFIED (ea3f731ef50ea16985fd4a0562f0c091bb8109b2)

TAG:
v0.4.0
VERIFIED (local == remote == candidate)

PLAN B+:
PUBLISHED AND VERIFIED

INTERACTIVE WORKFLOW:
AUTO-ROUTED AT VERIFIED GOVERNED BOUNDARY

HUMAN AUTHORITY:
PRESERVED

CHGR:
AUTOMATICALLY CONSUMED

PUBLICATION EXECUTION OWNERSHIP:
AUTOMATICALLY INVOKED

PERMISSION BROKER:
SELECTED EFFECT PATH VERIFIED

CORRUPT-STORE HARDENING:
VERIFIED

BUILD TOOLCHAIN:
BOUND (hatchling==1.32.0)

WHEEL:
PUBLISHED AND CHECKSUM-VERIFIED

SDIST:
PUBLISHED AND CHECKSUM-VERIFIED

POST-PUBLICATION INSTALL:
PASS

RUNTIME:
Observed / observe / unavailable

PYPI:
NOT PUBLISHED

ARTICLE:
STOPPED

RELEASE STATUS:
COMPLETE
```

## 14. Recommended next strategic direction

Do not automatically resume article work. Per Section 50 of the phase
spec, the next strategic decision is which deferred mature PCAE
capability should become production-consumed next. Candidates for
reassessment from current evidence (not selected or started in this
phase):

- Repository Intelligence internal consumption
- Runtime/plugin capability-aware orchestration
- Remaining Permission Broker coverage
- Runtime Enforcement consumption
- Rollback readiness/evidence integration
- Advisory context consumption
