# Phase 149O.20L.7O.2S.6 — FGSC-001 Real Self-Hosting Acceptance (S22.1 Positive + S22.2 Negative)

## Purpose

Exercise FGSC-001's real self-hosting acceptance requirements against the
actual PCAE governed lifecycle machinery (`src/pcae/core/fast_green_attribution.py`,
`src/pcae/core/phase_reports.py`), not synthetic unit tests, per the S22
acceptance directive following 149O.20L.7O.2S.5.

## Phase entry

- Phase-entry HEAD / origin/main: `696fa665ea19bf233716ac3378f8cd3356b4d2ea` (equal, clean).
- FGSC-001 contract: `docs/contracts/FAST_GREEN_SELF_CERTIFICATION_LIFECYCLE_CONTRACT.md` v1.0, frozen.
- Structured Fast Green implementation revision under test: `src/pcae/core/fast_green_attribution.py`
  and `src/pcae/core/phase_reports.py` (lines ~1712-1791) as of the phase-entry commit above,
  unmodified throughout this acceptance phase.

## Disposable environment design

Two isolated local clones (`git clone --local`, origin remote removed — no network, no
shared state with the real repo) rooted at phase-entry HEAD, one per scenario:

- S22.1 positive clone, S22.2 negative clone.

Both used the real, unmodified `pcae` CLI (globally installed, pointed at the disposable
clone's cwd) and the real `fast_green_attribution`/`phase_reports` modules — no mocking of
checkpoint logic, structured evidence validation, finalization diff authority, or Stage B.

Two test-harness bugs were found and fixed during setup (not production defects):
1. `derive_phase_entry_baseline`'s commit-subject regex (`^Phase\s+(\S+?)\s*[:—–-]`) stops
   at the *first* hyphen — an initial phase-id choice containing a hyphen
   (`S22.1-DISPOSABLE`) parsed as `S22.1` only, causing baseline collapse. Fixed by using
   hyphen-free ids `S221DISPOSABLE` / `S222DISPOSABLE`. Real project phase ids use dots only,
   so this does not affect production usage — carried as an observation, not a finding.
2. First finalization attempt in the S22.1 clone used a generic commit message string
   rather than the project's own governed-task lifecycle, so `pcae check` correctly flagged
   the persisted evidence artifact as outside active-task scope. Fixed by running the real
   `pcae task new` / `pcae task update --allowed-file` governance for the disposable phase.

## S22.1 — POSITIVE

- Disposable phase id: `S221DISPOSABLE`.
- Baseline commit: `696fa665ea19bf233716ac3378f8cd3356b4d2ea` (method:
  `parent_of_oldest_phase_attributed_commit` — real, non-degenerate baseline derivation).
- Candidate / verification checkpoint commit: `79c5777eaa5d3520901c3af385ebe895bdd4135f`
  (`Phase S221DISPOSABLE: candidate behavior-bearing change` — added one deterministic test
  file `tests/test_phase_149o_20l_7o_2s_6_s22_acceptance_fixture.py`).
- Structured evidence (`pcae phase fast-green-attribution --phase-id S221DISPOSABLE
  --pushed-status local_only`, real full `pytest -m fast_green` run at both baseline and
  candidate): verdict **PASS**, 0 validation issues, raw failed 346 / raw errors 9 (355 total,
  all real pre-existing failures in this environment), `attributable_failures: []`,
  `excluded_preexisting_failures`: 355. Structured self-certification was the sole completion
  authority — no scalar `fast_green` value or pytest-deselection fallback was used anywhere in
  this scenario.
- Post-checkpoint authorized finalization delta (real governed task lifecycle: `pcae task new`
  + `pcae task update --allowed-file`, then edits to `PROJECT_STATUS.md` and task/evidence
  files — all Class B per contract §4): finalization HEAD
  `a1a22979f1ae1fd255617c9473aa92263d884291`, distinct from the checkpoint.
- `check_finalization_delta(checkpoint, final_head)` (real function): **0 issues** — delta
  fully Class-B-authorized, ancestry holds, no merge commits.
- `run_stage_b_focused_checks` (real function, runs the actual `pcae check`): **0 issues** —
  `pcae check` passed in the disposable clone at final HEAD.
- Lifecycle termination: 2 commits after checkpoint (finalization delta), finite, no
  circular re-verification loop observed.
- Push: not exercised against a real remote (the disposable clones have no origin); the
  mechanism proven is the trust-boundary check itself (`check_finalization_delta` /
  `run_stage_b_focused_checks`, the same functions `phase_reports.py` calls before a report
  can be promoted), not the network push step.
- **S22.1 verdict: PASS.** Real disposable governed phase reached a state where structured
  FGSC evidence, checkpoint/finalization-delta authority, and Stage B all independently
  passed via the real self-certification code path, with no scalar+deselection fallback used
  as completion authority.

## S22.2 — NEGATIVE

- Disposable phase id: `S222DISPOSABLE`.
- Baseline commit: `696fa665ea19bf233716ac3378f8cd3356b4d2ea` (method:
  `parent_of_oldest_phase_attributed_commit`).
- Valid checkpoint: `16432e00a56f575fc3153eaf406d8f8dc72fb717`
  (`Phase S222DISPOSABLE: candidate behavior-bearing change`). Structured evidence at this
  checkpoint: verdict PASS, 0 issues, `attributable_failures: []` — a genuinely valid,
  passing checkpoint was established before the forbidden change.
- Forbidden post-checkpoint change: `078f5761c86d2d835d739f856915a479b6e64404` — a minimal,
  reversible edit appending one function to
  `tests/test_phase_149o_20l_7o_2s_6_s22_2_negative_fixture.py` (a `tests/**` path, Class A
  per contract §4 — verification-affecting).
- **Rejection result**: `check_finalization_delta(checkpoint, forbidden_head)` returned one
  issue: *"post-checkpoint change to
  'tests/test_phase_149o_20l_7o_2s_6_s22_2_negative_fixture.py' (status=M, mode=100644) is
  Class A (verification-affecting or unrecognized) — forbidden after the verification
  checkpoint (contract §4/§6); checkpoint invalidated, Stage A must be regenerated."*
- Exact rejection boundary: diff-authority path classification
  (`classify_finalization_path` / `diff_authority_issues`, contract §4/§6) — before Stage B,
  before canonical trust gate, before any push consideration. Fail-closed, deterministic, no
  dependence on pytest pass/fail outcome (the appended test itself was a passing assertion —
  rejection was purely path-classification-based, matching contract intent that checkpoint
  invalidation is independent of pytest result).
- No manual override was applied or needed to observe the rejection — the real,
  unmodified function returned the issue on the real post-commit git diff.
- Fresh-verification recovery path was not separately re-executed as a full second phase (not
  required for S22.2 per the acceptance directive); the S22.1 scenario already demonstrates
  that a freshly-established checkpoint (`S221DISPOSABLE`) reaches a clean, unblocked state,
  which is the recovery path S22.2 would take.
- **S22.2 verdict: PASS.** Old checkpoint/evidence was genuinely rejected; no canonical
  completion or push eligibility was reachable from it; the failure is fail-closed and occurs
  before any trust-gate promotion.

## Focused regressions (real repository, unmodified)

`pytest tests/test_phase_149o_20l_7o_2s_2_fgsc_001_lifecycle_implementation.py
tests/test_phase_149o_20l_7o_2s_3_fgsc_001_lifecycle_independent_verification.py
tests/test_phase_149o_20l_7o_2s_4_fgsc_001_staleness_carveout_repair.py
tests/test_phase_149o_20l_7o_2s_5_fgsc_001_staleness_carveout_independent_verification.py`:
**67 passed, 0 failed** (14.14s).

## Carried findings (unchanged, not repaired in this phase)

N1 (overbroad `docs/contracts/**` digest-binding citation), N2 ("class C" naming
inconsistency), N3 (push-correction-loop termination empirical, not structurally bounded),
2R.1 findings (raw artifact-content trust boundary; environment-timeout exclusion weakness;
commit-message-derived baseline authority; artifact retention observation), 2S.5's
issue-identity prefix-match Non-Blocking finding. None of these were triggered as
Blocking by real S22 execution.

## New observations (Non-Blocking, test-harness only — not production defects)

- The phase-commit-subject baseline regex's first-hyphen-stop behavior (see "Disposable
  environment design" above) is worth a documentation note for anyone choosing ad hoc
  phase ids containing hyphens; real project phase ids (dot-separated) are unaffected.

## No production code changes

`src/pcae/**` was not modified. No Blocking defect was discovered — both S22.1 and S22.2
passed using the real, unmodified implementation.

## Scope not touched

Phase 149O.20L.7O.2P: untouched, still quarantined — no reconciliation attempted. HATP,
FIDO2, WebAuthn, Dell deployment, HMIC: untouched, not exercised.

## Overall verdict

**FGSC-001 v1.0 — REAL STRUCTURED FAST GREEN SELF-HOSTING — OPERATIONALLY CERTIFIED.**

- S22.1 POSITIVE: PASS — real governed phase completed through structured self-certification;
  scalar+deselection fallback not used as completion authority; checkpoint != final head
  supported through an authorized finalization delta; Stage B passed.
- S22.2 NEGATIVE: PASS — forbidden post-checkpoint change detected; old checkpoint/evidence
  rejected; fresh verification required.
- Phase 2P: still unchanged / quarantined.
- 2P reconciliation: authorized as a next, separate phase (149O.20L.7O.2T) per the acceptance
  directive — this phase does not itself reconcile or promote 2P.

## Recommended next phase

149O.20L.7O.2T — Phase 149O.20L.7O.2P Attribution-Aware Reconciliation and Canonical
Promotion Assessment (per the acceptance directive's own framing: 2T must first determine
whether historical 2P evidence can legitimately be re-evaluated under the now-certified
structured model before any promotion, reconstructing 2P's original baseline, frozen
candidate, raw results, attribution evidence, and commit reachability).
