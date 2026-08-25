# Phase 149O.20L.7O.3H.1 Complete — PCAE v0.4.1 Public Release

**Verdict: PUBLICLY RELEASED. ZERO BLOCKING FINDINGS.**
Publication-only phase. Publicly released PCAE v0.4.1 under explicit
human authorization given in the active session ("Approved") after
independent re-verification of the frozen `149O.20L.7O.3H` release
candidate reached a zero-blocking/zero-must-fix PUBLICATION READY
checkpoint. Runtime unchanged (`Observed`/`observe`/`unavailable`).

## Summary

**Release candidate:** `9869cb65d890b70d8649ddd4216ffda4e7d98df5` (full
SHA independently derived). Phase-entry `HEAD` (`7eaaee1a`) contained
only 3H's own lifecycle/reporting commits since the candidate — zero
release-facing drift (`git diff 9869cb65..HEAD -- src/pcae
pyproject.toml docs/RELEASE_NOTES_V0_4_1.md` empty).

**Build reproducibility:** 3H's own frozen wheel/sdist bytes were not
preserved between phases (built in disposable `/tmp` venvs, destroyed
after use). Independently rebuilt via two fresh clean clones pinned to
the candidate commit, using the unmodified `v0.4.0` process
(`hatchling==1.32.0`, `build 1.5.0`, Python 3.14.5). Build A == Build B
byte-for-byte, and both matched 3H's frozen record exactly (wheel
SHA-256 `1994dc04...8309`, 2,350,582 bytes; sdist SHA-256
`f8712b9b...5e16cf`, 2,052,499 bytes).

**Installed-artifact rollback Permission Broker smoke:** reconstructed
a 19-check suite from production `pcae.core.*` APIs only (no
test-suite imports) — dry-run, real ALLOW, forced DENY,
missing-active-task DENY, broker failure, malformed result,
`HATP_MANDATORY` isolation (adapter never invoked), human `--per-id`
trigger requirement, dry-run readiness unaffected by missing task.
19/19 passed identically on the rebuilt wheel, the rebuilt sdist, and
— after upload — the **downloaded public wheel**.

**Source-level regression sweeps** (byte-identical source to the
verified candidate, run at phase-entry `HEAD`): Permission Broker
broad sweep 1109 passed/5 failed, Plan B+/corrupt-store 43 passed/0
failed, intake/Codex-Ox 430 passed/8 failed/1 error, 3F+3F.1+AG5+18D
focused bucket 202 passed/5 failed, packaging 20 passed/0 failed —
every failure matched 3H's own documented pre-existing set by name.
`fast_green`: 336 failed/8731 passed/5 skipped/9 errors, within the
same flake tolerance 3H itself documented (zero source drift since the
candidate). **Zero attributable regressions.**

**Publication actions:** created annotated tag `v0.4.1` pinned
explicitly to the release-candidate commit (not `HEAD`); pushed it
(local tag target == remote tag target == candidate, verified both
ways); created the public GitHub Release (`--latest`, correct target,
not draft/prerelease); recomputed frozen artifact hashes immediately
before upload (exact match, no rebuild) and uploaded them; downloaded
the public assets post-upload and verified filename/size/SHA-256 exact
match to the local frozen artifacts; confirmed public release state
(tag, target, Latest pointer, notes) correct; installed the public
wheel and public sdist into fresh disposable venvs with no local
source on path — version/import/CLI all PASS.

**v0.4.0 isolation:** tag, GitHub Release, and both assets confirmed
unchanged both before and after `v0.4.1` publication.

**PyPI: NOT PUBLISHED** (unauthorized, out of scope). **Article:
STOPPED**, not resumed. `~/repos/pcae-deepseek-research` untouched.

**BLOCKING: 0. MUST-FIX: 0.** No production source, version, or build
configuration change made this phase.

**Does not self-authorize the deferred capability roadmap.**
Recommends a reassessment of runtime preflight disclosure, rollback
readiness/evidence auto-generation, and Repository Intelligence +
Advisory integration next — none selected this phase.

See `docs/PHASE_149O_20L_7O_3H_1_PCAE_V0_4_1_PUBLIC_RELEASE.md` for the
full evidence trail.
