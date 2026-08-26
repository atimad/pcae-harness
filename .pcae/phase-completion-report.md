# Phase 149O.20L.7O.3O Complete — PCAE v0.4.3 Release Hardening

**Verdict: RELEASE-CANDIDATE PREPARATION ONLY — COMPLETE. NO PUBLICATION PERFORMED.**

Implemented the human-selected **RELEASE NOW** decision from `3N`/`3N.1`: prepared a frozen,
independently-verified `v0.4.3` release candidate shipping `3M`'s already-verified rollback
evidence-visibility enhancement as a narrow, unbundled patch. Confirmed the only post-`v0.4.2`
product delta was `3M`'s two-file change (`src/pcae/commands/agent.py`,
`src/pcae/core/agent.py`) — no other product behavior change exists, so no scope reassessment
was required.

## Version

`0.4.2` → `0.4.3` in `pyproject.toml` and `src/pcae/__init__.py`.
`docs/RELEASE_NOTES_V0_4_3.md` created (theme: Rollback Evidence Visibility). States rollback
preparation was **already automatic before `v0.4.3`**; this release changes evidence
surfacing/observability only. Permission Broker, HATP, human authority, and runtime are all
explicitly unchanged.

## Candidate and build

`release_candidate_commit = 63580893b1de4782a694ab802ff7bdebdf29b0e6`. Two independent
clean-clone builds (Python 3.14.5, `build==1.2.2`, `hatchling==1.32.0` pinned) produced
byte-identical artifacts:

```
wheel: pcae_harness-0.4.3-py3-none-any.whl / 2,352,742 bytes /
  sha256:e42ca72c136e95fbb179582c3058b1d6c2001edbbbe80f61af8c45002a8ff5e4
sdist: pcae_harness-0.4.3.tar.gz / 2,054,469 bytes /
  sha256:8a088983971b19d6e16f0e6ce3d7a9aa69fa27e987b574c4a109e74589977276
reproducibility: PASS
```

Artifact-content inspection clean: no `.git`, no `.claude/worktrees`, no private-research
content, no secrets/keys, no caches, no stale distributions.

## Installed-artifact verification

Both artifacts installed into fresh venvs: version `0.4.3` confirmed, golden path (`init` →
`session bootstrap` → `task new` → `intake from-files` → `intake list`/`show`) passed on both.
Installed-**wheel** rollback evidence-visibility smoke, via disposable PER/ECP fixtures and the
real installed `pcae` CLI (subprocess, not in-process):

- Dry-run: `Rollback: DRY RUN`, `file_plan:` visible, no `AUTHORIZED` claim.
- Real rollback, **no prior dry-run**, ALLOW path: `Rollback: COMPLETED`, `divergence_check:`
  visible, effect occurred (file removed) exactly as before `3M`/`3O`.
- Divergence conflict: effect stopped (target file unchanged), `file_plan`/`divergence_check`
  still visible in JSON output, `execution_allowed: false` — evidence does not override the
  block.

## Regression coverage

Representative suites re-run from source: rollback Permission Broker (`3F`/`3F.1`, 40 tests), RI
Advisory attachment (`3J`/`3J.1`, 46 tests), Plan B+ connected governance (`3C.2`, 22 tests),
corrupt-store fail-closed (`3C.3.1`/`3C.3.2`, 43 tests), Intake/Codex-Ox (`2X`, 19 tests) — all
green (170/170). Focused `3M` suite: 18/18 passed. Independent `3M.1` suite: 24/26 passed; the 2
failures are an environment-only missing `rg` (ripgrep) binary in this sandbox (only a
shell-function shim exists, not a real binary on `PATH` reachable by a Python subprocess) —
manually re-verified via equivalent `grep`/direct-import checks, and independently confirmed
non-attributable by Fast Green attribution (both present identically on the pre-phase baseline).

## Fast Green

`pcae phase fast-green-attribution --phase-id 149O.20L.7O.3O --pushed-status not_pushed`:
baseline `674dc8a3`, candidate `63580893`. Raw failures 351 (342 failed / 9 errors).
**Attributable: 0.** Pre-existing: 350. Environment: 0. **Verdict: PASS.**

## Invariants held throughout

`pcae runtime inspect`: `Observed` / `observe` / `unavailable` — unchanged before and after all
rollback smoke testing. `v0.4.2` (`bc7935f4`) and `v0.4.1` (`9869cb65`) tags unchanged; no
`v0.4.3` tag exists. Human rollback trigger unchanged (`automatic_rollback_allowed: False`,
`rollback_requires_explicit_human_command: True`). Evidence non-authority confirmed: clean
evidence plus a blocking condition (divergence or PB DENY) still produces zero mutation.

## Blocker table

```
BLOCKING:
0
MUST-FIX:
0
```

Accepted debt (carried forward, not repaired this phase): the `rg`-tooling environment gap in 2
`3M.1` tests; Fast Green's mutable push-state attribution self-referential classification issue;
F1/F2/Decision-Evaluation-surfacing deferred findings (unrelated to this phase's scope).

## Mature-capability-program status

`MATURE CAPABILITY CONSUMPTION PROGRAM: CURRENTLY EXHAUSTED AT S/M SCOPE` (reconfirmed from
`3N.1`, not reopened by this release).

## Publication

```
release: v0.4.3
candidate: 63580893b1de4782a694ab802ff7bdebdf29b0e6
wheel: pcae_harness-0.4.3-py3-none-any.whl / sha256:e42ca72c...
sdist: pcae_harness-0.4.3.tar.gz / sha256:8a088983...
release notes: docs/RELEASE_NOTES_V0_4_3.md
tag target: candidate
GitHub Latest: intended
PyPI: separately unauthorized
human publication authorization: required
```

**PUBLICATION NOT PERFORMED.** No tag, no tag push, no GitHub Release, no PyPI upload.

## Final verdict

```
PCAE v0.4.3 RELEASE CANDIDATE:
VERIFIED
RELEASE THEME:
ROLLBACK EVIDENCE VISIBILITY
ROLLBACK PREPARATION:
ALREADY AUTOMATIC BEFORE v0.4.3
v0.4.3 CHANGE:
EVIDENCE SURFACING / OBSERVABILITY
PERMISSION BROKER:
UNCHANGED
HUMAN AUTHORITY:
UNCHANGED
HATP:
UNCHANGED
RUNTIME:
Observed / observe / unavailable
BUILD REPRODUCIBILITY:
VERIFIED
ATTRIBUTABLE REGRESSIONS:
0
BLOCKING:
0
MUST-FIX:
0
MATURE S/M CONSUMPTION PROGRAM:
EXHAUSTED
PUBLICATION:
NOT PERFORMED
```

See `docs/PHASE_149O_20L_7O_3O_PCAE_V0_4_3_RELEASE_HARDENING.md` for the full 42-section evidence
trail. Recommended next phase: `149O.20L.7O.3O.1` — PCAE v0.4.3 Public Release (publication-only;
requires explicit human authorization). After successful publication, recommend a fresh read-only
Post-Consumption Strategic Runtime / Provider Architecture Reassessment. Article remains STOPPED;
private research repository not inspected/modified.
