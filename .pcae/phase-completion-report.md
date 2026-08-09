# Phase 149O.18F Complete — HMRC Assembled Attack Matrix + Activation Guard

**Phase ID:** 149O.18F
**Mode:** implementation (bounded — Wave F of the 149O.17 plan; final assembly/hardening of HMRC-001, depending on Waves A-E)
**Predecessor:** 149O.18E (CLI + Legacy Authority Migration Integration — completed, VERDICT: CLI + LEGACY AUTHORITY MIGRATION INTEGRATION: IMPLEMENTED — READY FOR 149O.18F)
**Date:** 2026-08-09
**Status:** completed
**Verdict:** HMRC-001 MANDATORY PRODUCTION CONSUMPTION: ASSEMBLED IMPLEMENTATION COMPLETE — READY FOR INDEPENDENT IMPLEMENTATION VERIFICATION. 149O.18F: IMPLEMENTED — READY FOR 149O.19.
**Commits:** 861fb04f, fa7d3a99, d13819b8, e1727c27
**Pushed:** pending
**origin/main..HEAD:** 4
**Metadata consistency:** consistent

This is the lightweight staging header for `pcae phase complete`. The
full document
(`docs/PHASE_149O_18F_HMRC_ASSEMBLED_ATTACK_MATRIX_ACTIVATION_GUARD.md`)
is the canonical artifact of this phase. Confirmed baseline: repo clean,
`origin/main..HEAD=0`, 149O.18E complete, `HMRC-001 v1.0` `VERIFIED WITH
NON-BLOCKING FINDINGS — CONFORMS`, HATP production NOT READY, runtime
`Observed/observe/unavailable`. Read `HMRC-001` in full (independently
re-extracted all 85 requirements, 14 invariants, and the 45-scenario
§29 attack matrix directly from contract text), the remainder of the
149O.17 plan, all five 18A-18E phase documents, and the actual current
production code for every module named in the phase brief.

Implemented the HMRC-REQ-054/055 activation-readiness/activation-guard
additions to `src/pcae/core/hatp_mandatory_cutover.py` — additive-only,
the sole production file touched: `assess_hatp_mandatory_activation_
readiness` (sole production readiness entrypoint, resolves the protected
root/repository identity internally, no cache, no caller override,
evaluates HMRC-REQ-054's exact six-item conjunction — Class-B protected
storage, repository identity, HATP substrate operational, HSCE signing
availability, mandatory-consumption-implementation-independently-
verified [always unmet pre-149O.19, by design], production dependency
provenance, Protected Activation Authority mechanism — deliberately
never touching PB/MC-14 per HMRC-REQ-055's explicit non-requirement) and
`activate_hatp_mandatory` (sole production activation entrypoint,
structurally `PREPARED -> HATP_MANDATORY` only, fresh lock-held
readiness re-check immediately before write, no caller-supplied
readiness/force/mode/PB-decision override anywhere). No application-
level `ProtectedAdminPrincipal` was invented — 149O.18A's documented
OS-level protected-root file-permission-boundary decision is reused
unchanged, and the new activation function is never called from
`cli.py`/`commands/agent.py`/`core/agent.py` (AST-confirmed).

Independently re-extracted and mechanically represented all 45
HMRC-001 §29 attack scenarios against the real, assembled A-F
production code — all 45 pass, zero bypass found, current real POL-005
`DENY` + zero effect confirmed for both AG3 and AG5 against the
unmodified dependency chain (no test seam). 69 new tests across three
files, all added to Fast Green. A first regression pass surfaced two
genuine defects in this phase's own first-draft readiness code (a raw
`HATPTrustStore(...)` constructor call and an unlisted `inspect_hatp_
verification_substrate_readiness` caller, both violating pre-existing
dependency-closure boundaries) — repaired properly by threading an
already-resolved `trust_store` object through instead of reconstructing
one internally. Updated eleven historical phase-boundary snapshot
assertions across six files per the established 149O.5-F-3 methodology
(each pinned to its own historical phase's frozen commit range rather
than an open-ended `HEAD` comparison, since this phase's additive
extension necessarily and correctly invalidated their prior "byte-
unchanged since my baseline, forever" assumption).

Ran a full A/B-attributed regression sweep via an isolated `git
worktree` at the pre-149O.18F commit (`0881346a`): broad HMRC/HATP/RAE/
PB sweep baseline 156 failed/4405 passed vs. final 154 failed/4476
passed (zero new failures, exact failing-test-name diff, exactly 2
pre-existing 149O.18A stale assertions fixed); Fast Green baseline 30
failed/5389 passed vs. final **28 failed/5460 passed/1 skipped** (zero
new failures, same 2 fixed) — the value recorded in this phase's
structured `fast_green` metadata field.

No `HMRC-001`/`HSCE-001`/`HATP-001`/`RAE-001`/`RWMPC-001`/`PBPA-001`/
`PBPC-001` contract change. No Permission Broker/POL-005 change. No
COMP-002 capability implemented. No real Class-B provisioning. No real
`HATP_MANDATORY` activation occurred anywhere. No production Cutover
Record or activation marker created. Current deployment remains
non-mandatory; runtime remains `Observed/observe/unavailable`.
`assess_hatp_mandatory_activation_readiness` against the real production
root on this host returns `ready=False` (no provisioned Class-B
protected root; 149O.19 independent verification not yet performed).
B-149O-1..4 remain **INDEPENDENTLY VERIFIED AT THE HATP-GATED AUTHORITY
BOUNDARY — SYSTEM EXECUTION CLOSURE DEFERRED**, unchanged and not
self-closed by this phase.

**Verdict:** `HMRC-001 MANDATORY PRODUCTION CONSUMPTION: ASSEMBLED
IMPLEMENTATION COMPLETE — READY FOR INDEPENDENT IMPLEMENTATION
VERIFICATION` / `149O.18F: IMPLEMENTED — READY FOR 149O.19`. Not
"VERIFIED" — independent verification is 149O.19's own obligation.

**Recommended next phase:** 149O.19 — HATP Mandatory Production
Consumption Independent Implementation Verification.
