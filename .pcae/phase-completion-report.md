# Phase 148G.1 Complete — Permission Broker Production Consumption Operational Hardening

**Phase ID:** 148G.1
**Mode:** Bounded production operational hardening (one `src/pcae/**` file
changed; zero `docs/contracts/**` changes; no `POL-001..012` semantic
change; no new runtime capability)
**Predecessor:** 148G (Permission Broker Production Consumption Operational
Readiness / Chapter 148 Assessment)
**Date:** 2026-08-03
**Status:** completed
**Pushed:** pending_push

This is the lightweight staging header for `pcae phase complete`. The
full document
(`docs/PHASE_148G.1_PERMISSION_BROKER_PRODUCTION_CONSUMPTION_OPERATIONAL_HARDENING.md`)
is the canonical artifact of this phase.

---

## Executive Summary

Phase 148G.1 closes both findings 148G carried forward from 148F.

**F-148F-3 (`REPAIR_REQUIRED_BEFORE_CLOSURE` → CLOSED):** Independently
re-derived `PBPC-001` v1.2 Section 17 (`PBPC-REQ-059`-`061`): re-observe
local HEAD, branch, unpushed-commit count, and active task ID (the four
fields `PBPC-REQ-056` identifies as locally, transactionally bindable)
immediately before each of `pcae push`'s two dispatch sites; any
mismatch against the value bound at broker-evaluation time is material;
material mismatch invalidates the existing `ALLOW`, dispatches nothing,
and requires a fresh evaluation cycle (not an automatic in-place
re-evaluation). Implemented via a new in-process `_PushDecisionSnapshot`
(never persisted) captured inside `_evaluate_push_permission` at the
moment of broker evaluation, and a new shared
`_validate_push_permission_freshness()` helper called immediately
before each real `git push` dispatch on both the ordinary and
`--staged-file-aware` paths.

**F-148F-1 (`REPAIR_RECOMMENDED_POST_CLOSURE` → CLOSED):** Widened
`_evaluate_push_permission`'s `try:` block to cover `PermissionBroker()`
construction as well as `.evaluate()`, following the existing
`command_path_observation.py:70-84` precedent. Construction failure now
produces the same graceful `"Push blocked: Permission Broker evaluation
failed (...)"` diagnostic and exit code `1` that evaluation failure
already produced.

**Test hygiene:** repaired the stale 148C.10-era invariant test
(latent since 148E's intentional `PermissionBroker` wiring) and two
148F tests that had encoded the pre-repair F-148F-1 bug as expected
behavior — both explicitly predicted this exact rewrite in their own
docstrings. Added a new focused hardening suite,
`tests/test_permission_broker_push_operational_hardening.py` (9 tests).

**Regression:** 31/31 (148E/148F PBPC suites), 20/20 (148C.10 suite),
9/9 (new hardening suite), 455/455 (Foundation/PBPA suites), 186/186
(runtime suites), 186/186 (full push-suite regression across 8 files),
Fast Green (`-m fast_green -n auto`) 4391/4391 passed — unchanged from
the 148D/E/F/G baseline.

**Contract/Foundation boundary:** `git diff --name-only
<pre-148G.1>..HEAD -- docs/contracts/` empty (`PBPC-001` remains v1.2,
`PBPA-001` remains v1.0). `git diff --name-only <pre-148G.1>..HEAD --
src/pcae/core/permission_broker_foundation.py
src/pcae/core/permission_broker.py` empty (`HARD_BLOCK_REGISTRY`
unchanged, 12 entries).

**Deliberate deviation:** 148G's own recommendation text additionally
suggested adding a "construction failure" row to `PBPC-001` §18's
failure-ownership table. The actual 148G.1 governing task instructions
explicitly prohibit amending `PBPC-001`, so this specific sub-item was
not done — flagged here as an open item for a future,
separately-scoped contract-amendment phase rather than silently
dropped.

**Verdict:** Implementation complete. Zero new Blocking findings. Both
entering findings (F-148F-1, F-148F-3) closed.

**Recommended next phase:** 148G.2 — Permission Broker Production
Consumption Operational Hardening Independent Verification (must not
trust this phase's own tests, docstrings, or claims), before a
dedicated 148H — Chapter 148 Certification phase.

See
`docs/PHASE_148G.1_PERMISSION_BROKER_PRODUCTION_CONSUMPTION_OPERATIONAL_HARDENING.md`
for full detail.
