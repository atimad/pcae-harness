# Phase 135O Complete — Shared Transition Input and Dual-Derivation Implementation

## Phase identity

- Phase ID: `135O`
- Status: completed
- Classification: production implementation (Stage 1 — Dual Derivation, Legacy Authority)
- Verdict: **STAGE 1 IMPLEMENTED, LEGACY AUTHORITY PRESERVED, ZERO PRODUCTION AUTHORITY CHANGE**
- Report completeness: complete

## Summary

Phase 135O implements Stage 1 of the verified 135M/135N migration
contract. A new `src/pcae/cltr/migration/` package provides: one shared,
immutable transition-input package assembled at exactly the two capture
points 135M §8.4 binds (pre-transaction facts; legacy-completion
enrichment, at the same point `_observe_shadow_cltr` already occupies)
— a disclosed fidelity decision rather than the phase brief's
illustrative four-way Stage A/B/C/D split, documented in
`enums.InputStage`'s docstring; a design-B independent `transition_id`
(UUID4, retry-stable via a durable per-`(phase_id, entry_point)`
logical-key registry, never colliding with `phase_id`); a
dual-derivation coordinator running the existing legacy path and the
existing, unmodified production CLTR package (schema v1.0.1, all 37
invariants, all 15 representation adapters) against the same shared
input; deterministic comparison across all 18 of 135M §12's wire result
classes; migration-evidence persistence in a dedicated
non-authoritative namespace (`.pcae/cltr-migration/`); and two strictly
read-only CLI surfaces (`pcae cltr migration status` /
`reconcile --phase-id`). Integrated through the one shared
`run_finalization_transaction()` boundary all four production entry
points already funnel through, at two new, entry-point-agnostic call
sites; no entry-point file itself was modified.

Stage 1 is disabled by default. Legacy lifecycle remains the sole
production authority throughout — no code path, flag, or flag
combination this phase's code can construct resolves
`production_authority` to `CLTR`.

## Evidence and validation

- Governed phase commit: `a7f9f094` (30 files: the new
  `src/pcae/cltr/migration/` package (14 modules), `src/pcae/commands/
  cltr_migration.py`, the `pcae cltr migration` CLI registration in
  `cli.py`, two new call sites in `finalization_transaction.py`, one new
  autouse env-isolation fixture in `tests/conftest.py`, 7 new test files
  totaling 77 tests, the phase documentation, `PROJECT_STATUS.md`,
  `CHANGELOG.md`, and task-contract bookkeeping).
- 77/77 new focused migration tests passed
  (`tests/test_cltr_migration_config.py`,
  `test_cltr_migration_transition_identity.py`,
  `test_cltr_migration_shared_input.py`,
  `test_cltr_migration_derivation.py`,
  `test_cltr_migration_coordinator.py`,
  `test_cltr_migration_cli.py`,
  `test_cltr_135o_integration.py`).
- 362/362 combined CLTR + migration regression
  (`python -m pytest tests/test_cltr_*.py -q`: 285 pre-existing,
  unmodified tests + 77 new).
- 117/117 affected finalization regression
  (`test_finalization_transaction_134e10`, `test_finalization_gate_enforcement`,
  `test_finalization_notification_guarantee`,
  `test_finalization_configuration_identity_cross_agent_134b3`,
  `test_phase_113v_n_notification_finalization_repair`).
- Fast Green: 4391/4391 — unchanged from the pre-phase baseline,
  confirmed via `--collect-only` before and after this phase's changes.
- Full suite: 39 pre-existing-task-contract-scope failures resolved by
  opening this phase's own task contract with matching `--allowed-file`
  patterns; re-running the 10 affected files after opening the contract:
  680/685 passed, with exactly 5 inherited failures confirmed unrelated
  to 135O (`test_bootstrap_todo_consistency` x2, `test_advisory_runtime_
  contract`/`architecture` x2, `test_rendering_134e5` x1 — none of the
  files these exercise were touched by this phase; the `src/pcae/advisory`
  directory dates to Phase 124E and `tasks/TODO.md` was last modified
  2026-07-13, before Phase 135J).
- No-go/execution-boundary tests: `subprocess.run`/`Popen`/`call` and
  `socket.socket` monkeypatched to raise across a full capture-to-evidence
  cycle; the cycle completes normally, proving no migration code path
  ever reaches them. Structural checks confirm zero `subprocess`/`socket`
  imports anywhere in `src/pcae/cltr/migration/`.
- `pcae health` healthy; `pcae check` passed; task memory clean; push
  check clean; runtime inspect Observed/observe/execution unavailable;
  Telegram outbound delivery configured, enabled, ready.

## Inherited finding dispositions

- **135N F-135N-2** (missing predecessor-transition-identity field) —
  **resolved**: `predecessor_transition_id` is now a first-class
  `PRE_TRANSACTION_FIELDS` entry.
- **135N F-135N-3** (135M §35 Git-attribution wording) — deferred,
  unchanged (135S editorial-hygiene scope, not implementation).
- **135L's 4 Non-Blocking findings** — individually dispositioned in
  full detail in
  `docs/PHASE_135_SHARED_TRANSITION_INPUT_AND_DUAL_DERIVATION_IMPLEMENTATION.md`
  §37. F-135L-2's `transition_id == phase_id` collision half is resolved
  by construction for migration evidence (design-B `transition_id` is
  never `phase_id`); its `adapter_sources`-unwired half remains, carried
  forward as N-135O-3.
- **135J's 4 Non-Blocking findings** — citation/prose-precision notes,
  not applicable to this implementation phase's scope.
- **New findings this phase**: N-135O-1 (`intended_transition`/
  `recovery_classification` intentionally excluded from cross-derivation
  comparison — genuinely distinct vocabularies), N-135O-2 (recovery
  classification is currently entry-point-derived, not scenario-specific),
  N-135O-3 (`adapter_sources` not yet wired into the migration
  coordinator, inherited from F-135L-2). None touch authority, recovery
  safety, or exactly-once correctness; full detail and required-future-phase
  disposition in the phase documentation §37-§38.

## Safety and no-go confirmation

Legacy lifecycle remains the sole production authority. CLTR remains
derivative. Dual derivation does not mean dual authority. No atomic
authoritative publication occurred. No authority cutover occurred. No
legacy authority was demoted or retired. Migration code never calls
production certification, promotion, notification dispatch, checkpoint,
marker, or receipt functions — verified structurally and by the full
no-go test suite. No production report, completion metadata, or
Architecture Status generation was changed. No CLTR generation was
published into the shadow store by migration code (avoiding two
competing "current" pointers for one transition). No production latest
pointer was changed. No execution capability, backend invocation, or
Telegram inbound capability was introduced. No raw git commit, raw git
push, force push, or hook bypass was used. CLTR-001, CLTR-SCHEMA-001
v1.0.1, PFN-001, and PFR-001 remain unchanged. Runtime remains Observed
/ observe / execution unavailable throughout. Phase 135P was not
started.

## Recommended next phase

Phase 135P — Shared Transition Input and Dual-Derivation Independent
Verification (not started). Per the phase brief's explicit instruction,
135P must independently re-derive and adversarially verify this Stage 1
implementation — particularly the two-capture-point simplification of
135M's Stage A/B/C/D framing, the entry-point-derived recovery
classification, and the unwired adapter sources — before any Stage 2
atomic-publication rehearsal work begins.
