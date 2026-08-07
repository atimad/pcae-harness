# Phase 149O.5 — HATP RAE Integration Independent Verification

**Phase ID:** 149O.5
**Phase type:** Verification-only (independent adversarial re-verification of Wave 6)
**Baseline:** `HEAD` = commit `85db3152` (Phase 149O.4, complete/pushed) at phase start
**Frozen contract:** `docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md` (HATP-001 v1.0, 117 requirements, byte-unchanged, re-confirmed)
**Independent verification suite:** `tests/test_phase_149o_5_hatp_rae_integration_independent_verification.py` (47 passed)

---

## 0. Verdict summary

| Question | Verdict |
|---|---|
| Activation conjunction | **HATP ACTIVATION CONJUNCTION: INDEPENDENTLY VERIFIED** — exhaustive 8-row truth table, only RAE∧HATP-VALID∧OPERATIONAL yields `True` |
| 13-state HATP status integration | **HATP STATUS INTEGRATION: ONLY VALID MAY SATISFY THE HATP TERM; ALL OTHER STATUSES FAIL CLOSED** |
| RAE/HATP binding | **RAE/HATP BINDING: DECISION ID + DIGEST, BINDING ID + DIGEST, OPERATION, REPOSITORY, AND DEPLOYMENT ARE CONSUMPTION-TIME BOUND** |
| Revocation | **CONSUMPTION-TIME TRUST: SIGNER / AUTHORITY / DEPLOYMENT REVOCATION INVALIDATES APPROVAL WITHOUT REWRITING ARTIFACTS** |
| Legacy-path | **LEGACY RAE-ONLY PATH: NON-AUTHORITY-BEARING FOR PRODUCTION APPROVAL** (no production consumer of either API exists yet) |
| Threat-A | **THREAT-A FORGED ARTIFACT CHAIN: CANNOT PRODUCE HATP-GATED APPROVAL** |
| Current deployment | **CURRENT DEPLOYMENT: approval_present CANNOT BECOME TRUE** |
| B-149O-1..4 | **REPAIRED AT IMPLEMENTATION LEVEL, INDEPENDENTLY VERIFIED AGAINST THE GATED API — SYSTEM-LEVEL CLOSURE DEFERRED** (HATP-REQ-105/106 requires AG3/AG5 Permission Broker wiring, which does not exist yet; no production authority consumer, gated or legacy, exists) |
| Overall Wave-6 verdict | **VERIFIED WITH NON-BLOCKING FINDINGS — HATP WAVE 6 RAE INTEGRATION CONFORMS** |
| Blocking findings | **ZERO** |
| Wave-7 readiness | **WAVE 6: READY FOR WAVE 7 DEPLOYMENT / ACTIVATION IMPLEMENTATION** |
| HATP production readiness | **HATP PRODUCTION: NOT READY** |
| Runtime | **Observed / observe / unavailable** (unchanged, before and after) |

**Recommended next phase:** 149O.6 — HATP Class-B Deployment + Activation Implementation (Wave 7), per the 149O.1D plan's own wave ordering.

---

## 1. Initial inspection (independently re-run)

| Check | Result |
|---|---|
| `git status --short` | clean |
| `git rev-list --count origin/main..HEAD` | 0 |
| `pcae health` | healthy |
| `pcae check` | passed |
| `pcae status coherence` | coherent |
| `pcae doctor task-memory` | warnings (7 pre-existing `tasks/DONE.md` sync gaps, unrelated) |
| `pcae push check` | clean (`nothing_to_push`) |
| `pcae runtime inspect` | Observed / observe / unavailable |
| `pcae notify status` | telegram configured/enabled/ready |
| `pcae phase-report show --latest` / `reconcile --phase-id 149O.4` | 149O.4 completed, pushed, report completeness `complete`, reconciled `already_dispatched` |

All expected preconditions confirmed independently.

---

## 2. Wave-6 requirement re-derivation (from contract text directly, §29/§34)

| Requirement | Exact normative meaning | Implementation | Independent verification |
|---|---|---|---|
| HATP-REQ-095 | RAE-001 v1.0 COMPATIBLE AS-IS; HATP supplies an *additional* required condition; RAE fields reused by reference, never redefined | `resolve_rollback_approval_evidence`/`derive_rollback_approval_present` byte-identical (confirmed by diff, §3) | `test_threat_a_genuine_rae_chain_no_hatp_proof_cannot_approve_through_gated_api` proves the legacy function alone still resolves `True` while the gated function requires the additional proof |
| HATP-REQ-096 | Trusted **iff** HATP proof VALID **and** RAE's own requirements independently pass; neither substitutes | `_derive_hatp_gated_approval_present` | `test_pure_conjunction_exhaustive_8_rows` (independently authored, all 8 rows) |
| HATP-REQ-101 | No RWMPC-001 (mutation freshness/execution ownership) change | No RWMPC import; diff touches no RWMPC-owned file | `git diff` file list (§3) |
| HATP-REQ-102 | No PBPA-001 change; POL-004 interprets only the truthful `approval_present` fact | `HATPIntegratedApprovalEvidence` carries no permission/execution field; zero PB import | `test_integrated_evidence_carries_no_permission_or_execution_field`, `test_no_permission_broker_or_agent_import_in_gated_module` |
| HATP-REQ-103 | No PBPC-001 (`pcae push`) change | No `pcae push`/PBPC-001 file touched | `git diff` file list (§3) |
| HATP-REQ-104 | VALID HATP proof does not itself transform `HUMAN_REVIEW` into `ALLOW`; fresh PB evaluation still required | No PB call added anywhere in the module; `approval_present` is a fact, not a PB decision | `test_permission_broker_approval_present_is_caller_supplied_not_rae_derived` — PB's `approval_present`/`human_approval_present` are plain caller-supplied CLI booleans today, with zero RAE/HATP import in the PB module chain |

No requirement omitted; HATP-REQ-097–100 (CHGR/IWC/AESIC/TAMC boundaries) confirmed unaffected (no new dependency on any of those subsystems).

---

## 3. Exact production diff (independently reconstructed via `git diff 43a9e2fc^..43a9e2fc`)

**Exactly one production file:** `src/pcae/core/rollback_approval_evidence.py` (+279/-0). `UNRELATED = 0`.

| Hunk | Classification |
|---|---|
| New imports (`hatp_bootstrap.HATPTrustStore`, `hatp_providers.HATPProofVerifierProvider`, `human_approval_trusted_provenance.*`) | `HATP_IMPORT` |
| `HATPIntegratedApprovalEvidence` dataclass | `PUBLIC_INTEGRATION_API` |
| `_hatp_expected_operation_for` | `EXPECTED_OPERATION_BINDING` |
| `_derive_hatp_gated_approval_present` | `ACTIVATION_GATE` |
| `resolve_rollback_approval_evidence_with_hatp` (RAE delegation + HATP call + digest cross-check + conjunction) | `HATP_VERIFICATION` + `DIGEST_BINDING` + `APPROVAL_DERIVATION` |
| `derive_rollback_approval_present_with_hatp` | `PUBLIC_INTEGRATION_API` |
| `__all__` update | `PUBLIC_INTEGRATION_API` |

**Legacy RAE byte-equivalence:** confirmed directly from the diff — the pre-existing `resolve_rollback_approval_evidence` (line 1218) and `derive_rollback_approval_present` (line 1394) bodies show **zero changed lines**; all 279 new lines are additions after the existing `derive_rollback_approval_present` definition. Not reconstructed from prose claims — read directly off the unified diff.

**Two pre-existing test files** were narrowly updated (`test_hatp_verification_engine.py`, `test_phase_149o_1j_hatp_verification_engine_independent_verification.py`): both previously asserted zero production call sites for `verify_hatp_proof`/`inspect_hatp_verification_substrate_readiness` including in `rollback_approval_evidence.py`; both now exclude exactly that one file while continuing to forbid `permission_broker*.py`/`agent.py` absolutely — confirmed narrow and justified by re-reading the diff hunks directly (§10 below), not merely trusting 149O.4's description.

**Whole-phase diff since 149O.3** (`59cd4391..HEAD`, i.e. including 149O.4's finalization commits): `src/` changes are still exactly the one file; no `pyproject.toml` change (zero dependency drift); no `docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md` change (byte-unchanged, confirmed via `git diff`, empty).

---

## 4. Activation conjunction — independently derived and verified

```
approval_present =
      RAE_GATE        (resolve_rollback_approval_evidence(...).approval_present is True)
  AND HATP_GATE        (verify_hatp_proof(...).status is VALID, plus a Decision/Binding
                         digest cross-check `verify_hatp_proof` itself does not perform)
  AND ACTIVATION_GATE  (inspect_hatp_verification_substrate_readiness(...).operational is True)
```

Independently re-derived from HATP-REQ-096 (the RAE∧HATP iff-rule) and HATP-REQ-108/§37 (the activation/operational ceiling) — matches the implementation exactly, confirmed by direct inspection of `_derive_hatp_gated_approval_present`'s source: three sequential `if not X: return False` guards, no default/else branch, unconditional `return True` only after all three.

**`_derive_hatp_gated_approval_present` is pure**: keyword-only arguments, no I/O, no global/module state read or written, confirmed by direct source inspection.

**Independent 8-row exhaustive truth table** (`test_pure_conjunction_exhaustive_8_rows`, `@pytest.mark.parametrize` over all three booleans): only `(True, True, True) → True`; all other seven rows → `False`. Matches expectation exactly.

**Independent 13-state HATP matrix** (`test_13_state_matrix_only_valid_passes`): `HATP_VERIFICATION_STATUS_VALUES` independently confirmed to have exactly 13 members (read directly from `human_approval_trusted_provenance.py`'s `HATPVerificationStatus` enum); with `rae_approval_present=True, activation_operational=True`, only `VALID` yields `True`, all 12 others `False`.

**No default-to-success on unknown/foreign status** (`test_unknown_future_status_cannot_default_to_success`): a foreign status object with `.value == "VALID"` but which is *not* the enum member (and whose `__eq__` always returns `False`) is independently confirmed to still fail the gate — the guard uses `is not HATPVerificationStatus.VALID`, i.e. identity/enum equality, not a loose string comparison a spoofed value could satisfy.

**No hidden fourth bypass**: `test_no_hidden_fourth_disjunctive_success_path_in_source` greps the full source of both the integration function and the pure conjunction for `or approval`/`or legacy_approval`/`or human_authorization`/`or existing` — none found. `test_activation_gate_not_a_caller_parameter` confirms neither public function accepts `activation_operational`/`operational` as a parameter — the `True` branch of `ACTIVATION_GATE` is reachable only by calling the pure helper directly with a synthetic value, never through any production entry point.

**Real activation path is architecturally, not merely procedurally, incapable of `True`**: `inspect_hatp_verification_substrate_readiness`'s `operational = all(value for _name, value in terms)` is computed from seven named terms, two of which — `provider_profile_available`, `provider_attestation_trusted` — are **hardcoded Python `False` literals** in this wave (Wave 5/6 provider wiring exists but this function's own body still assigns them unconditionally). The trailing `assert operational is False` is a secondary, redundant safety net — independently noted as an **OBSERVATION**: that specific `assert` statement would be silently stripped under `python -O`/`PYTHONOPTIMIZE`, but this has **no security consequence**, since `operational` is already forced `False` by the two hardcoded literals feeding `all(...)`, not by the assert. Confirmed by direct source inspection (`test_wave4_operational_ceiling_source_still_load_bearing`) and by `test_readiness_inspection_independently_not_ready`, which checks the two hardcoded terms directly rather than trusting the aggregate `operational` field alone.

---

## 5. RAE/HATP binding — Decision, Binding, operation, repository, deployment

Independently re-verified, each via a dedicated forged-field test against a genuine baseline (`_Harness`, built exclusively from real, unmodified `create_rollback_approval_decision`/`create_rollback_approval_binding`/`verify_hatp_proof` APIs — no fixtures imported from 149O.4's own suite):

- **Decision ID mismatch** → `WRONG_OPERATION`, `approval_present=False` (`test_decision_id_mismatch_rejected`)
- **Binding ID mismatch** → `WRONG_OPERATION`, `False` (`test_binding_id_mismatch_rejected`)
- **Decision digest replay** (correct id, stale digest) → `WRONG_OPERATION`, reason `decision_record_digest_mismatch`, `False` (`test_stale_decision_digest_replay_rejected`) — this is the Wave-4-deferred, Wave-6-closed check (§6.4 of the 149O.4 doc); independently confirmed present and load-bearing, not merely claimed
- **Binding digest replay** → `WRONG_OPERATION`, reason `binding_digest_mismatch`, `False` (`test_stale_binding_digest_replay_rejected`)
- **AG3 wrong job_id** → `WRONG_OPERATION`, `False`
- **AG3↔AG5 cross-family replay, both directions** → `WRONG_OPERATION` / `False` (`test_ag5_proof_cannot_approve_ag3_operation`, `test_ag3_proof_cannot_approve_ag5_operation` — the latter independently constructs a second, genuine AG5 Binding/Decision pair from scratch and attempts an AG3 proof against it)
- **Wrong repository** → non-`VALID` (`UNAUTHORIZED_SIGNER` in the current implementation's documented, non-normative failure-precedence ordering — the authority lookup for the forged `repository_id` fails before the explicit `repository_id != current_repository_id` equality check is reached; both are fail-closed, `approval_present=False` either way), `False`
- **Wrong deployment root** → `WRONG_DEPLOYMENT`, `False`
- **Copied genuine proof against a different genuine Binding** → `False` (`test_threat_a_copied_genuine_proof_wrong_binding_context_rejected`)

---

## 6. Consumption-time revocation and no cached VALID

Independently confirmed for all three revocable facts, each via: establish a genuine `VALID` baseline, mutate the trust-store registry in place (correctly, including the schema-required `revoked_at` field — see finding F-1 below), re-derive with a fresh `HATPTrustStore` instance over the same root:

- **Signer revocation** → `REVOKED_SIGNER`, `False`
- **Authority revocation** → `UNAUTHORIZED_SIGNER`, `False`
- **Deployment-binding revocation** → `WRONG_DEPLOYMENT`, `False`
- **No caching across calls in the same process** — an identical proof object re-derived after a registry mutation reflects the new state, never the earlier `VALID` (`test_no_cached_valid_survives_trust_store_mutation_same_process`)

**Finding F-1 (OBSERVATION, not a defect):** the trust-store schema parser (`_require_revoked_at_consistency`, `hatp_bootstrap.py`) *requires* a `revoked_at` timestamp whenever `status` is `"revoked"`, and raises `HATPTrustStoreMalformedError` otherwise. During test authoring, an incomplete hand-mutation (flipping `status` to `"revoked"` without adding `revoked_at`) was independently discovered to still fail closed — via `environment_status()`/`lookup_signer()` raising, caught by `verify_hatp_proof`'s own `except HATPTrustStoreError` handlers, producing `MISSING`/`trust_store_unavailable` rather than the intended specific status. This is **additional, unplanned defense-in-depth** (a malformed revocation record cannot accidentally leave a signer looking `active`), not a defect — recorded here because it is a genuinely independent discovery, not because it changes any verdict.

---

## 7. Exception / fail-closed matrix (independently re-confirmed)

| Scenario | Result |
|---|---|
| Trust store raises on every method | `approval_present=False` |
| Provider raises (`RuntimeError`) | `approval_present=False` |
| `inspect_hatp_verification_substrate_readiness` itself raises (monkeypatched) | `approval_present=False`, non-`None` diagnostic |

No exception from any injected dependency propagates past `resolve_rollback_approval_evidence_with_hatp`'s outer `except Exception` umbrella.

---

## 8. Legacy-flag search and trusted-dependency boundary analysis

- **No caller-reachable bypass parameter**: `inspect.signature` on both public functions contains none of `approval_present`, `approved`, `human_authorization`, `is_authorized`, `hatp_valid`, `verification_status`, `trusted`, `operational`, `force_operational`, `allow_test_provider`, `skip_hatp`, `legacy_approval`, `existing_flag`.
- **`hatp_provider`/`hatp_trust_store` have no default** — no caller can silently resolve a test provider/store by omission.
- **Dependency-injection trust boundary (Finding F-2, NON-BLOCKING/DEFERRED):** `HATPProofVerifierProvider` is a structural `typing.Protocol`; `TestHATPProofVerifierProvider` independently confirmed (`isinstance` check) to satisfy it. Nothing in the Python type system, and nothing runtime-enforced in `resolve_rollback_approval_evidence_with_hatp` itself, prevents a *future* caller from passing `TestHATPProofVerifierProvider`/a non-production `HATPTrustStore` into this function — isolation today rests entirely on there being **zero production call sites** (§9), not on any code-enforced provenance check. This is explicitly acceptable under HATP-REQ-094's framing (verification is performed by trusted PCAE code — the caller *is* the trusted boundary) as long as no untrusted caller exists, but it is a real design question for Wave 7: the future PB/AG3/AG5 adapter should itself assert production-provider provenance (e.g. reject non-factory-sourced providers) rather than relying solely on code-review discipline at the call site. Recorded as a recommendation for Wave 7's design, not a Wave-6 defect — no adapter exists yet to misuse it.

---

## 9. Production call-site inventory — the central B-149O-1..4 closure question

Independently searched (`grep`/AST, not trusting 149O.4's own claim):

- **Zero** production modules outside `rollback_approval_evidence.py` itself reference `resolve_rollback_approval_evidence_with_hatp` or `derive_rollback_approval_present_with_hatp` (the new, gated API).
- **Zero** production modules outside `rollback_approval_evidence.py` itself reference `resolve_rollback_approval_evidence` or `derive_rollback_approval_present` (the legacy, RAE-alone API) either.
- **No rollback CLI command exists** that imports this module at all (`src/pcae/commands/` has zero `rollback_approval_evidence`/`hatp` references).
- **Permission Broker's `approval_present`/`human_approval_present`** (`permission_broker.py`, `permission_broker_foundation.py`, `mutation_permission.py`) are confirmed, via AST import inspection, to import **neither** `rollback_approval_evidence` **nor** `human_approval_trusted_provenance` anywhere in that module chain — the boolean PB receives today is a plain caller-supplied fact (a CLI flag, `--approval-present`/`--human-approval-present`), entirely independent of RAE or HATP.

**Adjudication:** Wave 6 is **API-level integration only** — it supplies a derivation function a *future* AG3/AG5 adapter will call, but **no production authority path exists yet that could be either exploited or protected** by either the legacy or the gated function. This is exactly the outcome anticipated by the governing prompt's item 63 and matches HATP-REQ-105/106's own framing: B-149O-1..4 closure explicitly requires "AG3/AG5 Permission Broker wiring" as a *separate*, not-yet-taken step, in addition to independent adversarial verification (now done). Because there is **no** parallel gated/ungated authority path today (there is no authority path of either kind), the specific Blocking condition "parallel gated and ungated authority paths exist" does **not** fire. B-149O-1..4 therefore remain classified:

> **REPAIRED AT IMPLEMENTATION LEVEL AND INDEPENDENTLY VERIFIED AGAINST THE GATED API — SYSTEM-LEVEL CLOSURE DEFERRED PENDING WAVE-7 AG3/AG5 PERMISSION BROKER WIRING.**

Each individually:

| Finding | Attack reproduced through gated API | Status |
|---|---|---|
| B-149O-1 (fake CHGR + fake receipt) | `test_threat_a_hand_forged_rae_chain_no_hatp_proof_rejected` — `MISSING`, `False` | Implementation-level blocked; system closure deferred (no PB wiring) |
| B-149O-2 (real Decision + fake Binding + fake registration) | Covered by digest/identity replay tests (§5); no genuine-looking forged Binding can carry a valid HATP proof bound to it | Implementation-level blocked; system closure deferred |
| B-149O-3 (fully handcrafted chain, zero legitimate API calls) | `test_threat_a_hand_forged_rae_chain_no_hatp_proof_rejected` + `test_threat_a_genuine_rae_chain_no_hatp_proof_cannot_approve_through_gated_api` | Implementation-level blocked; system closure deferred |
| B-149O-4 (fresh attacker key) | `test_threat_a_hand_forged_hatp_proof_unenrolled_signer_rejected` — `UNKNOWN_SIGNER`, `False` | Implementation-level blocked; system closure deferred |

---

## 10. Threat-A full forgery — independently reproduced through the gated API

- **Unenrolled attacker signer key**, self-signed with an attacker-controlled fake provider, otherwise-correct identity/digest fields → `UNKNOWN_SIGNER`, `False`.
- **Fully hand-forged RAE chain, no HATP proof at all** → `MISSING`, `False`.
- **Fully genuine RAE chain (real CHGR Decision, real publication, real Binding — the exact scenario HATP-REQ-095 confirms resolves `True` through the legacy function alone), no HATP proof, through the gated API** → `MISSING`, `False`. This is the precise, minimal demonstration of what Wave 6 adds: identical RAE evidence, different (gated) entry point, different outcome.
- **Copied genuine, validly-signed proof presented for a different genuine Binding** → `False` (rejected on identity mismatch before digest checks are reached).

No variant reached `approval_present=True`.

---

## 11. Current real deployment

`test_current_real_deployment_cannot_approve`: genuine RAE evidence + genuine, fully `VALID` HATP proof + the real, unmodified `inspect_hatp_verification_substrate_readiness` → `activation_operational=False` → `approval_present=False`. Mandatory, independently confirmed.

---

## 12. Boundary / scope confirmation

- `test_no_permission_broker_or_agent_import_in_gated_module` (AST-based): no import of any name containing `permission_broker`, `mutation_permission`, `agent`, `fido2`, `cryptography`, `hatp_hardware_credentials` in `rollback_approval_evidence.py`.
- `test_hatp_module_has_no_reverse_import_of_rae` (AST-based, corrected during authoring to avoid the same docstring-substring false positive 149O.4 itself documented encountering): `human_approval_trusted_provenance.py` imports nothing from `rollback_approval_evidence`.
- `test_integrated_evidence_carries_no_permission_or_execution_field`: `HATPIntegratedApprovalEvidence` has no `permission`/`allow`/`deny`/`execute`/`authorized_to_execute` field.
- `test_no_production_source_changed_by_this_phase`: `git diff --name-only HEAD -- src/pcae/` is empty at time of this phase's own verification — 149O.5 modifies no production source.

No Permission Broker semantic change, no rollback execution change, no Runtime Enforcement change, no agent/prompt-dispatch capability — confirmed by absence of any reference, not by absence of a diff alone.

---

## 13. Regressions (independently re-run, this session)

| Suite | Command | Result | vs. 149O.4 baseline |
|---|---|---|---|
| Wave-6 new suite (149O.4's own) | `pytest tests/test_phase_149o_4_hatp_rae_integration.py -q` | **52 passed** | exact match |
| Wave-4 | `pytest tests/test_hatp_verification_engine.py tests/test_phase_149o_1j_hatp_verification_engine_independent_verification.py -q` | **136 passed** | exact match |
| Wave-5 | `pytest tests/test_phase_149o_2_hatp_hardware_provider_implementation.py tests/test_phase_149o_3_hatp_hardware_provider_independent_verification.py -q` | **2 skipped** (fido2 extra not installed; PEP 668) | exact match |
| RAE full (149J/149M/149N/149O + Wave-6) | `pytest tests/test_rollback_approval_evidence_*.py tests/test_phase_149j_*.py tests/test_phase_149m_*.py tests/test_phase_149n_*.py tests/test_phase_149o_rollback_approval_evidence_*.py tests/test_phase_149o_4_hatp_rae_integration.py -q` | **255 passed, 4 failed** (the known-open B-149O-1..4 reproductions against RAE-alone) | exact match |
| Report trust | `pytest tests/test_phase_reports.py tests/test_phase_reports_cli.py tests/test_phase_report_trust_hard_fail.py -q` | **187 passed** | exact match |
| Permission Broker | `pytest tests/ -k permission_broker -q` | **978 passed, 2 failed, 2 skipped** | **discrepancy found — see Finding F-3** |
| 149O.5 independent suite (new, this phase) | `pytest tests/test_phase_149o_5_hatp_rae_integration_independent_verification.py -q` | **47 passed** | new |
| Fast Green | `pytest -m fast_green -q` | **4590 passed, 2 skipped, 0 failed** | exact match |
| Import smoke | `python -c "import pcae.core.rollback_approval_evidence"` | clean | — |

**Python interpreter:** CPython 3.14.5 (this environment's active interpreter). Python 3.9 lexical-portability debt (149O.3's 91-failure finding) is retained, unrelated to Wave 6, not re-tested this phase — no Wave-6/HATP file is implicated in that debt.

**Finding F-3 (NON-BLOCKING, corrects a 149O.4 regression-accounting discrepancy):** `pytest tests/ -k permission_broker -q` shows **2** failures in this environment, not the 1 recorded in 149O.4's own phase report. The second is `tests/test_phase_149o_1f_hatp_repository_identity_trust_store_foundation_independent_verification.py::test_rae_permission_broker_agent_still_byte_unchanged_since_freeze`, which asserts `git diff --name-only a278cd93 HEAD -- <RAE/PB/agent files>` is empty — a boundary pinned to the pre-Wave-6 commit `a278cd93`. Since `rollback_approval_evidence.py` was legitimately, deliberately modified by Wave 6 (HATP-REQ-095/096), this assertion is now permanently false by design. **Independently reproduced against commit `43a9e2fc` itself** (149O.4's own implementation commit, via a detached worktree) — the failure already existed at the moment 149O.4 made its change, before any of 149O.4's own finalization commits, and the test file has been byte-identical since. This means 149O.4's regression table (`979 passed, 1 failed`) undercounted by one failure that its own diff produced. This is the same class of issue as the two Wave-4 boundary tests 149O.4 *did* correctly narrow (§10 of the 149O.4 doc) — this one test was simply missed. **Not blocking**: the test's assertion is about diff-scope hygiene, not approval-authority correctness, and its failure mode is "correctly detects Wave 6's own legitimate, intended change," not a false pass. **Recommended narrow follow-up** (not performed by this verification-only phase): update `test_rae_permission_broker_agent_still_byte_unchanged_since_freeze`'s target list to exclude `rollback_approval_evidence.py`, mirroring the two Wave-4 boundary-test updates 149O.4 already made, or re-pin its baseline commit forward past 149O.4.

---

## 14. Findings summary

| ID | Class | Summary |
|---|---|---|
| F-1 | OBSERVATION | Trust-store schema requires `revoked_at` alongside `status="revoked"`; an incomplete mutation fails closed via a different (also-correct) status. Defense-in-depth, not a defect. |
| F-2 | NON-BLOCKING / DEFERRED | `HATPProofVerifierProvider`/`HATPTrustStore` are caller-injected with no runtime production-provenance check; isolation rests on zero call sites today. Recommend Wave 7's PB/AG3/AG5 adapter enforce provenance itself. |
| F-3 | NON-BLOCKING | 149O.4's own Permission-Broker regression count (`979 passed, 1 failed`) undercounted by one pre-existing, still-present failure (`test_rae_permission_broker_agent_still_byte_unchanged_since_freeze`), reproduced as already present at commit `43a9e2fc`. Narrow follow-up recommended, not performed here. |
| — | BLOCKING | **None found.** |

No finding satisfies any of the enumerated Blocking conditions (non-VALID/RAE-invalid/activation-forced/caller-forced-operational/identity-or-digest-mismatch/revoked-signer-or-authority-or-deployment/expired/cached-VALID/legacy-bypass/Threat-A-through-gated-path/parallel-gated-and-ungated-authority-path/test-provider-reaches-production/current-deployment-approves/HATP-VALID-changes-PB-decision/execution-or-runtime-change).

---

## 15. No-Go confirmations

HATP-001 v1.0 remained byte-unchanged this phase. No production source was modified by Phase 149O.5 (`git diff --name-only HEAD -- src/pcae/` empty, enforced by this phase's own test). Legacy RAE-001 semantics remained unchanged (untouched by 149O.4, re-confirmed unchanged this phase — no further edit possible under 149O.5's own scope). Wave-1 (`repository_identity.py`), Wave-2 (`hatp_bootstrap.py` — read, not modified), Wave-3 (proof/canonicalization semantics), Wave-4 (`verify_hatp_proof`/`inspect_hatp_verification_substrate_readiness`), and Wave-5 (provider modules) semantics remained unchanged this phase. B-149O.1H-1, B-149O.1H.4-1, B-149O.1H-2, B-149O.1F-1, B-149O.1R-1, and B-149O.1R-2 remain closed, unaffected (no Wave-1/2/3 source touched, no re-adjudication performed or required). No Class-B deployment was provisioned. No HATP production activation occurred. No Permission Broker policy meaning changed. No rollback execution behavior changed. No Runtime Enforcement behavior changed. No Prompt Generation, Prompt Dispatch, or agent-invocation capability was implemented. HATP VALID remains distinct from approval; approval remains distinct from PB permission; permission remains distinct from capability and execution (confirmed structurally, §12). The current same-principal deployment cannot derive `approval_present=True` (§11). HATP production remains **NOT READY**. Runtime remains **Observed / observe / unavailable**, confirmed before (§1) and after (this section) this phase's work.

---

## 16. Recommended next phase

**149O.6 — HATP Class-B Deployment + Activation Implementation (Wave 7)**, per the 149O.1D plan's own wave ordering: Class-B deployment provisioning, production activation prerequisites, and the HATP operational-readiness transition. Wave 7 should additionally: (a) design the AG3/AG5 Permission Broker wiring that HATP-REQ-105/106 identifies as the remaining prerequisite for B-149O-1..4 system-level closure, using the gated API exclusively (never the legacy RAE-alone function, per this phase's §9 adjudication); (b) address Finding F-2 by having its own adapter enforce production-provider/trust-store provenance rather than relying solely on the absence of a call site; (c) as a narrow, separately-tracked item, correct Finding F-3's stale boundary-test target list. Do **not** equate a verified Wave 6 with HATP production readiness — that remains gated on Wave 7 and its own independent verification.
