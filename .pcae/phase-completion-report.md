# Phase 149O.20L.7O.2Y Complete — Post-v0.3 Release Hardening and Release Scope Reassessment

**Verdict: COMPLETE — RELEASE SCOPE DERIVED, W.1 FINDINGS ADJUDICATED,
BOUNDED HARDENING APPLIED, PACKAGE/INSTALL VERIFIED, v0.3.1
RECOMMENDED.** 0 Blocking findings. Post-`v0.3.0` development; the
published `v0.3.0` tag/release/package version are untouched. No release
published, tagged, or uploaded.

Reconstructed the complete post-v0.3 change inventory directly from
`git diff v0.3.0..HEAD` (31 commits, 6 production files, +350/−107
lines) — every change traces to 2W/2W.1 (Generic Producer Intake Helper)
or 2X/2X.1 (Codex-Ox Agent Registration), zero unrelated/deferred
changes. Derived a release-candidate capability set, a
stable-vs-current-vs-proposed matrix, and a full supported-agent matrix
from live source inspection, reconfirming "registered agent" is never
confused with "PCAE-native executable backend."

Adjudicated both carried-forward W.1 findings: independently reproduced
the malformed-agent-lock defect fresh, traced its exact mechanism (a
packaged CLI command, `pcae intake from-files`, crashed with a raw
traceback on a corrupted lock file; `pcae session bootstrap` was
accidentally unaffected because `json.JSONDecodeError` subclasses
`ValueError`), reclassified it SHOULD-FIX-BEFORE-RELEASE, and **repaired
it this phase** with narrowly-scoped bounded hardening in
`derive_producer_provenance`. Reconfirmed the empty-agent_id finding as
SAFE-TO-DEFER and deliberately left it unrepaired.

Found README.md and `docs/QUICKSTART_V0_3.md` stale relative to `main`'s
actual capability set — neither mentioned `pcae intake from-files` or
`codex-ox` — and repaired both additively this phase.

Verified the package boundary by building real local wheel and sdist
artifacts and running a clean-environment install smoke against both,
covering the full generic-intake + codex-ox golden path end-to-end with
zero external network/AI calls.

## Summary

Recommends **`v0.3.1` (patch)**: every change is additive identity
registration, consolidation of the existing v0.3.0 generic-intake
feature, or small bounded hardening — no breaking change. Release
blocker table has zero remaining BLOCKING/MUST-FIX items scoped to this
phase's own changes; the one MUST-FIX item found (stale `pyproject.toml`
version string) is a publish-time action, correctly deferred to the next
phase. Article readiness: READY AFTER RELEASE, with a scoping caveat
that the four `undeclared`-adapter identities (DeepSeek/Gemini/Grok/
Perplexity) must not be described as supported integrations — the
article itself was not read, modified, or published.

## Test Evidence

9 fresh independent tests + 439 targeted regression (2X/2X.1/2W/2W.1/
2U.2/2U.3/2U.4/review/promotion) + `test_agent.py`/`test_session.py`
full files (4381 passed, 0 failed) = **4829 tests run and passing this
phase**.

Independent Fast Green A/B (fixed `git worktree` clean baseline vs. this
phase's own working tree): 335 vs. 352 failed (344 vs. 361 total incl. 9
errors each). Of the 18 new failures, 16 are unrelated historical
"no `src/pcae` files dirty" guard tests (expected, resolves on commit).
The remaining 2 were independently re-run in isolation: one passed
cleanly, the other reproduced the same concurrent-load subprocess-
timeout mechanism independently confirmed in 2X.1. Zero attributable
regressions.

## Governance

`pcae health`: healthy. `pcae check`: passed. `pcae status coherence`:
coherent. `pcae runtime inspect`: `execution_capability: unavailable`,
unchanged. v0.3.0 tag/release/package: untouched. Article:
unchanged/unpublished. Private `~/repos/pcae-deepseek-research`: not
inspected. No tag, release, or upload of any kind occurred.

## Recommended Next Phase

**149O.20L.7O.2Z — Post-v0.3.1 Release Candidate Final Verification**:
version bump to `0.3.1` in `pyproject.toml`, packaged artifacts rebuilt
against that version, checksums, a repeated clean install across wheel
and sdist, the supported workflows this phase smoke-tested,
documentation truth (including promoting `pcae intake from-files` to the
quickstart's primary golden path), the regression baseline established
here, stable-tag isolation, release notes, and the publication
checklist. Must not publish automatically.

Full text:
`docs/PHASE_149O_20L_7O_2Y_POST_V0_3_RELEASE_HARDENING_AND_SCOPE_REASSESSMENT.md`.
