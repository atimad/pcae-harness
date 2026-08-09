# Phase 149O.19.4 Complete — HATP Mandatory Independent-Verification Certification Implementation Plan

**Phase ID:** 149O.19.4
**Mode:** implementation plan only (no `src/pcae/**` file modified; no contract file modified)
**Predecessor:** 149O.19.3R.1 (HMIC Frozen Implementation Identity Contract Repair Independent Re-Verification — completed, B-149O.19.3-1 INDEPENDENTLY CONFIRMED CLOSED, HMIC-001 v1.0 CONFORMS)
**Date:** 2026-08-09
**Status:** completed
**Plan verdict:** `HMIC-001 IMPLEMENTATION PLAN: COMPLETE — READY FOR BOUNDED IMPLEMENTATION`
**Commits:** 5e491c5a169d2477761d3e3dfa76b37c4d163ca2
**Pushed:** pending
**origin/main..HEAD:** 4
**Metadata consistency:** consistent

This is the lightweight staging header for `pcae phase complete`. The
full document
(`docs/PHASE_149O_19_4_HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_IMPLEMENTATION_PLAN.md`)
is the canonical artifact of this phase. Confirmed baseline: repo
clean, `origin/main..HEAD=0` at entry, 149O.19.3R.1 completed/complete
at `19ed7cab`, HMIC-001 status `FROZEN — REPAIRED, INDEPENDENTLY
RE-VERIFIED`, B-149O.19.3-1 INDEPENDENTLY CONFIRMED CLOSED, hardcoded
`False` readiness ceiling unchanged, HATP production NOT READY, runtime
`Observed/observe/unavailable`.

Read the full live HMIC-001 v1.0 contract text directly — not trusting
any prior phase's own tables — and mechanically extracted all 144
`HMIC-REQ` requirements, 12 `CIVC` invariants, and 32 attack scenarios,
mapping every one to a concrete production owner, failure/behavior,
test owner, and implementation wave.

**Selected module architecture:** one new core module,
`src/pcae/core/hatp_mandatory_certification.py` (data model + canonical
parsing — Wave A; implementation/repository/deployment/contract
identity derivation — Wave B; protected store + locking — Wave C;
validation engine — Wave D), mirroring `hatp_mandatory_cutover.py`'s own
monolithic single-module precedent; plus a separate, non-agent-reachable
admin script, `scripts/hatp_certification_admin.py` (create/activate/
revoke ceremony — Wave E), never imported by `cli.py`/`commands/
agent.py`. `hatp_mandatory_cutover.py`'s `False`-to-validator wiring is
isolated to a single, later-gated Wave F.

**Self-reference/circularity resolved, not deferred again:** the
future HMIC validator's own module must itself join the frozen
implementation-identity set — `hatp_mandatory_cutover.py` is already
item 1 of HMIC-REQ-050's 22-file set, establishing exactly this
precedent. This plan introduces explicit **Stop Condition W-1**: Wave F
(the `False`→validator wiring) SHALL NOT begin until a dedicated
HMIC-001 v1.1 contract-amendment phase adds `hatp_mandatory_
certification.py` to the frozen file set and that amendment is itself
independently verified. Waves A-E and G are unaffected by this gate.
Separately proved the admin writer does **not** need frozen-set
protection: the validation algorithm's steps 9-11 always re-derive
implementation identity/contract versions/certification-id fresh and
compare against the stored record rather than trusting it, so a
compromised writer can at worst produce a record that fails to
validate.

**Full traceability achieved:** 144/144 requirements, 12/12 invariants,
32/32 attacks — every row carries a concrete owner, test owner, and
wave; no authority-sensitive TBD remains.

**Added a new 20-test planning-completeness suite**
(`tests/test_phase_149o_19_4_hmic_implementation_plan_completeness.py`)
that mechanically re-extracts the 144/12/32 counts directly from
HMIC-001's live contract text — not from this plan's own prose — and
cross-checks the plan document's tables against them; verifies every
row has a non-empty owner/test-owner/wave; verifies the file-ownership
matrix and Stop Condition W-1 text are present; and independently
confirms, via two separate `git diff` extraction methods, that no
`src/pcae/**` file and none of the 8 upstream contracts changed. **20
passed, 0 failed.**

Ran full Fast Green under the repository's virtualenv
(`.venv/bin/python`): **28 failed/5592 passed/1 skipped** before this
phase's new test file existed (reproduced via `git stash -u` A/B);
**5612 passed/0 failed/1 skipped** with the 28 pre-existing failures
deselected. Identical 28 named pre-existing/unrelated failures in both
runs (older `149O.13`–`149O.18*`-phase byte-diff/file-allowlist tests
anchored to their own historical baselines, none referencing HMIC-001);
passed count increased by exactly 20, matching this phase's new suite
exactly, zero new failures introduced.

No `src/pcae/**` file was modified. No contract file (`HMIC-001` or any
of `HMRC-001`/`HATP-001`/`HSCE-001`/`RAE-001`/`RWMPC-001`/`PBPA-001`/
`PBPC-001`) was modified — all remain byte-unchanged (independently
verified by `git diff --name-only`/`--name-status` against this phase's
own entry commit `11d7c616`). No Permission Broker/`POL-005` change. No
`COMP-002` capability implemented. No certification artifact,
active-certification pointer, or revocation record created anywhere in
the repository. No Cutover Record or activation marker created or
modified. No real Class-B provisioning. No real `HATP_MANDATORY`
activation occurred anywhere.

**B-149O.19.3-1 (unchanged, carried forward):** remains INDEPENDENTLY
CONFIRMED CLOSED. This planning phase does not reopen or alter it.

**B-149O-1..4 verdict (unchanged, carried forward):**
**INDEPENDENTLY CONFIRMED CLOSED AT SYSTEM IMPLEMENTATION/ENFORCEMENT
BOUNDARY — DEPLOYMENT/OPERATIONAL ACTIVATION DEFERRED.** This
implementation-plan-only phase does not reopen or alter this finding.

**Plan verdict:** `HMIC-001 IMPLEMENTATION PLAN: COMPLETE — READY FOR
BOUNDED IMPLEMENTATION`.

**Recommended next phase:** `149O.19.5A` — HMIC Certification Data
Models + Canonical Parsing (first bounded implementation wave). This
plan does not authorize `149O.19.5B`–`G` in advance, and Wave F is
additionally gated on Stop Condition W-1 clearing first.
