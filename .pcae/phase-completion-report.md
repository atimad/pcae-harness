# Phase 149O.20L.7O.3C Complete — PCAE v0.3.2 Release Hardening and Release Candidate Verification

**Verdict: COMPLETE — RELEASE CANDIDATE VERIFIED. RELEASE THEME:
EXISTING CAPABILITY PRODUCT EXPOSURE. PRODUCTION FEATURE IMPLEMENTATION
CHANGES: 0. WHEEL: VERIFIED. SDIST: VERIFIED. CLEAN INSTALLS: PASS.
RELEASE BLOCKERS: 0. MUST-FIX: 0. RUNTIME: Observed / observe /
unavailable. PUBLICATION: NOT PERFORMED.**

Froze and independently re-verified the exact v0.3.2 release candidate
selected in Phase 3B, from source in disposable repositories, then
built and verified real wheel/sdist artifacts from the clean committed
release-candidate commit.

## Summary

All four v0.3.2 capabilities (runtime/plugin introspection, Interactive
Workflow/CHGR, Repository Intelligence, `pcae authority inspect`) were
independently re-exercised end-to-end from source, including
reproducing the Repository Intelligence `latest.json` write in a
disposable repository and completing a full `governance-record
publish` chain to a real published CHGR record. Existing documentation
(`docs/CAPABILITY_REFERENCE_V0_3_2.md`) was audited and found already
accurate — `snapshot generate` is correctly labeled a LOCAL WRITE, not
read-only; no documentation correction was required for any of the
four capabilities. `docs/COMMANDS.md`'s generated content was
reconfirmed byte-identical to its generator's output.

Version bumped `0.3.1` → `0.3.2` (`pyproject.toml`,
`src/pcae/__init__.py` — the only production-source change).
`docs/RELEASE_NOTES_V0_3_2.md` written.

## Findings

**Packaging finding (caught, not a release blocker):** building the
sdist directly inside the local development checkout picked up 6
unintended duplicate files (`README.md`/`LICENSE`/`pyproject.toml`/two
schema `README.md`s) from a stray, gitignored `.claude/worktrees/`
directory left over from an unrelated prior agent session — hatchling's
explicit `include` patterns are not anchored to the repository root and
matched these filenames wherever found on disk, VCS-ignore status
notwithstanding. This does **not** reproduce from a fresh clone:
independently verified twice, building from two separate clean clones
of the exact release-candidate commit produced byte-identical wheel
*and* sdist checksums both times, with zero forbidden or unexpected
content. The officially recorded/verified artifacts below are the
clean-clone build. The contaminated in-place build directory was
deleted and never committed. Recommendation for future release
phases: always build release artifacts from a fresh clone (or a
checkout independently confirmed free of untracked/gitignored
matching-named cruft), never directly inside a long-lived local
development working directory.

**Fast Green noise (explained, zero attributable regressions):** the
full `fast_green`-marked suite showed 334–338 failures across three
runs at the release-candidate commit — all state-sensitive/
host-dependent/git-history-count/flaky tests unrelated to this phase
(e.g. HATP Class-B real-host hardware checks, historical-CHGR-count
assertions, shell-gate audit-corpus timing), consistent with Phase
2Z's own documented historical baseline (336 failed/8691 passed/9
errors). A disposable git-worktree A/B comparison against the
phase-entry commit (846ec6c7) found exactly two differing nodeids:
`test_head_equals_origin_main` (expected — this phase's own commits
were not yet pushed at test time) and
`tests/test_shell_gate.py::TestAuditPersistence::test_audit_verify_cli`
(independently reproduced as flaky across three isolated runs: 1 fail,
2 pass — matching the already-disclosed shell-gate audit-corpus
performance debt). A fully deselected run excluding exactly the 345
pre-existing failing/erroring nodeids produced **8691 passed, 5
skipped, 0 failed, 0 errors**.

## Final v0.3.2 Batch (unchanged from Phase 3B, independently reconfirmed)

1. Runtime/plugin introspection (`pcae runtime inspect`) — VERIFIED, full product workflow
2. Interactive Workflow/CHGR — VERIFIED, full product workflow, one documented UX rough edge
3. Repository Intelligence — VERIFIED, self-inspection scope
4. `pcae authority inspect` — VERIFIED, advanced CLTR-tooling docs only

## Release Candidate

- **Release-candidate commit:** `8bb8c882` (implementation commit — version bump, release notes, phase document, `PROJECT_STATUS.md`/`CHANGELOG.md`).
- **Wheel:** `pcae_harness-0.3.2-py3-none-any.whl`, 2,339,194 bytes, SHA-256 `9de9a0d636e80a7bcae5c984f892d34d6e3d28561240b5770cf4be7f35c8d785`.
- **Sdist:** `pcae_harness-0.3.2.tar.gz`, sourced from the clean-clone build, SHA-256 `3baa336afed310980a5c200b1f01623ff618d8735b41f8f0fd36e4e4062161bf`.
- Both checksums independently reproduced identically across two separate fresh-clone builds.
- Clean wheel install: version `0.3.2` confirmed via `import pcae; pcae.__version__`; `pcae --help` works; v0.3.1 golden path (`init`→`session bootstrap`→`task new`→`intake from-files`→`show`/`list`) ACCEPTED; all four v0.3.2 workflows exercised successfully.
- Clean sdist install: identical CLI registration (`pcae --help` byte-identical to wheel); v0.3.1 golden path ACCEPTED; all four v0.3.2 workflows exercised successfully (including a full CHGR publish to a real record). No wheel/sdist divergence found.

## Test Evidence

962 targeted focused-capability tests (Phase 3B's exact suite set) — 962
passed, 0 failed, unchanged from the 3B baseline. Full `fast_green`
suite from the clean release-candidate tree: 8691 passed, 5 skipped, 0
failed, 0 errors after deselecting the 345 pre-existing/environmental
nodeids identically present at the phase-entry commit (see Findings
above) — zero attributable v0.3.2 regressions.

## Governance

`pcae health`: healthy. `pcae check`: passed. `pcae status coherence`:
coherent. `pcae doctor task-memory`: warnings, unchanged,
repository-maintainer-only. `pcae runtime inspect`:
`execution_capability: unavailable`, unchanged before/after this phase.
`v0.3.1` tag confirmed unchanged (`5d7edef9`) at both phase entry and
phase close. No `v0.3.2` tag, no GitHub Release, no PyPI action. No
article read/modified/published. No inspection of the private
`~/repos/pcae-deepseek-research` repository.

## Release Blocker Table

BLOCKING = 0. MUST-FIX = 0. All items ACCEPTED or ACCEPTED-DEBT (task-
memory warnings, shell-gate timeout debt — both pre-existing,
unrelated). See the full table in the phase document.

## Publication Checklist

Produced in the phase document (§34) — final human authorization
required before any tag, GitHub Release, or artifact upload.

## Recommended Next Phase

**3D — PCAE v0.3.2 Public Release.** Publication-only: reverify the
exact release-candidate commit (`8bb8c882`) and the frozen wheel/sdist
checksums above, confirm explicit human publication authorization,
create and publish an annotated `v0.3.2` tag, create a GitHub Release
with the exact verified artifacts attached, verify checksums
post-attachment, run a post-publication clean-install smoke test,
verify Latest/stable pointers, keep PyPI untouched unless separately
authorized, keep the article stopped.

Full text:
`docs/PHASE_149O_20L_7O_3C_PCAE_V0_3_2_RELEASE_HARDENING_AND_RELEASE_CANDIDATE_VERIFICATION.md`.
