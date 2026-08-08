# Phase 149O.12C Complete — HATP Signing CLI Integration + Full HSCE Attack-Matrix Implementation

**Phase ID:** 149O.12C
**Mode:** implementation (bounded production implementation — Wave E + Wave F of the 149O.11 plan; no signing-core semantics change, no evidence-model/store semantics change, no rollback command change, no mandatory AG3/AG5 consumption, no Permission Broker change, no Class-B provisioning, no production activation)
**Predecessor:** 149O.12B (HATP Signing Ceremony Resolver + Orchestrator Implementation — completed, pushed, HATP SIGNING CEREMONY RESOLVER + ORCHESTRATOR: IMPLEMENTED — READY FOR 149O.12C, recommended 149O.12C next)
**Date:** 2026-08-08
**Status:** completed
**Verdict:** HATP SIGNING CLI + HSCE ASSEMBLED IMPLEMENTATION: IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION
**Commits:** 478e49c9, f5c5b42a, 68e6e0b0
**Pushed:** pending
**origin/main..HEAD:** 3
**Metadata consistency:** consistent

This is the lightweight staging header for `pcae phase complete`. The
full document
(`docs/PHASE_149O_12C_HATP_SIGNING_CLI_INTEGRATION_FULL_HSCE_ATTACK_MATRIX_IMPLEMENTATION.md`)
is the canonical artifact of this phase. Implemented exactly two
production changes per the 149O.11 plan's own allowlist:
`src/pcae/commands/hatp.py` (NEW) — the `pcae hatp sign rollback --site
{ag3|ag5} (--job-id|--per-id) [--json]` CLI handler, calling only the
zero-override `production_sign_rollback_evidence` (never the injectable
`sign_rollback_evidence`), a centralized closed 12-member
`error_type` → 9-category exit-code mapping, and human/JSON output with
no authority-claiming field anywhere; and `src/pcae/cli.py` (MODIFY,
registration-only, a pure addition — zero lines removed, independently
confirmed via `git diff --numstat`). 103 new tests across 2 files, all
passing: 78 grammar/forbidden-flag/zero-override/help/error-mapping
tests (`tests/test_hatp_cli.py`) plus 25 tests covering all 21 mandatory
HSCE attacks and 4 extra implementation attacks through the fully
assembled CLI handler (`tests/test_phase_149o_12c_hsce_attack_matrix.py`).
Production diff exactly the two planned files, zero unrelated hunks;
HSCE-001 v1.1, HATP-001 v1.0, RAE-001 v1.0, and 149O.12A/149O.12B's
three core modules all remain byte-unchanged. Six pre-existing
phase-boundary test files' stale "no HATP CLI exists yet" snapshots
widened/inverted/narrowed per the established 149O.5-F-3 precedent, with
every other invariant those files protect left unchanged. Full
`hatp`/`rollback_approval` sweep shows exactly 13 pre-existing, unrelated
failures (down from a 15-failure raw baseline, since two were themselves
fixed by this phase's own 149O.5-F-3 widening — independently
reconfirmed via a `git stash -u` baseline comparison); rollback/PB
focused sweep and `test_agent.py`'s rollback subset show no new
failures — no rollback dispatch behavior changed. Report-trust suite:
272 passed, 0 failed. Fast Green 4868 passed, 2 skipped, 0 genuine
failures (+40 over the 149O.12B baseline, matching exactly this phase's
own newly registered tests). The 149O.12B Python-3.9
`_parse_timestamp` defect was reconfirmed still present, still
out-of-scope, worked around only at the test layer (duplicated, not
imported, autouse fixture), no production file touched. This completes
the full six-wave 149O.11 decomposition — HSCE Signing Ceremony +
Evidence Store Implementation is now COMPLETE at the
model/store/resolver/orchestrator/CLI level; production rollback
consumption, execution enforcement, and HATP production activation
remain explicitly NOT complete/NOT READY. No AG3/AG5 mandatory
consumption wiring, no rollback dispatch change, no Permission Broker
change, no hardware touch outside this phase's own deterministic tests,
no automatic `.pcae/hatp-evidence/` consumption. Recommended next phase:
149O.13, HATP Signing Ceremony + Evidence Store Independent
Implementation Verification.
