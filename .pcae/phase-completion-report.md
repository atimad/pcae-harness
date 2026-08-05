# Phase 149O.1F.1 Complete — HATP Production Trust-Store Path Hardening

**Phase ID:** 149O.1F.1
**Mode:** narrow foundation repair (production trust-root resolver
only; no Wave 3+, no Class-B OS provisioning, no contract amendment)
**Predecessor:** 149O.1F (HATP Repository Identity + Trust-Store
Foundation Independent Verification — completed, `NOT VERIFIED --
BLOCKING HATP FOUNDATION FINDING`, recommended this repair)
**Date:** 2026-08-06
**Status:** completed
**Pushed:** pending
**origin/main..HEAD:** 4

This is the lightweight staging header for `pcae phase complete`. The
full document
(`docs/PHASE_149O_1F_1_HATP_PRODUCTION_TRUST_STORE_PATH_HARDENING.md`)
is the canonical artifact of this phase.

---

## Executive Summary

Phase 149O.1F independently attacked the Wave 1
(`src/pcae/core/repository_identity.py`) and Wave 2
(`src/pcae/core/hatp_bootstrap.py`) foundation implemented by 149O.1E,
rather than trusting its report. Source was read directly; the
production diff, the Wave-1/2 requirement mapping, the repository-
identity model, and the trust-store model were all independently
reconstructed. A new adversarial test file
(`tests/test_phase_149o_1f_hatp_repository_identity_trust_store_foundation_independent_verification.py`,
22 tests) was authored — no 149O.1E test file was modified.

**Held under independent attack:** caller-controlled-ID rejection at
every production API surface; malformed-identity fail-closed with no
auto-heal; symlink-write refusal both before and after the atomic write;
zero static/hardcoded identity in `templates.py`; clone non-propagation
(identity path gitignored, confirmed via `git check-ignore -v`);
full-copy and repository-ID-theft attacks resolving to no authorized
deployment; worktree-distinct identity; path-move identity preservation
with no auto-rebind; same-ID-wrong-root and same-root-wrong-ID both
rejected; canonical-root `.`/`..`/symlink aliasing resolving
identically; strict closed-schema registry validation with duplicate
records rejected outright, not resolved by mtime or file order; no
wildcard/global authority fallback; this repository's live deployment
and every agent-controllable permission mode never reporting `READY`; a
monkeypatched root-UID probe still routing through the same-user check;
zero public mutation methods on `HATPTrustStore`; zero
`approval_present`/`HATP_TRUSTED_OPERATIONAL`/`verify_*` symbols; and the
RAE/Permission-Broker/agent boundary byte-identical since the 149O.1B.3
freeze.

**BLOCKING finding (recorded, not repaired):** `HATPTrustStore.production()`
resolves via `Path.home() / ".pcae-hatp" / "trust-store"`. `Path.home()`
on POSIX consults `$HOME`, an ordinary, agent-controllable
process-environment variable — verified directly by setting `HOME` and
observing `Path.home()` relocate. An agent that controls its own `HOME`
can therefore redirect the "authoritative" trust-store root to a
self-owned directory and author its own `registry.json` there; a
subsequent `resolve_deployment_authorization()` call returns a real,
non-`None` `DeploymentBinding` for a repository/root pair the agent
fabricated end to end. This contradicts the module's own claimed
environment-independence invariant; the 149O.1E adversarial suite
checked four guessed HATP-specific variable names but never `HOME`, the
actual resolver dependency. `resolve_deployment_authorization` does not
compose with the (independently sound) same-user `environment_status()`
check, so nothing in Wave-1/2 itself prevents a future consumer from
trusting a `HOME`-redirected binding.

**Verification verdict: NOT VERIFIED — BLOCKING HATP FOUNDATION
FINDING.**

HATP-001 v1.0 remains byte-unchanged (`git diff --name-only -- docs/contracts/`:
empty). No production source was modified by this phase
(`git diff --name-only HEAD -- src/pcae/`: empty). `B-149O-1` through
`B-149O-4` remain OPEN, reproduced identically. `F-149O.1C-1` remains
pending actual Wave-3 proof-schema implementation; `F-149O.1C-2` remains
editorial debt only. Foundation software NOT READY pending a narrow
trust-store path hardening repair; HATP production remains NOT READY
regardless (Waves 3-7 unimplemented). New independent suite: 22/22
passing. Existing 149O.1E suites reproduced unchanged: 51 passed.
149O.1C regression: 95 passed. 149O.1D regression: 32 passed. Permission
Broker/RAE regression: 1243 passed, 4 failed (pre-existing B-149O-1..4
reproductions, expected). Fast Green: 4431 passed — identical to the
entering baseline, no regression. Runtime remains Observed / observe /
unavailable throughout.

**Recommended next phase:** 149O.1F.1 — HATP Production Trust-Store Path
Hardening (narrow repair of `_default_production_trust_root()` only, in
`src/pcae/core/hatp_bootstrap.py`).

See
`docs/PHASE_149O_1F_HATP_REPOSITORY_IDENTITY_TRUST_STORE_FOUNDATION_INDEPENDENT_VERIFICATION.md`
for the full analysis.
