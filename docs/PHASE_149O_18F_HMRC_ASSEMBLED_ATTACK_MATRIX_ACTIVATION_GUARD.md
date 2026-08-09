# Phase 149O.18F -- HMRC Assembled Attack Matrix + Activation Guard

Final assembly/hardening phase of the HMRC-001 v1.0 implementation
(HATP Mandatory Rollback Consumption Contract), Wave F of the 149O.17
implementation plan (`docs/PHASE_149O_17_HATP_MANDATORY_PRODUCTION_
CONSUMPTION_IMPLEMENTATION_PLAN.md` Sec.9.1/Sec.10.3). Depends on Waves
A-E (149O.18A-149O.18E), all already implemented, independently tested,
and byte-unchanged by this phase except the one additive extension
documented in Sec.6 below.

## 1. Baseline

Latest completed phase entering 149O.18F: 149O.18E -- CLI + Legacy
Authority Migration Integration. Status: completed, report completeness:
complete, commits 8fc4b679/a4945208/76cd8309, pushed, `origin/main..HEAD`
= 0. HMRC-001 v1.0: `VERIFIED WITH NON-BLOCKING FINDINGS -- CONFORMS`.
Runtime: `Observed / observe / unavailable`. Current development
deployment: `LEGACY_COMPATIBLE` (no Cutover Record exists anywhere real).
HATP production: `NOT READY`.

Implemented HMRC waves entering this phase: 149O.18A (Cutover State
Foundation), 149O.18B (Evidence Consumption Adapter), 149O.18C (AG3
Mandatory Consumption Integration), 149O.18D (AG5 Mandatory Consumption
Integration), 149O.18E (CLI + Legacy Authority Migration Integration).

## 2. Wave-F Requirement Subset (149O.17 plan Sec.10.3/Sec.15)

The 149O.17 plan assigns Wave F exactly: `assess_hatp_mandatory_
activation_readiness` (Sec.9.1, deferred to Wave F because it needs B-E
to exist to check "implementation version present"), the truthful
`simulation_only=False` real-effect path's final integration proof, and
the full assembled 45-attack suite run against the complete, wired
system. "No new production module; may touch `hatp_mandatory_cutover.py`
only to add the readiness-checker function (still additive, no behavior
change to A's existing surface)." HMRC-REQ ownership: 031-056 (cutover
portion, shared with Wave A), specifically **HMRC-REQ-054/055** (the
activation-prerequisite conjunction and the explicit non-requirement of
MC-14 execution-enforcement capability for activation).

| Requirement | Normative meaning | Production owner (before 18F) | 18F change | Test owner | MC | Attack |
|---|---|---|---|---|---|---|
| HMRC-REQ-054 | PREPARED requires a 6-item conjunction (Class-B deployment, HATP substrate operational, HSCE signing available, mandatory-consumption impl present+verified, dependency provenance valid, Protected Activation Authority mechanism available) | Not implemented | **New**: `assess_hatp_mandatory_activation_readiness` | `test_hatp_mandatory_activation_guard.py` | MC-6 | n/a (prerequisite, not an attack row) |
| HMRC-REQ-055 | Activation does NOT additionally require MC-14 execution-enforcement capability to exist | Not implemented | **New**: readiness conjunction deliberately omits any PB/MC-14 check | `test_hatp_mandatory_activation_guard.py::test_readiness_never_calls_permission_broker_or_uses_simulation_result` | MC-14 (non-interaction) | n/a |
| HMRC-REQ-041 | Activation reachable only by Protected Activation Authority | `_write_cutover_transition` (18A, internal-only) | **New**: `activate_hatp_mandatory` reuses 18A's authority-scope decision unchanged (OS-level protected-root boundary, no application-level principal invented) | `test_hatp_mandatory_activation_guard.py` | MC-6, MC-7 | n/a |
| HMRC-REQ-038/039 | Only `LEGACY_COMPATIBLE->PREPARED` and `PREPARED->HATP_MANDATORY` transitions valid | `is_valid_cutover_transition` (18A, unchanged) | None -- reused as-is by the new activation guard | `test_hatp_mandatory_activation_guard.py` | MC-7 | n/a |
| HMRC-REQ-049/050 | Write-once monotonic marker, no downgrade | 18A (unchanged) | None -- reused as-is | `test_hatp_mandatory_activation_guard.py` | MC-7 | 22, 39-42 |
| All other 85 requirements | (see Sec.4) | Waves A-E | Assembled/attacked, not modified | See Sec.4 | See Sec.4 | See Sec.5 |

No Wave-F-owned requirement is left unmapped. No already-complete A-E
behavior was modified without a demonstrated defect (none was found; see
Sec.9).

## 3. A-E Production Reconstruction (read directly from source, not from
prior phase reports' line numbers, per this phase's own instruction)

- **AG3** (`src/pcae/core/agent.py::execute_rollback`): structural
  preconditions (idempotency, legacy approval-state gate under non-
  mandatory modes, eligibility, mode-recommendation, dirty-tree,
  ancestor-reachability) all run before a fresh `resolve_production_
  hatp_cutover_mode` re-check and the Mandatory Consumption Boundary,
  placed immediately before `_run_git_revert`. Missing `hatp_evidence_id`
  under `HATP_MANDATORY` raises `ValueError` before any git mutation.
- **AG5** (`src/pcae/core/agent.py::build_rollback_execution`): PER/ECP/
  in-progress/divergence structural checks all run first (dry-run returns
  before any of the RER-persistence/mandatory-gate code); the Mandatory
  Consumption Boundary sits after divergence-check RER persistence and
  before the first `write_text`/`write_bytes`/`unlink()` in the restore
  loop. Denial persists RER status `aborted_hatp_mandatory_denied`
  (terminal, `completed_at` set) via a typed dict return, never an
  exception.
- **Legacy approve** (`src/pcae/core/agent.py::approve_rollback`): mode
  resolved fresh immediately before the mutation line;
  `LEGACY_COMPATIBLE` unchanged, `PREPARED` unchanged plus a
  `deprecation_warning` key, `HATP_MANDATORY` raises `ValueError` before
  any mutation.
- **CLI** (`src/pcae/cli.py`): `--hatp-evidence-id` registered on both
  `remote rollback execute` (AG3) and `rollback` (AG5) parsers, no alias,
  `default=None`. No `hatp activate`/cutover-mode subcommand exists
  anywhere (confirmed by grep across the whole file).
- **Consumption adapter** (`src/pcae/core/hatp_rollback_consumption.py`):
  `evaluate_for_real_effect`/`evaluate_for_advisory` differ only in a
  hardcoded `simulation_only` value; neither accepts `simulation_only`,
  `hatp_proof`, `hatp_evidence`, `provider`, or `trust_store` as
  parameters. RAE lookup key is the loaded proof's own `binding_id`, never
  the caller's HSCE `evidence_id`.
- **Cutover state** (`src/pcae/core/hatp_mandatory_cutover.py`, before
  this phase's addition): `resolve_production_hatp_cutover_mode` is the
  sole production read entrypoint, resolving `HATPTrustStore.production
  ().root` internally with no override; `_write_cutover_transition` was
  the sole (internal-only, never production-paired) write function.

No un-audited caller of `execute_rollback`/`build_rollback_execution` was
found beyond the two known, already-gated production callers in
`commands/agent.py` (attack 24, Sec.5, Sec.9).

## 4. MC-1..MC-14 Assembled Coverage

| MC | Production enforcement point(s) | A-F owner | Assembled test(s) | Status |
|---|---|---|---|---|
| MC-1 | Evidence ID is a locator only | `HATPRollbackConsumptionRequest` (no authority field) | attack-matrix 16/17 | Implemented |
| MC-2 | Fresh re-verification every attempt | `_internal_consume_hatp_rollback_evidence`, no cache | attack-matrix 25/26 | Implemented |
| MC-3 | No cached verification/approval/PB decision | B (unchanged) | attack-matrix 25/26 | Implemented |
| MC-4 | No legacy fallback post-cutover | C, D | attack-matrix 20/21/45 | Implemented |
| MC-5 | No caller-supplied approval boolean | C, D, request/signature checks | AG3/AG5 signature tests | Implemented |
| MC-6 | Only protected Class-B state determines mode | A, **F (readiness reuses this)** | activation-guard suite | Implemented |
| MC-7 | One-way transition for ordinary principals | A, **F (activation guard preserves `is_valid_cutover_transition`)** | activation-guard suite (monotonicity/no-downgrade) | Implemented |
| MC-8 | AG3/AG5 bind to their exact signed operation | B | attack-matrix 4/36-38 | Implemented |
| MC-9 | Cross-family evidence cannot authorize | B | attack-matrix 5/6 | Implemented |
| MC-10 | Approval always passes through PB | B, C, D | attack-matrix 32/33 | Implemented |
| MC-11 | Every effectful caller covered identically | C, D, **F (caller re-inventory, attack 24)** | attack-matrix 24 | Implemented |
| MC-12 | PB ALLOW != execution capability | B (unchanged) | attack-matrix 34, assembled `test_ag3/ag5_cli_assembled_current_real_pol005_deny_zero_*` | Implemented |
| MC-13 | Signing itself never changes authority | Unmodified HSCE modules | (unchanged from prior waves) | Implemented |
| MC-14 | Real effect never proceeds on `simulation_only=True` | B, C, D, **F (final assembled proof)** | attack-matrix 34, assembled CLI PB-DENY tests | Implemented |

All 14 invariants map to a concrete production enforcement point and at
least one assembled Wave-F test. This is Wave F's own assembled proof --
not an independent verification (149O.19's obligation, Sec.15).

## 5. 45-Attack Matrix (independently re-extracted from HMRC-001 Sec.29)

Exactly 45 rows, `1`-`45`, no gaps, no duplicates, no unspecified
outcome, mechanically enforced by
`tests/test_phase_149o_18f_hmrc_assembled_attack_matrix.py::
test_exactly_45_attacks_structured_no_gaps_no_duplicates` and
`test_all_45_attacks_have_at_least_one_executed_representative_test`.

| # | Threat | Entry point | Expected outcome | Test |
|---|---|---|---|---|
| 1 | Missing evidence ID | hatp_rollback_consumption | fail closed | test_attack_01 |
| 2 | Malformed evidence envelope | hatp_rollback_consumption | fail closed | test_attack_02 |
| 3 | Digest mismatch | hatp_rollback_consumption | fail closed | test_attack_03 |
| 4 | Wrong operation | hatp_rollback_consumption | fail closed | test_attack_04_36 |
| 5 | AG3 evidence for AG5 dispatch | hatp_rollback_consumption | fail closed | test_attack_05 |
| 6 | AG5 evidence for AG3 dispatch | hatp_rollback_consumption | fail closed | test_attack_06_37_38 |
| 7 | Wrong repository | hatp_rollback_consumption | fail closed | test_attack_07 |
| 8 | Wrong deployment | hatp_rollback_consumption | fail closed | test_attack_08 |
| 9 | Expired proof | hatp_rollback_consumption | fail closed | test_attack_09 |
| 10 | Revoked signer | hatp_rollback_consumption | fail closed | test_attack_10 |
| 11 | Revoked authority | hatp_rollback_consumption | fail closed | test_attack_11 |
| 12 | Decision changed after signing | hatp_rollback_consumption | fail closed | test_attack_12 |
| 13 | Binding changed after signing | hatp_rollback_consumption | fail closed | test_attack_13 |
| 14 | Fresh unregistered key | hatp_rollback_consumption | fail closed | test_attack_14 |
| 15 | Forged signer | hatp_rollback_consumption | fail closed | test_attack_15 |
| 16 | Caller `approval_present=True` | hatp_rollback_consumption | structurally impossible | test_attack_16_17 |
| 17 | Caller HATP VALID spoof | hatp_rollback_consumption | structurally impossible | test_attack_16_17 |
| 18 | Test-provider injection | hatp_rollback_consumption | structurally impossible | test_attack_18_19 |
| 19 | Trust-store injection | hatp_rollback_consumption | structurally impossible | test_attack_18_19 |
| 20 | Legacy-approved + missing evidence, post-cutover | execute_rollback | fail closed | test_attack_20 |
| 21 | Legacy-approved + invalid evidence, post-cutover | execute_rollback | fail closed | test_attack_21 |
| 22 | Delete Cutover Record | hatp_mandatory_cutover | fail closed, no downgrade | test_attack_22 |
| 23 | CLI-flag downgrade | cli | rejected | test_attack_23 |
| 24 | Alternate effect caller bypass | agent.py caller inventory | no un-audited caller | test_attack_24 |
| 25 | Cached VALID reused | hatp_rollback_consumption | structurally impossible | test_attack_25_26 |
| 26 | Cached PB ALLOW reused | hatp_rollback_consumption | structurally impossible | test_attack_25_26 |
| 27 | Evidence deleted after success, retry | hatp_rollback_consumption | fail closed on retry | test_attack_27 |
| 28 | Evidence modified after success, retry | hatp_rollback_consumption | fail closed on retry | test_attack_28 |
| 29 | Two valid IDs, none supplied | cli/hatp_rollback_consumption | rejected, explicit required | test_attack_29 |
| 30 | Raw `hatp_proof` bypass | execute_rollback/build_rollback_execution | rejected | test_attack_30_31 |
| 31 | Raw `hatp_evidence` bypass | execute_rollback/build_rollback_execution | rejected | test_attack_30_31 |
| 32 | PB HUMAN_REVIEW despite valid HATP | execute_rollback | effect blocked | test_attack_32_33 |
| 33 | PB DENY despite valid HATP | execute_rollback | effect blocked | test_attack_32_33 |
| 34 | PB ALLOW under `simulation_only=True` | hatp_rollback_consumption | does not authorize effect | test_attack_34 |
| 35 | Pre-cutover evidence consumed post-cutover | execute_rollback | allowed if fresh/valid | test_attack_35 |
| 36 | Wrong AG3 job | hatp_rollback_consumption | fail closed | test_attack_04_36 |
| 37 | Wrong AG5 PER | hatp_rollback_consumption | fail closed | test_attack_06_37_38 |
| 38 | Wrong AG5 ecp_id | hatp_rollback_consumption | fail closed | test_attack_06_37_38 |
| 39 | Cutover-record corruption | hatp_mandatory_cutover | fail closed | test_attack_39 |
| 40 | Cutover-record wrong repository | hatp_mandatory_cutover | not-present-for-repo | test_attack_40 |
| 41 | Cutover-record unknown version | hatp_mandatory_cutover | fail closed | test_attack_41 |
| 42 | Cutover-record boolean version | hatp_mandatory_cutover | rejected | test_attack_42 |
| 43 | Repository moved/cloned, evidence reused | hatp_rollback_consumption | fail closed | test_attack_43 |
| 44 | Divergence-blocking AG5 state + valid HATP | build_rollback_execution | structural check still blocks | test_attack_44 |
| 45 | Evidence exists without explicit ID | execute_rollback/build_rollback_execution | no effect | test_attack_45 |

All 45 pass against the assembled A-F production code.

## 6. Activation-Guard Ownership and Design

**Exact production module**: `src/pcae/core/hatp_mandatory_cutover.py`
(additive-only extension, per 149O.17 plan Sec.10.3). New public API:

- `HATPMandatoryActivationReadinessCheck` (frozen dataclass:
  `name, satisfied, detail`).
- `HATPMandatoryActivationReadiness` (frozen dataclass: `ready, checks,
  reasons` -- no `force`/`skip_check`/`assume_ready` field).
- `assess_hatp_mandatory_activation_readiness(root: HarnessPath) ->
  HATPMandatoryActivationReadiness` -- the sole production readiness
  entrypoint; resolves the protected root and repository identity
  internally, exactly mirroring `resolve_production_hatp_cutover_mode`.
- `activate_hatp_mandatory(root: HarnessPath, *, activated_by: str) ->
  CutoverRecord` -- the sole production `HATP_MANDATORY` activation
  entrypoint; resolves the protected root internally, performs a fresh,
  lock-held readiness re-evaluation immediately before the write.
- Internal test seams (never production-callable):
  `_assess_hatp_mandatory_activation_readiness_at_root`,
  `_activate_hatp_mandatory_at_root` -- mirror `_resolve_cutover_mode_
  at_root`'s existing shape exactly.
- `HATPMandatoryActivationReadinessError` -- raised when activation is
  attempted but readiness is unmet; no transition is persisted.

**No new module was created.** `_write_cutover_transition` (18A,
internal-only, never called with the production root anywhere) gained one
new, purely additive, optional keyword parameter, `readiness_check:
Optional[Callable[[], HATPMandatoryActivationReadiness]] = None`. Every
pre-existing caller of `_write_cutover_transition` (there were none in
production, and all 18A test callers) passes no such argument and
observes byte-identical behavior. When supplied and `target_mode ==
HATP_MANDATORY`, the callback is invoked exactly once, **while the
transition lock is still held**, immediately before the Cutover Record is
written.

**No application-level `ProtectedAdminPrincipal` was invented.** Wave F
reuses 18A's documented decision unchanged: the authority boundary is the
OS-level file-permission boundary on the fixed, non-agent-writable
protected root. `activate_hatp_mandatory` is, like `_write_cutover_
transition` before it, never called from any CLI/agent/environment path
in this repository (Sec.9).

## 7. Activation Readiness Type

`HATPMandatoryActivationReadiness(ready: bool, checks: Tuple[
HATPMandatoryActivationReadinessCheck, ...], reasons: Tuple[str, ...])`.
Authority-neutral: no field a caller can set to force `ready=True`.
`assess_hatp_mandatory_activation_readiness(root)` has exactly one
parameter (`root`) and produces a fresh result on every call -- no cache,
no memoization.

## 8. Activation Prerequisites (HMRC-REQ-054, exact conjunction)

1. `class_b_protected_storage_available` -- protected root exists as a
   real, non-symlink directory.
2. `repository_deployment_identity_valid` -- local
   `repository_instance_id` resolves to a valid UUID4.
3. `hatp_substrate_operational` -- `inspect_hatp_verification_substrate_
   readiness(...).operational` against the protected root (read-only,
   never provisions).
4. `hsce_signing_implementation_available` -- `hatp_signing_ceremony`
   module importable (structural presence check).
5. `mandatory_consumption_implementation_independently_verified` --
   **always reports unmet** on this repository today: the implementation
   (Waves A-F) is present, but 149O.19 (the dedicated 149O.16-class
   independent verification) has not yet run. This is the single
   dominant reason current readiness is `False` and is expected to remain
   so until 149O.19 completes.
6. `production_dependency_provenance_valid` -- `HATPTrustStore`
   construction over the protected root succeeds without exception.
7. `protected_activation_authority_mechanism_available` -- protected root
   permission bits exclude group/other write.

Per **HMRC-REQ-055** (load-bearing, confirmed against the contract text
directly, not assumed): activation does **not** additionally require the
MC-14 real-effect PB-`ALLOW` execution capability to exist -- only that
*truthful* enforcement be structurally present (owned by `hatp_rollback_
consumption.py`/the permission-broker production module, unchanged by
this phase). No readiness check queries PB or requests `ALLOW`
(`test_readiness_never_calls_permission_broker_or_uses_simulation_
result`).

## 9. Freshness, Locking, PREPARED Requirement, No Real Activation

- **Fresh readiness**: recomputed on every `assess_hatp_mandatory_
  activation_readiness` call and again, independently, inside
  `activate_hatp_mandatory`'s own lock-held write path -- no cached
  "was ready" result is ever trusted at write time.
- **Locking**: `activate_hatp_mandatory` -> `_write_cutover_transition`
  acquires the same `fcntl.flock` exclusive lock 18A already uses,
  re-resolves the current mode fresh, validates the transition, performs
  the readiness re-check, and only then writes -- all inside one lock
  hold. Concurrency test (`test_concurrent_activation_attempts_no_
  duplicate_marker_no_corruption`): 6 concurrent threads, exactly 1
  success, 5 rejected, no duplicate/corrupt marker.
- **PREPARED requirement**: activation is structurally `PREPARED ->
  HATP_MANDATORY` only, enforced by the same `is_valid_cutover_
  transition` every other transition uses. No caller-supplied target
  mode exists on `activate_hatp_mandatory`'s signature (`root,
  activated_by` only).
- **Failed activation side effect**: none. When readiness is unmet, no
  Cutover Record is written and the existing `PREPARED` record (if any)
  is left byte-identical (`test_activation_refused_when_readiness_
  unmet_and_no_record_written`).
- **No real production activation**: every test in this phase uses an
  isolated `tmp_path`-rooted protected root via the internal test seams.
  `test_real_production_protected_root_untouched_by_this_suite` confirms
  no new cutover state exists at the real production location as a side
  effect of this phase's own test run.
- **Current readiness result on this deployment**: `False`. Dominant
  reasons: no provisioned Class-B protected root on this development
  host, and item 5 above (149O.19 independent verification not yet
  performed) -- exactly the outcome HMRC-001's own prerequisites predict,
  not assumed.

## 10. Current POL-005 Consequence (confirmed, not worked around)

`ExecutionDisabledRule` (POL-005, `permission_broker_foundation.py`)
remains byte-unchanged: `simulation_only=False` unconditionally resolves
`DENY` (`decision_reason="execution_boundary_unavailable"`). Every
assembled real-effect test in this phase that exercises the real,
unmodified dependency chain (no test seam) confirms `DENY` and zero
effect: `test_attack_09_expired_proof`-style adapter tests and, at the
CLI layer, `test_ag3_cli_assembled_current_real_pol005_deny_zero_effect`
/ `test_ag5_cli_assembled_current_real_pol005_deny_zero_mutation`. This
was never monkeypatched or weakened.

## 11. Regressions, Findings, Retained Observations

No blocking finding. No new defect found in A-E's implementation; the
149O.18C identity-absence correction, 149O.18D RER terminal-status
handling, 149O.18B RAE lookup-key design, and 149O.18A single-slot
topology observation were each re-attacked (Sec.5, misc items 105-109)
and confirmed unchanged/correct.

Two 149O.18A-era phase-boundary test assertions in `tests/test_phase_
149o_18a_hatp_mandatory_cutover_state_foundation.py`
(`test_only_the_new_cutover_module_was_added_to_src_pcae` /
`test_no_forbidden_production_file_touched`) were already stale before
this phase started (invalidated by 149O.18B-149O.18E's own legitimate
production changes, never repaired at the time) and one additional
assertion (`test_internal_test_seam_never_paired_with_production_root_
in_module_source`) became stale as a direct, intentional consequence of
this phase's own Sec.6 addition. All three were updated in place
(149O.5-F-3 methodology: update the stale snapshot to the corrected
expectation, document the reason, never delete the underlying security
check) -- see the updated file's inline `149O.5-F-3 note`.

A second round of A/B-attributed sweeps (`git`-worktree baseline at the
pre-149O.18F commit vs. the working tree) surfaced eight further stale
assertions, all newly invalidated by this phase's own additive extension
of `hatp_mandatory_cutover.py`, and two genuine (not merely stale)
findings in this phase's own first-draft implementation:

- **Genuine finding, repaired**: the first-draft readiness/dependency
  checks called the `HATPTrustStore(...)` raw constructor directly
  inside `hatp_mandatory_cutover.py` (via the `_test_only_root=`
  test-only seam, misused from production code) -- a real violation of
  this repository's "only `hatp_bootstrap.py` itself, or the
  `.production()` factory, may construct `HATPTrustStore`" boundary
  (`tests/test_phase_149o_1f_2_..._reverification.py::
  test_ordinary_production_construction_uses_factory_not_raw_
  constructor`) and of the narrower "only `rollback_approval_evidence.py`
  may call `inspect_hatp_verification_substrate_readiness`" allowlist
  (`tests/test_phase_149o_1j_..._verification.py::
  test_no_production_call_sites_for_verify_hatp_proof_outside_own_
  module`). Fixed by threading an already-resolved `trust_store` object
  through `_assess_hatp_mandatory_activation_readiness_at_root`/
  `_activate_hatp_mandatory_at_root` instead of reconstructing one
  internally -- the public wrappers (`assess_hatp_mandatory_activation_
  readiness`/`activate_hatp_mandatory`) resolve `HATPTrustStore.
  production()` exactly once via the existing factory and pass the
  instance down; test callers construct their own isolated instance in
  the *test file*, never in production source. The 149O.1J allowlist test
  was updated in place to add `hatp_mandatory_cutover.py` as a second,
  narrowly-scoped, documented legitimate consumer of the read-only
  substrate-readiness inspection (HMRC-REQ-054 requires exactly this
  check) -- the `verify_hatp_proof` restriction itself is untouched.
- **Stale assertions, updated per 149O.5-F-3** (six tests across four
  files, each pinned from an open-ended `HEAD` comparison to the
  historical phase's own frozen entry/completion commit range, so each
  test again verifies only what it was written to verify):
  `test_phase_149o_15_..._contract_freeze.py::
  TestNoProductionOrExistingContractChange::test_no_src_pcae_files_
  changed`; `test_phase_149o_18c_..._integration.py::
  TestClassifiedCutoverResolverCorrection::test_diff_confined_to_one_
  function`; `test_phase_149o_18d_..._integration.py::
  TestProductionFileAllowlist::test_18a_cutover_module_byte_unchanged`;
  and three in `test_phase_149o_18e_..._integration.py::
  TestProductionFileAllowlist` (`test_18a_cutover_module_byte_unchanged`,
  `test_exactly_expected_files_changed`, `test_no_forbidden_production_
  file_touched`).

A/B-confirmed via an isolated `git worktree` at the pre-149O.18F commit
(`0881346a`): **zero new test failures anywhere in either the broad
HMRC/HATP/RAE/PB sweep or Fast Green** after these repairs -- the only
delta from baseline in both suites is the 2 fixed 149O.18A assertions
above (net -2 failures in each). See Sec.14.

Retained, unchanged by this phase: single-slot protected-root topology
(149O.18A, non-blocking deployment-topology limitation, fail-closed);
RAE lookup-key design (149O.18B); HMRC N-1 category-index omission of
REQ-083-085 (149O.16); REQ-080 duplicate-numbering editorial observation
(149O.17); 149O.12B-Obs-PY39-1 (independently confirmed resolved,
149O.16.2); double-Z CPython 3.9 `fromisoformat` quirk (repository-wide
parser-hardening debt, not inherited by this module's own strict-regex
timestamp parser, unchanged); historical monkeypatch fixtures (no
cleanup, out of scope).

**Pre-existing, unrelated test-environment finding** (independently
A/B-confirmed via `git stash -u`, present identically with and without
this phase's changes): `test_hatp_mandatory_cutover.py::
test_accept_strict_timestamp[2026-08-08T12:00:00.0Z]` fails under this
host's `.venv` interpreter -- a single-digit-fraction ISO timestamp
(`.0Z`) that a different CPython minor version accepted is rejected by
`datetime.fromisoformat` on the interpreter actually in use here. Not
caused by, and not repaired by, this phase (parser-hardening debt,
consistent with the retained double-Z finding above). See Sec.14 (Fast
Green) for the interpreter-version discrepancy this finding sits inside.

No HATP_MANDATORY activation occurred against any real deployment. No
production Cutover Record or activation marker was created outside an
isolated test fixture. Runtime remains `Observed / observe / unavailable`.
Current deployment cutover mode remains non-mandatory (unchanged,
confirmed by re-running `resolve_production_hatp_cutover_mode` against
the real host both before and after this phase's test suite executes).

## 12. B-149O-1..4

Unchanged. Remain **INDEPENDENTLY VERIFIED AT THE HATP-GATED AUTHORITY
BOUNDARY -- SYSTEM EXECUTION CLOSURE DEFERRED**. This phase's own
assembled 45-attack pass and activation-guard implementation are **not**
a substitute for 149O.19's independent re-derivation; 149O.19 must
re-attempt all 45 attacks against the real merged code without trusting
this phase's own tables, perform a fresh exhaustive caller-inventory
audit, and formally re-assess B-149O-1..4 against HMRC-REQ-083's 7 listed
conditions.

## 13. HMRC Implementation Completeness

- **85/85 requirements**: mapped to a production owner, wave, and test
  (Sec.2 for the Wave-F subset; the 149O.17 plan Sec.6/Sec.15 and each of
  18A-18E's own phase documents cover the remaining requirement rows,
  restated and cross-checked, not re-derived from scratch, per this
  phase's mandate to assemble rather than re-verify A-E).
- **14/14 invariants**: Sec.4 above.
- **45/45 attacks**: Sec.5 above, mechanically enforced by
  `test_exactly_45_attacks_structured_no_gaps_no_duplicates` and
  `test_all_45_attacks_have_at_least_one_executed_representative_test`.

## 14. Test Evidence

Three new test modules, all added to Fast Green:

- `tests/test_hatp_mandatory_activation_guard.py` (22 tests): readiness
  result shape, no-caller-input signatures, honest not-ready result on an
  unprovisioned fixture, no-PB/no-simulation-probe in readiness, no
  provisioning side effect, no caller override on `activate_hatp_
  mandatory`, PREPARED requirement, failed-readiness-blocks-activation
  with zero partial write, mid-flight readiness-becomes-false, successful
  isolated activation (readiness force-satisfied via test-only
  monkeypatch), 6-way concurrent-activation race (exactly 1 success, no
  corruption), monotonic no-downgrade, no real production root touch, no
  CLI/agent reference to the activation function, no env/repo-marker
  activation switch, wrong-repository activation rejection, no PB/Runtime
  touch on success.
- `tests/test_phase_149o_18f_hmrc_assembled_attack_matrix.py` (40 tests,
  representing all 45 attack numbers -- several tests each cover more
  than one closely-related attack number, tracked via an explicit
  `_represents(...)` registry mechanically cross-checked against the
  declared 45-row table): real `HATPEvidenceStore`/RAE-store/`verify_
  hatp_proof` integration for the crypto/binding-layer attacks (1-19,
  25-31, 34, 36-38, 43), real AG3/AG5/CLI/cutover-record integration for
  the effect-boundary/CLI/cutover-state attacks (20-24, 32-33, 35, 39-42,
  44-45).
- `tests/test_hatp_mandatory_consumption_assembled.py` (7 tests): full
  CLI (`pcae.cli.main`) -> `commands/agent.py` -> `core/agent.py` ->
  Wave B -> PB assembled integration for AG3/AG5, including a real temp
  git repo (AG3) and real temp filesystem (AG5), deterministic-ALLOW
  control-flow proof at the CLI layer, real current-POL-005-DENY
  zero-effect confirmation at the CLI layer (no test seam), and AG5
  dry-run zero-mutation/no-evidence-required across every cutover mode.

**Regression** (18A cutover suite + 18A phase-boundary suite): 184/185
(1 pre-existing, unrelated, A/B-confirmed environment failure,
`test_accept_strict_timestamp[...0.0Z]`) after the stale-assertion
updates (Sec.11).

**Broad HMRC/HATP/RAE/PB sweep** (`pytest -k "149o or hatp or rae or
permission_broker or rollback"`), final A/B-attributed via an isolated
`git worktree` at the pre-149O.18F commit (`0881346a`) rather than
`git stash` (all of this phase's changes are committed, not working-tree
diffs):

- Baseline (worktree at `0881346a`): 156 failed, 4405 passed, 4 skipped.
- With this phase's changes (final, after all repairs): 154 failed, 4476
  passed, 4 skipped.
- Exact failing-test-name diff (`comm` against sorted `FAILED` lines from
  both runs): **zero new failures introduced by this phase**; exactly the
  2 pre-existing 149O.18A stale assertions (Sec.11) are fixed and no
  longer fail. Every one of the baseline's 156 failures not among those 2
  remains present, byte-identically named, in the with-changes run --
  primarily CPython-version-dependent ISO-timestamp grammar-probe tests
  (`test_phase_149o_1h_6_...`, `test_phase_149o_1h_...`) and further
  historical "no production diff since my own baseline commit" snapshot
  assertions in numerous `test_phase_149o_*` files predating this phase.
  None of these are touched or claimed fixed by 149O.18F.

**Fast Green** (`pytest -m fast_green -n auto`), same worktree A/B
method:

- Baseline: 30 failed, 5389 passed, 1 skipped.
- With this phase's changes (final): **28 failed, 5460 passed, 1
  skipped**.
- Exact failing-test-name diff: zero new failures; exactly the same 2
  pre-existing 149O.18A assertions fixed, net -2. This 28/5460/1 triple
  is the value recorded in the structured `fast_green` metadata field
  (clean, attributable, no caveat string, per this project's governance
  rule that the structured field must never carry a raw count with a
  caveat).

This phase's own three new test modules (69 tests) and the 8 updated
historical phase-boundary assertions are 100% green in both the isolated
per-file runs and within both broad sweeps.

**Interpreter note**: this host's `.venv/bin/python3` reports Python
3.9.6; the ambient shell `python3` reports a materially newer version.
All test runs in this phase used `.venv/bin/python3 -m pytest`
consistently, matching 18A-18E's own convention as best could be
independently confirmed.

## 15. Assembled Implementation Verdict

```
HMRC-001 MANDATORY PRODUCTION CONSUMPTION: ASSEMBLED IMPLEMENTATION
COMPLETE -- READY FOR INDEPENDENT IMPLEMENTATION VERIFICATION

149O.18F: IMPLEMENTED -- READY FOR 149O.19
```

Not "VERIFIED" -- independent verification is 149O.19's obligation, not
self-certifiable by the phase that implemented the feature under test.

## 16. HATP Production Readiness

Remains **NOT READY**. This phase implements the activation guard and
proves the assembled system's attack resistance; it does not activate,
provision, or certify any real deployment. `assess_hatp_mandatory_
activation_readiness` against the real production root on this host
returns `ready=False` (Sec.9). No further implementation is recommended
before 149O.19 completes, unless 149O.19 finds a Blocking defect.

## 17. Recommended Next Phase

**149O.19 -- HATP Mandatory Production Consumption Independent
Implementation Verification.**
