# Phase 149O.18D Complete — AG5 Mandatory Consumption Integration

**Phase ID:** 149O.18D
**Mode:** implementation (bounded — Wave D of the 149O.17 plan; AG5 effect-boundary wiring, mirroring 149O.18C's AG3 wiring)
**Predecessor:** 149O.18C (AG3 Mandatory Consumption Integration — completed, VERDICT: AG3 MANDATORY HATP CONSUMPTION INTEGRATION: IMPLEMENTED — READY FOR 149O.18D)
**Date:** 2026-08-08
**Status:** completed
**Verdict:** AG5 MANDATORY HATP CONSUMPTION INTEGRATION: IMPLEMENTED — READY FOR 149O.18E
**Commits:** d2798a03, 92c5c783, 66b2a504, 8b3efba0
**Pushed:** pending
**origin/main..HEAD:** 4
**Metadata consistency:** consistent

This is the lightweight staging header for `pcae phase complete`. The
full document
(`docs/PHASE_149O_18D_AG5_MANDATORY_CONSUMPTION_INTEGRATION.md`) is the
canonical artifact of this phase. Confirmed baseline: repo clean,
`origin/main..HEAD=0`, 149O.18C complete, `HMRC-001 v1.0` `VERIFIED WITH
NON-BLOCKING FINDINGS — CONFORMS`, HATP production NOT READY, runtime
`Observed/observe/unavailable`. Read `HMRC-001`, the 149O.18A/18B/18C
phase documents, and `build_rollback_execution` in full, independently
re-inventoried every production caller (exactly one: `commands/agent.py`'s
`pcae rollback --per-id` dispatch site).

Wired 149O.18A's fresh `resolve_production_hatp_cutover_mode` and
149O.18B's real-effect `evaluate_for_real_effect` into
`build_rollback_execution`'s Mandatory Consumption Boundary, placed
after every existing structural precondition (PER eligibility, payload
availability, ECP lookup, in-progress conflict, divergence check, RER
record persistence, `dry_run` early return) and immediately before the
first real filesystem mutation. AG5 has no legacy human-approval gate at
all — unlike AG3, no legacy-skip branch or earlier non-authoritative
mode read was needed; a deterministic HMRC ALLOW plus structural
validity alone reaches effect in `HATP_MANDATORY`. The boundary requires
an explicit `hatp_evidence_id`, constructs an `Ag5RollbackApprovalContext`
(already defined by 149O.17/18B anticipating this phase, unmodified),
calls `evaluate_for_real_effect` (never `evaluate_for_advisory`), and
requires `pb_decision == DECISION_ALLOW`; missing/invalid evidence, PB
`DENY`/`HUMAN_REVIEW`, raw-hook parameters, a direct-function-call
bypass, and a stale/reused prior decision all fail closed with zero
mutation. `dry_run` never mutates and never requires evidence in any
mode. Mode is read fresh, once, immediately before the effect, never
cached.

**Pre-existing bug fix and schema addition (§5 of the phase document):**
fixed two pre-existing, never-previously-exercised
`read_git_branch(str(root.path))` type-mismatch bugs inside
`build_rollback_execution`'s own Wave-7 (149O.6) advisory block and this
phase's new gate — same category 149O.18C fixed for AG3, discovered
while building tests that, for the first time, supply
`hatp_evidence_id` to this function; corrected to `read_git_branch(root)`.
Also added one new terminal RER status, `aborted_hatp_mandatory_denied`,
to the existing closed `_RER_VALID_STATUSES` vocabulary, so a
mandatory-gate denial persists the record in a genuine terminal state
rather than stuck `in_progress`; pre-existing status values are
untouched.

Authored 48 new tests (22 behavioral + 26 phase-specific), all added to
Fast Green. Ran a full HMRC/HATP/RAE/PB regression sweep; via a
`git stash`-based A/B baseline comparison against the clean 149O.18C
state, independently attributed every resulting failure to either a
pre-existing, unrelated cause (37), the necessary, mechanical "no
`src/pcae/` diff since my own baseline" snapshot-assertion consequence
this phase's own production diff produces (9, documented identically by
18A/18B/18C for themselves), or one assertion (18C's own
`test_build_rollback_execution_source_unchanged_since_entry`) that is
legitimately and necessarily invalidated by this phase's own stated
purpose. No AG3/AG5/Permission-Broker behavioral regression found. Fast
Green with the 17 attributed items deselected: **5316 passed, 0 failed,
2 skipped** (raw undeselected: 5316 passed, 17 failed, 2 skipped).

No `--hatp-evidence-id` CLI plumbing, no legacy `approve`-command
change, and no Permission Broker/POL-005 change was made. HMRC-001 v1.0
and all six upstream contracts remain byte-unchanged; `hatp_mandatory_
cutover.py` (149O.18A), `hatp_rollback_consumption.py` (149O.18B), and
AG3's `execute_rollback` remain byte-unchanged. No real Cutover Record
or `HATP_MANDATORY` activation occurred. B-149O-1..4 remain
INDEPENDENTLY VERIFIED AT HATP-GATED AUTHORITY BOUNDARY — SYSTEM
EXECUTION CLOSURE DEFERRED. HATP production remains NOT READY. Runtime
remains `Observed/observe/unavailable`.

**Recommended next phase:** 149O.18E — CLI + Legacy Authority Migration
Integration.
