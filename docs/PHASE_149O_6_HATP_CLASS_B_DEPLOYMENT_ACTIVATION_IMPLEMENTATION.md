# Phase 149O.6 — HATP Class-B Deployment + Activation Implementation (Wave 7)

**Phase ID:** 149O.6
**Phase type:** Implementation (Wave 7 — Class-B deployment/activation semantics, AG3/AG5 Permission Broker wiring)
**Baseline:** `HEAD` = commit `17a2c1b4` (Phase 149O.5, complete/pushed) at phase start
**Frozen contract:** `docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md` (HATP-001 v1.0, 117 requirements) — **byte-unchanged, confirmed**
**New independent test suite:** `tests/test_phase_149o_6_hatp_wave7_class_b_deployment_activation.py` (26 passed)

---

## 0. Verdict summary

| Question | Verdict |
|---|---|
| Class-B readiness | **CLASS-B ACTIVATION MODEL: IMPLEMENTED — CURRENT DEPLOYMENT REMAINS NOT READY** |
| Provider/trust-store provenance (F-2) | **PRODUCTION HATP DEPENDENCIES: PROTECTED PRODUCTION PROVIDER / TRUST ROOTS ONLY — TEST DEPENDENCY INJECTION CANNOT ESTABLISH PRODUCTION AUTHORITY** (closed structurally: the production adapter accepts no `hatp_provider`/`hatp_trust_store` parameter at all) |
| AG3 | **AG3 APPROVAL FACT: DERIVED EXCLUSIVELY THROUGH HATP-GATED RAE CONSUMPTION** (when `hatp_evidence_id` is supplied; otherwise unchanged from pre-Wave-7 behavior — see §7 for the scope decision) |
| AG5 | Same as AG3 |
| Legacy path | **LEGACY RAE-ONLY APPROVAL: NON-AUTHORITY-BEARING FOR AG3/AG5 PRODUCTION PERMISSION** (the new adapter never imports the legacy narrow API) |
| B-149O-1..4 | **REPAIRED AT SYSTEM IMPLEMENTATION LEVEL, PENDING INDEPENDENT WAVE-7 VERIFICATION** (see §9 for exact scope) |
| Wave-7 implementation verdict | **HATP WAVE 7 CLASS-B DEPLOYMENT / ACTIVATION IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION** |
| HATP production readiness | **HATP PRODUCTION: NOT READY** (this deployment: same-principal, no hardware provider attached) |
| Runtime | **Observed / observe / unavailable** (unchanged, before and after) |

**Recommended next phase:** 149O.7 — HATP Class-B Deployment / Activation Independent Verification.

---

## 1. Initial inspection (independently confirmed)

| Check | Result |
|---|---|
| `git status --short` | clean |
| `git rev-list --count origin/main..HEAD` | 0 |
| `pcae health` | healthy |
| `pcae check` | passed |
| `pcae status coherence` | coherent |
| `pcae doctor task-memory` | warnings (7 pre-existing `tasks/DONE.md` sync gaps, unrelated to this phase) |
| `pcae push check` | clean (`nothing_to_push`) |
| `pcae runtime inspect` | Observed / observe / unavailable |
| `pcae notify status` | telegram configured/enabled/ready |
| `pcae phase-report show --latest` / `reconcile --phase-id 149O.5` | 149O.5 completed, pushed, report completeness `complete`, reconciled `already_dispatched` |

---

## 2. Wave-7 requirement reconstruction (from contract text directly)

**HATP-REQ-105** (§35, verbatim): "B-149O-1 through B-149O-4 remain OPEN. This contract freeze does not repair them. Their future closure requires: HATP implementation, RAE-001/HATP-001 integration, AG3/AG5 Permission Broker wiring, and independent adversarial verification — none of which occur in this phase." (i.e. the 149O.1B.3 freeze phase.) Wave 6 (149O.4/149O.5) closed the first two prerequisites; this phase's scope is exactly the third: AG3/AG5 Permission Broker wiring.

**HATP-REQ-106** (§35, verbatim): the per-attack closure mapping — B-149O-1 (fake CHGR + fake receipt) closes once no valid hardware-backed HATP proof can be forged; B-149O-2 (real Decision + fake Binding + fake registration) closes once the Binding digest is covered by a valid HATP proof; B-149O-3 (fully handcrafted chain) closes for the same reason as B-149O-1; B-149O-4 (fresh attacker key) closes once the key is mechanically absent from the registry and verification enforces `UNAUTHORIZED_SIGNER`.

**§46 "Implementation Readiness Status"** (load-bearing prose, non-numbered): as of the contract freeze, `AG3 / AG5: UNWIRED`. This phase's central deliverable is making that line no longer accurately describe a *possible* production path (a real, production-callable, independently-tested wiring now exists), while explicitly not changing the frozen contract text itself.

Additional governing requirements consulted: **HATP-REQ-108** (frozen current-deployment-readiness status block; deliberately not reproduced with different values by this phase — this deployment remains NOT READY), **HATP-REQ-109** (Agent OS principal / Human-Admin OS principal threat-capability matrix — normative source for Class-B topology, already enforced by Wave 2's `inspect_bootstrap_environment`), **HATP-REQ-115** ("actual current provisioning of the Class-B OS boundary... remains NOT READY" — the activation-readiness question this phase's `inspect_hatp_verification_substrate_readiness` update answers mechanically rather than in prose).

| Requirement | Normative meaning | Wave-7 implementation owner | Production location | Verification |
|---|---|---|---|---|
| HATP-REQ-105 | AG3/AG5 PB wiring required for B-149O-1..4 closure | `hatp_ag_authority.py` (new) | `resolve_ag3_gated_rollback_authority`/`resolve_ag5_gated_rollback_authority` | `test_phase_149o_6_...py` §3-4 |
| HATP-REQ-106 | Per-attack closure criteria | Same adapter, consuming Wave-6's unchanged binding/digest checks | Same | `test_b_149o_1/2/4_..._blocked_through_real_consumer` |
| HATP-REQ-108/§37 | Current deployment remains NOT READY absent real Class-B + hardware | `inspect_hatp_verification_substrate_readiness` (updated) | `human_approval_trusted_provenance.py` | `test_current_real_deployment_still_not_ready` |
| HATP-REQ-109 | Class-B OS-principal separation | Unchanged — already enforced by Wave 2's `inspect_bootstrap_environment` (`agent_and_admin_share_os_principal` → `UNSAFE_CONFIGURATION`) | `hatp_bootstrap.py` (untouched) | Re-exercised via `class_b_bootstrap_environment_safe` term, `test_removing_any_single_readiness_term_forces_not_ready[class_b_bootstrap_environment_safe]` |
| HATP-REQ-115/§37 | Activation readiness must be mechanically derived, not asserted | `inspect_hatp_verification_substrate_readiness` | `human_approval_trusted_provenance.py` | `test_synthetic_full_class_b_reaches_operational`, one-term-removed matrix |

---

## 3. Wave-4 activation ceiling: from hardcoded to real

`inspect_hatp_verification_substrate_readiness` (`src/pcae/core/human_approval_trusted_provenance.py`) computed a 7-term conjunction. Through Wave 6, two terms — `provider_profile_available`, `provider_attestation_trusted` — were permanently `False`, with a trailing `assert operational is False` tripwire enforcing the Wave-4-era invariant "this can never be reachable."

Wave 7 replaces both terms with real derivations, using the Wave-5 hardware-provider layer that did not exist when Wave 4 wrote the placeholder:

- `provider_profile_available`: `True` iff `hatp_providers.discover_hardware_providers()` reports a `HATP_HARDWARE_PROVIDER_V1` availability entry with both `library_installed` and `device_detected` true.
- `provider_attestation_trusted`: `True` iff, additionally, `hatp_providers.create_production_hardware_provider(...)` succeeds and the resulting provider's `capabilities().hatp_conformant` is `CONFORMANT` or `CONFORMANT_WITH_NON_BLOCKING_LIMITATIONS`.

The `assert operational is False` tripwire is removed; `HATPVerificationSubstrateStatus` gains an `OPERATIONAL` member alongside the pre-existing `NOT_READY`. No parameter or code path lets a caller force any individual term or the overall conjunction — every term is read-only inspection of the supplied trust store or of provider discovery/capability facts, exactly mirroring the discipline the removed assertion previously enforced by brute force.

**On this deployment** (same-principal, no hardware attached): `provider_profile_available` is mechanically `False` (no `HATP_HARDWARE_PROVIDER_V1` device discovered), so `operational` remains mechanically `False` — the identical fail-closed outcome as before this phase, now reached through real derivation rather than a hardcoded literal.

**Synthetic verification**: `test_synthetic_full_class_b_reaches_operational` constructs a fully self-consistent Class-B deployment (real repository identity check, real trust-store enrollment/authority records, a safe bootstrap-environment override standing in for genuine OS-principal separation which this single-user test machine cannot honestly provision, and a monkeypatched conformant hardware-provider discovery) and confirms `operational=True`/`status=OPERATIONAL` is reachable. `test_removing_any_single_readiness_term_forces_not_ready` (parametrized over all 6 non-trivial terms) confirms removing any single one collapses the whole conjunction back to `NOT_READY` — no term is redundant, no term is load-bearing-but-untested.

Two pre-existing boundary tests from earlier phases encoded the now-superseded Wave-4 invariants literally (`assert operational is False` in source; `HATPVerificationSubstrateStatus` has exactly one member) — updated narrowly, with justification, to the new two-member/no-hardcoded-assert reality; both still independently re-confirm the *behavioral* invariant (this deployment mechanically cannot reach operational) via the real function rather than via source-text matching. See §11.

---

## 4. Production authority adapter: `pcae.core.hatp_ag_authority`

New module, the "future AG3/AG5 adapter" `resolve_rollback_approval_evidence_with_hatp`'s own Wave-6 docstring named but did not itself construct. Two public entry points:

- `resolve_ag3_gated_rollback_authority(root, *, job_id, original_commit_sha, task_id, repository_state, evidence_id, hatp_proof, hatp_evidence, evaluation_time=None, evidence_store=None, publication_root=None) -> GatedRollbackAuthorityResult`
- `resolve_ag5_gated_rollback_authority(root, *, per_id, ecp_id, task_id, repository_state, evidence_id, hatp_proof, hatp_evidence, evaluation_time=None, evidence_store=None, publication_root=None) -> GatedRollbackAuthorityResult`

Each: (1) resolves production HATP dependencies internally — `HATPTrustStore.production()`, `hatp_providers.create_production_hardware_provider(HATP_HARDWARE_PROVIDER_V1)` — never from a caller-supplied provider/trust-store argument (F-2 closure, §5); (2) resolves the current repository identity (`repository_identity.read_repository_identity`) and canonical deployment root (`hatp_bootstrap.resolve_canonical_deployment_root`); (3) calls the unchanged Wave-6 `resolve_rollback_approval_evidence_with_hatp`, never the legacy narrow API; (4) constructs a `PermissionBrokerRequest` (`action_type="rollback"`, `execution_class="rollback"`, `requested_component="COMP-008"`) with `approval_present` set exclusively from the just-derived gated fact, and evaluates it through the real, unmodified `PermissionBroker` policy engine. `evidence_store`/`publication_root` remain overridable (mirroring Wave 6's own signature) — this is an RAE evidence *location* parameter, not a trust/authority dependency, and is unrelated to F-2's provider/trust-store provenance concern.

Every dependency-resolution failure (no repository identity provisioned, unsupported platform, no hardware provider) is caught and converted to `approval_present=False`, never propagated as an exception — mirroring RAE-REQ-042/the Wave-6 fail-closed umbrella.

---

## 5. F-2 closure (149O.5 finding, previously non-blocking/deferred)

149O.5 found that `HATPProofVerifierProvider` is a structural `typing.Protocol`, so `TestHATPProofVerifierProvider` satisfies it via `isinstance`, and recommended (verbatim): *"the future PB/AG3/AG5 adapter should itself assert production-provider provenance ... rather than relying solely on code-review discipline at the call site."*

Wave 7 closes this by construction rather than by runtime `isinstance` check (which cannot reliably reject a structurally-conforming fake): `resolve_ag3_gated_rollback_authority`/`resolve_ag5_gated_rollback_authority` accept **no** `hatp_provider`/`hatp_trust_store` parameter at all. There is no argument through which an ordinary production caller — or a test calling the public API — could substitute a test provider or an arbitrary trust store. The only injection points are the module-level production factory functions themselves, reachable only via `monkeypatch` (a test-harness technique operating on the module namespace, not a caller-facing parameter) — confirmed by `test_ag3_adapter_has_no_provider_or_trust_store_parameter`/`test_ag5_...` (signature inspection) and `test_adapter_module_never_references_test_provider` (source-text guard).

**F-2 closure criterion, confirmed met**: ordinary production callers cannot substitute a test provider or arbitrary trust store for the protected production dependencies used by AG3/AG5 approval derivation.

---

## 6. Legacy-path and caller-boolean exclusion

`test_adapter_module_never_calls_legacy_rae_only_derivation` confirms the adapter's source never references the legacy narrow API (`resolve_rollback_approval_evidence(` / ` derive_rollback_approval_present(`), only the Wave-6 gated variant. `test_pb_receives_gated_fact_not_caller_boolean` and the F-2 signature tests jointly confirm no `approval_present` parameter exists anywhere on the adapter's public surface — the Permission Broker request's `approval_present` field is provably the derived fact, never a caller-suppliable value.

Two pre-existing 149L/149M-era boundary tests encoded "AG3/AG5 must remain unwired" and "zero production consumers of the RAE API exist outside `rollback_approval_evidence.py`" as literal invariants. Both are updated narrowly (§11) to name the new, single, intentional, independently-reviewed consumer this phase adds — the underlying invariant they protect (no *undetected* new consumer) is preserved, just re-scoped to include exactly one named, reviewed addition.

---

## 7. AG3/AG5 wiring: scope decision (read this before evaluating "wiring" claims)

`execute_rollback` (AG3) and `build_rollback_execution` (AG5) in `src/pcae/core/agent.py` each gain three new **keyword-only, optional** parameters: `hatp_evidence_id`, `hatp_proof`, `hatp_evidence`, all defaulting to `None`.

- **When `hatp_evidence_id` is omitted** (every pre-Wave-7 caller, and every existing CLI command today — no CLI flag currently supplies these): behavior is unchanged. Neither function imports or calls `hatp_ag_authority` at all; the pre-existing dispatch preconditions (`rollback_approval_state == "approved"` for AG3; PER status/divergence checks for AG5) remain the sole gate on the real `git revert`/file-restore mutation, byte-identical to before this phase. Confirmed by `test_execute_rollback_default_invocation_never_touches_hatp_module` (the adapter is monkeypatched to raise if invoked, and the pre-existing "unknown job" error surfaces unchanged) and the full pre-existing AG3/AG5 regression suite (§10).
- **When `hatp_evidence_id` is supplied**: the function derives `approval_present` through the gated production adapter and evaluates Permission Broker, attaching both facts to the return value under a new `hatp_authority` key (`approval_present`, `rae_result`, `hatp_status`, `activation_operational`, `permission_broker_decision`) for governance/audit visibility. **This does not itself gate whether the git revert/file-restore runs** — the pre-existing preconditions remain the sole dispatch gate, unchanged.

This is a deliberate, load-bearing design choice, not an oversight, for two independent reasons:

1. **System-wide Permission Broker architecture.** `permission_broker_foundation.py`'s own module docstring: "Current implementation status: **execution unavailable**. Every decision this broker returns — including ALLOW — carries `implementation_status='execution_unavailable'`, because no execution boundary (`COMP-002`) exists yet." PB is advisory everywhere else in PCAE today (its only two other production call sites, `push.py` and `mutation_permission.py`, likewise never let a PB decision block a real mutation on its own). Making AG3/AG5 the first and only place PB decisions gate real execution would be a materially larger, system-architecture-level change than "AG3/AG5 Permission Broker wiring" — and the governing brief for this phase explicitly prohibits scope creep of that kind ("must NOT... change unrelated runtime execution").
2. **No CLI/signing-ceremony surface exists to respect it.** There is no production way today for a human to supply a `HumanApprovalProvenanceProof` through the CLI — proofs are only ever produced by a real hardware provider's `request_signature()`. Making the *default* CLI invocation of `pcae remote rollback execute`/`pcae rollback` suddenly require HATP evidence that no CLI flag can supply would not "wire" anything; it would silently disable rollback execution entirely for every existing caller. Building a new proof-authoring CLI surface from scratch was judged out of this phase's chartered scope ("Class-B deployment + activation implementation" and "AG3/AG5 Permission Broker wiring" — not "build a human-presence signing ceremony UX").

The wiring that *does* exist is real and production-callable: `hatp_ag_authority.py`'s two functions are genuine, F-2-closed, fully-tested production code, reachable from the real AG3/AG5 command functions via a real (if currently unexercised by any CLI flag) parameter path. A future phase wiring a CLI/signing-ceremony surface to these parameters — and, separately, deciding whether/how PB decisions should gate AG3/AG5 dispatch once a real execution boundary exists — is the natural continuation; this phase deliberately does not attempt either, and says so.

---

## 8. Historical attacks reproduced through the actual production consumer

`tests/test_phase_149o_6_hatp_wave7_class_b_deployment_activation.py` constructs a genuine RAE Binding + HATP proof chain (mirroring the 149O.4 harness pattern) and drives it through `resolve_ag3_gated_rollback_authority` itself — the real production entry point, not `resolve_rollback_approval_evidence_with_hatp` directly — with production factories monkeypatched to a controlled synthetic deployment (the only way to exercise this deterministically without real hardware/OS principals).

| Attack | Result through the real consumer |
|---|---|
| B-149O-1 (unenrolled attacker signer, otherwise well-formed) | `approval_present=False`, `hatp_status != VALID` |
| B-149O-2 (mutated Binding digest) | `approval_present=False` |
| B-149O-4 (fresh key absent from registry) | `approval_present=False`, `hatp_status=UNKNOWN_SIGNER` |
| B-149O-3-shaped (genuine RAE chain, no HATP proof at all — the scenario that resolves `True` through the legacy API alone) | `rae_result=VALID`, `approval_present=False` |
| Wrong repository | `approval_present=False` |
| HATP VALID + no active task (POL-001) | `hatp_status=VALID` but `permission_decision=DENY`, never `ALLOW` — confirms no direct HATP→ALLOW mapping |
| No HATP evidence at all | `permission_decision=HUMAN_REVIEW` (POL-004), not a hardcoded HATP-status mapping |

No variant reached `approval_present=True` on this (non-conformant-provider) deployment, and no variant reached PB `ALLOW` without every independent PB policy also passing.

---

## 9. B-149O-1..4 status

**REPAIRED AT SYSTEM IMPLEMENTATION LEVEL, PENDING INDEPENDENT WAVE-7 VERIFICATION** — scoped precisely: a real, F-2-closed, independently-tested production consumer of the gated HATP/RAE derivation now exists (`hatp_ag_authority.py`), reachable from the real AG3/AG5 command functions, and all four historical attacks are blocked through that actual consumer (§8). This phase does not self-close B-149O-1..4 to system-level (per the governing brief's own instruction not to); that adjudication is left to the recommended 149O.7 independent verification phase. The qualification in §7 — that this consumer is reachable via an optional parameter no CLI flag currently populates — is the honest boundary of what "wired" means as of this phase and should be the starting point for that verification.

---

## 10. Regressions

| Suite | Expected/prior baseline | This phase |
|---|---|---|
| Wave 4 (`test_hatp_verification_engine.py` + `test_phase_149o_1j_...py`) | 136 passed | **136 passed** (2 tests narrowly updated, §11) |
| Wave 5 (`test_phase_149o_2_...py` + `test_phase_149o_3_...py`) | 2 skipped (no fido2 hardware) | **2 skipped**, unaffected |
| Wave 6 (`test_phase_149o_4_hatp_rae_integration.py`) | 52 passed (doc-cited) | **51 passed, 1 pre-existing failure** (`test_rae_stale_plus_valid_hatp_still_false` — a RAE freshness/staleness bug, reproduced identically on a clean stash before any Wave-7 change; unrelated to AG3/AG5 wiring; not fixed by this phase, retained as a non-blocking pre-existing finding) + 1 test narrowly updated (§11) |
| Wave 6.5 (`test_phase_149o_5_...py`) | 47 passed | **46 passed + 1 transient** (`test_no_production_source_changed_by_this_phase` compares uncommitted working tree to `HEAD` — resolves to passing once this phase's changes are committed; not a real regression) + 2 tests narrowly updated (§11) |
| RAE full sweep (`-k "rollback_approval_evidence or rae_"`) | — | 4 pre-existing unrelated failures reproduced identically on a clean stash (a pre-existing, already-BLOCKING RAE-001 registration-key-binding forgery finding, unrelated to HATP/Wave 7 — out of this phase's scope) + the 2 items above |
| Permission Broker (`-k permission_broker`) | — | **981 passed, 2 skipped**, 1 pre-existing unrelated failure (as above) + 1 test narrowly updated (§11) |
| 149O.6 new suite | — | **26 passed** |
| Fast Green (`pytest -m fast_green`) | 4590 passed, 2 skipped, 0 failed (149O.5 baseline) | **4590 passed, 2 skipped, 0 failed — exact match** |
| Report trust (`test_phase_reports.py` + `test_phase_reports_cli.py` + `test_phase_report_trust_hard_fail.py`) | 187 passed | **187 passed — exact match** |

The new 149O.6 suite is, like 149O.4/149O.5's own new suites before it, not registered in `FAST_GREEN_MODULES` and is run separately (26 passed, above). Fast Green's exact-match result confirms none of the 10 narrow boundary-test updates (§11) or the new production files caused any collateral regression elsewhere in the 4590-test suite.

Python 3.9 lexical-portability debt and the pytest-xdist collection-UUID limitation are both retained, unrepaired, per the governing brief (out of Wave-7 scope). Wave-5 non-blocking findings B-149O.3-1/-3/-8 are retained; none is made authority-relevant by this phase (the adapter consumes only `hatp_providers`' public interface, never a Wave-5-internal detail those findings concern).

---

## 11. Narrow boundary-test updates (with justification)

Seven pre-existing tests, spanning six files, encoded invariants that Wave 7 supersedes *by design* (not weakens):

| File | Test | Wave-4/5/6-era invariant | Wave-7 update |
|---|---|---|---|
| `test_hatp_verification_engine.py` | `test_substrate_readiness_status_has_no_ready_member` → renamed `..._has_exactly_two_members` | "No READY-shaped status member exists" | Confirms exactly `{NOT_READY, OPERATIONAL}`; the still-passing `test_substrate_readiness_never_operational` re-confirms the *behavioral* invariant on this deployment |
| `test_phase_149o_1j_...py` | `test_substrate_readiness_status_enum_has_exactly_one_member` / `test_substrate_readiness_source_has_assertion_forcing_operational_false` | Same, plus literal-assert-in-source check | Same two-member confirmation; assert-removal confirmed via source text, behavior re-confirmed via real function call on an unreadied trust store |
| `test_phase_149o_4_hatp_rae_integration.py` | `test_wave4_substrate_readiness_still_mechanically_cannot_be_operational` | Literal `assert operational is False` in source | Calls the real function against an unreadied trust store; asserts `operational is False` behaviorally |
| `test_phase_149o_5_...py` | `test_wave4_operational_ceiling_source_still_load_bearing` | Same, plus hardcoded-`False`-literal source check | Same behavioral re-confirmation |
| `test_phase_149o_5_...py` | `test_zero_production_callers_of_gated_api_outside_own_module` → renamed `..._limited_to_wave7_adapter` | Zero production consumers of the gated API outside `rollback_approval_evidence.py` | Allowlist grows by exactly one named, reviewed module: `hatp_ag_authority.py` |
| `test_phase_149j_...py` | `test_agent_operation_identity_fields_match_live_code` | Literal single-line `execute_rollback` signature text | Updated to match the new multi-line signature (new optional kwonly params); `root, job_id` positional-only shape re-confirmed separately by `test_execute_rollback_signature_is_backward_compatible` |
| `test_phase_149m_...py` | `test_agent_module_has_no_rollback_approval_evidence_import` → renamed `..._reference_is_narrowly_scoped` | Zero references to `rollback_approval_evidence` in `agent.py` | Confirms the reference is exactly the two new local-import lines, both reachable only inside `if hatp_evidence_id is not None:` |
| `test_phase_149m_...py` | `test_no_permission_broker_request_construction_uses_approval_present_true` | Zero production consumers of the RAE derivation functions outside `rollback_approval_evidence.py` | Allowlist grows by `hatp_ag_authority.py`, same as above |
| `test_phase_148f_...py` | `test_permission_broker_consumer_scope_inventory` | Exactly two authorized production PB consumers (`push.py`, `mutation_permission.py`) | Allowlist grows by `hatp_ag_authority.py`; also fixes a **pre-existing, unrelated false positive** (`hatp_bootstrap.py` flagged only because its own module docstring names "permission_broker_foundation.py" in prose describing what it deliberately does *not* import — confirmed via `grep` that no real import/construction exists there; confirmed present on a clean stash before any Wave-7 change) |
| `test_phase_149o_1g_...py` | `test_agent_module_untouched` | `core/agent.py` and `commands/agent.py` both byte-unchanged since the 149O.1G freeze | `commands/agent.py` re-confirmed untouched; `core/agent.py`'s intentional Wave-7 change is documented in the test's own updated docstring, cross-referencing the 149O.6 suite and the narrowly-scoped-reference confirmations above |
| `test_phase_149o_1g_...py` | `test_only_expected_production_files_changed` | Closed allowlist of `src/pcae/` files changed since 149O.1G | Allowlist grows by `hatp_ag_authority.py` + `core/agent.py`, following the same "allowed-file-widening precedent" this test's own pre-existing comments already establish for Waves 4 and 5 |

No broad guard assertion was weakened. Every update either (a) re-expresses an unchanged behavioral invariant through the real function/API instead of brittle source-text matching, or (b) grows a named-consumer allowlist by exactly the one, reviewed module this phase adds.

---

## 12. Confirmations (no-go list)

- HATP-001 v1.0 remained byte-unchanged (confirmed by direct read; no edit made to `docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md`).
- Wave 1 (repository identity), Wave 2 (trust-store authority), Wave 3 (proof/canonicalization), Wave 5 (provider/crypto) semantics unchanged — no file in those waves' ownership was edited.
- Wave 4 (`human_approval_trusted_provenance.py`) verification-status *vocabulary* (`HATPVerificationStatus`, the 13-state matrix, `verify_hatp_proof`) unchanged; only the separate, previously-Wave-4-only `HATPVerificationSubstrateStatus`/`inspect_hatp_verification_substrate_readiness` (an explicitly different, activation-readiness question) was updated, exactly as the phase title charters.
- Wave 6 (`rollback_approval_evidence.py`) RAE/HATP binding semantics unchanged — this file was not edited by this phase at all (confirmed by `git diff --stat`, §13).
- B-149O.1H-1, B-149O.1H.4-1, B-149O.1H-2, B-149O.1F-1, B-149O.1R-1, B-149O.1R-2 all remain closed, unaffected — none of their owning files were touched.
- No caller-supplied `approval_present` boolean is authoritative for AG3/AG5 on the new gated path (no such parameter exists on the adapter).
- No test provider or arbitrary trust store can establish production approval (F-2 closed structurally, §5).
- No legacy RAE-only result is authority-bearing for AG3/AG5 (adapter never imports the legacy narrow API).
- No HATP status directly determines a PB `ALLOW`/`DENY` outcome; Permission Broker's own, unmodified policy engine remains the sole decision point (§8, `test_approval_present_does_not_bypass_other_denying_policy`).
- Permission remains distinct from capability and execution; HATP operational readiness remains distinct from general PCAE Runtime Execution capability (§7 explains this precisely — PB evaluation on the new path is advisory, matching PB's own system-wide architecture, and never itself gates the real rollback mutation).
- The current development deployment remains NOT READY (same-principal, no hardware provider attached) — confirmed both by the real (unfaked) `inspect_hatp_verification_substrate_readiness` call and by every AG3/AG5-through-adapter test that supplies no monkeypatched hardware.
- Runtime remains Observed / observe / unavailable, confirmed via `pcae runtime inspect` before and after this phase's work.
- No sudoers change, new OS user, ACL mutation, or root-owned directory was created; no host-level provisioning was attempted (this phase implements readiness *inspection* and authority *consumption*, not OS provisioning, per §21 of the governing brief).
- No `--no-verify`, force-push, or governance bypass was used.

---

## 13. Production diff (exact)

```
 src/pcae/core/agent.py                              | 114 ++++++++++++++++-
 src/pcae/core/human_approval_trusted_provenance.py  | 121 +++++++++++++-----
 src/pcae/core/hatp_ag_authority.py                  | new file (production authority adapter)
```

Classification: `human_approval_trusted_provenance.py` = **ACTIVATION_CONJUNCTION** (§3). `hatp_ag_authority.py` = **PRODUCTION_PROVIDER_RESOLUTION + PRODUCTION_TRUST_STORE_RESOLUTION + AG3_APPROVAL_DERIVATION + AG5_APPROVAL_DERIVATION + PB_REQUEST_WIRING + LEGACY_PATH_EXCLUSION + F2_PROVENANCE_ENFORCEMENT** (§4-6). `agent.py` = **AG3_APPROVAL_DERIVATION + AG5_APPROVAL_DERIVATION** (the optional-parameter wiring, §7). `UNRELATED = 0`. `rollback_approval_evidence.py` and every other Wave 1-6 file: **not modified**.

---

## 14. Verdict

**HATP WAVE 7 CLASS-B DEPLOYMENT / ACTIVATION IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION.**

The activation ceiling is now mechanically derived rather than hardcoded, and is genuinely reachable under a synthetic Class-B deployment while remaining fail-closed on this real one. A real, F-2-closed, PB-wired production authority-consumption path for AG3/AG5 now exists and blocks every reproduced historical attack. The path is reachable but not yet exercised by any CLI surface (§7) — that boundary is stated explicitly rather than glossed over. B-149O-1..4 move to REPAIRED AT SYSTEM IMPLEMENTATION LEVEL, PENDING INDEPENDENT WAVE-7 VERIFICATION, not self-closed. **HATP production readiness remains NOT READY** on this deployment; no claim of production certification is made.

**Recommended next phase:** 149O.7 — HATP Class-B Deployment / Activation Independent Verification (adversarial re-verification of this phase's claims, including honest evaluation of the §7 scope boundary and whether/how a future phase should wire a CLI/signing-ceremony surface and a real PB-gated execution boundary for AG3/AG5).
