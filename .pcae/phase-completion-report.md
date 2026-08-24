# Phase 149O.20L.7O.2U.5.1 Complete — v0.3.0-rc1 Publication Documentation Consistency Pass

**Verdict: Documentation wording aligned with the already-published,
verified `v0.3.0-rc1` release. No product mismatch found.** No
`src/pcae/**` file touched. No new tag or release created — the
existing `v0.3.0-rc1` tag/release (published in Phase 149O.20L.7O.2U.5)
were not moved, retagged, or overwritten.

Downloaded the actual public GitHub release assets
(`gh release download v0.3.0-rc1`) and confirmed their SHA-256
checksums match the reviewed 2U.5 clean-checkout build exactly, for
both the wheel and the sdist — no substitution, no re-build drift.

Installed the publicly downloaded wheel into a fresh, empty virtualenv
and re-ran the full ALLOW (accepted → reviewed → promoted → target file
write verified by direct read) and DENY (exit code 1,
`out_of_scope_path`, no ECP, file unchanged) smoke test against it in a
disposable repository — using the actual bytes a real user would
download, not the local `/tmp` build.

Found and corrected two genuine documentation-drift points:
- `docs/INSTALLATION.md`'s `## v0.2 release-candidate notes` section
  was dated framing with no mention of the new intake path — retitled
  `## Current release posture (v0.3.0-rc1)` and updated to describe
  `pcae intake` and link the quickstart/release notes.
- `README.md`'s "Historical note" line didn't mention `v0.3.0-rc1`
  existing — updated to name it explicitly.

Added a clean, user-facing `## v0.3.0-rc1` summary section at the top
of `CHANGELOG.md` (What's New / Unchanged / Known Limitations),
distinct from the existing internal phase-bullet log, per the explicit
instruction to emphasize user-visible change over phase history.

Confirmed: every reference to `scripts/claude_code_intake_adapter.py`
explains how to obtain it (source checkout via the documented
`git clone` install path); no document claims general autonomous/
runtime execution or unsupported platform guarantees; all Non-Blocking
limitations from 2U.5 (Windows path caveat, repository-fingerprint
caveat, text-only intake, single-active-task scope, Claude Code as
reference-not-required) remain intact across every document touched.

**No substantive product mismatch was found** — every correction this
phase made was wording alignment with already-verified behavior,
within the release-preparation authorization; nothing required
stopping before publication (publication had, in fact, already
correctly occurred in 2U.5 before this consistency pass began).

Full text: this report and
`docs/PHASE_149O_20L_7O_2U_5_V0_3_RELEASE_CANDIDATE_PREPARATION.md`
(2U.5's original RC readiness report, unchanged).

**Recommended next step**: a short v0.3.0-rc1 post-release observation
phase — confirm continued clean installs from the public source over
time, collect/fix genuine RC blockers if any are reported, evaluate the
Windows-path and repository-fingerprint findings for v0.3.0 final
disposition, and decide whether v0.3.0 final can follow without
additional feature work.
