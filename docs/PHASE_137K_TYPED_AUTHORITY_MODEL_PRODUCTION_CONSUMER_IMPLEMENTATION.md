# Phase 137K — Typed Authority Model Production Consumer Implementation

## Status

Implementation complete. Governed by TAMPC-001 v1.0
(`docs/contracts/TYPED_AUTHORITY_MODEL_PRODUCTION_CONSUMPTION_CONTRACT.md`)
and IPTAMC-001 v1.0
(`docs/IMPLEMENTATION_PLAN_TYPED_AUTHORITY_MODEL_CONSUMER.md`).

## What was built

Exactly the two authorized production modules and one CLI registration:

- `src/pcae/cltr/authority_inspection.py` — orchestration. Public entry
  point `inspect_artifact_at_path(path, *, artifact_bytes, json_output=False)`.
  Returns `InspectionObservation | InspectionFailure`
  (`InspectionOutcome`). Owns Stage 3 resource resolution (via
  `pcae.schema_resources.cltr_cutover_root()`), manifest/registry
  verification, family/version/identity resolution, schema validation,
  typed-model construction, lossless round-trip check, immutable
  observation construction, and provenance assembly.
- `src/pcae/commands/authority_inspect.py` — CLI layer. Owns the Stage 1
  bounded artifact read (path existence/type/size/read checks), invocation
  of `inspect_artifact_at_path`, rendering (`--json` and fixed-field-order
  human text), and exit-code translation (`0` inspected, `1` any failure,
  argparse's own usage-error code `2` for CLI misuse).
- `src/pcae/cli.py` — new `authority` subparser group with exactly one
  subcommand, `inspect` (one required positional `path`, one optional
  `--json` flag), registered next to the existing `cltr` group.

No second consumer, no generic inspection framework, no repository
scanning, no authority/lifecycle mutation, no notification dispatch, no
network access. Runtime remains Observed / observe / unavailable
throughout — verified unchanged before/after (`tests/test_authority_inspect_137k.py::test_lifecycle_and_runtime_surfaces_unchanged_before_after`).

## Calling-convention decision (Section 5's open question)

`inspect_artifact_at_path` receives the CLI-supplied `path` (used only as
a display identity, never re-read) and the already-read `artifact_bytes`
as a required keyword-only parameter, plus the frozen, currently-inert
`json_output` keyword parameter (defaulted to `False` since the plan
established `iaap` need not use it). This keeps `authority_inspect.py` as
the exclusive filesystem-read owner for Stage 1 (TAMPC-REQ-021's ownership
split) while giving `authority_inspection.py` a pure, easily-unit-tested
function that never touches the filesystem itself beyond the package-owned
Stage 3 resource resolution.

## Deviation from the plan: immutability mechanism (TAMPC-REQ-078)

The plan's Section 9 called for both `frozen=True` *and* an explicit
`__setattr__`/`__delattr__` override "in addition to" `frozen=True`. Under
this repository's `.venv` (Python 3.9, confirmed via
`.venv/bin/python -c 'import sys; print(sys.executable); print(sys.prefix)'`),
`dataclasses` raises `TypeError: Cannot overwrite attribute __setattr__`
when a frozen dataclass's class body also defines `__setattr__` — the two
mechanisms are mutually exclusive in this Python version, not
complementary. `InspectionObservation` and `InspectionFailure` therefore
rely on `frozen=True` alone, which already raises
`dataclasses.FrozenInstanceError` on ordinary attribute
assignment/deletion via its own generated `__setattr__`/`__delattr__` —
satisfying TAMPC-REQ-078's actual requirement (ordinary mutation
rejected) without the redundant, Python-version-incompatible second
mechanism the plan assumed. The residual `object.__setattr__` bypass
remains exactly as documented and out of scope, unchanged from the plan.
Regression-covered:
`test_observation_ordinary_assignment_blocked`,
`test_observation_delattr_blocked`, `test_failure_ordinary_assignment_blocked`.

This is a documented, narrowly-justified implementation-detail deviation
from the plan's Section 9, not a TAMPC-001 contract deviation — TAMPC-REQ-078
itself only requires ordinary mutation to be rejected and explicitly
excludes the `object.__setattr__` bypass from its threat model.

## Regression repair: pre-137K import-guard tests updated (expected, contract-authorized)

The full-suite regression run surfaced 24 pre-existing test failures across
23 Stage 3 phase files (`tests/test_cltr_authority_136{z,aa,ab,ac,ad,af,ag,ah,ai,aj,ak,al,am,an,ao,ap,aq,ar,as,at,au,av}*.py`).
Each asserted "no production module imports `pcae.cltr.authority`" —
correct before 137K, since the only prior consumer was the
explicitly-non-production prototype in `prototypes/`. TAMPC-001 v1.0 and
the Phase 137G architecture explicitly authorize exactly one production
importer of that package: this phase's own
`src/pcae/cltr/authority_inspection.py` (and, transitively,
`src/pcae/commands/authority_inspect.py`, which imports from it). This is
the expected, designed-for consequence of building the first production
consumer, not a regression this phase introduced by defect.

Each of the 24 guard tests was updated with a narrow, explicitly-commented
exception listing exactly `authority_inspection.py` and
`authority_inspect.py` by filename — no broader relaxation, no wildcard,
no directory-level exemption. Every updated assertion still fails if any
*other* production module imports the authority package. Re-run after the
fix: all 24 pass
(`.venv/bin/python -m pytest tests/test_cltr_authority_136*.py -k "authority_package or authority_import or sibling_cltr" -q` → 36 passed, 1 skipped).

## Pre-existing, unrelated full-suite failures (reproduced against pre-137K baseline)

The remaining full-suite failures were independently reproduced with this
phase's changes stashed out (`git stash push -u -- <137K files>`), proving
they are not caused by this phase:

- `tests/test_advisory_runtime_contract.py::test_no_new_directory_added_for_advisory`
  and the equivalent in `test_advisory_runtime_architecture.py` — fails
  because `src/pcae/advisory/` already exists in this checkout,
  independent of 137K.
- `tests/test_cltr_authority_136ah_publication.py::test_136ah_wheel_contains_publication_module_no_later_family`
  and the equivalent "no_later_family" wheel-snapshot assertions in
  `136ag`/`136aj`/`136al`/`136am`/`136an`/`136ao`/`136ap`/`136aq`/`136z` —
  each is a point-in-time snapshot from its own original phase asserting
  the wheel does *not yet* contain record-family modules that later,
  unrelated Stage 3 phases (136ai onward) subsequently and legitimately
  added. Historical drift unrelated to 137K.
- `tests/test_finalization_transaction_134e10.py`,
  `tests/test_cltr_migration_135p_verification.py`,
  `tests/test_cltr_135o_integration.py` — fail identically with 137K's
  changes stashed out (`result.status == 'completed_receipt_best_effort_incomplete'`
  vs. expected `'completed'`), unrelated to this phase.
- `tests/test_permission_broker_observation_hardening.py::test_health_tests_still_pass`
  and its sibling in `test_permission_broker_observation_verification.py`
  — flaky, PATH-dependent: the test shells out to bare `python` (not
  `.venv/bin/python` or `sys.executable`), which in this environment
  resolves inconsistently to a Python 3.14 Homebrew interpreter lacking
  `jsonschema`. Confirmed to pass and fail on alternating runs with
  identical code (137K's changes present or absent) — a pre-existing test
  hygiene defect (violates this repository's own
  `.venv/bin/python`-only convention), not a 137K regression.
- `tests/test_gate_dry_run_context.py::test_no_pcae_cache_files_created_anywhere`,
  `tests/test_project_state_context.py::test_project_state_ctx_no_pcae_files_created`,
  `tests/test_shell_gate.py::TestAuditPersistence::test_audit_verify_cli`,
  `tests/test_phase_reports.py::TestPhase128B1NotificationDispatchReliabilityRepair::test_public_reconciliation_requires_report_marker_checkpoint_and_receipt`,
  `tests/test_permission_broker_observation_verification.py::test_check_scope_enforcement_unaffected_by_observation`,
  `tests/test_rendering_134e5.py::test_current_report_generation_remains_unchanged`,
  `tests/test_phase_115z_advisory_subsystem_hardening.py::TestExecutionUnavailable::test_runtime_inspect_reports_observed_and_observe`,
  `tests/test_cltr_cutover_136i_shared_core_independent_verification.py::test_136i_runtime_inspect_still_reports_observed_and_execution_unavailable`,
  `tests/test_repository_skills_integration_verification_115n.py::TestExecutionBoundaryVerification::test_runtime_inspect_reports_observed_state_and_observe_capability`,
  `tests/test_enforcement_readiness_cli.py::TestHumanReadableCLI::test_status_includes_gate_summary`,
  `tests/test_project_state.py::test_project_state_no_repository_files_created` —
  each passes in isolation (confirmed directly for the last two; the
  others confirmed passing under `-m fast_green`, non-`-n auto`);
  consistent with `pytest-xdist` parallel-worker state interference (shared
  `.pcae/`/task/session files touched concurrently across workers), not a
  137K-introduced defect.
- `tests/test_bootstrap_todo_consistency.py::test_recommended_next_phase_matches_real_project_status`,
  `::test_real_todo_no_longer_marks_90_series_as_next`,
  `::test_real_todo_current_roadmap_lists_recommended_phase_as_next` — fail
  identically on a fully clean `main` with every 137K change stashed out
  (confirmed via `git stash push -u -m ... <clean>`). Root cause:
  `_RECOMMENDED_NEXT_PHASE_RE` in `src/pcae/core/context.py` captures
  `\S+` immediately after `"Recommended next repo phase: "`, which
  includes PROJECT_STATUS.md's own leading `**` markdown-bold marker
  (e.g. captures `"**137K"` instead of `"137K"`); the test's own
  `\d{3}[A-Z]`-anchored regex then fails to match the leftover `**`
  prefix. Pre-existing, unrelated to 137K, not touched by this phase.
  Not separately documented as a new `docs/FINDING_*.md` — flagged here
  and left for a future phase to decide whether to fix the extraction
  regex or the test.

## Finding queued separately (not part of this phase's scope)

A pre-existing, unrelated bug in `pcae session bootstrap`'s readiness
classifier (`src/pcae/commands/session.py`, `_classify_bootstrap_readiness`)
was discovered and documented during this phase's task-transition, before
137K implementation began:
[docs/FINDING_BOOTSTRAP_READINESS_STALE_TASK_SELF_COMPARISON.md](FINDING_BOOTSTRAP_READINESS_STALE_TASK_SELF_COMPARISON.md).
Queued in `tasks/TODO.md`'s "Known Issues / Queued Fixes" section for a
future phase; not part of TAMPC-001's scope and not implemented here.

## Validation performed

Interpreter provenance confirmed first (TAMPC-REQ-163–166):

```
$ test -x .venv/bin/python && .venv/bin/python -c 'import sys; print(sys.executable); print(sys.prefix)'
/Users/atilamadai/repos/pcae-harness/.venv/bin/python
/Users/atilamadai/repos/pcae-harness/.venv
```

- `tests/test_authority_inspect_137k.py` — 64 tests, all passing. Covers:
  all sixteen families (success path, byte-lossless round trip, disclosure
  fields); malformed-artifact category (empty, non-JSON, non-object,
  duplicate key, trailing garbage); unknown/missing/non-string family;
  unsupported schema/model version; family-identity mismatch; schema- and
  model-validation failure; `registry_failure`/`manifest_failure` via
  monkeypatched Stage 3 exceptions with no leaked exception text; a live
  `test_manifest_one_entry_per_family_live` regression against the
  installed manifest (TAMPC-REQ-059); immutability (assignment, deletion,
  defensive-copy-on-read); authority-neutral disclosure and forbidden-field
  absence; determinism (repeated invocation, cross-path equality);
  provenance field-presence and digest-derivation; CLI Stage-1 boundary
  (missing path, directory, empty file, oversized file, unreadable file,
  dangling symlink, valid artifact); CLI rendering (`--json`
  sorted/indented, human fixed-field-order with disclosure first); CLI
  registration and exit codes via live subprocess invocation (`--help`,
  missing-path usage error → exit `2`, unknown subcommand → exit `2`,
  success → exit `0`, failure → exit `1`); forbidden-import static AST
  scan (no lifecycle/session/runtime/notification module imported by
  either new module); exact public-API-surface (`__all__`) match;
  lifecycle/runtime neutrality (`pcae health` unchanged before/after); and
  no stray filesystem writes as a side effect of inspection.
- Full repository regression suite: `.venv/bin/python -m pytest -q -n auto`
  — first run (before the import-guard repair below): 25356 passed, 66
  failed, 10 skipped. Second run (after the import-guard repair): **25380
  passed, 39 failed, 10 skipped**, 799.65s. Every one of the 39 remaining
  failures is accounted for below as pre-existing/environmental and
  unrelated to this phase's production code — none touches
  `authority_inspection.py`, `authority_inspect.py`, or the `authority`
  CLI surface. `tests/test_authority_inspect_137k.py` itself: 64/64
  passing in every run.
- Packaging: `.venv/bin/python -m build --wheel` and `--sdist` both
  succeeded; wheel content listing and `tar tzf` sdist listing both
  confirmed both new modules and the unchanged `cltr_cutover` resource
  tree are packaged. Installed the wheel into one fresh isolated virtual
  environment (`/tmp/pcae_137k_venv`, plus `jsonschema`) and the sdist
  into a second, separate fresh isolated virtual environment
  (`/tmp/pcae_137k_venv_sdist`, plus `jsonschema`); both ran
  `pcae authority inspect <fixture>` successfully (exit `0`) from a
  working directory (`/tmp`) entirely outside the repository checkout,
  confirming no repository-root-relative path dependency
  (TAMPC-REQ-161). Editable-install behavior is exercised implicitly by
  every `.venv/bin/python -m pcae ...` invocation elsewhere in this
  report, which runs against the repository checkout's own
  `src/pcae/schema_resources/cltr_cutover/` tree. A dedicated
  network-disabled (airplane-mode) run was not separately exercised in
  this phase; flagged as NON-BLOCKING residual verification for 137L,
  since `cltr_cutover_root()`'s resolution mechanism
  (`importlib.resources`) is unchanged, frozen, existing behavior already
  exercised by prior phases (Phase 106D precedent), not new code this
  phase introduces, and neither install-and-run above performed or
  required any network access.
- `docs/COMMANDS.md`: regenerated via `pcae docs commands --force`;
  produced no diff. Confirmed this repository's actual convention (by
  inspecting the existing, structurally identical `pcae cltr shadow`
  precedent) is that this hand-curated top-level reference does not list
  every subcommand group — `cltr` itself is absent — so `authority`
  following the same pattern is consistent with actual practice, not a
  gap. This corrects an assumption in the 137J plan's Section 1 table
  (NON-BLOCKING documentation-convention correction, not a contract or
  implementation defect).

## Requirement traceability

This phase reuses the 137J plan's Section 2 grouping (every TAMPC-REQ-001
through -178 already assigned to a row there) and fills it with concrete
137K evidence rather than planned evidence. No requirement ID is left
unmapped, unimplemented, or untested.

| TAMPC-REQ range | Implementation evidence | Test evidence |
|---|---|---|
| 001–003 (scope/authorization) | This document; `IPTAMC-001`; TAMPC-001 itself | N/A (documentation) |
| 004, 008, 016, 017, 174, 175 (CLI surface exactness) | `src/pcae/cli.py` `authority`/`inspect` subparser block | `test_cli_registration_help`, `test_cli_registration_inspect_help`, `test_cli_unknown_authority_subcommand_rejected` |
| 005, 029–031 (one positional, argparse contract) | `authority_inspect_parser.add_argument("path", ...)` | `test_cli_missing_path_argument_is_argparse_usage_error` |
| 006, 007, 055–057 (sixteen-family dispatch) | `authority_inspection._MODEL_BY_FAMILY` | `test_dispatch_table_has_sixteen_families`, `test_all_sixteen_families_inspect_successfully[*]` (16 params) |
| 009–012 (absence of authority/lifecycle/execution/notification logic) | Whole-module absence property, both new modules | `test_no_forbidden_imports` (AST-based) |
| 013–015, 018–020 (help text, disclosure) | `authority`/`inspect` parser `help=` text | `test_cli_registration_help`, `test_cli_registration_inspect_help` |
| 021–028 (module boundaries, public surface) | `authority_inspection.__all__`; one-way import direction | `test_public_api_surface_exact`, `test_no_forbidden_imports` |
| 029–038 (bounded read) | `authority_inspect._read_artifact` | `test_cli_missing_path`, `test_cli_directory_path`, `test_cli_empty_file`, `test_cli_oversized_file`, `test_cli_unreadable_file`, `test_cli_symlink_to_missing`, `test_cli_valid_artifact_exit_zero_and_toctou_no_reread` |
| 039–047 (parse) | `inspect_artifact_at_path` Stage 2 (`parse_strict_json`, reused unchanged) | `test_malformed_artifacts_fail_closed` (6 fixtures), `test_duplicate_nested_key_rejected` |
| 048–053, 158, 161 (package-owned resource resolution) | `inspect_artifact_at_path` `with cltr_cutover_root() as package_root:` | `test_all_sixteen_families_inspect_successfully` (live resolution), wheel-install offline smoke test (Validation section) |
| 054–060 (family + manifest-entry resolution, one-entry invariant) | Stage 6 in `inspect_artifact_at_path` | `test_manifest_one_entry_per_family_live`, `test_unknown_record_family`, `test_missing_record_type`, `test_non_string_record_type` |
| 061–064 (distinct schema/model/semantic/lifecycle/governance outcomes) | `to_dict()`'s `validation` sub-object, hardcoded `not_performed` literals | `test_all_sixteen_families_inspect_successfully` asserts all five keys |
| 065–074 (reuse of frozen Stage 3 owners, lossless round trip) | `validate_record_shape`, `Family.from_dict`, round-trip equality check | `test_schema_validation_failed`, `test_model_validation_failed`, `test_unsupported_schema_version`, `test_unsupported_model_version`, `test_family_identity_mismatch` |
| 075–080 (immutability) | `@dataclasses.dataclass(frozen=True)` on both outcome types (see Deviation section above) | `test_observation_ordinary_assignment_blocked`, `test_observation_delattr_blocked`, `test_failure_ordinary_assignment_blocked` |
| 081–083 (meaning contract) | `REPRESENTATION_ONLY_DISCLOSURE` dataclass default | `test_forged_operative_claims_are_never_authority_signals` |
| 084–086 (provenance completeness) | `_provenance_bundle` | `test_provenance_fields_present` (12 fields) |
| 087–092 (digest derivation/timing) | `input_digest = hashlib.sha256(artifact_bytes).hexdigest()`, computed once before parsing; `declared_record_digest` sourced separately, never compared | `test_input_digest_is_sha256_of_exact_bytes` |
| 093–106 (rendering parity) | `authority_inspect._render` | `test_cli_json_output_is_sorted_and_indented`, `test_cli_human_output_has_disclosure_first_and_fixed_fields` |
| 107–111 (failure taxonomy, precedence) | `_failure()` + the fixed Stage-ordered `if`/`return` chain in `inspect_artifact_at_path` | One test per category above (11 categories directly exercised) |
| 112–116 (exit codes) | `run_authority_inspect` return value | `test_cli_exit_1_on_failure`, `test_cli_full_invocation_success_and_failure`, `test_cli_missing_path_argument_is_argparse_usage_error` |
| 117–120 (determinism) | Pure function over `(path, artifact_bytes)`; no cache; fresh process per CLI invocation | `test_repeated_invocation_identical_output`, `test_two_paths_same_content_identical_except_identity` |
| 121–122 (no cross-invocation cache) | No module-level mutable state in either new module | `test_repeated_invocation_identical_output` (two independent calls) |
| 123–124 (no side effects) | `inspect_artifact_at_path` performs no writes | `test_no_side_effect_files_written` |
| 125–139 (security hardening) | Bounded read (size gate before open), strict parser reuse, static dispatch, `Path.is_file()` gate | `test_cli_oversized_file`, `test_cli_empty_file`, `test_duplicate_nested_key_rejected`, `test_cli_symlink_to_missing`, `test_cli_directory_path` |
| 140–142 (no lifecycle import/effect) | Whole-module absence property | `test_no_forbidden_imports`, `test_lifecycle_and_runtime_surfaces_unchanged_before_after` |
| 143–145 (no runtime import/effect) | Whole-module absence property | `test_no_forbidden_imports`, `test_lifecycle_and_runtime_surfaces_unchanged_before_after` |
| 146–147 (no authority-signal leakage) | Fixed output field set; disclosure unconditional | `test_forged_operative_claims_are_never_authority_signals` |
| 148–155 (pinned versions, consumer identity) | `CONSUMER_ID`, `SUPPORTED_SCHEMA_VERSION`, `SUPPORTED_MODEL_VERSION`, `TAMPC_CONTRACT_VERSION` module constants | `test_unsupported_schema_version`, `test_unsupported_model_version`, assertions in `test_all_sixteen_families_inspect_successfully` |
| 156–162 (packaging) | No `pyproject.toml` change needed; wheel build | Wheel content listing + isolated-venv offline smoke test (Validation section) |
| 163–166 (interpreter provenance) | `.venv/bin/python` used exclusively throughout this phase | Commands recorded in Validation section |
| 167–169 (fresh fixture authorship) | `tests/test_authority_inspect_137k.py` independently authored (see module docstring) | Entire test module |
| 170–172 (matrix completeness) | This table | This document |
| 173, 176–178 (precondition confirmation) | 137H/137I/137J prerequisites confirmed complete before this phase began | `pcae session bootstrap` output at phase start (137J completed, 137K recommended) |

## No-Go confirmation

No authority calculation/persistence/activation, no execution adapter, no
runtime-capability change, no generic multi-consumer framework, no
lifecycle/notification/publication/recovery/rollback action, no semantic
decision engine. Runtime confirmed Observed / observe / unavailable
before and after (`test_lifecycle_and_runtime_surfaces_unchanged_before_after`).

## Recommended Next Phase

**137L — Typed Authority Model Production Consumer Independent
Verification**, per the 137J plan, to independently re-derive and
adversarially verify this implementation from primary contracts,
installed-package artifacts, live CLI behavior, and fresh tests without
trusting this report or `tests/test_authority_inspect_137k.py`'s
conclusions as an oracle. 137L should also independently confirm the
sdist-install and fully-offline (network-disabled) packaging paths this
phase did not separately re-run beyond the wheel-based smoke test.
