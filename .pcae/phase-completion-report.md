# Phase 149O.18A Complete — HATP Mandatory Cutover State Foundation

**Phase ID:** 149O.18A
**Mode:** implementation (bounded — Wave A of the 149O.17 plan; one new production module only)
**Predecessor:** 149O.17 (HATP Mandatory Production Consumption Implementation Plan — completed, VERDICT: HATP MANDATORY PRODUCTION CONSUMPTION IMPLEMENTATION PLAN: COMPLETE — READY FOR BOUNDED IMPLEMENTATION)
**Date:** 2026-08-08
**Status:** completed
**Verdict:** HATP MANDATORY CUTOVER STATE FOUNDATION: IMPLEMENTED — READY FOR 149O.18B
**Commits:** d80778d2, 3db8f902, 178e39e2
**Pushed:** pending
**origin/main..HEAD:** 3
**Metadata consistency:** consistent

This is the lightweight staging header for `pcae phase complete`. The
full document
(`docs/PHASE_149O_18A_HATP_MANDATORY_CUTOVER_STATE_FOUNDATION.md`) is the
canonical artifact of this phase. Confirmed baseline: repo clean,
`origin/main..HEAD=0`, 149O.17 complete, `HMRC-001 v1.0` `VERIFIED WITH
NON-BLOCKING FINDINGS — CONFORMS`, HATP production NOT READY, runtime
`Observed/observe/unavailable`. Read `HMRC-001` in full, the 149O.17
implementation plan in full (especially §9.1's Wave A module design),
`hatp_bootstrap.py` and `repository_identity.py` in full, and confirmed
`HATPTrustStore.production().root` is the existing public protected-root
accessor this phase reuses unmodified.

Added the sole new production module
`src/pcae/core/hatp_mandatory_cutover.py`: the `CutoverMode(str, Enum)`
vocabulary (`LEGACY_COMPATIBLE`/`PREPARED`/`HATP_MANDATORY`, no fourth
mode value); the closed-schema `CutoverRecord` model/parser (strict
integer version with explicit boolean rejection, duplicate-JSON-key
rejection, a new `Z`-suffix-only fully-anchored strict timestamp grammar
independent of either existing permissive `fromisoformat`-based parser);
protected persistence under the existing trust root (no modification to
`hatp_bootstrap.py`); the fresh-every-call mode-resolution algorithm
(first-install, valid record, wrong-repository, and deleted/corrupt/
unknown-version/boolean-version record all fail-closed via monotonic-
marker consultation, never a silent downgrade); the separate write-once
monotonic activation-history marker; and centralized transition-graph
validation (only the two frozen forward transitions permitted, every
reverse/skip transition rejected or inexpressible).

Resolved the 149O.17 plan's deferred admin-authority-mechanism question
by direct source reading: no application-level Protected-Activation-
Authority principal type exists anywhere in this codebase, so none was
invented — the internal transition writer is never paired with the
production protected root anywhere in the module (AST-verified), relying
instead on the same OS-level file-permission boundary already protecting
the sibling `registry.json`. Implemented real concurrent-transition
safety via `fcntl.flock` plus fresh mode re-resolution before write,
verified with real `threading`-based concurrency tests.

Authored 114 new tests (85 unit + 29 phase-specific), both added to Fast
Green. Ran a full HMRC/HATP/rollback/PB regression sweep; via a true
isolated `git worktree` baseline checkout at the phase-entering commit,
independently attributed every resulting failure to either a pre-
existing, unrelated cause, or a necessary, well-understood consequence of
this phase's required production module now existing (historical
snapshot assertions in five older phase-verification files). No AG3/
AG5/rollback/Permission-Broker behavioral regression found (PB suite
234/234 passed; rollback-focused suite 78/78 passed). Fast Green with
the 9 necessarily-invalidated snapshot assertions and 2 pre-existing-
unrelated tests deselected: **5237 passed, 0 failed, 2 skipped** (raw
undeselected: 5237 passed, 10 failed, 2 skipped, 1 pre-existing
collection error).

No evidence consumption, no AG3/AG5 gating, no CLI plumbing, no legacy-
authority change, no Permission Broker change, and no real
`HATP_MANDATORY` activation of the current deployment. HMRC-001 v1.0 and
all six upstream contracts remain byte-unchanged. B-149O-1..4 remain
INDEPENDENTLY VERIFIED AT HATP-GATED AUTHORITY BOUNDARY — SYSTEM
EXECUTION CLOSURE DEFERRED. HATP production remains NOT READY. Runtime
remains `Observed/observe/unavailable`.

**Recommended next phase:** 149O.18B — HATP Mandatory Evidence
Consumption Adapter.
