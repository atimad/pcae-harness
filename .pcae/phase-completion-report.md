# Phase 149O.18E Complete — CLI + Legacy Authority Migration Integration

**Phase ID:** 149O.18E
**Mode:** implementation (bounded — Wave E of the 149O.17 plan; AG3/AG5 CLI evidence-ID transport plus legacy-approve cutover-mode migration)
**Predecessor:** 149O.18D (AG5 Mandatory Consumption Integration — completed, VERDICT: AG5 MANDATORY HATP CONSUMPTION INTEGRATION: IMPLEMENTED — READY FOR 149O.18E)
**Date:** 2026-08-08
**Status:** completed
**Verdict:** CLI + LEGACY AUTHORITY MIGRATION INTEGRATION: IMPLEMENTED — READY FOR 149O.18F
**Commits:** 8fc4b679, a4945208, 76cd8309
**Pushed:** pending
**origin/main..HEAD:** 3
**Metadata consistency:** consistent

This is the lightweight staging header for `pcae phase complete`. The
full document
(`docs/PHASE_149O_18E_CLI_LEGACY_AUTHORITY_MIGRATION_INTEGRATION.md`) is
the canonical artifact of this phase. Confirmed baseline: repo clean,
`origin/main..HEAD=0`, 149O.18D complete, `HMRC-001 v1.0` `VERIFIED WITH
NON-BLOCKING FINDINGS — CONFORMS`, HATP production NOT READY, runtime
`Observed/observe/unavailable`. Read `HMRC-001` §6-8/20/22, the
149O.17 plan's Wave-E decomposition, and the 149O.18C/18D phase
documents (both explicitly deferred `--hatp-evidence-id` CLI
registration to this phase), and the exact pre-phase argparse
registration/handler bodies for `pcae remote rollback execute`,
`pcae rollback`, and `pcae remote rollback approve`, independently
re-inventorying every production caller of `approve_rollback` (exactly
one: `commands/agent.py`'s `run_remote_rollback_approve`).

Registered `--hatp-evidence-id` on the AG3 (`pcae remote rollback
execute`) and AG5 (`pcae rollback --per-id`) CLI surfaces, transporting
exactly one neutral locator into `execute_rollback`/
`build_rollback_execution`'s existing `hatp_evidence_id` keyword — both
effect functions were already wired by 18C/18D but unreachable from any
CLI path pre-phase; their own bodies are byte-unchanged, only their
`commands/agent.py` callers changed. Made `pcae remote rollback approve`
cutover-mode-aware inside `approve_rollback` itself (`core/agent.py`,
the sole production-reachable mutation boundary, mirroring AG3/AG5's own
direct-call-bypass-prevention discipline): unchanged under
`LEGACY_COMPATIBLE` (HMRC-REQ-057), unchanged plus a non-authoritative
`deprecation_warning` dict key under `PREPARED` (HMRC-REQ-058), and a
deterministic `ValueError` refusal with zero mutation under
`HATP_MANDATORY` (HMRC-REQ-059) — mode is resolved fresh on every call,
immediately before the mutation line, with no cache and no earlier read
to grow stale.

`approve_rollback` never consumes HATP evidence and never evaluates
Permission Broker in any mode; `rollback_approval_state` is retained as
historical/migration metadata, never deleted. AG5's `--dry-run`
continues to require zero evidence in every mode (18D's dry-run early
return is untouched). No raw proof/evidence/envelope CLI flag, caller
authority boolean, mode override, PB override, or provider/trust-store
override flag exists on any of the three parsers this phase touches
(confirmed by a parametrized forbidden-flag test suite across 28
forbidden flags). No implicit/auto-selected evidence lookup exists.

Authored 144 new tests across two files (120 in
`tests/test_hatp_cli_migration.py`, 24 in
`tests/test_phase_149o_18e_cli_legacy_authority_migration_integration.py`),
all added to Fast Green. Narrowly updated two historical 149O.8 snapshot
assertions legitimately invalidated by this phase's own stated purpose
(same narrowing precedent 149O.12C already set): the raw-proof/envelope
CLI-absence check (narrowed — the neutral evidence-ID transport this
contract always intended 18E to add is not a raw proof/envelope
surface) and the `approve_rollback`-never-references-HATP check
(narrowed — cutover-mode awareness is not evidence consumption or PB
evaluation, both of which `approve_rollback` still never performs).
Both updated tests pass; underlying invariants unweakened.

Ran a full regression sweep (`tests/test_agent.py -k rollback`: 78/78
passed, byte-identical AG3/AG5/legacy-approve behavior; `pytest -m
fast_green` A/B-diffed via `git stash` against the clean 149O.18D
baseline: 16 pre-existing failures unrelated to this phase, confirmed
identical with and without this phase's changes; exactly 17
newly-invalidated, every one the identical mechanical "no
`src/pcae/{cli.py,commands/agent.py,core/agent.py}` diff since my own
baseline" or "`--hatp-evidence-id` flag/kwarg does not exist yet"
snapshot pattern every prior phase whose own regression suite checks a
working-tree diff against its own frozen historical commit necessarily
carries whenever a later phase touches those files — no AG3/AG5/
legacy-approve/Permission-Broker behavioral regression found anywhere in
the sweep). Fast Green with the 33 attributed items deselected: **5324
passed, 0 failed, 2 skipped** (raw undeselected: 5324 passed, 33 failed,
2 skipped).

No Permission Broker/POL-005 change, no COMP-002, no real Cutover Record
or `HATP_MANDATORY` activation occurred. HMRC-001 v1.0 and all six
upstream contracts remain byte-unchanged; `hatp_mandatory_cutover.py`
(149O.18A), `hatp_rollback_consumption.py` (149O.18B), and
`execute_rollback`/`build_rollback_execution`'s own bodies (149O.18C/
18D) remain byte-unchanged. B-149O-1..4 remain INDEPENDENTLY VERIFIED AT
HATP-GATED AUTHORITY BOUNDARY — SYSTEM EXECUTION CLOSURE DEFERRED. HATP
production remains NOT READY. Runtime remains
`Observed/observe/unavailable`.

**Recommended next phase:** 149O.18F — HMRC Assembled Attack Matrix +
Activation Guard.
