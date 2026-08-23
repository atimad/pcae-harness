# Phase 149O.20L.7O.2U.5 Complete — v0.3 Release Candidate Preparation

**Verdict: B — RELEASE READY WITH DOCUMENTED NON-BLOCKING LIMITATIONS —
HUMAN PUBLICATION CONFIRMATION REQUIRED.** No `src/pcae/core/**` or
`src/pcae/commands/**` runtime logic modified (version metadata only).
No `v0.3.0-rc1` tag or GitHub Release created.

Verified the live published release baseline (`v0.1.0-rc1`, `v0.2.0`)
and confirmed `v0.3.0-rc1` has no conflicting tag/branch/release/package
version. Bumped package version to `0.3.0`
(`pyproject.toml`, `src/pcae/__init__.py`).

**Packaging**: built sdist/wheel from a **clean git checkout**, not the
live dirty working tree — this avoided a build-hygiene issue (a stray
untracked, gitignored local worktree directory would otherwise leak
into the sdist via basename-anywhere `include` pattern matching;
non-sensitive content, fully eliminated by the clean-checkout build,
confirmed by direct archive inspection). Installed the built wheel into
a fresh, empty virtualenv.

**RC ALLOW**: using only the RC wheel install, in a disposable
repository, a direct generic-JSON candidate (no Claude Code involved)
targeting the task's in-scope file was accepted, reviewed
(`promotion-review create --promotion-authorized`), and promoted
(`pcae promote`) — the target file's new content verified by direct
file read.

**RC DENY**: the same RC install, a candidate targeting an out-of-scope
path was rejected (`pcae intake create` exit code 1,
`out_of_scope_path`), produced no ECP, left the file unchanged.

**Claude adapter**: separately re-ran the real
`scripts/claude_code_intake_adapter.py` from the source checkout
against the same RC-versioned installed package — confirmed still
functional.

**Quickstart**: re-derived and re-exercised `docs/QUICKSTART_V0_3.md`'s
command sequence against this RC state; added a previously-missing
repo-fingerprint-collision limitation bullet.

**Regression**: 2U.2/2U.3/2U.4 suites re-run clean (143/143). Focused
downstream regression: 846 passed, 21 failed/2 errored, identical
composition to 2U.4's last report — all pre-existing HATP/HMIC
byte-identity tests. Two independent raw `fast_green` runs (337/8689/5/9
and 336/8690/5/9 — a confirmed one-test flake, zero intake/ECP/
promotion matches in either) were diffed; a deselected re-run against
the disclosed 347-ID union produced **0 failed, 8688 passed, 5
skipped**. A supplementary full-suite run (36,599 tests) reported 637
failed/35935 passed/18 skipped/9 errors; every failure cluster
intersecting a file this phase changed was spot-verified via
`git stash -u` A/B to reproduce identically on the pre-phase baseline —
zero attributable regression anywhere.

**Findings dispositioned, none repaired**: Windows-backslash
path-admission gap (2U.3) — no public Windows-support promise exists
for the intake path, so this is a Documented Limitation, Non-Blocking.
Repository-fingerprint collision on byte-identical genesis commits
(2U.3) — Documented Limitation, Non-Blocking, now also surfaced in the
quickstart itself.

**Release must-haves**: all eight (generic intake, `pcae intake`
commands, Claude Code reference producer, real ALLOW, real DENY, audit
evidence, ~5-minute quickstart, existing promotion-chain integration)
classified READY. Zero release blockers.

Wrote `docs/RELEASE_NOTES_V0_3_0_RC1.md` and the full RC readiness
report
(`docs/PHASE_149O_20L_7O_2U_5_V0_3_RELEASE_CANDIDATE_PREPARATION.md` —
must-have matrix, capability matrix, findings dispositions, RC
checklist, GO recommendation). Updated `README.md` status line,
resource table, and roadmap.

**No `v0.3.0-rc1` tag or GitHub Release created this phase** —
publication remains pending explicit human confirmation, per the
phase's authority boundary.

Full text:
`docs/PHASE_149O_20L_7O_2U_5_V0_3_RELEASE_CANDIDATE_PREPARATION.md`.

**Recommended next step**: human publication decision — "v0.3.0-rc1 is
release-ready at commit `<SHA>`. May I create the public `v0.3.0-rc1`
tag and GitHub Release?" — once this phase's commits are pushed and the
tag-target SHA is finalized.
