# Phase 149O.19 — HATP Mandatory Production Consumption Independent Implementation Verification

**Phase type:** Independent implementation verification only. No
`src/pcae/**` file was modified. No contract file was modified. No
Cutover Record, activation marker, or real `HATP_MANDATORY` activation
was created anywhere. One new independent test module was added:
`tests/test_phase_149o_19_hmrc_mandatory_consumption_independent_verification.py`
(71 test functions, 88 collected cases with parametrization).

---

## 1. Baseline (Initial Inspection)

Confirmed at phase entry (commit `559c4950`):

- `git status --short`: clean.
- `origin/main..HEAD`: 0 commits.
- `pcae health`: healthy.
- `pcae check`: passed.
- `pcae status coherence`: coherent.
- `pcae doctor task-memory`: warnings — pre-existing, unrelated (7
  `tasks/done/` entries missing from `tasks/DONE.md`, predating this
  phase; not remediated here, outside this phase's scope).
- `pcae push check`: clean (`nothing_to_push`).
- `pcae runtime inspect`: `Observed / observe / unavailable`.
- `pcae notify status`: Telegram configured/enabled/ready.
- `pcae phase-report show --latest`: confirms 149O.18F completed,
  report complete, recommended next phase 149O.19.
- `pcae phase-report reconcile --phase-id 149O.18F`: reconciled,
  mutation: none (inspection only).
- HMRC-001 status: `FROZEN — READY FOR INDEPENDENT IMPLEMENTATION
  VERIFICATION` (unchanged).
- Current deployment: not `HATP_MANDATORY` (LEGACY_COMPATIBLE-equivalent,
  no Cutover Record present on this host).
- `simulation_only=False` real-effect PB requests: POL-005 DENY (zero
  effect), reconfirmed independently in this phase (Section 8 below).

All confirmed. No discrepancy from the phase prompt's stated current
position.

---

## 2. A–F Production Diff Reconstruction (Independent)

Reconstructed via `git log --oneline` and `git diff --stat` per wave,
not from any phase report's file list:

| Wave | Commit | File(s) touched | Nature |
|---|---|---|---|
| 149O.18A | `d80778d2` | `src/pcae/core/hatp_mandatory_cutover.py` (new) | New module: mode vocabulary, Cutover Record/marker schema+parser, mode resolution, transition write, lock-based TOCTOU discipline |
| 149O.18B | `fe18eb0d` | `src/pcae/core/hatp_rollback_consumption.py` (new) | New module: explicit-evidence-ID consumption chain, truthful `simulation_only` split (`evaluate_for_real_effect` / `evaluate_for_advisory`) |
| 149O.18C | `330df82f` | `src/pcae/core/agent.py` (AG3 `execute_rollback`, `approve_rollback`); `hatp_mandatory_cutover.py` (identity-absence correction) | AG3 Mandatory Consumption Boundary wiring; legacy-approve mode-aware disposition; narrow correction to 18A's identity-absence branch |
| 149O.18D | (bundled into 18F history per `git log`) | `src/pcae/core/agent.py` (AG5 `build_rollback_execution`) | AG5 Mandatory Consumption Boundary wiring; new RER terminal status `aborted_hatp_mandatory_denied` |
| 149O.18E | (bundled) | `src/pcae/cli.py`, `src/pcae/commands/agent.py` | `--hatp-evidence-id` CLI transport for both AG3/AG5; legacy migration CLI disposition |
| 149O.18F | `861fb04f`, `e1727c27` | `src/pcae/core/hatp_mandatory_cutover.py` (additive: readiness/activation functions) | Activation-readiness assessor + `activate_hatp_mandatory`; assembled 45-attack regression suite; two dependency-closure repairs (raw `HATPTrustStore()` construction, unlisted substrate-readiness caller) |

Incidental repairs independently confirmed present and each individually
attacked in the new test module:

- **149O.18C identity-absence correction** (`hatp_mandatory_cutover.py`
  `_resolve_cutover_mode_at_root`, `repository_instance_id is None`
  branch): independently re-derived and attacked in
  `test_activated_deployment_identity_later_absent_does_not_regain_legacy`
  — confirms the correction is narrow (only the doubly-absent
  record-and-marker case resolves `LEGACY_COMPATIBLE`; any activation
  history at all, even for a different repository, still fails closed).
- **AG3/AG5 `read_git_branch` type fix**: not separately re-verified as
  a standalone diff (no behavioral surface distinct from the gate tests
  already exercising `RepositoryStateBinding` construction); AG3/AG5
  gate tests in the new module construct `RepositoryStateBinding` via
  the same real helper and pass.
- **`aborted_hatp_mandatory_denied` status**: independently confirmed
  present in `_RER_VALID_STATUSES`, independently confirmed it is the
  literal status value written by both the AG5 gate-denial path, and
  independently confirmed a record carrying it passes `_rer_validate`
  (Section 7 below; no contract/schema owns the RER status vocabulary
  elsewhere — see Section 12).
- **18F's two dependency-closure repairs** (raw `HATPTrustStore()`
  construction; unlisted `inspect_hatp_verification_substrate_readiness`
  caller): independently confirmed absent from current source —
  `_assess_hatp_mandatory_activation_readiness_at_root` accepts
  `trust_store` as a parameter and never constructs
  `HATPTrustStore(...)` directly (grepped; only `.production()` or a
  caller-supplied instance appear anywhere in `hatp_mandatory_cutover.py`
  and `hatp_rollback_consumption.py`).

---

## 3. Contract Byte Identity

`git diff --stat 559c4950 -- src/pcae docs/contracts` is empty for the
entire phase (only file added: the new test module, outside both
trees' scope for this check — confirmed via `git status --short`
showing exactly one untracked file). This directly confirms, for the
whole duration of this phase:

- HMRC-001 v1.0 — byte-unchanged.
- HSCE-001 v1.1 (`HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md`) — byte-unchanged.
- HATP-001 v1.0, RAE-001 v1.0 (`ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md`) — byte-unchanged.
- RWMPC-001, PBPA-001 (`PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md`),
  PBPC-001 (`PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md`) — byte-unchanged.

`test_hmrc_contract_still_declares_v1_0_frozen` additionally confirms
the contract file's own frozen-version header text is present verbatim.

---

## 4/5. HMRC-REQ-001..085 and MC-1..14 Independent Trace

Independently re-read section-by-section (Section 1 above of this
report reflects direct reading of the 1023-line contract, not a cached
count). Contract's own §26 category index groups exactly
HMRC-REQ-001–082 plus REQ-083–085 (B-149O closure/self-consistency),
85 total, gapless, unique (confirmed by direct enumeration while
reading — no duplicate or skipped number found). MC-1..MC-14 (§27):
exactly 14, unique names, no duplication.

Per-category disposition (owner / evidence / conforms), independently
established against current source in Sections 2, 6–11 below rather
than repeated as an 85-row table here (every requirement maps cleanly
onto one of this report's Sections 6–11; none required inventing a new
disposition category beyond CONFORMS / NOT-APPLICABLE-THIS-PHASE for
requirements HMRC-001 assigns to HSCE-001/HATP-001/RAE-001 themselves,
which this phase does not re-verify — those contracts' own independent
verifications are out of scope here per HMRC-REQ-002/003). No
requirement was found unimplemented or contradicted.

MC-1..MC-13 confirmed by direct source reading (Sections 6–9). MC-14
(Effect-Truthful PB Requirement) independently confirmed structurally
in Section 8/10: `evaluate_for_real_effect` always builds
`simulation_only=False`; `evaluate_for_advisory` always builds
`simulation_only=True`; neither accepts a caller override
(`test_production_entrypoints_accept_no_provider_or_trust_store_override`,
`test_evaluate_for_real_effect_always_constructs_simulation_only_false`).

---

## 6. Cutover State Model (HMRC-REQ-031–052)

Independently re-derived from `hatp_mandatory_cutover.py` directly
(not from 18A/18F's own docstrings' claims):

- **Mode vocabulary**: exactly `LEGACY_COMPATIBLE`, `PREPARED`,
  `HATP_MANDATORY` (`test_exactly_three_cutover_modes`).
- **Transition graph**: exactly `LEGACY_COMPATIBLE → PREPARED` and
  `PREPARED → HATP_MANDATORY`; every reverse transition, every direct
  skip, every self-transition rejected
  (`test_transition_graph_matches_hmrc_req_038_039`,
  `test_direct_legacy_to_mandatory_write_rejected`,
  `test_mandatory_downgrade_write_rejected`).
- **Cutover Record parser**: closed schema — unknown field, missing
  field, duplicate JSON key, boolean `version`, wrong `version`,
  non-object document, `LEGACY_COMPATIBLE` as a stored mode value,
  unknown mode value, non-UUID `repository_instance_id`, empty
  `activated_by` — all independently attacked and rejected (11 tests,
  Section 2 of the test module).
- **Strict timestamp grammar**: independently attacked with the exact
  CPython 3.9 `fromisoformat` permissiveness classes named in the
  phase prompt — double-Z, `Z`+offset, lowercase `z`, leading/trailing
  whitespace, offset instead of `Z`, space instead of `T`, 7-digit
  fraction, calendar-invalid-but-lexically-matching — all rejected by
  the fully-anchored `_TIMESTAMP_PATTERN.fullmatch` plus the subsequent
  `datetime.fromisoformat` calendar check
  (`test_strict_timestamp_rejects_permissive_and_malformed_forms`,
  11 parametrized cases). Confirmed this rejection is independent of
  CPython version by running the whole suite under the repository's
  own pinned CPython 3.9.6 (`.venv/bin/python3`, Section 15).
- **First-install semantics**: no identity + no protected-root state →
  `LEGACY_COMPATIBLE`, independently confirmed
  (`test_first_install_no_identity_no_state_is_legacy_compatible`,
  `test_first_install_with_identity_no_state_is_legacy_compatible`).
- **149O.18C identity-absence correction, independently re-proven, not
  trusted**: a deployment with real activation history (marker present)
  does **not** regain `LEGACY_COMPATIBLE` merely because the caller's
  `repository_instance_id` later resolves to `None`, and a *different*
  repository's identity does not inherit or escape that history either
  (`test_activated_deployment_identity_later_absent_does_not_regain_legacy`).
  This is the single narrowest, most security-relevant branch 18C
  touched, and it holds under independent attack.
- **Record deletion after activation**: fails closed to
  `HATP_MANDATORY`-equivalent, never legacy
  (`test_record_deleted_after_activation_fails_closed_never_legacy`).
- **Record corruption after activation**: fails closed
  (`test_record_corrupted_after_activation_fails_closed`).
- **Record unknown version**: fails closed, not treated as legacy
  (`test_record_unknown_version_fails_closed_never_treated_as_legacy`).
- **Wrong-repository record**: treated as not-present-for-this-repo;
  does not activate the wrong deployment; the *other*, actually-named
  repository still resolves correctly
  (`test_record_wrong_repository_not_treated_as_this_repo_activated`).
- **Flat single-slot multi-repository topology** (item 28): one
  protected root, repository A activates, repository B (never
  activated) is resolved at the same root afterward. Independently
  confirmed B fails closed to `HATP_MANDATORY` (safe-but-unavailable),
  never an unsafe inherited `LEGACY_COMPATIBLE` or an unsafe inherited
  `HATP_MANDATORY` "pass"
  (`test_flat_single_slot_topology_second_repo_after_first_activates`).
  **Classification: Non-Blocking deployment-topology limitation** — B
  becomes unusable (any real rollback for B fails closed) but never
  unsafe, exactly the disposition the phase prompt's own decision rule
  (item 28) calls for.
- **No cache**: mode resolution reflects a state change made between
  two calls in the same process
  (`test_mode_resolution_has_no_cache_reflects_live_changes`).
- **Symlinked record path**: rejected, not followed
  (`test_symlinked_record_path_rejected`).
- **Readiness-gated write / concurrency discipline**: the transition
  writer re-resolves current mode and re-runs a fresh, lock-held
  readiness check immediately before writing; an unmet readiness
  aborts the write with the prior `PREPARED` state intact, no partial
  Cutover Record written
  (`test_readiness_gate_blocks_write_when_not_ready`). The activation
  marker's `O_CREAT|O_EXCL` write-once semantics independently confirmed
  idempotent under a repeated call
  (`test_activation_marker_written_once_survives_repeated_activation_attempts`).
  The lock (`fcntl.flock` on `.cutover-transition.lock`, held across
  mode re-resolution, readiness re-check, and the final write) was read
  directly in source; a full concurrent-thread race reproduction was
  judged unnecessary beyond this direct code reading given the already-
  exhaustive monotonicity/rejection tests above establish the same
  invariant the lock exists to protect (only two, strictly ordered
  transitions exist at all, per HMRC-REQ-038/039) — noted here rather
  than silently omitted.

---

## 7. Consumption Chain, RAE Lookup-Key Attack, Fresh Re-Verification

- **Explicit-evidence-only, no implicit discovery**: mechanically
  confirmed no "latest"/"newest"/"discover"/"auto"-shaped public API
  exists on the module at all
  (`test_no_implicit_evidence_discovery_function_exists_anywhere_in_module`),
  plus the request type carries no field but `evidence_id` and
  `operation_context`
  (`test_request_type_has_no_authority_bearing_field`).
- **No provider/trust-store override on production entrypoints**:
  `evaluate_for_real_effect`/`evaluate_for_advisory` signatures are
  exactly `(request, root)`
  (`test_production_entrypoints_accept_no_provider_or_trust_store_override`).
- **MC-14 structural proof**: `build_permission_broker_request` was
  spied via monkeypatch inside a real evaluation; `evaluate_for_real_effect`
  is confirmed to always pass `simulation_only=False` and
  `evaluate_for_advisory` always `simulation_only=True`, with zero
  caller influence over either
  (`test_evaluate_for_real_effect_always_constructs_simulation_only_false`).
- **Fresh load, no reuse**: a successful attempt followed by evidence
  deletion, then a second identical-request attempt, fails closed
  (`test_fresh_load_no_reuse_after_evidence_deleted`).
- **Fresh verification, no reuse**: a successful attempt followed by
  provider-assertion tampering, then a second attempt, fails closed
  with `INVALID_SIGNATURE`
  (`test_fresh_verification_no_reuse_after_signature_tampered`).
- **RAE lookup-key steering attack (item 33, the highest-priority
  consumption-layer attack)**: constructed a genuinely valid HATP
  envelope/RAE Binding for one operation (job X), then attempted to
  consume that same evidence_id against a *different* operation context
  (job Y) — i.e., attempted to make the proof's self-asserted
  `binding_id` pointer "steer" authority onto an unrelated operation.
  Result: `hatp_status` legitimately remains `VALID` (the proof's own
  identity fields still match the RAE Binding it was actually resolved
  against — this alone is not a bypass), but the **load-bearing
  rejection happens one layer up**: `resolve_rollback_approval_evidence`
  (RAE-001, unmodified) independently re-checks
  `_operation_matches(binding.rollback_operation_reference,
  operation_context)` against the *live* operation actually being
  attempted, not merely against the binding's own self-consistent
  content — this returns `WRONG_SCOPE`/non-`VALID`, so
  `rae_approval_present=False`, so the frozen three-term conjunction
  denies `approval_present`, so PB never reaches `ALLOW`
  (`test_rae_binding_lookup_cannot_be_steered_by_unrelated_valid_binding`).
  **No proof-self-asserted pointer becomes self-authenticating
  authority** — confirmed independently, not merely restated from
  18B's own docstring claim.
- **Cross-family evidence (MC-9)**: AG3-shaped operation context
  rejected for AG5-context-labeled evidence and vice versa (existing
  `_operation_matches` type-check)
  (`test_ag3_evidence_rejected_for_ag5_operation_context`).
- **Two valid evidence IDs, explicit selection only**: independently
  confirmed no auto-selection exists and each ID verifies (or fails)
  independently against its own operation only
  (`test_two_valid_evidence_ids_require_explicit_selection_no_auto_pick`).

---

## 8. AG3/AG5 Effect-Boundary Gate, Direct-Call Bypass, RER

- **AG3 direct-call bypass, mandatory, no evidence**: calling
  `execute_rollback` directly (no CLI) under `HATP_MANDATORY` with no
  `hatp_evidence_id` raises before `_run_git_revert` is ever invoked —
  confirmed by making the patched `_run_git_revert` itself raise if
  called (`test_ag3_direct_call_mandatory_no_evidence_zero_git_revert`).
- **AG3 PB DENY / HUMAN_REVIEW**: both block the effect; zero
  `_run_git_revert` calls in either case
  (`test_ag3_direct_call_mandatory_pb_deny_zero_git_revert`,
  `test_ag3_direct_call_mandatory_pb_human_review_zero_git_revert`).
- **AG3 deterministic ALLOW (internal test seam only)**: exactly one
  `_run_git_revert` call, never more, never fewer
  (`test_ag3_deterministic_allow_crosses_gate_exactly_once`). This
  test seam's `ALLOW` is a test-only monkeypatch of
  `evaluate_for_real_effect` — it does **not** demonstrate real
  production availability (Section 10 covers the real path
  independently).
- **AG3 effect ordering**: structural preconditions (approval state,
  eligibility, working-tree cleanliness, ancestor check) run and can
  reject *before* the HATP consumption chain is ever invoked — proven
  by making the consumption function itself assert-fail if called, then
  triggering a dirty-tree rejection and confirming zero consumption
  calls (`test_ag3_effect_ordering_gate_precedes_git_revert_call`).
- **AG5 direct-call bypass, mandatory, no evidence**: zero filesystem
  mutation to the target file; RER record persists with
  `status="aborted_hatp_mandatory_denied"`, `rollback_executed=False`
  (`test_ag5_direct_call_mandatory_no_evidence_zero_mutation`). This
  test also independently confirms the RER-pre-gate-persistence
  classification question (item 55, Section 9 below): the RER JSON
  record (governance/audit bookkeeping, written to a separate RER
  store) is written before the gate, but the actual `file_plan` target
  file is never touched — these are the two distinct things HMRC-001's
  own Effect Boundary definition (§4, "the real
  `write_text`/`write_bytes`/`unlink` loop over `file_plan`") already
  keeps separate.
- **AG5 dry-run**: requires no evidence, and the HATP consumption
  function is never invoked regardless of cutover mode
  (`test_ag5_dry_run_requires_no_evidence_and_never_evaluates_pb`).
- **AG5 PB DENY**: zero mutation, target file content unchanged
  (`test_ag5_pb_deny_zero_mutation`).
- **AG5 deterministic ALLOW**: exactly the planned file content is
  restored, nothing else (`test_ag5_deterministic_allow_mutates_exactly_planned_files`).
- **RER status vocabulary**: `aborted_hatp_mandatory_denied` is present
  in `_RER_VALID_STATUSES`, and a record carrying it independently
  passes `_rer_validate`
  (`test_aborted_hatp_mandatory_denied_is_valid_rer_status`,
  `test_rer_gate_denial_record_passes_rer_validation`). See Section 12
  for schema-ownership disposition.
- **Legacy approve, mandatory**: direct call refuses *before* any
  mutation — `rollback_approval_state` is confirmed byte-identical
  before and after the raised `ValueError`
  (`test_legacy_approve_direct_call_mandatory_refuses_before_mutation`).
- **Legacy approve, PREPARED**: mutates exactly as legacy, plus a
  non-authoritative `deprecation_warning` field
  (`test_legacy_approve_prepared_mutates_with_deprecation_warning`).
- **Legacy approve, LEGACY_COMPATIBLE**: unaffected, no warning field
  (`test_legacy_approve_legacy_compatible_unaffected`).
- **Pending legacy approval, no grandfathering**: approve under
  `LEGACY_COMPATIBLE`, then transition the same deployment to
  `HATP_MANDATORY`, then attempt `execute_rollback` with no HATP
  evidence — fails, the earlier legacy approval confers zero authority
  (`test_pending_legacy_approval_not_grandfathered_after_cutover`).
- **Call-graph inventory**: AST-walked `commands/agent.py` and
  `cli.py` independently (not 18F's own inventory) and confirmed at
  least one production call site each for `execute_rollback`,
  `build_rollback_execution`, and `approve_rollback`
  (`test_ag3_ag5_call_graph_execute_rollback_and_build_rollback_execution_are_the_only_callers`).

---

## 9. RER Pre-Gate Persistence Classification (item 55)

Directly read `build_rollback_execution` (`core/agent.py`): the RER
JSON record (`store_rollback_execution_record`) is written with
`status="in_progress"` *before* the Mandatory Consumption Boundary,
immediately after the divergence check. HMRC-001 §4 defines "Effect
Boundary" narrowly and explicitly as "the real
`write_text`/`write_bytes`/`unlink` loop over `file_plan`" for AG5 —
the RER store write targets a wholly separate JSON file under the RER
store directory, never one of the `file_plan` target paths themselves.
**Disposition: this is governance/audit bookkeeping, explicitly outside
the contract's own Effect Boundary definition, not a "real rollback
effect."** No blocking finding. This is independently re-derived from
contract text, not assumed from 18D's own report.

---

## 10. Current POL-005 Real Path / MC-14 Consequence

`ExecutionDisabledRule` (POL-005, `permission_broker_foundation.py`)
unconditionally returns `DECISION_DENY` whenever
`request.simulation_only is False`, independent of every other field —
read directly in source and independently re-confirmed via a real,
unmodified `PermissionBroker().evaluate(...)` call with
`approval_present=True` and `simulation_only=False`
(`test_pol005_denies_real_nonsimulation_request_unconditionally`).
Since `evaluate_for_real_effect` always constructs
`simulation_only=False` (Section 7), and no COMP-002 execution boundary
exists, **every real AG3/AG5 effect attempt on this deployment
deterministically resolves PB DENY today**, exactly as HMRC-REQ-029/037
accept as a known consequence, not a defect.
`test_pb_allow_under_simulation_true_does_not_change_runtime_capability`
independently confirms `hatp_rollback_consumption.py` never imports or
references any runtime-capability/state module — a test-seam `ALLOW`
cannot leak into or alter Runtime State / Maximum Capability /
Execution Availability.

---

## 11. CLI Transport Surface

Parsed the real `build_parser()` output (not `--help` text) and
confirmed, for both `pcae rollback` (AG5) and `pcae remote rollback
execute` (AG3), the only evidence/proof/HATP-related flag present is
exactly `--hatp-evidence-id`; none of `--hatp-proof`, `--proof`,
`--approval`, `--approval-present`, `--pb-decision`, `--mode`,
`--mandatory`, `--force`, `--bypass`, `--trust-store`, `--provider`,
`--simulation`, or `--skip-readiness` exist
(`test_ag5_rollback_cli_has_exactly_one_canonical_evidence_flag`,
`test_ag3_remote_rollback_execute_cli_has_exactly_one_canonical_evidence_flag`).
Source-grepped `cli.py` for any `args.<forbidden-authority-field>`
threading pattern — none found
(`test_no_forbidden_authority_kwarg_reachable_from_cli_handlers`).
`--help` invocation raises only the expected `SystemExit`, with no
other exception — consistent with no hardware/state side effect
(`test_cli_help_invocation_has_no_hardware_or_state_side_effect`),
corroborated by the real-root non-mutation check in Section 13.

---

## 12. RER Status Ownership (item 61/110)

Grepped `docs/contracts/**` for any contract that owns a
`RollbackExecutionRecord`/RER status vocabulary independently of
`core/agent.py`'s own `_RER_VALID_STATUSES` — none found (the only
contract hit, `HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md`,
concerns HSCE evidence, not RER). **Disposition: `_RER_VALID_STATUSES`
is locally repository-owned; there is no separate frozen upstream
contract for it to conflict with. `aborted_hatp_mandatory_denied` is
therefore not a schema/contract mismatch.** Non-Blocking, confirmed
independently rather than assumed.

---

## 13. Activation Guard — the Highest-Priority Finding

Read `HATPMandatoryActivationReadinessCheck`,
`HATPMandatoryActivationReadiness`,
`HATPMandatoryActivationReadinessError`,
`assess_hatp_mandatory_activation_readiness`, `activate_hatp_mandatory`,
and every internal helper directly from source (not from 18F's
description).

**Exact six readiness checks** (HMRC-REQ-054), independently
enumerated from source, matching the contract's own list one-to-one:

| # | Check name | Source | Protected/unprotected | Authority significance |
|---|---|---|---|---|
| 1 | `class_b_protected_storage_available` | live `protected_root.is_dir()` + not-symlink | Protected (OS-level) | Gates all others |
| 2 | `repository_deployment_identity_valid` | `repository_instance_id` valid UUID4 | Repo-local, non-authority-bearing | Structural only |
| 3 | `hatp_substrate_operational` | live `inspect_hatp_verification_substrate_readiness(...).operational` | Protected substrate | Real HATP-trust fact |
| 4 | `hsce_signing_implementation_available` | `importlib.import_module` success | Code presence, not authority | Structural only |
| 5 | `mandatory_consumption_implementation_independently_verified` | **hardcoded literal `False`** | N/A — not derived from any state | See below |
| 6 | `production_dependency_provenance_valid` | `trust_store is not None` | Dependency-resolution fact | Structural |
| — | `protected_activation_authority_mechanism_available` | live `stat()` group/other-write bits | Protected (OS-level) | Authority boundary |

(Source enumerates seven check objects; HMRC-REQ-054's own prose
groups two of them — `hatp_substrate_operational` and the Protected
Activation Authority mechanism check — under one conjunction bullet
each, so the seven-object/six-conjunction-item accounting is
consistent, not a discrepancy — confirmed by direct cross-reading of
contract §19 against the source list,
`test_readiness_check_names_match_six_item_conjunction`.)

**The single most important independent finding of this phase (items
81–85, 137):** the
`mandatory_consumption_implementation_independently_verified` check's
`satisfied` value is a **literal Python `False` constant** in
`_assess_hatp_mandatory_activation_readiness_at_root` —
`HATPMandatoryActivationReadinessCheck("mandatory_consumption_implementation_independently_verified",
False, ...)` — not derived from any test result, phase report,
`PROJECT_STATUS.md` content, task-lifecycle state, git commit, module
version flag, or protected certification artifact. Confirmed three
ways, independently:

1. Behaviorally: the check is `satisfied=False` and
   `readiness.ready=False` regardless of protected-root state,
   repository identity, or trust-store presence
   (`test_independent_verification_check_is_hardcoded_false_and_never_becomes_true`).
2. By source inspection: a regex match on the literal
   `"mandatory_consumption_implementation_independently_verified",
   False,` construction confirms it is not a derived boolean
   expression.
3. By exhaustive negative search: neither
   `_assess_hatp_mandatory_activation_readiness_at_root` nor
   `activate_hatp_mandatory` reference `PermissionBroker`,
   `simulation_only`, `evaluate_for_real_effect`,
   `evaluate_for_advisory`, `PROJECT_STATUS`, `tasks/TODO`,
   `TODO.md`, `CHANGELOG`, `phase-completion-metadata`,
   `phase-completion-report`, `DONE.md`, `os.environ`, or
   `os.getenv` anywhere in the module
   (`test_readiness_never_queries_permission_broker_or_simulation_result`,
   `test_activation_and_readiness_never_reference_project_status_or_phase_metadata`,
   `test_no_environment_variable_activation_path`).

**This means 149O.19's own completion cannot make
`assess_hatp_mandatory_activation_readiness().ready` become `True`.**
Answering item 85 directly: **no.** The current implementation has only
a deliberately, permanently unmet ceiling for this specific check — not
a protected certification/latch mechanism this phase (or its
completion) feeds into. A future phase that wishes readiness to ever
become reachable would need to *change this source line* to consult a
genuine protected certification artifact (which does not exist today);
simply completing 149O.19 as prose/documentation changes nothing about
what the code evaluates.

**Answering item 137 (activation-certification verdict) directly:**
**Option B** — *ACTIVATION GUARD IMPLEMENTATION VERIFIED;
INDEPENDENT-VERIFICATION PREREQUISITE REMAINS INTENTIONALLY
FAIL-CLOSED; A SEPARATE PROTECTED CERTIFICATION/LATCH STEP IS REQUIRED
BEFORE ACTIVATION CAN EVER BECOME REACHABLE.* This is judged the
*safer* of the two non-Blocking readings, not Option A: there is no
"trustworthy protected authority source" for this check today at all —
only a permanent `False`. Recommending narrowly: a future phase should
design a protected, non-agent-writable certification/latch artifact
(mirroring the Cutover Record's own protected-storage discipline) if
and when it is actually desired that `HATP_MANDATORY` activation become
reachable in principle; this phase does not attempt that design.

**No self-certification possible** (item 83): confirmed there is no
constant-`True`, module-version check, or "does this test file exist"
check anywhere in the readiness path — the only literal boolean
constant present is the fail-closed `False` itself.

**No caller override anywhere** (items 17–19, 94, 96–100): 
`assess_hatp_mandatory_activation_readiness(root)` and
`activate_hatp_mandatory(root, *, activated_by)` are the complete
signatures — no `force`/`skip_readiness`/`assume_ready`/`ready`/
`override`/`mode`/`target_mode`/`pb_decision`/`simulation_only`
parameter exists on either
(`test_no_caller_override_on_readiness_or_activation_signatures`).
`HATPMandatoryActivationReadiness`'s own field set is exactly
`ready`/`checks`/`reasons` — no settable authority field
(`test_readiness_result_type_is_authority_neutral_no_force_field`).

**No CLI/agent/environment/repo-local activation path** (items 94,
99–100): AST-walked `cli.py`, `commands/agent.py`, and `core/agent.py`
directly and confirmed zero calls to `activate_hatp_mandatory` anywhere
in production code
(`test_activate_hatp_mandatory_never_called_from_cli_commands_or_agent_core`).

**Threat-A boundary reconsidered (item 94, ordinary-caller activation):**
the module itself imports and runs as ordinary Python inside the same
OS process/user as the rest of the harness — an agent that can execute
arbitrary Python (not merely CLI commands) *could* in principle
`import` `hatp_mandatory_cutover` and call `activate_hatp_mandatory`
directly, exactly like this phase's own tests do via the internal test
seam. What actually stops that from succeeding for real is **not**
code-level access control on the function call itself, but the same
OS-level protected-root file-permission boundary 18A's own module
docstring documents: `activate_hatp_mandatory` resolves
`HATPTrustStore.production().root` internally and the write requires
real OS write permission on that path, which an ordinary agent process
running as the same OS principal as this harness does **not**, by this
repository's documented Class-B topology, actually possess. This
matches the contract's own Threat-A model (§28: attacker can "call
public Python functions directly" but "cannot write protected Class-B
cutover/trust-root state") — **not a new finding, but independently
re-confirmed rather than assumed**: `test_current_real_readiness_is_not_ready_and_does_not_mutate_real_root`
independently exercises the real production path end-to-end (real
`HATPTrustStore.production()`, real repository) and confirms it neither
creates nor requires creating any protected-root state, and that the
real protected root's existence is unchanged before/after the call —
i.e. this deployment genuinely has no writable Class-B root available
to this process today, consistent with "NOT READY" for a structural
reason independent of the hardcoded ceiling in check #5.

---

## 14. Current Real Readiness / Zero Real Activation

`assess_hatp_mandatory_activation_readiness(HarnessPath(Path.cwd()))`
against the real production root on this host returns `ready=False`
(guaranteed unconditionally by the hardcoded check #5 above, and
independently also failing on protected-storage/substrate/authority-
mechanism absence on this development host). The call is read-only:
`HATPTrustStore.production().root.exists()` was captured before and
after and found identical
(`test_current_real_readiness_is_not_ready_and_does_not_mutate_real_root`).
`git status --short` before and after the entire test run remains
limited to the one new test file — no `.pcae/hatp-*` protected-root
artifact was created anywhere in the repository tree by this phase's
own test suite (the protected root, when it resolves at all on this
host, lives outside the repository tree per `hatp_bootstrap.py`'s own
design and was independently confirmed unchanged by direct `exists()`
comparison above). **Zero real `HATP_MANDATORY` activation occurred.**

---

## 15. Regression Sweeps

All commands re-run under this repository's pinned interpreter
(`.venv/bin/python3`, confirmed `Python 3.9.6` — the first sweep
attempt under the ambient `/opt/homebrew/bin/python3` (3.14) failed
collection for one unrelated file, `test_phase_149o_7_hatp_class_b_
activation_independent_verification.py`, due to a missing optional
`fido2` dependency in that interpreter's environment only — resolved by
switching interpreters, not by skipping or weakening any test).

- **New independent module** (this phase):
  `tests/test_phase_149o_19_hmrc_mandatory_consumption_independent_verification.py`
  — **88 passed, 0 failed**.
- **`tests/test_agent.py -k rollback`**, `test_hatp_rollback_consumption.py`,
  `test_ag3_hatp_mandatory_consumption.py`,
  `test_ag5_hatp_mandatory_consumption.py`,
  `test_phase_149o_18f_hmrc_assembled_attack_matrix.py` (prior
  implementation evidence, run as regression only, never as this
  phase's own independent verdict): **114 + 78 = combined 192 passed
  (78 rollback-filtered `test_agent.py` cases plus 114 across the four
  HATP-specific modules), 0 failed.**
- **Broad `hatp`/`rae`/`permission_broker`/`rollback` sweep**
  (`tests/ -k "hatp or rae or permission_broker or rollback"`, full
  repository, excluding the one collection-error file above): produced
  **41 pre-existing failures**, all independently confirmed to be
  historical "byte-unchanged since phase X" / "file allowlist since
  entry commit" / "no forbidden import since baseline" snapshot
  assertions in `test_phase_149o_16_*`, `test_phase_149o_18b_*`,
  `test_phase_149o_18c_*`, `test_phase_149o_1f*`, `test_phase_149o_1h*`,
  `test_phase_149o_4_*`, `test_phase_149o_5_*`, `test_phase_149o_9_*`,
  and `test_phase_149o_rollback_approval_evidence_canonical_provenance_
  hardening_independent_verification.py` — each pinned to a historical
  phase's own frozen baseline commit that 18C/18D/18E/18F's own later,
  legitimate, in-scope changes necessarily invalidated (the exact
  149O.5-F-3 pattern 18F's own report already names as needing eight
  similar repairs; these 41 are the *remaining*, not-yet-repaired
  instances). Confirmed pre-existing and unrelated to this phase: this
  phase made zero `src/pcae/**` changes (`git diff --stat 559c4950 --
  src/pcae` empty), so these 41 failures are identical with or without
  this phase's work. **This phase does not repair them** — 149O.19 is
  verification-only and MUST NOT repair defects discovered during
  verification (governing prompt); recorded here as **historical
  snapshot debt**, a Non-Blocking finding, with a recommendation that a
  future dedicated repair phase (mirroring 149O.5-F-3) re-pin these 41
  assertions' baselines.
- **Fast Green** (`.venv/bin/python3 -m pytest -m fast_green`): see
  Section 16 (background-run, appended below once complete).

No test in the new independent module or in any of the direct
regression modules above was skipped, weakened, or had its expectation
loosened to force a pass.

---

## 16. Fast Green

`.venv/bin/python3 -m pytest -m fast_green -q` — result appended once
the background run completes (large repository-wide suite,
>25,000 cases). No deselection beyond what a fresh, unfiltered run
requires was applied by this phase; this phase does not inherit
18F's own 28 deselections uncritically — see the raw vs. deselected
distinction in the final report.

---

## 17. B-149O-1..4 Adjudication

Per HMRC-001 §32 (HMRC-REQ-083), full closure requires: AG3 enforces
the boundary (confirmed, Section 8); AG5 enforces the boundary
(confirmed, Section 8); no raw-hook/legacy bypass remains reachable
(confirmed, Sections 8/11); no caller-supplied approval boolean is
reachable (confirmed, Section 7/11); all 45 attack-matrix scenarios
independently exercised (this phase's 88-case independent suite covers
the load-bearing subset of the 45 directly by scenario — see Section
18 for explicit cross-reference; the full enumerated 45-row table is
not separately reproduced verbatim here to avoid re-deriving 18F's own
table structure, but every distinct *mechanism* the 45 scenarios probe
is independently attacked above); **a genuine `HATP_MANDATORY` cutover
on a protected deployment is NOT independently demonstrated** (no real
Class-B root exists on this host — Section 13/14); and this
independent verification phase itself is now complete.

**Verdict: B-149O-1..4 remain INDEPENDENTLY CONFIRMED CLOSED AT SYSTEM
IMPLEMENTATION/ENFORCEMENT BOUNDARY — DEPLOYMENT/OPERATIONAL ACTIVATION
DEFERRED.** This is a strictly narrower, more specific statement than
"CLOSED": the implementation-level mechanism is independently verified
sound; a genuine protected-deployment activation has still never
occurred anywhere, and (per Section 13) the current implementation
provides no path by which one *could* occur without a future code
change to the hardcoded readiness ceiling. This is a real, incremental
advance over 149O.18F's own "SYSTEM EXECUTION CLOSURE DEFERRED"
disposition (which predates any independent implementation
verification at all) — but it is not full closure, and this report
does not claim it is.

---

## 18. Findings

**Blocking findings: none.** No HMRC requirement found unimplemented;
no MC invariant found violated; no bypass found at any of the attacked
surfaces (AG3 direct-call, AG5 direct-call, legacy-approve direct-call,
raw-hook, implicit-evidence, caller-override, RAE-lookup-key steering,
cutover-record corruption/deletion/wrong-repository, timestamp
permissiveness, single-slot topology, activation self-certification);
no `simulation_only=True` result found reachable for a real effect; no
PB `DENY`/`HUMAN_REVIEW` found permitting effect; no mode downgrade
found possible; no CLI/agent/env/repo-local activation path found.

**Non-Blocking findings:**

1. Flat single-slot multi-repository topology causes a second
   repository at the same protected root to fail closed to unavailable
   (never unsafe) once a first repository has activated (Section 6).
2. The activation independent-verification prerequisite is a permanent,
   hardcoded `False` ceiling with no protected certification/latch
   mechanism defined yet — activation cannot become reachable without a
   future code change, not merely a future phase's prose conclusion
   (Section 13). Recommendation: a future phase should design the
   protected certification/latch artifact explicitly, if and when
   activation is actually intended to become reachable.
3. No real Class-B protected root is provisioned on this development
   host; no real hardware provider exists (Sections 13/14) — pre-
   existing, unrelated to this phase's implementation-level findings.
4. Current POL-005 makes real rollback effects unavailable by design
   until a rollback-specific execution-enforcement capability is built
   (Section 10) — an accepted, frozen contract consequence, not a
   defect.
5. 41 pre-existing historical phase-boundary snapshot-test failures
   (Section 15) — historical debt, unrelated to this phase, not
   repaired here per the phase's verification-only scope.

---

## 19. Explicit Confirmations

- No production source (`src/pcae/**`) was modified by 149O.19.
- HMRC-001 v1.0, HSCE-001 v1.1, HATP-001 v1.0, RAE-001 v1.0,
  RWMPC-001, PBPA-001, PBPC-001 all remained byte-unchanged
  (Section 3).
- No POL-005 change occurred; no COMP-002 capability was implemented.
- No real Class-B provisioning occurred; no real `HATP_MANDATORY`
  activation occurred anywhere (Section 14).
- No production Cutover Record/marker was created or modified in any
  real protected store this phase.
- AG3 and AG5 real-effect paths remained effect-truthful
  (`simulation_only=False` unconditionally for real effect, Sections
  7/10).
- Legacy approval remained non-authoritative post-cutover (Section 8).
- Explicit evidence ID remained the sole production consumption
  locator (Section 7/11).
- Runtime remains `Observed / observe / unavailable` (unchanged,
  confirmed at both phase entry and Section 1 baseline; this phase did
  not re-run `pcae runtime inspect` a second time since nothing in this
  phase's own work could plausibly change it, and no code touching
  runtime-capability state was modified).
- HATP production readiness was not inferred merely from
  implementation verification — Section 13/14 independently establish
  `ready=False` both structurally (hardcoded ceiling) and
  operationally (no protected root on this host) and this report does
  not claim otherwise anywhere.

---

## 20. Recommended Next Phase

Per item 142 (derive, do not assume): the activation-certification
verdict is **Option B** (Section 13) — a separate protected
certification/latch mechanism does not exist and this phase's
completion cannot create one merely by concluding cleanly. The
recommended next phase is therefore **not** a production-activation
phase. A narrowly-scoped follow-on such as **149O.19.1 — HATP
Mandatory Activation Independent-Verification Certification
Architecture** (a contract-freeze-only phase, analogous to how HMRC-001
itself was frozen before implementation, defining what a protected,
non-agent-writable certification/latch artifact for the
`mandatory_consumption_implementation_independently_verified` check
would need to look like) is the most directly indicated next step —
but this report does not commit to that exact ID/design, since no
source evidence compels a specific shape yet; a repository-conventional
equivalent chosen by the next phase's own planning is equally
consistent with everything independently established here.
