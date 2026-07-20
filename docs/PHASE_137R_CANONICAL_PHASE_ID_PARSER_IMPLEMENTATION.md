# Phase 137R — Canonical Phase ID Parser Implementation

## Objective

Implement the canonical Phase ID parser defined by CPIPC-001 v1.0
(`docs/contracts/CANONICAL_PHASE_ID_PARSING_CONTRACT.md`) and migrate
every inventoried lifecycle consumer (CPIPC-001 §14) to the shared
implementation while preserving all externally observable behavior.
Implementation phase only — the architecture (137P) and contract (137Q)
are frozen; this phase does not redesign the grammar, reinterpret
comparison semantics, introduce new Phase ID forms, or expand lifecycle
behavior.

Runtime remained: State: Observed. Maximum Capability: observe.
Execution Availability: unavailable.

## Deliverable

`src/pcae/core/phase_id.py` — the canonical Phase ID parser. Exposes
`parse`, `is_valid`, `normalize`, `format`, `validate`, `scan_tokens`,
`find_first_token`, `match_leading_token`, `equals`, `compare`,
`same_series`, `same_branch`, the immutable `PhaseId` value type, and
the closed `PhaseIdError`/`ErrorKind` taxonomy — implementing CPIPC-001
§4 (grammar), §5 (representation), §8 (API contract), §9 (parsing
semantics), §10 (comparison semantics), §11 (error taxonomy), and §16
(security requirements) verbatim from the frozen contract.

## Implementation summary

- **Grammar (CPIPC-001 §4)**: implemented as a single `fullmatch`-based
  regex derived directly from the frozen EBNF, with no narrower or
  wider acceptance than specified. Reserved forms (bare numeric series,
  leading-zero series) are recognized and rejected with their specific
  taxonomy kinds (`reserved_syntax`, `unsupported_syntax`) rather than
  a generic `invalid_syntax`.
- **Representation (CPIPC-001 §5)**: `PhaseId` is a frozen dataclass;
  `normalized_text`, `comparison_identity`, and `serialization_identity`
  are all properties derived from the same stored fields (never
  independently computed), satisfying CPIPC-REQ-016 structurally.
- **Comparison (CPIPC-001 §10)**: `compare` returns one of
  `less`/`greater`/`equal`/`not_comparable`; branch ordering uses
  spreadsheet-column rollover arithmetic (`_branch_rank`), not lexical
  string comparison; the exceptional (`"X"`) branch is excluded from
  mainline comparability; no artificial total ordering exists anywhere
  in the module (CPIPC-REQ-042).
- **Error taxonomy (CPIPC-001 §11)**: the nine closed kinds are a
  `Literal` type; `_classify_invalid` deterministically maps every
  rejected input to exactly one kind.
- **Security (CPIPC-001 §16)**: the module performs no filesystem,
  repository, network, or governance access; every public function is a
  pure function of its arguments; no module-level mutable state exists.

## Consumer migration

All ten CPIPC-001 §14 consumer groups (the fifteen originally
inventoried call sites) were migrated in this phase, with one
deliberate, documented exception. Full per-consumer disposition,
rationale, and the specific behavioral narrowings/widenings this
migration necessarily introduces are recorded in
`docs/CANONICAL_PHASE_ID_PARSER_MIGRATION.md`.

Summary:

- **Migrated (9 of 10 groups, all fifteen call sites except the
  deferred one)**: `core/phase_reports.py` (title extraction,
  commit-subject scanning, `is_phase_id_backward`, `_is_milestone_phase_id`),
  `core/check.py`, `core/architecture_status.py`, `core/context.py`,
  `core/agent.py` (both `_TSA_*` and `_SIT_*`), `cltr_prototype/identity.py`,
  `cltr_prototype/compatibility.py`, `commands/phase.py` (queue
  validation and commit-range expansion), `commands/push.py`,
  `core/repository_transition_integration.py` — including the one
  consumer CPIPC-001 §13 flagged as still carrying the unrepaired
  truncation defect at contract-freeze time.
- **Deliberately deferred**: `cltr/authority/identity.PhaseIdentity` —
  an opaque wire-format/charset boundary type bound to
  `identity.schema.json`, not a Phase ID structural grammar; Phase
  137P §15's own "charset-reservation risk" remains open and is not
  resolved by this phase. See the migration record for full rationale.
- **Duplicate definitions removed outright** (CPIPC-REQ-052, not
  deprecated or shimmed): `check._PHASE_CODE_RE` /
  `agent._TSA_PHASE_CODE_RE` (the exact-duplicate pair Phase 137P
  named) and every other module-level Phase ID regex in the migrated
  set.

## Regression tests

`tests/test_phase_id.py` — 62 tests covering: every historically valid
Phase ID form (§4.1 union), reserved and invalid forms with exact error
kind assertions, case-insensitivity and normalization, the canonical
representation's field semantics, comparison semantics (numeric
subphase ordering, branch rollover including the non-lexical `AA > B`
rollover case, exceptional-branch exclusion, no-artificial-total-
ordering), token scanning, and dedicated historical regression tests
replaying the specific truncation defects this contract exists to
foreclose (137F.1V, 137MV.1, the `repository_transition_integration.py`
sibling, and the 113X.3 branch-comparison defect).

Existing tests that asserted internals of a since-removed local regex
(`_CANONICAL_TITLE_PHASE_ID_RE`, `_COMMIT_SUBJECT_PHASE_TOKEN_RE`) were
updated to assert the equivalent behavior of the still-public extraction
functions instead of a private, now-retired regex object. One legacy
test that asserted the pre-migration single-letter subphase-suffix cap
was updated to assert the CPIPC-001-mandated widening instead, with an
explanatory comment.

## Validation

- `python -m pytest -n auto` (full suite): passed, with exactly one
  pre-existing, unrelated failure confirmed present on unmodified `main`
  via `git stash` before any 137R changes were applied
  (`TestPhase128B1NotificationDispatchReliabilityRepair::test_public_reconciliation_requires_report_marker_checkpoint_and_receipt`).
- `pcae health`, `pcae check`, `pcae doctor task-memory`, `pcae push
  check`: all clean.
- Runtime confirmed unchanged: Observed / observe / unavailable
  throughout.

## Non-Goals (restated, honored)

This phase did not: modify the grammar, modify CPIPC-001, expand CLI
behavior, change lifecycle semantics, change governance, change runtime
capability, introduce parser heuristics, or introduce consumer-specific
parsing. `cltr/authority/identity.PhaseIdentity` and the residual
`phase_reports.py` regexes outside CPIPC-001 §14's formal inventory
(documented in the migration record) remain open for a future governed
phase.

## Recommended Next Phase

**137S — Canonical Phase ID Parser Independent Verification**

Purpose: treat the implementation as untrusted. Independently derive
parser behavior solely from CPIPC-001 v1.0, verify every migrated
consumer, confirm elimination of duplicated parser ownership (except
the one documented, deliberate exception), replay all historical parser
defects, validate complete backward compatibility across historical
Phase IDs, and determine whether the canonical parser fully satisfies
the frozen contract without introducing lifecycle regressions.
