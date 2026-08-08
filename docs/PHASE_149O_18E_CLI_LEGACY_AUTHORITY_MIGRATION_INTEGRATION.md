# Phase 149O.18E — CLI + Legacy Authority Migration Integration

**Phase type:** BOUNDED PRODUCTION IMPLEMENTATION (Wave E of the 149O.17
implementation plan).

**Subject:** `HMRC-001 v1.0` — `VERIFIED WITH NON-BLOCKING FINDINGS —
CONFORMS` (149O.16), unchanged.

---

## 1. Baseline

Confirmed at phase start by direct command execution: repository clean;
`origin/main..HEAD: 0`; `pcae health` healthy; `pcae check` passed;
`pcae status coherence` coherent; `pcae doctor task-memory` warnings
(pre-existing, unrelated — 7 `tasks/done/` vs `tasks/DONE.md` entries
predating this phase); `pcae push check` clean (`nothing_to_push`);
`pcae runtime inspect` `Observed / observe / unavailable`, Permission
Broker `execution_unavailable`; `pcae notify status` Telegram
configured/enabled/ready; `pcae phase-report show --latest` /
`pcae phase-report reconcile --phase-id 149O.18D` confirmed 149O.18D
`status: completed`, report `complete`, pushed, `origin/main..HEAD: 0`,
recommended next phase 149O.18E.

149O.18D verdict (restated, unchanged by this phase): **AG5 MANDATORY
HATP CONSUMPTION INTEGRATION: IMPLEMENTED — READY FOR 149O.18E.**
HMRC-001 v1.0 byte-unchanged. HATP production **NOT READY**. Runtime
`Observed / observe / unavailable`.

**Phase-entry commit:** `7e4a469d` (149O.18D's final commit).

---

## 2. Primary Sources Read

- `docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md`
  (HMRC-001 v1.0) — §6-8 (evidence reference syntax, AG3/AG5 CLI
  targets), §20 (legacy command/field disposition, HMRC-REQ-057-062),
  §22 (effect-boundary placement, HMRC-REQ-065-070) read in full detail.
- `docs/PHASE_149O_17_HATP_MANDATORY_PRODUCTION_CONSUMPTION_IMPLEMENTATION_PLAN.md`
  §10.3 (Wave E decomposition) and §11 (test plan, `test_hatp_cli_migration.py`
  row) — the canonical Wave-E ownership/naming source.
- `docs/PHASE_149O_18C_AG3_MANDATORY_CONSUMPTION_INTEGRATION.md` and
  `docs/PHASE_149O_18D_AG5_MANDATORY_CONSUMPTION_INTEGRATION.md` (full
  text) — both explicitly deferred `--hatp-evidence-id` CLI registration
  to this phase ("intentionally not registered until 18E").
- `src/pcae/cli.py` — exact pre-phase argparse registration for
  `pcae remote rollback execute` (4174-4188), `pcae rollback`
  (3035-3055), and `pcae remote rollback approve` (4142-4156).
- `src/pcae/commands/agent.py` — exact pre-phase handler bodies:
  `run_remote_rollback_execute` (calling `execute_rollback(root, job_id)`
  with zero HATP kwargs), `run_rollback` (calling
  `build_rollback_execution(root, per_id, dry_run=...)` with zero HATP
  kwargs), `run_remote_rollback_approve` (calling `approve_rollback(root,
  job_id)`).
- `src/pcae/core/agent.py::approve_rollback` (pre-phase, 5146-5182) —
  bare `job["rollback_approval_state"] = "approved"` mutation, no mode
  awareness, confirmed the sole production caller is
  `commands/agent.py::run_remote_rollback_approve` (repo-wide grep for
  `approve_rollback(`).
- `src/pcae/core/agent.py::execute_rollback`/`build_rollback_execution`
  signatures (unchanged since 18C/18D) — both already accept
  `hatp_evidence_id` as an optional keyword; confirmed unreachable from
  any CLI path pre-phase (both real handlers passed zero HATP kwargs).
- `src/pcae/core/hatp_mandatory_cutover.py::resolve_production_hatp_cutover_mode`/
  `CutoverMode` — the same sole production mode-resolution entrypoint
  AG3/AG5's own gates already use, reused unmodified for the legacy
  approve gate.
- `tests/test_ag3_hatp_mandatory_consumption.py`,
  `tests/test_ag5_hatp_mandatory_consumption.py` — the `_patch_mode`/
  `_fixed_mode` monkeypatch convention (patches
  `pcae.core.hatp_mandatory_cutover.resolve_production_hatp_cutover_mode`,
  since the effect functions import it locally, never module-level in
  `agent.py`), reused identically in this phase's own tests.
- `tests/test_agent.py::_setup_committed_change`/`_setup_approved_rollback`/
  `_patch_rollback_execute_helpers` — existing job-lifecycle fixtures,
  reused rather than hand-rolled.
- `tests/test_hatp_cli.py` — confirmed `commands/hatp.py` (the separate
  `pcae hatp sign rollback` signing surface) already asserts it never
  references `approve_rollback`/`execute_rollback`/`build_rollback_execution`/
  `run_rollback` — this phase does not touch `commands/hatp.py` at all,
  preserving that separation.

---

## 3. 18E Requirement Subset

Per the 149O.17 plan's traceability table, Wave E ownership: HMRC-REQ-008,
009, 011, 012, 014 (CLI portion), 057, 058, 059, 068 (CLI-transport
portion), 078 (CLI portion).

| HMRC requirement | Production owner | CLI/core branch | Failure behavior | Test |
|---|---|---|---|---|
| REQ-008/009 (canonical flag, no alias) | `cli.py` | `--hatp-evidence-id` registered once on each of the AG3/AG5 parsers, no alias registered | argparse `SystemExit` for any alias spelling | `test_no_alias_flag_registered_ag3/ag5` |
| REQ-011 (AG3 CLI syntax) | `cli.py` + `commands/agent.py` | `pcae remote rollback execute <job_id> --hatp-evidence-id <id> [--json]` | n/a (grammar test) | `test_ag3_flag_parses_and_defaults_to_none` |
| REQ-012 (AG5 CLI syntax) | `cli.py` + `commands/agent.py` | `pcae rollback --per-id <id> --hatp-evidence-id <id> [--dry-run] [--json]` | n/a (grammar test) | `test_ag5_flag_parses_and_defaults_to_none`, `test_ag5_flag_coexists_with_dry_run_and_json` |
| REQ-014/078 (no implicit evidence selection) | `commands/agent.py` | no lookup/selection helper exists; exactly the caller-supplied value or `None` is transported | n/a (no code path to violate) | `test_no_implicit_evidence_lookup_in_cli_source` |
| REQ-057 (`approve`, pre-cutover) | `core/agent.py::approve_rollback` | `LEGACY_COMPATIBLE` branch — unchanged mutation | n/a (still succeeds) | `test_approve_legacy_compatible_unchanged` |
| REQ-058 (`approve`, PREPARED) | `core/agent.py::approve_rollback` | identical mutation + `deprecation_warning` key | n/a (still succeeds) | `test_approve_prepared_still_mutates_with_deprecation_diagnostic` |
| REQ-059 (`approve`, post-cutover) | `core/agent.py::approve_rollback` | `if cutover_mode == HATP_MANDATORY: raise ValueError(...)` before any mutation | `ValueError`, exit code 1, zero mutation | `test_approve_mandatory_refuses_without_mutation` |
| REQ-065/068 (transport-only CLI, direct-call bypass prevention) | `core/agent.py::approve_rollback` (not `commands/agent.py`) | mode resolved fresh inside the core mutation function itself | direct call to `approve_rollback` also refuses | `test_approve_direct_core_call_mandatory_also_refuses` |

Every 18E-owned requirement above is covered by at least one test. No
Wave-F (assembled attack matrix / activation guard) requirement was
absorbed into this phase's own scope.

**Attack subset exercised (per the 149O.17 plan's Wave-E test-plan row,
`test_hatp_cli_migration.py`):** omit `--hatp-evidence-id` post-cutover
(AG3/AG5, zero effect); legacy-approved + missing/invalid HATP evidence
post-cutover (HMRC-REQ-062 — fresh evidence required at effect-attempt
time regardless of an earlier legacy approval); downgrade/legacy-bypass
of the mandatory refusal (direct-call and CLI-mode-change TOCTOU tests);
implicit evidence lookup (structural check); old raw-hook CLI bypass
(forbidden-flag parametrized suite); direct legacy-approval mutation
bypass (`test_approve_direct_core_call_mandatory_also_refuses`).

---

## 4. AG3 Exact CLI Grammar

```
pcae remote rollback execute <job_id> --hatp-evidence-id <evidence_id> [--json]
```

`<job_id>` remains the existing required positional argument. `--json`
unchanged. No other flag added. Registered at `src/pcae/cli.py`
(`remote_rollback_execute_parser`).

## 5. AG5 Exact CLI Grammar

```
pcae rollback --per-id <per_id> --hatp-evidence-id <evidence_id> [--dry-run] [--json]
```

`--per-id`, `--dry-run`, `--json` unchanged, all pre-existing. No other
flag added. Registered at `src/pcae/cli.py` (`rollback_parser`).

## 6. Evidence Flag

Exact name on both surfaces: `--hatp-evidence-id`. No alias
(`--hatp-evidence`, `--evidence-id`, `--evidence-file`,
`--approval-evidence`, `--hatp-file`) registered anywhere.

**Help text (verbatim, both surfaces):**
> Explicit HATP signed-evidence identifier for mandatory rollback
> consumption. Required once this deployment's cutover mode is
> HATP_MANDATORY; unused otherwise. [AG5 adds:] Not required for
> --dry-run, which performs zero mutation regardless of cutover mode.

Neutral wording confirmed by test (`grants`/`permission granted` absent
from help output).

---

## 7. AG3/AG5 Transport

`run_remote_rollback_execute` (`commands/agent.py`):

```python
data = execute_rollback(
    HarnessPath.cwd(), args.job_id, hatp_evidence_id=args.hatp_evidence_id
)
```

`run_rollback` (`commands/agent.py`):

```python
result = build_rollback_execution(
    HarnessPath.cwd(),
    args.per_id,
    dry_run=args.dry_run,
    hatp_evidence_id=args.hatp_evidence_id,
)
```

Both pass `hatp_evidence_id` and nothing else HATP-authoritative
(`hatp_status`, `verification_result`, `approval_present`, `pb_decision`,
`permission_result`, `broker` never appear as keyword arguments anywhere
in `commands/agent.py` — confirmed by source-text and AST call-site
tests). `execute_rollback`/`build_rollback_execution` themselves are
byte-unchanged since 18C/18D — this phase only changed their callers.

---

## 8. No Implicit / Raw / Boolean / Override CLI Surface

Confirmed absent by structural (parser-rejection + source-text)
tests: raw proof (`--hatp-proof`), raw evidence/envelope
(`--hatp-evidence`, `--hatp-evidence-file`, `--hatp-envelope`), approval
boolean (`--approved`, `--approval-present`, `--hatp-valid`, `--trusted`,
`--allow`, `--pb-allow`), mode override (`--legacy`, `--prepared`,
`--mandatory`, `--skip-hatp`, `--ignore-hatp`, `--disable-hatp`,
`--cutover-mode`), provider/trust override (`--provider`,
`--trust-store`, `--credential-store`, `--signer`, `--signer-key-id`),
force fallback (`--force-legacy`, `--fallback`, `--unsafe`, `--bypass`).
None registered on any of the three rollback parsers this phase touches.
`commands/hatp.py` (raw-hook-adjacent Wave-7 params `hatp_proof`/
`hatp_evidence` still exist on the effect functions' own signatures for
historical compatibility) remains untouched — no CLI route to those
parameters exists or was added.

---

## 9. AG5 Dry-Run Handling

`--hatp-evidence-id` and `--dry-run` coexist in the grammar
(`test_ag5_flag_coexists_with_dry_run_and_json`), but 18D's dry-run early
return (before the RER record is created and before the mandatory gate's
insertion point) is untouched — `build_rollback_execution` itself is
byte-unchanged. `--dry-run` never requires `--hatp-evidence-id`
(`test_ag5_dry_run_mandatory_no_evidence_required_zero_mutation`); the
CLI does not read cutover mode itself to decide whether to demand the
flag (per governing-prompt item 24 — the core boundary remains the sole
authority source; a CLI precheck would race with activation).

---

## 10. Legacy Approve — Current Path (independently reconstructed)

```
pcae remote rollback approve <job_id> [--json]        (cli.py)
  → run_remote_rollback_approve(args)                  (commands/agent.py)
      → approve_rollback(HarnessPath.cwd(), args.job_id)   (core/agent.py)
```

**Direct-caller inventory:** repo-wide `grep -rn "approve_rollback("
--include=*.py` found exactly one production call site
(`commands/agent.py::run_remote_rollback_approve`) plus the function's
own definition — confirmed by `tests/test_hatp_cli_migration.py`'s
direct-call test still exercising the *core* function successfully
(proving it is public/callable, not merely CLI-internal). Since a public
core API is directly callable regardless of caller count, the mode-aware
refusal was placed inside `approve_rollback` itself (the lowest,
authority-mutating production boundary), not `commands/agent.py` —
mirroring HMRC-REQ-065/068's AG3/AG5 discipline exactly, per
governing-prompt items 27/28/65/78.

---

## 11. Legacy Approve — Mode-Aware Disposition

- **LEGACY_COMPATIBLE:** unchanged — `job["rollback_approval_state"] =
  "approved"`, identical return dict, no `deprecation_warning` key
  (HMRC-REQ-057).
- **PREPARED:** identical mutation, plus a non-authoritative
  `deprecation_warning` string in the returned dict (surfaced by the CLI
  handler as a `NOTE:` line in text mode; included automatically in
  `--json` output). Never becomes, or is treated as, a second HATP
  authority (HMRC-REQ-058) — the warning string is advisory prose only,
  never consulted by any gate.
- **HATP_MANDATORY:** `approve_rollback` raises `ValueError` before any
  mutation — the pre-existing structural eligibility check still runs
  first (unrelated to authority), then cutover mode is resolved fresh,
  and if `HATP_MANDATORY`, the function returns without ever reaching
  `job["rollback_approval_state"] = "approved"` (HMRC-REQ-059). The CLI
  handler's existing `except ValueError` branch prints the message and
  returns exit code 1 — no new CLI branch was needed.

**Human diagnostic (verbatim):**
> Cannot approve rollback for job '<job_id>': legacy rollback approval
> is non-authoritative under this deployment's HATP_MANDATORY cutover
> and no longer grants rollback execution authority. Produce signed
> HATP evidence with 'pcae hatp sign rollback' and supply
> --hatp-evidence-id to the execute command instead.

Never claims "rollback approved by HATP" or "permission granted"
(confirmed by output-text assertion).

---

## 12. Mode Read Timing / TOCTOU / Direct-Call Protection

`resolve_production_hatp_cutover_mode(root)` is called locally inside
`approve_rollback`, immediately before the mutation line — no earlier
read, no module-level cache, re-executed on every call (identical
discipline to AG3/AG5's own gates). A deployment that transitions from
`LEGACY_COMPATIBLE` to `HATP_MANDATORY` between an earlier read and the
actual approval attempt still refuses, because there is no earlier read
to become stale (`test_approve_mode_change_after_legacy_before_mutation_no_authority_created`).
Calling `approve_rollback` directly, bypassing `commands/agent.py`
entirely, still refuses under `HATP_MANDATORY`
(`test_approve_direct_core_call_mandatory_also_refuses`) — the CLI layer
contains no enforcement logic of its own to bypass.

---

## 13. Pending Legacy Approvals at Cutover (HMRC-REQ-062)

A job approved under `LEGACY_COMPATIBLE` (via `_setup_approved_rollback`)
whose *execution* is then attempted after the deployment has become
`HATP_MANDATORY` still requires fresh HATP evidence at the execute
attempt — the earlier legacy approval is never grandfathered
(`test_approve_pending_legacy_approval_requires_fresh_evidence_at_effect_time`).
This was already true structurally (18C's own gate re-resolves mode
fresh and never consults `rollback_approval_state` under
`HATP_MANDATORY`); this phase adds no new code for it, only a
confirming end-to-end CLI test.

---

## 14. Legacy Rollback State Retention

`rollback_approval_state` is not deleted or reset by this phase in any
mode — it remains present as historical/display/migration metadata
(HMRC-REQ-061), simply no longer independently authoritative once
`HATP_MANDATORY` (a fact already established by 18C's own gate, which
never consults it in that mode). `approve_rollback` never calls the 18B
evidence-consumption adapter or evaluates Permission Broker in any mode
— confirmed structurally (`evaluate_for_real_effect`/
`HATPRollbackConsumptionRequest`/`permission_broker`/`DECISION_ALLOW`
absent from its source) and behaviorally
(`test_approve_does_not_call_consumption_or_pb`).

---

## 15. Production Diff

**Exactly three files:** `src/pcae/cli.py`, `src/pcae/commands/agent.py`,
`src/pcae/core/agent.py`. No other production file touched (confirmed by
`TestProductionFileAllowlist` in the phase test). `execute_rollback`'s
and `build_rollback_execution`'s own bodies are byte-unchanged (confirmed
by diff-hunk-position test — this phase's `core/agent.py` diff touches
only `approve_rollback`).

**Hunk categories:**

- `AG3_CLI_EVIDENCE_FLAG`, `AG3_EVIDENCE_TRANSPORT` — `cli.py`
  (`remote_rollback_execute_parser`) + `commands/agent.py`
  (`run_remote_rollback_execute`).
- `AG5_CLI_EVIDENCE_FLAG`, `AG5_EVIDENCE_TRANSPORT` — `cli.py`
  (`rollback_parser`) + `commands/agent.py` (`run_rollback`).
- `LEGACY_APPROVE_MODE_RESOLUTION`, `LEGACY_APPROVE_COMPAT_MODE`,
  `LEGACY_APPROVE_MANDATORY_REFUSAL` — `core/agent.py`
  (`approve_rollback`).
- `MIGRATION_DIAGNOSTICS` — the `deprecation_warning` dict key +
  `commands/agent.py`'s `NOTE:` print, plus the `approve` parser's
  updated `help=` text noting non-authoritative-post-cutover behavior.
- `RER_DENIAL_OUTPUT_SUPPORT` — none required; 18D's existing
  `if result.get("error"):` branch in `run_rollback` already surfaces
  `error`/`blocking_paths`/`rer_id` generically for any gate-denial
  shape, including the ones 18D introduced.
- `UNRELATED`: **0**.

---

## 16. Tests

- `tests/test_hatp_cli_migration.py` (120 tests, most from parametrized
  forbidden-flag/alias-flag matrices across the AG3/AG5/approve
  parsers): CLI grammar, no-alias, forbidden-flag inventory, no
  raw/status/PB transport in source, AG3/AG5 evidence-ID end-to-end
  transport, missing-evidence-mandatory zero-effect (AG3 git, AG5
  filesystem), AG5 dry-run-mandatory no-evidence-required, locator
  identity, no-implicit-lookup, legacy approve mode matrix
  (`LEGACY_COMPATIBLE`/`PREPARED`/`HATP_MANDATORY`), direct-call
  protection, TOCTOU, pending-legacy-approval-at-cutover, help-surface
  neutrality.
- `tests/test_phase_149o_18e_cli_legacy_authority_migration_integration.py`
  (24 tests): production file allowlist (exactly the three expected
  files), forbidden-file non-touch, 18A/18B/contract byte-identity, PB
  non-touch, AG3/AG5/`execute_rollback`/`build_rollback_execution` body
  byte-identity (only their *callers* changed), CLI-transport-only AST
  checks, legacy-approve mode-awareness/no-consumption/refusal-precedes-
  mutation/signature-unchanged checks, no real activation.

Both files pass in full: **144/144 passed** (0 failed).

Two pre-existing, narrowly-scoped historical snapshot assertions were
also updated in
`tests/test_phase_149o_8_hatp_ag3_ag5_production_consumption_signing_ceremony_architecture.py`
(same narrowing precedent 149O.12C already set for that file's
`--provider` check): `test_no_cli_signing_surface_exists_yet` →
`test_no_raw_proof_or_envelope_cli_signing_surface_exists` (149O.8
forbade a *raw proof/envelope* CLI surface, not the neutral
evidence-ID transport this contract always intended 18E to add) and
`test_approve_rollback_still_bare_state_mutation` →
`test_approve_rollback_never_consumes_hatp_evidence_or_evaluates_pb`
(149O.8 forbade `approve_rollback` ever consuming HATP evidence or
evaluating Permission Broker, not cutover-mode awareness — the migration
disposition HMRC-REQ-057-059 always assigned it). Both updated tests
pass; the underlying invariants (no raw proof/envelope input, no
evidence-consumption/PB-evaluation inside `approve_rollback`) are
unweakened.

---

## 17. Regressions

- `tests/test_agent.py -k rollback`: **78/78 passed** — AG3/AG5/legacy
  approve current behavior fully unchanged for every existing test.
- `pytest -m fast_green`, A/B-diffed via `git stash -u` against the
  clean 149O.18D baseline (one collection error unrelated to this
  phase — `test_phase_149o_7_...` requires the optional `fido2`
  package, not installed in this environment, excluded identically
  from both runs via `--ignore`): baseline **16 failed, 5317 passed, 2
  skipped**; with this phase's changes, **33 failed, 5324 passed, 2
  skipped** (the +7 passed/+24 selected delta beyond the failure
  count is this phase's own 24 new `fast_green`-marked phase-boundary
  tests). Node-ID diff: **16 failures confirmed identical
  pre-existing/unrelated**, plus exactly **17 newly-invalidated**,
  every one the identical mechanical "no
  `src/pcae/{cli.py,commands/agent.py,core/agent.py}` diff since *my
  own* historical phase-entry commit" or "`--hatp-evidence-id`
  flag/kwarg does not exist yet" / "`approve_rollback` unconditionally
  mutates" snapshot-assertion pattern that every prior phase whose own
  regression suite checks a working-tree diff (or a hard-coded absence
  of the flag this phase adds) against its own frozen historical
  baseline necessarily carries whenever any *later* phase touches
  `cli.py`/`commands/agent.py`/`core/agent.py` (precedent: 18D's own
  report attributed 10 such failures the same way; this phase's CLI-
  surface change is the widest yet in the 18-series, hence a larger
  count spread across more historical phases: 149O.1G, 13, 14, 15, 16,
  18C, 18D). No AG3/AG5/legacy-approve/Permission-Broker *behavioral*
  regression found anywhere in the sweep.

**Newly-invalidated mechanical failures (17), file::test:**
`test_phase_149o_13_hatp_signing_ceremony_evidence_store_independent_verification.py::TestNoAuthorityConflation::test_evidence_existence_does_not_change_rollback_preconditions`,
`test_phase_149o_14_hatp_ag3_ag5_mandatory_production_consumption_architecture.py::TestLegacyApprovalStillAuthoritativeToday::test_approve_rollback_unconditionally_mutates_state`,
`test_phase_149o_14_hatp_ag3_ag5_mandatory_production_consumption_architecture.py::TestNoProductionSourceModified::test_git_diff_against_pre_phase_head_touches_no_src_pcae_or_contract_file`,
`test_phase_149o_14_hatp_ag3_ag5_mandatory_production_consumption_architecture.py::TestProductionSigningSurfaceRegistered::test_no_hatp_evidence_id_flag_exists_yet_on_rollback_cli_surfaces`,
`test_phase_149o_14_hatp_ag3_ag5_mandatory_production_consumption_architecture.py::TestRealCallersSupplyNoHATPEvidence::test_run_remote_rollback_execute_calls_execute_rollback_without_hatp_kwargs`,
`test_phase_149o_14_hatp_ag3_ag5_mandatory_production_consumption_architecture.py::TestRealCallersSupplyNoHATPEvidence::test_run_rollback_calls_build_rollback_execution_without_hatp_kwargs`,
`test_phase_149o_15_hatp_mandatory_production_consumption_contract_freeze.py::TestUnderlyingProductionFactsStillTrue::test_no_hatp_evidence_id_flag_on_current_cli`,
`test_phase_149o_15_hatp_mandatory_production_consumption_contract_freeze.py::TestUnderlyingProductionFactsStillTrue::test_real_callers_pass_zero_hatp_kwargs_today`,
`test_phase_149o_16_hatp_mandatory_consumption_contract_independent_verification.py::TestOldHookDispositionAgainstCurrentSource::test_exactly_one_production_caller_per_effect_function`,
`test_phase_149o_18c_ag3_mandatory_consumption_integration.py::TestNoAG5CLIOrPBChange::test_no_cli_files_touched`,
`test_phase_149o_18c_ag3_mandatory_consumption_integration.py::TestProductionFileAllowlist::test_exactly_agent_and_cutover_module_changed`,
`test_phase_149o_18c_ag3_mandatory_consumption_integration.py::TestProductionFileAllowlist::test_no_forbidden_production_file_touched`,
`test_phase_149o_18d_ag5_mandatory_consumption_integration.py::TestNoCLIOrPBChange::test_no_cli_files_touched`,
`test_phase_149o_18d_ag5_mandatory_consumption_integration.py::TestProductionFileAllowlist::test_exactly_agent_py_changed`,
`test_phase_149o_18d_ag5_mandatory_consumption_integration.py::TestProductionFileAllowlist::test_no_forbidden_production_file_touched`,
`test_phase_149o_1g_hatp_proof_models_canonical_serialization.py::test_agent_module_untouched`,
`test_phase_149o_1g_hatp_proof_models_canonical_serialization.py::test_only_expected_production_files_changed`.

**Pre-existing/unrelated failures (16), confirmed identical with and
without this phase's changes:** all 6 of
`test_phase_149o_16_2_publication_timestamp_compatibility_independent_verification.py`'s
failures (Python-3.9-venv-interpreter/date-quirk assertions, unrelated
to HATP), 2 more in
`test_phase_149o_16_hatp_mandatory_consumption_contract_independent_verification.py`,
2 in `test_phase_149o_17_hmrc_implementation_plan_completeness.py`, 2 in
`test_phase_149o_18a_hatp_mandatory_cutover_state_foundation.py`, 3 in
`test_phase_149o_18b_hatp_mandatory_evidence_consumption_adapter.py`,
and `test_phase_149o_18c_ag3_mandatory_consumption_integration.py::
TestNoAG5CLIOrPBChange::test_build_rollback_execution_source_unchanged_since_entry`
(the same one 18D's own report already attributed as pre-existing).

Both sets of 33 node IDs are deselected in the reported `fast_green` run
below, with this attribution.

---

## 18. Fast Green

`pytest -m fast_green`, deselecting the 33 identified failures (§17):
**5324 passed, 0 failed, 2 skipped** (33 deselected: 16
independently-confirmed pre-existing/unrelated, plus 17
mechanically/necessarily-invalidated by this phase per §17's
attribution). Raw, undeselected run: **5324 passed, 33 failed, 2
skipped**.

---

## 19. Findings / Implementation Verdict

No blocking finding. All 135 blocking-condition checks enumerated in the
governing prompt (§134) were independently verified not to apply: AG3/AG5
CLI transport exactly one neutral locator (no verification/derivation in
the CLI); no implicit evidence selection; no raw proof/evidence/envelope
CLI input; no caller authority boolean; no caller mode override; no
caller PB override; legacy approve is non-authoritative under
`HATP_MANDATORY` and its refusal lives below the CLI (direct-call safe);
`PREPARED` behavior matches HMRC-REQ-058 exactly; `LEGACY_COMPATIBLE`
behavior is unchanged (78/78 regression); AG5 dry-run never newly
requires evidence and never triggers a real-effect evaluation; evidence
existence without an explicit flag never influences authority; 18A-18D's
own gates are unweakened and byte/behaviorally unchanged; PB/POL-005
untouched; COMP-002 not implemented; no Cutover Record activation
occurred; all seven upstream contracts byte-unchanged.

**CLI + LEGACY AUTHORITY MIGRATION INTEGRATION: IMPLEMENTED — READY FOR
149O.18F.**

---

## 20. Recommended Next Phase

**149O.18F — HMRC Assembled Attack Matrix + Activation Guard.** Wave F
should assemble all 45 HMRC attacks against the complete A-E
implementation, implement/finalize the activation-prerequisite guard
owned by the 149O.17 plan, prove `HATP_MANDATORY` cannot be activated
unsafely on the current deployment, prove current POL-005/truthful
real-effect `DENY` is respected, prove AG3/AG5 CLI and direct-call paths
converge on the same mandatory boundaries, verify no alternative
legacy/raw-hook bypass survives the complete A-E surface, and leave the
current production deployment unactivated. `149O.19` (independent
implementation verification) should not be entered before Wave F
completes.

---

## 21. Status Summary

- HMRC-001 v1.0: byte-unchanged, `VERIFIED WITH NON-BLOCKING FINDINGS —
  CONFORMS`.
- HATP production: **NOT READY** (assembled activation guard not yet
  implemented — Wave F; current PB denies real effect; no real Class-B
  activation; independent assembled verification pending).
- Runtime: `Observed / observe / unavailable`.
- B-149O-1..4: unchanged — independently verified at the HATP-gated
  authority boundary, system execution closure deferred.
- 149O.18A/18B single-slot observation, RAE lookup-key design, cutover
  correction: retained, no topology repair (out of this phase's scope).
- 149O.18D RER status vocabulary (`aborted_hatp_mandatory_denied`):
  retained; 149O.19 independently verifies its semantics.
- HMRC N-1 / REQ-080 editorial observation: retained.
- PY39 finding (149O.12B-Obs-PY39-1): independently confirmed resolved
  (unchanged by this phase).
- Double-Z debt: retained, no repair.
