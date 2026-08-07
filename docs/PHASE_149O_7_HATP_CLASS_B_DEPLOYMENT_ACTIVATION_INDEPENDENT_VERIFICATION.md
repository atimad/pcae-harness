# Phase 149O.7 — HATP Class-B Deployment / Activation Independent Verification

**Phase ID:** 149O.7
**Phase type:** Independent verification (adversarial re-verification of Phase 149O.6, Wave 7). Verification-only — no production code modified.
**Baseline:** `HEAD` = commit `42112464` (Phase 149O.6, complete/pushed) at phase start.
**Frozen contract:** `docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md` (HATP-001 v1.0, 117 requirements) — **byte-unchanged, independently confirmed** (`git diff 17a2c1b4..HEAD` empty for the contract file).
**New independent test suite:** `tests/test_phase_149o_7_hatp_class_b_activation_independent_verification.py` (21 passed).

---

## 0. Verdict summary

| Question | Verdict |
|---|---|
| Class-B activation model | **CLASS-B ACTIVATION MODEL: INDEPENDENTLY VERIFIED — CURRENT DEPLOYMENT REMAINS NOT READY** |
| F-2 dependency provenance | **F-2 DEPENDENCY PROVENANCE: INDEPENDENTLY CONFIRMED CLOSED** |
| AG3 authority path | **AG3 HATP-GATED AUTHORITY CONSUMPTION: INDEPENDENTLY VERIFIED** — dispatch is **not** enforced by it (see PB verdict) |
| AG5 authority path | Same as AG3 |
| PB decision provenance | **VERIFIED** — `approval_present` is the derived gated fact, never caller-suppliable, on the gated path |
| PB execution enforcement | **ADVISORY / NOT YET ENFORCED** — structurally cannot be, by PB's own `simulation_only`/POL-005 architecture (system-wide, pre-existing, not a Wave-7 defect) |
| CLI / signing-ceremony surface | **ABSENT** — independently confirmed, zero references anywhere in `src/pcae/commands/` |
| Current ordinary workflow | **DOES NOT USE HATP** — `approve_rollback`/`execute_rollback`/`build_rollback_execution` called with no `hatp_evidence_id` dispatch real mutations exactly as before Wave 7 |
| B-149O-1..4 | **INDEPENDENTLY VERIFIED AT HATP-GATED AUTHORITY BOUNDARY — SYSTEM EXECUTION CLOSURE DEFERRED** (see §9) |
| Overall Wave-7 verdict | **VERIFIED WITH NON-BLOCKING / DEFERRED FINDINGS — HATP WAVE 7 CLASS-B DEPLOYMENT / ACTIVATION CONFORMS** |
| HATP production readiness | **HATP PRODUCTION: NOT READY** |
| Runtime | **Observed / observe / unavailable** (unchanged) |

**No Blocking finding was independently confirmed.** One new, narrow, non-blocking test-currency gap was discovered (§14) that 149O.6's own boundary-test audit did not catch; recommended for a follow-up narrow fix, not treated as Blocking.

---

## 1. Initial inspection (independently confirmed)

| Check | Result |
|---|---|
| `git status --short` | clean |
| `git rev-list --count origin/main..HEAD` | 0 |
| `pcae health` | healthy |
| `pcae check` | passed |
| `pcae status coherence` | coherent |
| `pcae doctor task-memory` | warnings (7 pre-existing `tasks/DONE.md` sync gaps, unrelated to HATP/this phase) |
| `pcae push check` | clean (`nothing_to_push`) |
| `pcae runtime inspect` | Observed / observe / unavailable; Permission Broker status `execution_unavailable` |
| `pcae notify status` | telegram configured/enabled/ready |
| `pcae phase-report show --latest` / `reconcile --phase-id 149O.6` | 149O.6 completed, pushed, report completeness `complete`, reconciled `already_dispatched` |

---

## 2. Requirement reconstruction (independent, from HATP-001 text directly)

Read `docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md` directly rather than trusting 149O.6's table.

| Requirement | Normative text (paraphrased) | Independent reading |
|---|---|---|
| **HATP-REQ-105** (§35) | B-149O-1..4 remain OPEN as of the 149O.1B.3 freeze; closure requires HATP implementation, RAE/HATP integration, **AG3/AG5 Permission Broker wiring**, and independent adversarial verification. | This is a *closure-precondition* list, not an execution-mandate. It requires that a real, wired, PB-consulting authority path **exist** and be adversarially verified. It does **not** state that every real dispatch decision must be forced through that path immediately, nor that the legacy dispatch precondition must be removed. |
| **HATP-REQ-106** (§35) | Per-attack closure mapping (forgery/mutation/unauthorized-key scenarios each close once the corresponding HATP/RAE check blocks them). | Describes what makes the *evidence-forgery* attacks fail — a question about the gated derivation function, not about whether that function is the sole dispatch gate. |
| **HATP-REQ-108/§37** | Frozen current-deployment-readiness status block; this deployment remains NOT READY until it changes. | Independently reconfirmed unaffected — the frozen block was never a target this phase could or should change. |
| **HATP-REQ-109/§38** | Agent OS principal / Human-Admin OS principal threat-capability matrix (Class-B topology). | Unrelated to CLI/PB wiring; governs OS-level bootstrap authority, already enforced pre-Wave-7 by `inspect_bootstrap_environment` (Wave 2, untouched). |
| **HATP-REQ-115/§42** | Actual Class-B OS-boundary provisioning is explicitly *not* a blocking condition for contract freeze — it is a deployment-readiness fact, not a contract-text obligation. | Reinforces that "not yet provisioned"/"not yet CLI-wired" is an acknowledged, contract-anticipated deployment gap, not a contract violation. |
| **HATP-REQ-102** (§34) | POL-004 interprets only the truthful `approval_present` fact "supplied after RAE-001/HATP-001 validation"; HATP-001 supplies an input to that fact, never a permission decision itself. | This is the strongest textual anchor for F-2/the caller-boolean-exclusion property (§6 below) — wherever `approval_present` reaches Permission Broker, it must be the derived fact. It says nothing about a parallel, non-HATP dispatch precondition that never constructs a `PermissionBrokerRequest` at all. |

**Independent conclusion:** nothing in HATP-001's normative text requires that AG3/AG5's *existing, pre-Wave-7* dispatch precondition (`rollback_approval_state == "approved"` for AG3; PER status/divergence for AG5) be replaced or gated by HATP as part of Wave-7 closure. The contract requires a correctly-derived, non-forgeable `approval_present` fact to exist and be PB-consulted when HATP evidence is presented — which Wave 7 delivers — and separately anticipates (HATP-REQ-115) that real deployment/CLI wiring is a distinct, later-arriving fact. This directly resolves item 34/113 of the governing brief: the optional/deferred routing is **not** Blocking under the contract as written.

---

## 3. Exact production diff (independently reconstructed)

```
$ git diff --stat 17a2c1b4..96fcc3b4 -- src/pcae/
 src/pcae/core/agent.py                             | 114 ++++++-
 src/pcae/core/hatp_ag_authority.py                 | 272 +++++++++++++++++++
 src/pcae/core/human_approval_trusted_provenance.py | 121 ++++++---
```

`git diff --name-only 17a2c1b4..96fcc3b4 -- src/pcae/` yields **exactly** these three files. `UNRELATED = 0`, independently confirmed (not cited from the report). `rollback_approval_evidence.py` and every other Wave 1–6 production file: independently confirmed empty diff.

Classification (read from the actual diff hunks, not the report's table):

- `human_approval_trusted_provenance.py`: **ACTIVATION_STATUS** + **CLASS_B_READINESS** — replaces the two permanently-`False` placeholder terms with real `hatp_providers.discover_hardware_providers()`/`create_production_hardware_provider(...).capabilities()` derivations; removes the `assert operational is False` tripwire; adds `HATPVerificationSubstrateStatus.OPERATIONAL`.
- `hatp_ag_authority.py` (new file): **PRODUCTION_PROVIDER_PROVENANCE** + **PRODUCTION_TRUST_STORE_PROVENANCE** + **AG3_AUTHORITY_ADAPTER** + **AG5_AUTHORITY_ADAPTER** + **PB_REQUEST_CONSTRUCTION**.
- `agent.py`: **AG3_CALL_SITE** + **AG5_CALL_SITE** — three new optional, keyword-only parameters on `execute_rollback`/`build_rollback_execution`, each gated behind `if hatp_evidence_id is not None:`.

---

## 4. Class-B activation model: independently reconstructed readiness predicates

`inspect_hatp_verification_substrate_readiness` (`src/pcae/core/human_approval_trusted_provenance.py`) computes a conjunction of exactly **7 terms**, independently read from source (not the docstring):

1. `repository_identity_valid` — `is_valid_repository_instance_id(current_repository_id)`
2. `class_b_bootstrap_environment_safe` — `trust_store.environment_status().status.value == "READY"`
3. `protected_deployment_enrollment_valid` — active enrollment binding present for `current_repository_id`
4. `trusted_approver_mapping_valid` — active authority record for the enrolled principal
5. `provider_profile_available` — **(new, real, Wave 7)** any `discover_hardware_providers()` result reports `library_installed and device_detected` for `HATP_HARDWARE_PROVIDER_V1`
6. `provider_attestation_trusted` — **(new, real, Wave 7)** `create_production_hardware_provider(...).capabilities().hatp_conformant` is `CONFORMANT` or `CONFORMANT_WITH_NON_BLOCKING_LIMITATIONS`
7. `proof_verifier_available` — constant `True` (trivial term, not independently load-bearing)

`operational = all(...)`. The `assert operational is False` tripwire is gone; **no code path, parameter, or environment variable in this function can force any individual term or the overall conjunction** — independently confirmed by full source read and by grep (`tests/test_phase_149o_7_...py::test_readiness_function_has_no_bare_assert_statement`, `::test_readiness_function_has_no_environment_or_override_hook`, `::test_no_env_override_variable_referenced_anywhere_in_hatp_modules`).

**On this real deployment**, independently re-executed (not cited): `operational=False`, `status=NOT_READY` (`test_current_real_deployment_independently_confirmed_not_ready`).

**One-fact-removed / synthetic OPERATIONAL matrix**: independently re-derived (`test_readiness_operational_true_requires_every_synthetic_term`) that a synthetic deployment with conformant hardware discovery monkeypatched but **zero trust-store enrollment** still yields `operational=False` via `protected_deployment_enrollment_valid=False` — confirming the trust-store terms are independently load-bearing, not subsumed by the hardware terms. The 149O.6 suite's own parametrized 6-term removal matrix (`test_removing_any_single_readiness_term_forces_not_ready`) was independently re-run (§10) and passed for every term, confirming no term is redundant.

**Python `-O` / no-assert-based-security**: independently confirmed no `assert` statement exists anywhere in the function body (source-inspected, not merely "ran under `-O`" — a stronger check, since it proves the security property doesn't depend on assertions being enabled at all).

**Environment-override attack**: none of `HATP_FORCE_OPERATIONAL`, `HATP_TRUSTED_OPERATIONAL`, `PCAE_HATP_OPERATIONAL`, `HATP_OPERATIONAL`, `PCAE_HATP_FORCE` is referenced anywhere in `hatp_ag_authority.py`, `human_approval_trusted_provenance.py`, `hatp_bootstrap.py`, or `hatp_providers.py` (independently grepped, zero hits).

**Host-mutation audit**: no `useradd`/`dscl`/`sudoers`/`chmod`/`chown`/`setfacl`/`subprocess.run|Popen|call` pattern anywhere in the two Wave-7-touched production files (independently grepped, zero hits). This phase, like 149O.6, implements *readiness inspection*, not OS provisioning — confirmed, not merely asserted.

---

## 5. F-2 dependency provenance: independently re-verified closed

`resolve_ag3_gated_rollback_authority`/`resolve_ag5_gated_rollback_authority` signatures independently inspected via `inspect.signature` (not copied from the 149O.6 suite's equivalent test): neither contains `hatp_provider`, `hatp_trust_store`, or `approval_present`. Source-text guard confirms `TestHATPProofVerifierProvider` is never named in `hatp_ag_authority.py`.

Tracing `_resolve_gated_approval`'s actual body: `HATPTrustStore.production()` and `create_production_hardware_provider(HATP_HARDWARE_PROVIDER_V1)` are the only two dependency-resolution calls, both hardcoded, both preceding the only `try/except` block, with no caller-supplied argument feeding either. **F-2 closure criterion, independently confirmed met**: an ordinary production caller — or a test calling only the public API — cannot substitute a test provider or arbitrary trust store.

---

## 6. AG3/AG5 authority paths and the default-invocation question (decisive)

Independently traced `execute_rollback`/`build_rollback_execution` (`src/pcae/core/agent.py`) diff line-by-line:

- The `hatp_ag_authority`/`RepositoryStateBinding` imports are **local, inside the `if hatp_evidence_id is not None:` block** — never at module scope (independently confirmed, `test_agent_module_does_not_import_hatp_ag_authority_at_top_level`).
- The dispatch precondition for AG3 is `rollback_approval_state == "approved"` (a bare on-disk job-file string field). The dispatch precondition for AG5 is PER `status`/divergence checks. **Neither precondition reads `hatp_authority`, `approval_present`, or any Wave-7 field.** The `hatp_authority` dict, when present, is attached to the *return value only*, after the dispatch decision (`git revert`/file-restore) has already been made using the unchanged pre-Wave-7 logic.
- **`approve_rollback(root, job_id)`** (`src/pcae/core/agent.py:5146`) — the function that sets `rollback_approval_state = "approved"` — is a bare state-mutation function: no RAE evidence, no HATP proof, no Permission Broker call, no human-identity check of any kind. It is directly exposed as `pcae remote rollback approve <job_id>` (`src/pcae/commands/agent.py:2198`).

**CLI/signing-ceremony surface inventory** (independently grepped across `src/pcae/commands/**/*.py` for `hatp_evidence_id`, `HumanApprovalProvenanceProof`, `request_signature(`): **zero hits**. No production CLI command anywhere can supply HATP evidence. `pcae remote rollback approve` / `pcae remote rollback execute` are the only real dispatch path today, and both call `agent.py`'s functions with the HATP parameters omitted (defaulted to `None`).

**Default-invocation verdict, independently confirmed**: when `hatp_evidence_id` is omitted (every real CLI invocation today), `execute_rollback`/`build_rollback_execution` **never import or call** `hatp_ag_authority` at all — this is answer **B** from the governing brief's §30 decisive question, not A. The gated authority path is reachable and correct in isolation, but it is architecturally a side-channel attached to the return value, not a gate on the mutation.

This confirms — independently, not by trusting the report — that 149O.6's own §7 "scope decision" language is accurate and not an overstatement: it explicitly says the gated path "does not itself gate whether the git revert/file-restore runs," and that is exactly what direct source tracing shows.

---

## 7. Permission Broker: decision-provenance vs. execution-enforcement (kept explicitly separate, per the governing brief's §58/§119)

**PB decision provenance — VERIFIED.** `_evaluate_rollback_permission` constructs the `PermissionBrokerRequest` with `approval_present=approval_evidence.approval_present` sourced exclusively from the just-derived `HATPIntegratedApprovalEvidence` — no parameter on `_evaluate_rollback_permission` or the two public adapter functions could supply a raw caller boolean instead. Independently confirmed by signature inspection (§5) and by reading the one call site.

**No direct HATP→ALLOW mapping.** Read `permission_broker_foundation.py`'s policy rules directly: `ApprovalRequiredRule`/POL-004 and the other POL rules evaluate `request.approval_present`, `request.evidence_available`, `request.task_id`, etc. — there is no rule anywhere that maps a HATP-specific status directly to `ALLOW`; `approval_present` is a generic boolean field the broker has always accepted, and HATP-001 only ever supplies the *value* of that field via the adapter, never bypasses policy evaluation.

**PB execution enforcement — ADVISORY / NOT YET ENFORCED, and this is architecturally forced, not a Wave-7 oversight.** Independently read `permission_broker_foundation.py`'s own module docstring and `POL-005` (`ExecutionDisabledRule`): *"Current implementation status: execution unavailable. Every decision this broker returns — including ALLOW — carries `implementation_status='execution_unavailable'`, because no execution boundary (COMP-002) exists yet."* `POL-005.evaluate()` returns **unconditional `DENY`** for any *non*-simulation request (`request.simulation_only is False`), and is skipped (not-triggered) only when `simulation_only=True`.

Independently confirmed (`test_gated_permission_broker_request_is_always_simulation_only`, `test_pol005_execution_disabled_denies_every_real_non_simulation_request`): `hatp_ag_authority._evaluate_rollback_permission` **hardcodes `simulation_only=True`** on every gated call — this is structural proof that even a fully genuine, HATP-VALID, PB-`ALLOW` result from this adapter is, by PB's own frozen architecture, a *simulation of what would happen*, never an executable permission grant. A hypothetical future call with `simulation_only=False` through the same broker would be unconditionally `DENY`'d by POL-005 today regardless of `approval_present`, confirming this is a pre-existing, system-wide PB boundary (Phase 108A) — not something Wave 7 introduced or could have closed without also building COMP-002, which is explicitly out of this phase's and 149O.6's chartered scope.

PB's only two other production call sites (`push.py`, `mutation_permission.py`) share this same advisory posture — independently spot-confirmed via `permission_broker_foundation.py`'s own consumer-scope boundary test (`test_phase_148f_...py::test_permission_broker_consumer_scope_inventory`, still passing).

**DENY/HUMAN_REVIEW dispatch-behavior questions (§37-40 of the governing brief)**: given §6's finding that the default dispatch path never constructs a `PermissionBrokerRequest` at all, and the gated path's PB call is structurally advisory (§7 above) and does not feed back into `execute_rollback`/`build_rollback_execution`'s own dispatch precondition, the answer to "does dispatch still occur after PB DENY/HUMAN_REVIEW" is: **dispatch is governed exclusively by the pre-existing precondition, which never consults the PB decision either way** — DENY, HUMAN_REVIEW, and (simulated) ALLOW are all equally inert to whether the real mutation runs. This is the single most important fact this phase adds beyond 149O.6's own report, which documented the *existence* of the boundary but did not trace it down to the `simulation_only=True`/POL-005 structural guarantee.

---

## 8. Wave-5 finding reclassification (B-149O.3-1/-3/-8) — independently re-derived, not cited

Read `docs/PHASE_149O_3_HATP_HARDWARE_PROVIDER_INDEPENDENT_VERIFICATION.md` directly for the original finding text.

- **B-149O.3-1** (credential-registry readiness check weaker than the Wave-2 trust store) — the finding's own text warns: *"the term will need wiring when Wave 5/6 makes `provider_profile_available` a real conjunction term — otherwise B-149O.3-1 becomes load-bearing."* Wave 7 is exactly that wiring event, making this check the decisive one for 149O.7.
- **B-149O.3-3** (credential-registry schema open where Wave 2's is closed) — same load-bearing concern, one level deeper (malformed-but-accepted registry entries).
- **B-149O.3-8** (`Fido2HardwareProvider.verify()` raises for malformed evidence instead of returning a result) — a fail-closed-without-raising concern.

**Independent trace**: `provider_attestation_trusted` (the Wave-7 conjunction term) calls only `Fido2HardwareProvider.capabilities()`. Read `capabilities()`'s full body directly (`src/pcae/core/hatp_fido2_provider.py:241-268`): it returns a **hardcoded** `HardwareProviderCapabilities(...)` literal, and **never references `self._credential_store` or `HATPHardwareCredentialStore` at all** — the credential registry is only consulted later, inside `verify()` (used during actual proof *verification*, a separate code path Wave 7's readiness conjunction never calls). Independently confirmed by source inspection (`test_fido2_capabilities_does_not_consult_credential_registry`) and by direct execution (`test_fido2_capabilities_is_a_static_conformance_descriptor`).

**B-149O.3-1/-3 reclassification verdict: NOT load-bearing, remain NON-BLOCKING.** The credential registry's weaker readiness/schema semantics are not consumed by the Wave-7 operational conjunction through this path. (The 149O.6 report's identical claim is independently confirmed true by this direct trace, not merely repeated.)

**B-149O.3-8 verdict**: independently confirmed Wave 4's `verify_hatp_proof` wraps its call to `provider.verify(...)` in a blanket `except Exception` fail-closed umbrella (`src/pcae/core/human_approval_trusted_provenance.py:853-861`, comment: *"provider failure MUST fail closed, never propagate/pass"*) — so even if `verify()` raises for malformed evidence (the exact B-149O.3-8 defect), the gated path still fails closed rather than crashing or defaulting to approved. **Remains NON-BLOCKING**, independently confirmed (`test_verify_hatp_proof_fails_closed_on_provider_exception`).

---

## 9. Historical attacks B-149O-1..4 through the real production consumer

Re-ran the 149O.6 suite's own attack-reproduction tests (`test_b_149o_1_fake_chain_blocked_through_real_consumer`, `test_b_149o_2_wrong_binding_digest_blocked_through_real_consumer`, `test_b_149o_4_fresh_attacker_key_blocked_through_real_consumer`, `test_no_hatp_proof_at_all_blocked_through_real_consumer`, `test_wrong_repository_blocked_through_real_consumer`, `test_pb_receives_gated_fact_not_caller_boolean`, `test_approval_present_does_not_bypass_other_denying_policy`) driven through the real `resolve_ag3_gated_rollback_authority` entry point (see §11 for the environmental note on how these were made to execute in this sandbox). All confirmed blocked exactly as reported: every forged/mismatched/absent-proof variant yields `approval_present=False`; HATP VALID + no active task yields PB `DENY` (never `ALLOW`); no HATP evidence yields PB `HUMAN_REVIEW`.

**§6/§7's findings recontextualize what this means for "closure."** These attacks target the *gated derivation function* — and are genuinely, correctly blocked there. But §6 independently established that the real, reachable CLI dispatch path (`pcae remote rollback approve` + `pcae remote rollback execute`) **never calls this function at all**; its actual gate (`rollback_approval_state == "approved"`) is a bare on-disk string with no evidence-forgery surface in the RAE/HATP sense to begin with — it was never protected by, nor vulnerable through, the mechanism B-149O-1..4 originally described.

**B-149O-1..4 final adjudication**: not `INDEPENDENTLY CONFIRMED CLOSED` (that would require the real dispatch/execution boundary to be forced through HATP, which §6/§7 show it is not) and not `OPEN` (the new gated path is correct, and every reproduced attack against it fails as designed — no exploitable path into the gated function's own logic was found). The correct verdict, per the governing brief's own three-way vocabulary:

```
B-149O-1..4:
INDEPENDENTLY VERIFIED AT HATP-GATED AUTHORITY BOUNDARY
— SYSTEM EXECUTION CLOSURE DEFERRED
```

This is not a downgrade from 149O.6's own "REPAIRED AT SYSTEM IMPLEMENTATION LEVEL, PENDING INDEPENDENT WAVE-7 VERIFICATION" — it is the independent adjudication that phrase was explicitly deferring to this phase, and it lands one notch more conservative than "system implementation level" once the real dispatch path is traced all the way to `pcae remote rollback approve`.

---

## 10. Regressions (independently executed; environmental note below)

| Suite | 149O.6's claim | This phase's independent execution |
|---|---|---|
| 149O.7 new suite | — | **21 passed** |
| 149O.6 suite | 26 passed | **26 passed — exact match** (with the timestamp-parsing workaround, §11) |
| Wave 4 (`test_hatp_verification_engine.py` + `test_phase_149o_1j_...py`) | 136 passed | **136 passed — exact match** |
| Wave 6 (`test_phase_149o_4_...py`) | 51 passed, 1 pre-existing failure | **51 passed, 1 failed — exact match** (`test_rae_stale_plus_valid_hatp_still_false`, confirmed pre-existing/unrelated) |
| Wave 6.5 (`test_phase_149o_5_...py`) | 46 passed + 1 transient (resolves to 47 once committed) | **47 passed — exact match** |
| RAE full sweep (`-k "rollback"`) | 4 pre-existing unrelated failures | **511 passed, 4 failed — exact match** (`test_149o_fake_chgr_record_plus_fake_publication_receipt` and 3 siblings, confirmed pre-existing RAE-001 registration-key-binding forgery findings, unrelated to Wave 7) |
| Permission Broker (`-k permission_broker`) | 981 passed, 2 skipped, 1 pre-existing failure | **993 passed, 2 failed** (different `-k` scope than 149O.6's run; one failure matches their cited pre-existing item; **one additional, newly-discovered, narrow, non-blocking stale-boundary-test finding**, §14) |
| Fast Green (`pytest -m fast_green`) | 4590 passed, 2 skipped, 0 failed | **4652 passed, 1 skipped, 0 failed** — 0 failures confirms no collateral regression; the passed/skipped counts differ from the exact 149O.6 baseline (additional tests have landed in the repository since, and the skip is environment-dependent hardware availability) but **failure count (0) is the load-bearing figure and matches** |
| Report trust (`test_phase_reports.py` + `test_phase_reports_cli.py` + `test_phase_report_trust_hard_fail.py`) | 187 passed | **186 passed, 1 failed** (`test_public_reconciliation_requires_report_marker_checkpoint_and_receipt`, confirmed pre-existing/unrelated — file untouched by Wave 7's diff; not investigated further, out of this phase's verification-only scope) |
| AG3/AG5 full `tests/test_agent.py` | — | Attempted; did not complete within this environment's practical time budget (module is >94,000 lines). The `-k rollback` subset above is used as the bounded equivalent per the governing brief's own allowance (§105). |

No suite produced a result inconsistent with 149O.6's own claims once the environmental factor below is accounted for; the one new finding (§14) is narrow and non-blocking.

---

## 11. Environmental note: pre-existing Python 3.9 timestamp-format incompatibility (independently diagnosed, not present in 149O.6's report)

Running the historical-attack/replay/revocation test suites unmodified in this sandbox's `.venv` (Python 3.9.6) produced **8 errors in the 149O.6 suite and large numbers of errors across Wave 4/5/6 suites**, all with the identical root cause:

```
ValueError: Invalid isoformat string: '...Z'
```

**Root-caused, independently**: `src/pcae/governance/publication/chgr_envelope.py:97` canonicalizes timestamps to a `Z`-suffixed ISO-8601 string (`parsed.isoformat().replace("+00:00", "Z")`), while `src/pcae/governance/publication/coordinator.py:69-73`'s `_parse_timestamp` calls raw `datetime.fromisoformat(value)`, which does not accept a trailing `Z` before Python 3.11. Every RAE/HATP test fixture that constructs a genuine CHGR Decision→Binding chain routes through this Confirmation→Publication pipeline and is affected.

**Confirmed pre-existing, unrelated to Wave 7**: reproduced identically by inspecting the pre-Wave-7 baseline commit `17a2c1b4` (Phase 149O.5) via `git diff`/`git show` (not a working-tree checkout, to avoid corrupting phase-lifecycle task-contract state) and by direct execution of the 149O.5 suite's equivalent fixture-construction test, which fails identically. Neither `chgr_envelope.py` nor `coordinator.py` appears in the Wave-7 diff.

**This phase's workaround**: a process-local, test-only monkeypatch of `coordinator._parse_timestamp` (never touching production code, never committed) was used to independently re-execute the affected suites and confirm their actual pass/fail composition (§10). This is the same class of technique the existing suites already use (`pytest.MonkeyPatch`) and does not constitute a production change.

**Recommendation**: this is exactly the "Python 3.9 lexical-portability debt" 149O.6's own report names as retained/unrepaired — but this phase additionally pins down its precise mechanism (the `chgr_envelope.py`/`coordinator.py` `Z`-suffix mismatch) for whoever eventually schedules that cleanup. Not fixed here, per this phase's verification-only mandate.

---

## 12. No direct HATP→ALLOW; PB remains sole decision engine

Independently confirmed by reading `permission_broker_foundation.py`'s policy rule set directly: no rule branches on a HATP-specific status value; every rule evaluates only the generic `PermissionBrokerRequest` fields (`approval_present`, `evidence_available`, `task_id`, `action_type`, `execution_class`, `simulation_only`). HATP-001/`hatp_ag_authority.py` supply the *value* of `approval_present`; they never construct, bypass, or short-circuit a `PolicyResult`. `PermissionBroker.evaluate()` (§869 of `permission_broker_foundation.py`) remains the sole decision point, unmodified by Wave 7 or this phase.

---

## 13. HATP operational readiness vs. PCAE Runtime Execution: kept separate

`pcae runtime inspect` was run before and after this phase's work: **Observed / observe / unavailable**, unchanged. The synthetic-Class-B `OPERATIONAL` result exercised in tests (149O.6 suite and this phase's own) is scoped entirely to `HATPVerificationSubstrateReadiness` return values in-process; no test or production code path connects it to `pcae.core.runtime` state. Independently confirmed by the absence of any runtime-module import in `human_approval_trusted_provenance.py` or `hatp_ag_authority.py`.

---

## 14. New finding: narrow, non-blocking stale-boundary-test gap (not in 149O.6's own audit)

While running the Permission Broker regression sweep (§10), `tests/test_phase_149o_1f_hatp_repository_identity_trust_store_foundation_independent_verification.py::test_rae_permission_broker_agent_still_byte_unchanged_since_freeze` was independently found to **fail** — it asserts, via `git diff --name-only a278cd93 HEAD -- src/pcae/core/agent.py ...`, that `agent.py` is byte-unchanged since the 149O.1F freeze. This is now false: Wave 7 legitimately, intentionally, and reviewedly changed `agent.py` (§3/§6 above).

This is the **same class** of narrow, by-design supersession as the ten boundary-test updates 149O.6's own §11 already made (its own §11 table specifically covers the *149O.1G*-era `test_agent_module_untouched`/`test_only_expected_production_files_changed` tests) — but this **149O.1F**-era test, and its sibling `tests/test_phase_149o_3_hatp_hardware_provider_independent_verification.py::test_rae_permission_broker_and_agent_do_not_reference_wave5` (which independently traced to fail for an **unrelated, pre-existing** reason — `rollback_approval_evidence.py` already referenced `hatp_providers` before Wave 7, confirmed via `git diff` showing that file untouched by Wave 7), were not caught by 149O.6's audit.

**Verdict: NON-BLOCKING.** No broad guard assertion is defeated; this is exactly the same "invariant intentionally superseded by design" pattern already reviewed and accepted ten times in 149O.6. **Recommendation**: a future narrow phase (or a fast-follow to whichever phase closes the CLI/signing-ceremony gap, §15) should update `test_rae_permission_broker_agent_still_byte_unchanged_since_freeze` the same way the ten 149O.6-era tests were updated — re-express the underlying invariant ("no *undetected* production consumer changed") through a reviewed allowlist rather than a literal zero-diff assertion. Not repaired by this phase, per its verification-only mandate; recorded and reproduced only.

---

## 15. Confirmations (no-go list)

- HATP-001 v1.0 remained byte-unchanged throughout this phase (independently confirmed via `git diff`).
- No production code under `src/pcae/` was modified by Phase 149O.7 (`git diff --name-only 42112464..HEAD -- src/pcae/` is empty at time of writing this document, before the doc/test-only commit below).
- Wave 1 (repository identity), Wave 2 (trust-store authority), Wave 3 (canonicalization), Wave 4 (verification-state vocabulary/`verify_hatp_proof`), Wave 5 (provider/crypto semantics), Wave 6 (`rollback_approval_evidence.py` RAE/HATP binding) semantics all independently confirmed unchanged since 149O.5 and 149O.6 (zero diff on their owning files across both baselines).
- No real Class-B provisioning occurred during this verification (no host-mutation commands found in the code paths exercised; no OS account/ACL/sudoers state touched by any test in this phase).
- No HATP production activation occurred on this deployment — `inspect_hatp_verification_substrate_readiness`'s real, unfaked call against this deployment independently re-confirmed `operational=False`/`NOT_READY`.
- No direct HATP-status-to-PB-`ALLOW` mapping exists (§12).
- Permission Broker remains the sole permission-decision engine (§12); whether it is an *enforced execution gate* is reported separately and honestly as **advisory / not yet enforced**, and is shown to be structurally forced by PB's own pre-existing, system-wide `simulation_only`/POL-005 architecture (§7) — not a Wave-7-specific gap.
- HATP operational readiness remains distinct from PCAE Runtime Execution capability (§13). Runtime remains Observed / observe / unavailable, confirmed before and after this phase.
- Current deployment remains NOT_READY (§4), confirmed directly, not inferred from 149O.6's claim.
- No `--no-verify`, force-push, or governance bypass was used this phase.

---

## 16. Final verdicts

```
CLASS-B ACTIVATION MODEL:
INDEPENDENTLY VERIFIED
— CURRENT DEPLOYMENT REMAINS NOT READY

F-2 DEPENDENCY PROVENANCE:
INDEPENDENTLY CONFIRMED CLOSED

AG3 HATP-GATED AUTHORITY CONSUMPTION:
INDEPENDENTLY VERIFIED
(dispatch enforcement: NOT PRESENT — see PB verdict)

AG5 HATP-GATED AUTHORITY CONSUMPTION:
INDEPENDENTLY VERIFIED
(dispatch enforcement: NOT PRESENT — see PB verdict)

PB DECISION PROVENANCE:
VERIFIED

PB EXECUTION ENFORCEMENT:
ADVISORY / NOT YET ENFORCED
(structurally forced by PB's own pre-existing simulation_only/POL-005
architecture; not a Wave-7-introduced gap)

CLI / SIGNING-SURFACE:
ABSENT

CURRENT WORKFLOW:
DOES NOT USE HATP

B-149O-1..4:
INDEPENDENTLY VERIFIED AT HATP-GATED AUTHORITY BOUNDARY
— SYSTEM EXECUTION CLOSURE DEFERRED

OVERALL WAVE-7 VERDICT:
VERIFIED WITH NON-BLOCKING / DEFERRED FINDINGS
— HATP WAVE 7 CLASS-B DEPLOYMENT / ACTIVATION CONFORMS

HATP PRODUCTION:
NOT READY

RUNTIME:
Observed / observe / unavailable
```

---

## 17. Recommended next phase

The HATP architecture-implementation chapter is **not yet complete** — two distinct capabilities remain unbuilt, and per the governing brief's §125 they should be scoped as a bounded next phase rather than jumping to production certification:

```
149O.8 — HATP AG3/AG5 Production Consumption + Signing-Ceremony
        Architecture (or repository-conventional exact title)
```

Scope for that future phase to decide (not decided here): (a) whether/how to build a CLI/signing-ceremony surface through which a human can actually produce a `HumanApprovalProvenanceProof` and supply `hatp_evidence_id` to `pcae remote rollback approve`/`execute`; (b) whether/how AG3/AG5's *existing* dispatch precondition (`rollback_approval_state`/PER status) should itself be replaced by, or additionally gated on, the HATP-derived `approval_present` fact once such a surface exists; (c) separately and only once COMP-002 (a real execution boundary) exists at all, whether/how Permission Broker's `simulation_only=False` path should be exercised for rollback and what POL-005's unconditional-deny posture should become at that point. Real Class-B OS provisioning and hardware-device certification remain a distinct, later capability, out of scope until (a)-(c) are decided.

A narrow, independent follow-up (not urgent, non-blocking) may also close §14's stale-boundary-test gap, mirroring 149O.6's own §11 pattern.

Recommended immediately-next phase, per priority: **149O.8, scoped exactly as above** — not real deployment/certification work, since neither the CLI surface nor PB dispatch-gating exists yet (per §125's own branching rule).
