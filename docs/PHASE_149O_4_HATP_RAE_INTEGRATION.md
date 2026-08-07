# Phase 149O.4 — HATP Wave 6, RAE Integration

**Phase ID:** 149O.4
**Phase type:** Implementation (RAE/HATP production integration)
**Subject requirements:** HATP-REQ-095, HATP-REQ-096, HATP-REQ-101, HATP-REQ-102, HATP-REQ-103, HATP-REQ-104
**Baseline:** commit `59cd4391` (Phase 149O.3, HATP Wave 5 independent verification) → `HEAD`
**Frozen contract:** `docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md` (HATP-001 v1.0, 117 requirements, byte-unchanged)
**Canonical plan:** `docs/PHASE_149O_1D_HUMAN_APPROVAL_TRUSTED_PROVENANCE_IMPLEMENTATION_PLAN.md`
**Implementation test suite:** `tests/test_phase_149o_4_hatp_rae_integration.py` (52 passed)

---

## 0. Verdict summary

| Question | Verdict |
|---|---|
| Wave-6 implementation | **HATP WAVE 6 RAE INTEGRATION IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION** |
| Activation conjunction | **HATP ACTIVATION CONJUNCTION: RAE-VALID ∧ HATP-VALID ∧ SUBSTRATE-OPERATIONAL — the exact contract-defined gate required for approval derivation** |
| RAE/HATP binding | **RAE/HATP BINDING: DECISION-ID + DECISION-DIGEST + BINDING-ID + BINDING-DIGEST + OPERATION + REPOSITORY + DEPLOYMENT ARE CONSUMPTION-TIME BOUND** |
| Approval derivation | **APPROVAL DERIVATION: RAE PASS ∧ HATP VALID ∧ ACTIVATION GATE — pure, injectable, no production bypass** |
| Live deployment | **CURRENT DEPLOYMENT: approval_present CANNOT BECOME TRUE** (mechanically enforced by Wave 4's unmodified `assert operational is False`) |
| HATP production readiness | **HATP PRODUCTION: NOT READY** (unchanged — Wave 7 Class-B provisioning does not exist) |
| Runtime | **Observed / observe / unavailable** (unchanged) |
| B-149O-1..4 | **REPAIRED AT IMPLEMENTATION LEVEL, PENDING INDEPENDENT WAVE-6 VERIFICATION** (the historical RAE-alone forgery paths no longer produce `approval_present=True` through the new HATP-gated derivation API; RAE-001's own, unmodified derivation remains — by contract design, HATP-REQ-095 — separately forgeable, since HATP is what closes that gap, not RAE) |
| Blocking findings | **ZERO** |

**Recommended next phase:** 149O.5 — HATP RAE Integration Independent Verification (per 149O.1D's own wave ordering; do **not** proceed to Wave 7 deployment provisioning).

---

## 1. Baseline confirmation

| Check | Result |
|---|---|
| `git status --short` | clean |
| `git rev-list --count origin/main..HEAD` | 0 |
| Latest completed phase | 149O.3, pushed, report completeness `complete` |
| `pcae health` | healthy |
| `pcae check` | passed |
| `pcae status coherence` | coherent |
| `pcae doctor task-memory` | warnings (7 pre-existing `tasks/DONE.md` sync gaps, unrelated to this phase) |
| `pcae push check` | clean (`nothing_to_push`) |
| `pcae runtime inspect` | Observed / observe / unavailable |
| `pcae notify status` | telegram configured, enabled, ready |
| `pcae phase-report reconcile --phase-id 149O.3` | reconciled, `already_dispatched`, receipt finalized |

All expected preconditions confirmed.

---

## 2. Wave-6 requirement reconstruction

Independently re-derived from `docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md` §29/§34 (not merely taken from 149O.3's summary):

| Requirement | Normative text (paraphrased) | RAE integration point | Test |
|---|---|---|---|
| HATP-REQ-095 | RAE-001 v1.0 is COMPATIBLE AS-IS; HATP supplies an *additional* required condition (a VALID proof) before `approval_present` MAY be `True`; RAE-001's existing fields (`governance_record_reference`, `evidence_id`, `rollback_operation_reference`, `expires_at`) are reused by reference | `resolve_rollback_approval_evidence` delegated to unchanged; `_hatp_expected_operation_for` derives HATP's `HATPExpectedOperation` from those exact reused fields | `test_genuine_rae_only_chain_no_hatp_proof_no_longer_approves` |
| HATP-REQ-096 | RAE provenance is trusted **iff** a HATP proof is VALID **and** RAE-001's own Decision/Binding/lifecycle requirements independently pass; neither substitutes for the other | `_derive_hatp_gated_approval_present` (pure two-of-three-visible, three-term conjunction) | full pure-conjunction matrix (§5 below) |
| HATP-REQ-101 | HATP-001 does not alter mutation freshness or execution ownership (RWMPC-001) | No RWMPC import added; no change to any RWMPC-owned module | import-boundary tests |
| HATP-REQ-102 | HATP-001 introduces no change to POL applicability (PBPA-001); POL-004 continues to interpret only the truthful `approval_present` fact | `HATPIntegratedApprovalEvidence` carries no permission/execution field; no Permission Broker import | `test_integrated_evidence_type_has_no_permission_or_execution_field`, `test_no_permission_broker_or_agent_import` |
| HATP-REQ-103 | No change to `pcae push` consumption of PBPC-001 | No `pcae push`/PBPC-001 code touched this phase | (unchanged files, confirmed by diff) |
| HATP-REQ-104 | A VALID HATP proof does not itself transform a `HUMAN_REVIEW` PB result into `ALLOW`; a fresh PB evaluation is required after fresh RAE/HATP validation | Not implemented here by design — this phase supplies only the `approval_present` fact; no PB call added | boundary tests (§9) |

No Wave-6 requirement is omitted; HATP-REQ-097–100 (CHGR/IWC/AESIC/TAMC boundaries) are unaffected — this phase adds no dependency on any of those subsystems.

---

## 3. Pre-integration RAE approval derivation (reconstructed from source, not from memory)

`resolve_rollback_approval_evidence` (`src/pcae/core/rollback_approval_evidence.py`, unmodified this phase) derives `approval_present` purely from RAE-001-owned facts: Binding existence, `content_digest` self-consistency, canonical creation registration, CHGR Decision resolution + publication receipt, `selected_option_id == approve_rollback`, eligible-authority text presence, `rollback_site`/operation-reference match against the live operation context, non-revocation, non-`used`, TTL (24h), `repository_state_binding` freshness, and non-supersession. It has **zero** HATP awareness — no import of any HATP module existed before this phase, confirmed by `tests/test_rollback_approval_evidence_contract.py`'s pre-existing import-boundary tests (still passing, still enforced by the same `_FORBIDDEN_IMPORT_PREFIXES` mechanism, unamended).

`tests/test_phase_149o_rollback_approval_evidence_canonical_provenance_hardening_independent_verification.py::test_149o_canonical_positive_control_still_valid` independently confirms (both before and after this phase's change — re-run against `HEAD~0` via `git stash`) that a fully **genuine**, legitimately-created RAE chain (real CHGR Decision, real publication, real Binding via the real API — no forgery at all) resolves `approval_present=True` through this pre-existing, unmodified function, with **no HATP proof involved whatsoever**. This is the precise shape of HATP-REQ-095's "COMPATIBLE AS-IS": RAE-001 alone remains a complete, self-sufficient (by its own contract) approval authority — it is HATP-REQ-096's *additional* condition, consumed through a *new* API surface, that this phase adds.

---

## 4. Historical B-149O-1..4 reproduction against pre-Wave-6 RAE

Re-run (unmodified) against the current tree:

```
pytest tests/test_phase_149o_rollback_approval_evidence_canonical_provenance_hardening_independent_verification.py -q
```

Result: **4 failed, 13 passed** — identical, byte-for-byte, to the result on `HEAD` *before* this phase's changes (verified via `git stash`/re-run). The four failures are the open B-149O-1..4 attack reproductions:

- `test_149o_fake_chgr_record_plus_fake_publication_receipt` (B-149O-1/B-149O-3 class)
- `test_149o_fake_binding_plus_fake_creation_registration` (B-149O-2 class)
- `test_149o_full_end_to_end_forgery_zero_legitimate_api_calls` (B-149O-1/B-149O-3 class)
- `test_149o_copied_registration_under_new_key_with_matching_fields_rejected` (B-149O-4 class)

Each demonstrates `resolve_rollback_approval_evidence` alone reaching `approval_present=True` from a hand-authored (agent-only, single-process) artifact chain with no genuine, independent, hardware-backed human decision behind it. This is expected and by design (HATP-REQ-095: RAE-001's own semantics are unmodified) — closing these paths is exactly HATP-REQ-096's job, and only for callers that use the *new* Wave-6 API.

---

## 5. HATP activation conjunction (derived from HATP-REQ-096, HATP-REQ-108, HATP-REQ-029)

```
approval_present =
      RAE_GATE            (resolve_rollback_approval_evidence(...).approval_present is True)
  AND HATP_GATE            (verify_hatp_proof(...).status is HATPVerificationStatus.VALID,
                             PLUS an RAE-integration-layer Decision/Binding *digest* check
                             verify_hatp_proof itself does not perform — §6 below)
  AND ACTIVATION_GATE      (inspect_hatp_verification_substrate_readiness(...).operational is True)
```

Implemented as the pure function `_derive_hatp_gated_approval_present` in `rollback_approval_evidence.py`. `ACTIVATION_GATE` is HATP-REQ-108/HATP-REQ-029's operational-readiness ceiling — the same, **unmodified** Wave-4 `inspect_hatp_verification_substrate_readiness`, whose own body still contains `assert operational is False` (mechanically confirmed unchanged, `test_wave4_substrate_readiness_still_mechanically_cannot_be_operational`). No caller of the public integration function can pass `activation_operational` directly; it is always computed internally from that real function. The `True` branch of `ACTIVATION_GATE` is reachable **only** by calling the pure conjunction helper directly with a synthetic value — never through any production entry point — which is exactly how the full-conjunction and one-fact-removed matrices below are tested.

No production `force_operational`, `allow_test_provider`, or `skip_hatp` parameter exists anywhere on the new API (`test_legacy_approval_flag_cannot_bypass_hatp_gate`, `test_no_default_provider_or_trust_store_production_bypass`).

---

## 6. RAE/HATP binding (Decision + Binding + Operation + Repository + Deployment)

`verify_hatp_proof` (Wave 4, unmodified) independently re-verifies proof *identity*: `decision_record_id`, `binding_id`, `rollback_site`, `operation_reference` (via a caller-supplied `HATPExpectedOperation`), plus `repository_id` and `canonical_deployment_root`. `_hatp_expected_operation_for` derives that `HATPExpectedOperation` **exclusively from the resolved RAE Binding**, never from a caller-supplied value — so a proof for a different Decision/Binding/operation cannot be substituted.

`verify_hatp_proof` does **not** compare `decision_record_digest`/`binding_digest` — documented in Phase 149O.1J as an intentional Wave-6 deferral, since Wave 4 alone has no RAE Binding to compare against. `resolve_rollback_approval_evidence_with_hatp` closes this: after a `VALID` per-identity result, it independently checks `hatp_proof.decision_record_digest == binding.governance_record_reference.record_digest` and `hatp_proof.binding_digest == binding.content_digest`, downgrading to `WRONG_OPERATION` on mismatch. This is the single piece of genuinely new verification logic this phase adds beyond wiring — everything else is composition of Wave-4/RAE-001 unmodified primitives.

AG3 (`job_id`/`original_commit_sha`) and AG5 (`per_id`/`ecp_id`) operation references are converted 1:1 between RAE's and HATP's independently-typed (never shared) dataclasses inside `_hatp_expected_operation_for`; cross-family substitution (an AG3 proof against an AG5 Binding, or vice versa) is rejected as `WRONG_OPERATION` by the identity check alone, confirmed by `test_ag3_proof_cannot_approve_ag5_operation` / `test_ag5_proof_cannot_approve_ag3_operation`.

---

## 7. Consumption-time reverification

`resolve_rollback_approval_evidence_with_hatp` performs no caching at any layer — every call re-derives `HATP_GATE` and `ACTIVATION_GATE` fresh from the trust store supplied that call. `test_consumption_time_revocation_defeats_previously_valid_proof` demonstrates: an identical proof verifies `VALID` before a signer revocation is written to the trust-store registry, and `REVOKED_SIGNER` immediately after, with no code path capable of preferring the earlier result.

---

## 8. 13-state HATP status matrix

The full closed vocabulary (`HATP_VERIFICATION_STATUS_VALUES`, 13 members) is exercised against the pure conjunction with `rae_approval_present=True, activation_operational=True` (`test_pure_conjunction_13_state_matrix_only_valid_can_pass`): **only** `VALID` yields `True`; all 12 others yield `False`. No default/fallback branch exists in `_derive_hatp_gated_approval_present` — it is three sequential `if not X: return False` guards followed by an unconditional `return True`, so an unlisted/future status added to the enum would need to *equal* `HATPVerificationStatus.VALID` to pass, which is impossible by construction for any other member.

Representative individually-verified statuses through the full, real integration path (not just the pure helper): `MISSING` (no proof), `UNKNOWN_SIGNER` (unenrolled key), `REVOKED_SIGNER`, `WRONG_REPOSITORY`, `WRONG_DEPLOYMENT`, `EXPIRED`, and `WRONG_OPERATION` (digest replay, cross-family replay, copied-evidence replay) — each independently confirmed `approval_present=False`. The remaining statuses (`MALFORMED`, `INVALID_SIGNATURE`, `UNAUTHORIZED_SIGNER`, `INVALID_ATTESTATION`, `USER_PRESENCE_NOT_PROVEN`) are exhaustively covered for the *verification* layer by Wave 4's own 136-test suite (unmodified, still passing) and for the *conjunction* layer by the 13-state pure-function matrix above — re-deriving per-status RAE-integration fixtures for all 13 would duplicate Wave 4's own independent coverage without adding signal, since `_derive_hatp_gated_approval_present` treats every non-`VALID` status identically.

---

## 9. Exception / fail-closed matrix

| Scenario | Result | Test |
|---|---|---|
| HATP trust-store raises on every method | `approval_present=False` | `test_hatp_trust_store_exception_fails_closed` |
| HATP provider raises (`RuntimeError`, simulating hardware I/O failure) | `HATPVerificationStatus.INVALID_SIGNATURE`, `approval_present=False` (Wave-4's own fail-closed discipline, unmodified) | `test_hatp_provider_exception_fails_closed` |
| `inspect_hatp_verification_substrate_readiness` itself raises | `approval_present=False` (caught by this module's outer `except Exception`) | `test_readiness_inspection_exception_fails_closed` |
| Any other internal error | `HATPIntegratedApprovalEvidence(approval_present=False, ...)`, no exception ever propagates | mirrors RAE-REQ-042 discipline, same pattern as `resolve_rollback_approval_evidence`'s own umbrella |

---

## 10. Boundary / scope confirmation

- **Production diff:** exactly one file, `src/pcae/core/rollback_approval_evidence.py` (+~260 lines: `HATPIntegratedApprovalEvidence`, `_hatp_expected_operation_for`, `_derive_hatp_gated_approval_present`, `resolve_rollback_approval_evidence_with_hatp`, `derive_rollback_approval_present_with_hatp`, plus new imports). No other `src/pcae/**` file touched.
- **New imports:** `pcae.core.hatp_bootstrap.HATPTrustStore`; `pcae.core.hatp_providers.HATPProofVerifierProvider` (interface only — no `fido2`/`cryptography`/concrete-provider import, confirmed by `test_no_fido2_or_cryptography_or_hardware_provider_import`); `pcae.core.human_approval_trusted_provenance` (Wave-3/4 types + `verify_hatp_proof` + `inspect_hatp_verification_substrate_readiness`).
- **Dependency direction:** one-way, RAE → HATP. `pcae.core.human_approval_trusted_provenance` does not import `rollback_approval_evidence` (`test_hatp_module_does_not_import_rae`); no import cycle (module imports cleanly, confirmed by direct `python -c "import pcae.core.rollback_approval_evidence"`).
- **No import of** `permission_broker.py`, `permission_broker_foundation.py`, `mutation_permission.py`, `agent.py`, `commands/agent.py`, `hatp_fido2_provider.py`, `hatp_hardware_credentials.py` — confirmed by AST-based import-name checks (`test_no_permission_broker_or_agent_import`), not substring search (substring search on this module's own docstrings, which *discuss* those boundaries in prose, produces false positives — corrected during test authoring).
- **No Permission Broker semantic change.** `HATPIntegratedApprovalEvidence` carries no `permission`/`allow`/`deny`/`execute` field (`test_integrated_evidence_type_has_no_permission_or_execution_field`).
- **No rollback execution, no AG3/AG5 dispatch, no Runtime Enforcement change, no `agent.py` change, no prompt/dispatch capability** — none added; this phase supplies a derivation function only, with no caller yet (mirrors `derive_rollback_approval_present`'s own pre-existing "narrow API a future consumer will call" status).
- **Wave-4 boundary test updates (expected, not a regression):** `tests/test_hatp_verification_engine.py::test_verify_hatp_proof_has_no_production_call_sites` and two tests in `tests/test_phase_149o_1j_hatp_verification_engine_independent_verification.py` previously asserted **zero** production call sites for `verify_hatp_proof`/`inspect_hatp_verification_substrate_readiness`, including in `rollback_approval_evidence.py` — a boundary that was correct through Wave 5 (no consumer existed) and is *supposed* to change exactly now, at Wave 6, per HATP-REQ-095/096. Updated to exclude `rollback_approval_evidence.py` specifically while continuing to forbid `permission_broker*.py`/`agent.py` absolutely (still enforced, still passing). This is the only modification to pre-existing test files this phase makes; Wave-4 **production** source (`human_approval_trusted_provenance.py`) is untouched.

---

## 11. Regressions

| Suite | Command | Result |
|---|---|---|
| Wave-4 (implementation + independent verification) | `pytest tests/test_hatp_verification_engine.py tests/test_phase_149o_1j_hatp_verification_engine_independent_verification.py -q` | **136 passed** (matches 149O.3's documented 59+77 baseline exactly) |
| Wave-5 (hardware provider) | `pytest tests/test_phase_149o_2_hatp_hardware_provider_implementation.py tests/test_phase_149o_3_hatp_hardware_provider_independent_verification.py -q` | **2 skipped** — the `fido2` extra (`hatp-hardware`) is not installed in this execution environment (`pip install` blocked by PEP 668 externally-managed-environment protection); this is a pre-existing environment characteristic, not a Wave-6 regression — Wave 6 touches no Wave-5 file |
| RAE full (149L/149J/149M/149N/149O + new Wave-6 suite) | `pytest tests/test_rollback_approval_evidence_*.py tests/test_phase_149j_*.py tests/test_phase_149m_*.py tests/test_phase_149n_*.py tests/test_phase_149o_rollback_approval_evidence_*.py tests/test_phase_149o_4_hatp_rae_integration.py -q` | **255 passed, 4 failed** — the 4 failures are the known-open B-149O-1..4 reproductions (§4), byte-identical to the pre-phase baseline (diffed via `git stash`) |
| Wave-6 new suite alone | `pytest tests/test_phase_149o_4_hatp_rae_integration.py -q` | **52 passed** |
| Fast Green | `pytest -m fast_green -q` | **4588 passed, 2 skipped** (the 2 skips are the same pre-existing `fido2`-extra-not-installed Wave-5 skips, §above), **2 failed while this phase's diff was still uncommitted**: `tests/test_phase_149o_1g_hatp_proof_models_canonical_serialization.py::test_rae_module_untouched` and `::test_only_expected_production_files_changed`. Both compare `git diff --name-only HEAD` (i.e. *currently uncommitted* changes) against a fixed allow-list authored for Phase 149O.1G's own diff window — they are not fixed-baseline regression tests, they resolve to a clean (empty) diff automatically once this phase's changes are committed, and were re-confirmed clean post-commit (§14) |
| Report trust | `pytest tests/test_phase_reports.py tests/test_phase_reports_cli.py tests/test_phase_report_trust_hard_fail.py -q` | **187 passed** (149O.3's baseline was 186 passed + 1 known live-`.pcae/`-state-dependent failure; that state-dependent test now passes because task/lifecycle state has since advanced — not a Wave-6 effect, since no report-trust file was touched this phase) |
| Permission Broker | `pytest tests/ -k permission_broker -q` | **979 passed, 1 failed, 2 skipped** — the 1 failure is the known pre-existing `test_permission_broker_consumer_scope_inventory` docstring-prose false positive (149O.3 §141 baseline); no new failure |
| Import smoke test | `python -c "import pcae.core.rollback_approval_evidence"` | clean, no circular-import error |

No suite shows a failure attributable to this phase's changes beyond the two intentionally-updated Wave-4 boundary tests documented in §10.

---

## 12. Contract/boundary invariant confirmations

- HATP-001 v1.0 remained byte-unchanged (no edit to `docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md` this phase).
- RAE-001 v1.0 remained unchanged (no RAE-001 contract file exists to edit; RAE-001's *implementation* semantics in `resolve_rollback_approval_evidence` are unmodified — only additive new functions were appended).
- Wave-1 (`repository_identity.py`), Wave-2 (`hatp_bootstrap.py`), Wave-3 (`human_approval_trusted_provenance.py` canonicalization/proof models), Wave-4 (`verify_hatp_proof`/`inspect_hatp_verification_substrate_readiness` semantics), Wave-5 (`hatp_providers.py`, `hatp_fido2_provider.py`, `hatp_piv_provider.py`, `hatp_hardware_credentials.py`) all remained unchanged — confirmed by `git diff --stat` showing exactly one modified `src/` file plus one new/two updated test files.
- B-149O.1H-1, B-149O.1H.4-1, B-149O.1H-2, B-149O.1F-1 remain independently confirmed closed (untouched this phase).
- No Class-B deployment was provisioned; no real production HATP activation occurred; `inspect_hatp_verification_substrate_readiness`'s `assert operational is False` remains present, unmodified, and load-bearing.
- No Permission Broker policy meaning changed; no AG3/AG5 Permission Broker wiring was added.
- No rollback execution behavior changed; no Runtime Enforcement behavior changed; no Prompt Generation/Dispatch/agent-invocation capability was implemented.
- HATP VALID remains distinct from approval (`HATPVerificationResult` still carries no approval/permission field, HATP-REQ-079/HATP-REQ-104 discipline preserved in the new integration layer).
- Approval remains distinct from Permission Broker permission; permission remains distinct from capability/execution.
- The current same-principal deployment cannot derive `approval_present=True` (§5, §11).
- HATP production remains **NOT READY**; runtime remains **Observed / observe / unavailable**.

---

## 13a. Post-commit diff-window re-verification

`tests/test_phase_149o_1g_hatp_proof_models_canonical_serialization.py::test_rae_module_untouched` and `::test_only_expected_production_files_changed` re-run **clean** once this phase's changes are committed (`git diff --name-only HEAD` returns empty for a clean, committed tree) — confirmed by re-running that file alone post-commit as part of phase finalization. See the phase-completion metadata for the exact post-commit command/result.

## 13. Recommended next phase

**149O.5 — HATP RAE Integration Independent Verification.** It must independently attack: the full three-term conjunction (including attempted synthetic-True forcing through any caller-reachable path), all 13 HATP statuses in the integration context, Decision/Binding digest and identity replay, AG3/AG5 cross-family replay, current-state revocation (signer/authority/deployment), legacy-flag bypass attempts, the full historical Threat-A forged-chain attack through the new gated API specifically, cached-VALID reuse, and confirmation that zero Permission Broker/agent/execution effects were introduced. Do **not** proceed to Wave 7 deployment/activation provisioning until that verification completes with zero BLOCKING findings.
