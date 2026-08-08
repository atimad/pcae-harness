# Phase 149O.18C Complete — AG3 Mandatory Consumption Integration

**Phase ID:** 149O.18C
**Mode:** implementation (bounded — Wave C of the 149O.17 plan; AG3 effect-boundary wiring plus one narrow, classified 18A correction)
**Predecessor:** 149O.18B (HATP Mandatory Evidence Consumption Adapter — completed, VERDICT: HATP MANDATORY EVIDENCE CONSUMPTION ADAPTER: IMPLEMENTED — READY FOR 149O.18C)
**Date:** 2026-08-08
**Status:** completed
**Verdict:** AG3 MANDATORY HATP CONSUMPTION INTEGRATION: IMPLEMENTED — READY FOR 149O.18D
**Commits:** 330df82f, 67a05cc1, 98387f08
**Pushed:** pending
**origin/main..HEAD:** 3
**Metadata consistency:** consistent

This is the lightweight staging header for `pcae phase complete`. The
full document
(`docs/PHASE_149O_18C_AG3_MANDATORY_CONSUMPTION_INTEGRATION.md`) is the
canonical artifact of this phase. Confirmed baseline: repo clean,
`origin/main..HEAD=0`, 149O.18B complete, `HMRC-001 v1.0` `VERIFIED WITH
NON-BLOCKING FINDINGS — CONFORMS`, HATP production NOT READY, runtime
`Observed/observe/unavailable`. Read `HMRC-001`, the 149O.18A/18B phase
documents, and `execute_rollback` in full, independently re-inventoried
every production caller (exactly one: `commands/agent.py:2238`).

Wired 149O.18A's fresh `resolve_production_hatp_cutover_mode` and
149O.18B's real-effect `evaluate_for_real_effect` into
`execute_rollback`'s Mandatory Consumption Boundary, immediately before
`_run_git_revert` (HMRC-REQ-066). The legacy `rollback_approval_state`
gate is skipped entirely once `HATP_MANDATORY` applies (zero authority
post-cutover, HMRC-REQ-061 — no residual legacy-AND-HATP requirement,
proven by an unapproved job still reaching effect given a deterministic
HMRC ALLOW); `LEGACY_COMPATIBLE`/`PREPARED` dispatch is byte-identical
to before. In `HATP_MANDATORY`, the boundary requires an explicit
`hatp_evidence_id`, calls `evaluate_for_real_effect` (never
`evaluate_for_advisory`), and requires `pb_decision == DECISION_ALLOW`;
missing evidence, PB `DENY`/`HUMAN_REVIEW`, raw-hook parameters, and a
direct-function-call bypass all fail closed with zero effect. Mode is
read fresh twice per attempt, never cached.

**Classified defect and narrow correction (§5 of the phase document):**
wiring the unmodified 149O.18A resolver exactly as specified regressed 8
pre-existing `tests/test_agent.py -k rollback` tests, because this real
deployment (and any deployment lacking `.pcae/repository-identity.json`)
has no local repository identity, and `_resolve_cutover_mode_at_root`
unconditionally failed closed to `HATP_MANDATORY` on identity-absence —
before ever consulting the protected root's Cutover Record or marker —
contradicting HMRC-REQ-032's explicit `LEGACY_COMPATIBLE` default for
every existing deployment, including the current local development
host. Classified as a narrow, proven API defect (HMRC-REQ-045's schema
itself requires `repository_instance_id` to exist at record-write time,
so identity-absence plus zero protected-root activation evidence is
unambiguous first-install proof) and corrected with a single-hunk
change reusing the existing, unmodified record/marker readers — only
the doubly-absent case changes outcome; the security-critical branch
(identity deletion cannot escape a genuinely activated deployment) is
unchanged and re-verified by dedicated tests. Also fixed two pre-
existing, never-previously-exercised `read_git_branch(str(root.path))`
type-mismatch bugs inside `execute_rollback`'s own Wave-7 (149O.6)
advisory block and this phase's new gate, discovered while building
tests that, for the first time, supply `hatp_evidence_id`.

Authored 44 new tests (20 behavioral + 24 phase-specific), plus one
stale 18A-suite assertion replaced and two new security-property tests
added, all added to Fast Green. Ran a full HMRC/HATP/rollback/PB
regression sweep; via a `git stash`-based A/B baseline comparison,
independently attributed every resulting failure to either a
pre-existing, unrelated cause, or the necessary, mechanical
"no `src/pcae/` diff since my own baseline" snapshot-assertion
consequence this phase's own production diff produces (documented
identically by 18A/18B for themselves). No AG3/AG5/rollback/
Permission-Broker behavioral regression found. Fast Green with the 12
attributed items deselected: **5358 passed, 0 failed, 1 skipped** (raw
undeselected: 5358 passed, 12 failed, 1 skipped).

No AG5 mandatory-consumption integration, no `--hatp-evidence-id` CLI
plumbing, no legacy `approve`-command change, and no Permission
Broker/POL-005 change was made. HMRC-001 v1.0 and all six upstream
contracts remain byte-unchanged; `hatp_rollback_consumption.py`
(149O.18B) remains byte-unchanged. No real Cutover Record or
`HATP_MANDATORY` activation occurred. B-149O-1..4 remain
INDEPENDENTLY VERIFIED AT HATP-GATED AUTHORITY BOUNDARY — SYSTEM
EXECUTION CLOSURE DEFERRED. HATP production remains NOT READY. Runtime
remains `Observed/observe/unavailable`.

**Recommended next phase:** 149O.18D — AG5 Mandatory Consumption
Integration.
