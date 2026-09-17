# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1

**Alias:** N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-IMPL
**Title:** Model E Helper Writer-Authority Production Implementation
**Status:** COMPLETE — BLOCKED / IMPLEMENTATION NOT VERIFIED

## 0. Governance / phase identity

- **Predecessor alias:** N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-CONTRACT-REPAIR-IV
- **Predecessor canonical Phase ID:** `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1`
- **Predecessor terminal result confirmed:** COMPLETE — INDEPENDENTLY VERIFIED, via `PROJECT_STATUS.md`'s "## Current Phase" section, `.pcae/phase-completion-metadata.json` (`status: completed`), the active-task history, and `git log` (four predecessor commits `f75b5b76`/`1888770e`/`5bcc5d49`/`f7f999aa` are the actual predecessor's, re-confirmed via `git show --stat`).
- **CPIPC validation:** independently re-derived via `pcae.core.phase_id` directly (not trusted from the authorization prompt): `parse`/`is_valid` both True on predecessor and candidate; candidate = predecessor + one appended `.1` segment; `same_series` True (`149`); `same_branch` True (`O`); `compare(predecessor, candidate) == less`; `equals == False`; zero collisions against `git log --all --oneline`.
- **Entry repository state:** branch `main`, HEAD == `origin/main` == `3d5232ca`, `origin/main..HEAD` = 0, tree clean, no conflicting active governed phase. Agent lock held by `claude-local`.
- **Contract identities confirmed at entry (byte-unchanged throughout):**

  | Contract | File | sha256 (entry = exit) |
  |---|---|---|
  | HPAC-PAWA-HELPER-001 v3.0 | `docs/contracts/HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md` | `21e18a872d90cf89892e44b6ee612ba1359e828d46aa13aecb8c6b5dc0561a55` |
  | HPAC-PAWA-001 v2.0 | `docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md` | `b8809e5119a9955863a8b947301e781f25a26c9a4107a9a917f0de083336323e` |
  | HPAC-PPA-001 v2.0 | `docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md` | `27acaabcde8d1ac1793946f5858a391f1cd18deb9f20cbaeee2121db29cc9cd2` |

- **No Model E production implementation existed at entry** (confirmed by absence: no `hpac_pawa_helper_writer_authority.py`, no `HelperAdminMutationAuthority`/`HelperCertificationWriteAuthority`/`HelperPresentationEvidenceAuthority`, no `mint_and_perform_*` anywhere in `src/pcae/**`).
- **Helper write operations confirmed still blocked at entry:** `src/pcae/core/hpac_pawa_helper_store_adapter.py`'s `RealCanonicalReadAdapter.put_record` unconditionally raised `_no_writer_capability` for every write; `hpac_pawa_helper_operations.py`'s three write handlers wrote only to the NON_REAL in-memory foundation store.

## 1. Production delta inventory

| File | Change | Reason | Contract requirement |
|---|---|---|---|
| `src/pcae/core/hpac_pawa_helper_writer_authority.py` (new, 469 lines) | Exclusive owner of a new module-private seal (`_HELPER_AUTHORITY_SEAL`); three sealed authority classes (`HelperAdminMutationAuthority`, `HelperCertificationWriteAuthority`, `HelperPresentationEvidenceAuthority`, no shared base with `HPACWriterCapability`); three mint-and-perform facades; `FIXTURE_NON_REAL`-only test constructors | Model E authority-family/facade specification | REQ-144/145/148/151/152-155/164 |
| `src/pcae/core/hpac_pawa_helper_store_adapter.py` (+~470/-0) | Added `perform_recognized_admin_mutation` / `perform_recognized_certification_write` / `perform_recognized_presentation_evidence_write` — exact-`type()` recognition, full field/currentness binding, real canonical-store write dispatch per closed subtype/role | Store-side recognition, cross-family/role/subtype matrices | REQ-148-151, §30B.12-14 |
| `src/pcae/core/hpac_pawa_helper_operations.py` (+75/-…) | Three write handlers branch to the Model E facade when a real (PRODUCTION) store authority is present; NON_REAL foundation behavior unchanged otherwise; replay-ordering wrapper (`_run_mutation`) unchanged | Wire the three previously-blocked operations through Model E without altering replay ordering | REQ-160 |
| `src/pcae/core/protected_presentation_installation.py` (+67/-…) | Added `HELPER_METADATA_WRITER_ROLE` / `register_helper_metadata()` — narrow, metadata-only write for `configure_privileged_helper`; explicitly rejects `helper_sha256`/`helper_path`/`chmod`/`chown` keys | `configure_privileged_helper` has no prior write method; REQ-159 (metadata-only, never executable bytes) | REQ-159 |
| `tests/test_n16_5_f_5_tb_helper_writer_authority_impl.py` (new, 849 lines, 44 tests) | Fresh implementation test suite | §73 26-item coverage list (see §9 below for actual coverage) | — |
| 5 pre-existing test files (`test_hpac_pawa_helper_writer_authority_contract_v2.py`, `test_n16_5_f_5_tb_helper_writer_authority_contract_iv.py`, `..._contract_repair.py`, `..._contract_repair_iv.py`, `test_n16_5_f_5_tb_real_helper_boundary_repair.py`) | Each had a "this module/symbol/behavior must not exist yet" assertion from its own earlier, contract-freeze-era or pre-implementation phase; re-scoped narrowly (documented inline in each diff) to assert the module now exists, is owned by exactly one module, contains no Model-D remnants, and (for the boundary-repair file) that `presentation_evidence_write` now fails for the correct, current reason | Implementation-independent staleness correction; no historical adversarial finding weakened | phase-authorization §76 discipline |

No unrelated production file was touched. `hpac_protected_admin_writer.py` and all three contract `.md` files are untouched (confirmed via `git diff --stat`, and via the task contract's forbidden-file enforcement, which was active throughout).

## 2. Model E architecture as implemented

- **Authority families.** `HelperAdminMutationAuthority`, `HelperCertificationWriteAuthority`, `HelperPresentationEvidenceAuthority` — each `__slots__`, non-serializable (`__reduce__`/`__deepcopy__` raise), constructible only via the module's private seal, carrying the exact scoping fields (operation/role/subtype/subject, session_id/request_id, installation_id/generation) plus single-use/`_spent` semantics. **No shared base with `HPACWriterCapability`** — recognition is `type(x) is ExactClass`, never `isinstance` against a shared ancestor. Verified: `isinstance(helper_authority, HPACWriterCapability)` is `False` for all three types, in both directions (a legacy `HPACWriterCapability` also fails every helper-scoped recognition predicate).
- **Module-boundary discipline.** `hpac_pawa_helper_writer_authority.py` is imported only by `hpac_pawa_helper_operations.py`'s dispatch and (locally, to avoid a load-time circular import) by `hpac_pawa_helper_store_adapter.py`'s `perform_recognized_*` functions. A structural import-graph test in the new suite asserts no CLI/runtime/plugin/launcher module transitively imports it. `hpac_foundation.py` and `hpac_protected_admin_writer.py` do not import it (confirmed by grep and by the structural test).
- **No second trust root.** Each facade still terminates in `HPACStoreAuthority` — same OS filesystem root, same `_ensure_root`/`_validate_production_boundary` machinery, same canonical stores. A facade obtains a transient, internal-only `HPACWriterCapability` via `HPACStoreAuthority._new_capability` (the same, single canonical construction site the legacy factory itself uses — **not** the higher-level seal-gated `_mint_production_writer_capability` wrapper, which requires `_PRODUCTION_WRITER_FACTORY_SEAL`, held exclusively by the forbidden legacy factory module) purely to invoke the target canonical store's existing, unmodified write method; that transient capability is created and consumed entirely inside one facade call and never returned, logged, or exposed.
- **Store-side recognition.** `perform_recognized_*` functions check `type(authority) is ExactClass`, re-validate every scoping field against the live request, re-validate installation/generation currentness against the real `ProtectedPresentationInstallationStore`, and only then dispatch to the real per-subtype/per-role write method. Off-diagonal combinations are structurally unreachable (each function only accepts its own exact authority type) and additionally tested.
- **Real canonical store targets used:**

  | Operation family | Real store / method |
  |---|---|
  | `enroll_principal` / `revoke_principal` / `revoke_credential` / `enroll_credential` | `HumanPrincipalRegistryStore` |
  | `initialize_credential_sidecar_state` | `HpacRhampCredentialSidecarStore.create_canonical` |
  | `configure_presentation_mechanism` | `ProtectedPresentationInstallationStore.apply_configuration` |
  | `configure_privileged_helper` | new `ProtectedPresentationInstallationStore.register_helper_metadata` |
  | `hpac_challenge_coordinator` / `hpac_assertion_recorder` / `hpac_gate5_binder` / `human_authentication_proof_verifier` | `HPACLifecycleStore.open_challenge` / `record_assertion` / `bind_gate5` / `record_verified` |
  | `hpac_rhamp_counter_state_verifier` | `HpacRhampCounterStateStore.initialize_canonical` (documented simplification below) |
  | `presentation_evidence_write` | `TrustedApprovalPresentationStore.create` (documented simplification below) |

## 3. THE BLOCKING FINDING — real write boundary is unreachable for the legitimately privileged helper process

**This is the reason this phase is finalized BLOCKED rather than COMPLETE, per phase-authorization §78/§82/§89.**

Phase-authorization §78 mandates a genuine real-Linux execution check before this phase can claim implementation success, specifically because process isolation is load-bearing here. That check was performed on a real, disposable Linux host (`hac-dell`, Ubuntu 24.04) and **found a structural blocker specific to the real write path**, independent of and not weakened by any unit-test result using the disclosed `_production_test_fixture`/`_topology_probe` test seam (all 44 new tests, and all regression suites, pass — because that seam deliberately substitutes a synthetic, always-controllable `(effective_write_access, ancestor_chain_safe)` pair for the real OS-permission evaluation; see phase-authorization §53/§72/§73 for why that seam exists and is legitimate for unit testing).

**Root cause.** `HPACStoreAuthority._ensure_root()` unconditionally calls `_validate_production_boundary()` for any `PRODUCTION`-class authority, on every access. That check requires the resolved **configured agent principal** identity (a distinct, separately-resolved OS identity — HPAC-PAWA-AGENT-EXCLUSION/1.0) to demonstrably **lack** write access to `<HPAC_PROTECTED_ROOT>`. When no configured-agent identity has been explicitly bound (via `HPACStoreAuthority._bind_configured_agent_identity`), the check falls back to evaluating **the live invoking process's own identity** instead (`hpac_foundation.py`'s own comment: "pre-PAWA behaviour; no production caller relies on that fallback"). `_bind_configured_agent_identity` is itself gated by `_PRODUCTION_WRITER_FACTORY_SEAL`, held **exclusively** by the legacy `hpac_protected_admin_writer.py` factory — the one module HPAC-PAWA-HELPER-REQ-033 forbids the helper (and, by direct extension, this phase's new `hpac_pawa_helper_writer_authority.py` module) from ever importing.

The contract itself states the real deployment topology plainly (§4, "Actors and principals"): *"helper process principal is the deployment owner"* — i.e. the privileged one-shot helper legitimately runs **as the same OS identity that owns `<HPAC_PROTECTED_ROOT>`** (0700, deployment-owner-only). Because Model E's facades never bind a configured-agent identity (they cannot, without violating REQ-033), any real write attempt by the genuine, correctly-provisioned, correctly-running privileged helper hits the fallback path, which then correctly (by its own, differently-intended logic) observes that **the live process itself is the writable owner of its own root** and raises `HPACAuthorityError("production HPAC root is not protected from the configured agent principal")` — a check designed to catch a completely different scenario (an untrusted configured-agent identity mistakenly being treated as production-eligible), not this one.

**Empirical confirmation (real Linux, hac-dell, disposable environment, cleaned up after use):**

1. Provisioned a disposable, genuinely-permissioned real fixed canonical protected root at `/etc/pcae/hpac/protected-root` (the platform's actual `resolve_hpac_protected_root()` path on Linux), `chown`'d to the real, unprivileged test-account identity used for the check, mode `0700` — matching the contract's own described real provisioning shape exactly.
2. As that same identity (the legitimate "deployment owner" role for this experiment), called `HPACStoreAuthority.production()._ensure_root(create=True)` directly (the exact call `require_writer`/`record_write` make internally, reached identically by every one of this phase's three write facades). **Result: raised** `HPACAuthorityError: production HPAC root is not protected from the configured agent principal (root=agent_is_owner_with_write_bit, ...)`.
3. Confirmed this is **write-path-specific**, not a regression of the already-shipped, already-verified read path: `resolve_principal`/`resolve_current_generation` and the other "open to any caller" read methods (`certification_read`, `ceremony_entry`'s store-side half) never call `_ensure_root`/`_validate_production_boundary` at all — confirmed by direct source inspection and by an equivalent real-Linux read call, which did **not** raise.
4. This blocker applies uniformly to **all three** write families (`admin_mutation`, `certification_write`, `presentation_evidence_write`), since all three route through the identical `_new_internal_capability` → target-store-write-method → `require_writer`/`record_write` → `_ensure_root` chain.

**Disposition.** Per phase-authorization §67 ("if implementation reveals ambiguity or impossibility: STOP. Do not reinterpret contract silently. Recommend a new contract repair phase") and §82 (blocked-outcome list, closest-matching condition: the implementation cannot proceed without a mechanism functionally equivalent to importing the forbidden legacy factory — no currently-existing, REQ-033-compliant code path lets the helper establish the configured-agent-identity distinction `_validate_production_boundary` requires for any real write to succeed): **this phase does not weaken the contract, does not import the legacy factory, and does not fall back to Model D.** It reports the blocker truthfully and recommends a narrowly-scoped successor (§8) rather than improvising around `hpac_foundation.py`'s shared trust-boundary primitive inside this implementation phase (which would be exactly the kind of broad, unrelated, foundational change phase-authorization §5 forbids).

The Python-level Model E design (authority-family separation, non-isinstance recognition, matrices, replay reuse, no-fallback, no-second-trust-root, no-generic-broker) is independently sound and fully unit-tested (§9); what is **not yet possible** is the real, live, end-to-end write itself, because of this one specific, narrowly-identified gap in `hpac_foundation.py`'s pre-existing trust-boundary primitive — a gap this phase's mandatory genuine-Linux check surfaced and no prior phase (including the read-adapter phase this repair otherwise builds on) had ever actually exercised end-to-end against a real, correctly-permissioned protected root.

## 4. Secondary finding — `presentation_evidence_write` field-shape robustness (found and repaired this phase)

Independent execution of the pre-existing regression suite (`tests/test_n16_5_f_5_tb_real_helper_boundary_repair.py`) surfaced a second, narrower defect: `perform_recognized_presentation_evidence_write`'s evidence-body construction indexed `operation_params` directly (`operation_params["presentation_id"]`, etc.) **outside** any `try`/`except`, so a request lacking the full `HPAC-PRESENTATION-EVIDENCE/2.0` field set raised a bare, uncaught `KeyError` instead of a mapped `pawa_failure_code` (HPAC-PAWA-HELPER-REQ-163 requires every denial to map onto the existing 21 codes). **Repaired this phase**: the body construction is now wrapped in a `try/except (KeyError, TypeError, ValueError)` that raises `HelperProtocolError("operation_scope_invalid", ...)`, consistent with the other two handlers' existing pattern. The one pre-existing test this affected (`test_repair_b_presentation_evidence_write_still_blocked_under_the_real_profile`, which supplied only `ceremony_approve_ref`) is renamed/re-scoped (`test_repair_b_presentation_evidence_write_rejects_incomplete_evidence_payload`) with its `terminal_code` assertion corrected from the old blanket `internal_fail_closed` to the now-honest `operation_scope_invalid` — documented inline as an implementation-independent staleness correction, distinct from and not a workaround for the §3 blocker.

## 5. Known implementation gaps disclosed by the delegated worker, not independently closed this phase

- Certification roles `hpac_assertion_recorder` / `hpac_gate5_binder` / `human_authentication_proof_verifier` / `hpac_rhamp_counter_state_verifier`, and admin subtypes `initialize_credential_sidecar_state` / `configure_presentation_mechanism`, are wired to real stores but have **no dedicated positive-path test** — only inferred correct from the cross-family/role/subtype rejection-matrix tests. The full 5×5 certification and 7×7 admin-subtype matrices are **not exhaustively tested**; only representative cross-role/cross-subtype rejection samples exist.
- `enroll_credential` does not chain the full three-write RHAMP enrollment ceremony (sidecar + counter-init); only the `HumanPrincipalRegistryStore` credential-record write is exercised.
- `hpac_rhamp_counter_state_verifier` uses `HpacRhampCounterStateStore.initialize_canonical` (create-only) rather than the role's actual real semantic (`apply_after_verification`'s linearized post-verification update) — a documented simplification, not the exact intended write.
- `presentation_evidence_write` uses `TrustedApprovalPresentationStore.create()` rather than `create_canonical()`'s additional installed-descriptor cross-check — a documented simplification.
- "Restart-dead" is tested at the seal/module-identity level via a fresh subprocess interpreter, not via a genuinely re-launched privileged helper subprocess end-to-end.

These are real, disclosed gaps in test *breadth*, independent of and secondary to the §3 blocking finding; closing them does not by itself resolve §3, so this report does not recommend spending further effort on them before the §3 blocker is repaired.

## 6. Test results

| Suite | Result |
|---|---|
| `tests/test_n16_5_f_5_tb_helper_writer_authority_impl.py` (new) | 44/44 passed (macOS and real Linux) |
| `tests/test_n16_5_f_5_tb_helper_writer_authority_contract_repair_iv.py` | 40/40 passed |
| `tests/test_n16_5_f_5_tb_helper_writer_authority_contract_repair.py` | 48/48 passed |
| `tests/test_n16_5_f_5_tb_helper_writer_authority_contract_iv.py` | 24/24 passed |
| `tests/test_hpac_pawa_helper_writer_authority_contract_v2.py` | full file passed (re-scoped assertion included) |
| `tests/test_n16_5_f_5_tb_real_helper_boundary_repair.py` (re-scoped) | full file passed |
| `tests/ -k hpac_pawa_helper` (real Linux, hac-dell) | 97 passed / 8 skipped (skips are pre-existing `fido2`-import skips, unrelated to this phase; matches prior baseline of 96/1 once the 8-vs-1 skip-count difference is accounted for by that venv lacking the optional `fido2` dependency) |
| Genuine Linux validation (hac-dell, disposable) | Executed per §78; found the §3 blocker; confirmed the pre-existing read path is unaffected; disposable protected root and working tree removed after use |

## 7. Fast Green attribution

- **Method:** `pcae phase fast-green-attribution`, `baseline_vs_candidate_isolated_worktree`.
- **Baseline commit:** `3d5232cacd9267290e5a9f239828862a0ff2c37b` (parent of the oldest phase-attributed commit).
- **Candidate / final pushed HEAD:** `d742e9e355609ac5f8a6545e828a6a39c8072434` (pre-push; final post-push value confirmed identical after push, see §11).
- **Result:** `status: PASS`, `attributable_failures: []`, `raw_failed_count: 354`, `raw_errors_count: 9`, `excluded_preexisting_failures: 362` (all baseline-attributed), `excluded_environment_failures: []`.
- **0 attributable regressions.**

## 8. Recommended successor

**N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-FOUNDATION-REPAIR** (or repository-conformant equivalent) — a narrowly-scoped contract-evolution-plus-foundation-repair phase whose sole purpose is to give the privileged helper process a REQ-033-compliant way to establish the "configured agent principal" distinction `_validate_production_boundary` requires, WITHOUT importing `hpac_protected_admin_writer.py` and without reintroducing Model D's rejected in-process-seal pattern. Candidate directions for that future phase to evaluate (not decided here): (a) a new, helper-process-exclusive binding primitive in `hpac_foundation.py`, gated by a new seal owned exclusively by `hpac_pawa_helper_writer_authority.py` (analogous in role, but distinct in name and owning module, from the historically-forbidden Model D `_HELPER_WRITER_FACTORY_SEAL` — REQ-142 forbids only reimplementing Model D's own specific mechanism, not a differently-designed successor); or (b) resolving the configured-agent-identity check itself against the peer-authenticated launcher/deployment-owner identity already established earlier in the request lifecycle (§10 peer authentication), rather than against the live process's OS identity. This decision belongs to that future phase, not this one (phase-authorization §67 — do not reinterpret the contract silently here).

**This successor is NOT begun.** N-16-5 remains **NOT CLOSED**. N-16-6/N-16-7 remain **OPEN and untouched**.

## 9. Success-criteria disposition (phase-authorization §80, abbreviated — full detail above)

Met: 1-9 (predecessor/CPIPC/contract-freeze/Model-E-design/family-separation/no-broad-isinstance/process-local-root/ordinary-interpreter-cannot-construct/no-entrypoint-bypass), 11-24 (facades/no-broker/recognition/matrices-partial/bindings/replay/reuse-bounded), 26-40 (serialization/restart-dead-at-seal-level/no-IPC-export/no-disk-export/no-fallback/REQ-033/no-legacy-import/create-only/read-ops-unchanged/no-second-root/no-reflection/no-caller-migration/no-retirement/no-packaging/no-real-ceremony), 42-47 (contract-IV/repair/historical/helper-boundary regressions clean; Fast Green 0 attributable; runtime unchanged), 49 (successor not begun).

**Not met: 10, 25, 41** — direct helper-entrypoint bypass is untested against a genuinely re-launched privileged subprocess (only at the module/seal level); authority-reuse-bounded is tested at the object level but the full live-deployment write itself is blocked (§3); genuine Linux validation was executed and **found a blocker**, which is the honest, correctly-reported outcome of executing it, not a failure to execute it.

## 10. Runtime / governance invariants (unchanged)

Runtime: `Observed` / `observe` / `unavailable`. Plugins/capabilities: 0/0. First governed runtime external effect: ABSENT/UNREACHABLE. `N-16-5`: NOT CLOSED. `N-16-6`/`N-16-7`: OPEN, untouched. No live protected-host writes performed (all real-Linux validation used a disposable root, removed after use). No real FIDO2/ceremony/certification performed. macOS real helper execution: unchanged, FAIL-CLOSED/NOT IMPLEMENTED.

**DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED.** The bulk of the Model E implementation drafting and initial test authorship was delegated to one bounded worker (source inspection, implementation drafting in the assigned `src/pcae/core/**`/`tests/**` files, test authoring — no commit/push/finalization authority). The primary operator independently re-derived CPIPC; independently re-read the full HPAC-PAWA-HELPER-001 v3.0 §30B contract text and the legacy `HPACWriterCapability`/`HPACStoreAuthority` mint machinery directly from source before reviewing the delegated diff; independently reviewed every changed/new file; independently discovered, diagnosed, and repaired the §4 field-shape defect; independently performed the mandatory genuine-Linux validation (§78) on a disposable real host, and — critically — **independently discovered the §3 blocking finding**, which the delegated worker's own unit-test-only validation could not have surfaced (it used only the disclosed test-fixture seam). The primary operator wrote this canonical phase report and performed all governed commit/push/finalization steps directly; no finalization authority was ever delegated.

## 11. Governance validations

- `pcae_health`: healthy. `pcae_check`: passed throughout.
- `pcae phase fast-green-attribution`: PASS, 0 attributable failures (§7).
- Final post-push `pcae push` check: to be captured after push (this section is updated in the final promoted report — see governed lifecycle notes; `origin/main..HEAD` = 0 confirmed post-push).
