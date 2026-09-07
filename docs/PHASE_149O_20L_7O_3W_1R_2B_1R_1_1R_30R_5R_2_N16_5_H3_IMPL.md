# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R — N-16-5 Production Certification Authority-Path Implementation Against HPAC-PAWA-001 v1.3 — H-3 Repair

**Alias:** N16-5-H3-IMPL (operator readability only; the full canonical CPIPC id above is authoritative in all task state, lifecycle, reports, completion metadata, evidence, and canonical project status).

**Status:** IN PROGRESS.

## 0. CPIPC verification

| Check | Result |
|---|---|
| Predecessor alias | N16-5-H3-PAWA13-IV |
| Expected canonical predecessor | `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R` |
| Candidate | predecessor + exactly one `.1R` |
| `phase_id.is_valid(pred)` / `is_valid(cand)` | True / True |
| `same_series` | True (series `149`, branch `O`) |
| `same_branch` | True |
| `compare(pred, cand)` | `less` — strict ordering, pred < cand |
| Direct successor | cand = pred + one `.1R`; no interposed token |
| Canonical id == proposed id | yes — alias is display-only; **no CPIPC discrepancy** |
| Uniqueness / no active conflicting phase | confirmed at `pcae task transition` |

## 1. Frozen inputs

- **I0 (implementation phase-entry SHA):** `74e52d59738007c4b9f6dbeb28f83990ba82e9a8`
- **HPAC-PAWA-001 v1.3** (`docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`) git blob: `9c816716bae2262831945ac24b1771cf79de4c55` — **MUST remain byte-unchanged**; `docs/contracts` normative diff expected EMPTY.
- Other directly relevant frozen contracts at I0:
  - HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md (HPAC-PPA-001 v1.0): `3832eb921eda26c4bc1fff90f3140297c1780431`
  - HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md: `16509b6b15df6edb3ba51787a6df3e22d003c2de`
  - REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md (RHAMP-001 v1.0): `ef218e99beea771d5797e440516ea2c15983ee28`
  - HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md: `79af6e959d6d753afb12c627ad8e996910ba4ca9`

## 2. Prerequisite state (carried from N16-5-H3-PAWA13-IV)

HPAC-PAWA-001 v1.3 FROZEN + INDEPENDENTLY VERIFIED. H-3 CONTRACT BLOCKER: INDEPENDENTLY VERIFIED RESOLVED. H-3 PRODUCTION IMPLEMENTATION: PENDING (this phase). F-5: DEPLOYMENT VERIFIED — CERTIFICATION BLOCKED PENDING H-3 IMPLEMENTATION. N-16-5: NOT CLOSED. N-16-6 / N-16-7: OPEN / UNTOUCHED (N-16-7 strictly last). Runtime: Observed / observe / unavailable. Plugins 0. Capabilities 0. First governed runtime external effect: ABSENT / UNREACHABLE.

## 3. Contract target (v1.3 clauses this phase implements)

| Clause | Requirement |
|---|---|
| §37 (REQ-084/085/086) | non-agent-importable admin-only production authority boundary; exact enumerated consumer inventory, no wildcard/prefix/glob |
| §33A (REQ-234–238) | dedicated `certification_writer(...)` factory in the same non-agent-importable module as `production_writer`; reuses §33 steps 1–9 verbatim as required conjuncts; then adds certification-consumer / role-allowlist / session-binding / mint / audit; fresh per call; one atomic recognition unit; fails closed |
| §38A (REQ-239–242) | exactly one authorized certification consumer category: `pcae.core.hpac_certification_coordinator`, reached only from `scripts/hpac_certification_admin.py`; deployment owner ≠ human approver |
| §39A (REQ-243–244) | consumer-inventory guard tests; only caller of `certification_writer` is the §33A path invoked by the §38A consumer; no glob/prefix broadening ever |
| §42B (REQ-245–251) | one closed **certification-lifecycle writer family**, NOT a new `PawaOperation`; closed five-role allowlist; per-role store/action; `HPAC-PRESENTATION-EVIDENCE/2.0` outside the family; FACTORY≠CONSUMER≠MINTER; audit event |
| §42C (REQ-252–254) | every rejection maps onto the existing 21 `pawa_failure_code` values; PAWA→RHAMP §57 map unchanged; no new code; BLOCK if genuinely unmappable |
| §43A (REQ-255–256) | each capability bound to exact `certification_session_id` + `subject` (proof_id for 4 lifecycle roles, credential_id for counter role) + exact `principal_id`+`credential_id`; no inference; reserve proof_id/session_id before ceremony |
| §44A (REQ-257) | preserve ALL existing currentness/replay semantics; no new TTL |
| §49A (REQ-258–260) | one canonical write per role, one ceremony; §45/§46/§47/§48 apply verbatim; short-lived admin invocation; additive spent-flag/one-shot-wrapper only |
| §68A (REQ-261–268) + PAWA-INV-13 | certification authority ≠ execution / Gate 6–10 / DispatchEnvelope / no-go override / runtime approval / PB permission / policy exception / RE result / runtime capability / adapter admission / runtime-state transition; coordinator does not manufacture APPROVE/REJECT/UP/UV/real presentation/real assertion/PRODUCTION principal/Gate result; real ≠ deterministic (`require_real_assurance` unrelaxed); Gate 5 not manufactured/not bypassed; test-only seals stay NON-PRODUCTION; mechanism neutrality; no instance data; N-16-6/N-16-7 exclusion; **path terminates no later than the bounded Gate-5 certification result** |

## 4. Reconstructed implementation architecture (delta map, from I0 primary source)

### 4.1 Existing production mint trust root — `src/pcae/core/hpac_protected_admin_writer.py` + `hpac_foundation.py`

- `_run_recognition_sequence(*, protected_root, configured_agent_identity_source, caller_module, topology_probe) -> _RecognizedAnchor` — the §33 steps 1–9 (root/manifest/descriptor/current-generation/provenance/agent-exclusion/exclusion-boundary/not-configured-agent/write-probe/**consumer check against `AUTHORIZED_FACTORY_CONSUMERS ∪ _TEST_FACTORY_CONSUMERS`**). One `try/except` → `PawaError("internal_fail_closed", …)` fail-closed boundary. Returns `_RecognizedAnchor(authority, root, live_root_identity, live_root_identity_digest, anchor_id, installation_id, generation, configured_agent)`.
- `production_writer(operation, …) -> ProductionWriterHandle` — calls `_run_recognition_sequence`, then `recognized.authority._bind_configured_agent_identity((uid,gids), _factory_seal=_PRODUCTION_WRITER_FACTORY_SEAL)`, then `recognized.authority._mint_production_writer_capability(role, subject, _factory_seal=_PRODUCTION_WRITER_FACTORY_SEAL, multi_write=bool)`, wraps in `ProductionWriterHandle` (one-shot at the factory layer via `.consume()`), records issuance evidence (§55).
- `HPACStoreAuthority._mint_production_writer_capability(role, subject, *, _factory_seal, multi_write=False)` — seal-guarded (`_PRODUCTION_WRITER_FACTORY_SEAL`), requires PRODUCTION class, re-runs `_ensure_root(create=False)` (re-validates F-1 boundary + root-identity binding each mint), returns `_new_capability(role, subject, single_use=True, multi_write=multi_write)` — the single construction site, registers the capability as canonically issued.
- `HPACWriterCapability.__slots__ = ("_authority_seal","role","subject","authority_class","_single_use","_spent","_multi_write")`; `_mark_spent(seal)` seal-guarded; `__reduce__` raises. Non-`_multi_write` `_single_use` capability spent by `record_write` on first write; `require_writer` checks `writer._authority_seal is self._seal` (identity), role/subject/authority_class, and canonical-registry issuance state (CONSUMED/`_spent`).
- `mint_protected_presentation_evidence_writer(authority, *, mechanism_id, _caller_module=None)` — precedent for a **second factory** in the same module: exact `PROTECTED_PRESENTATION_LAUNCHER_CONSUMERS` frozenset consumer check via `_detect_caller_module`, requires a PRODUCTION `HPACStoreAuthority`, calls `authority._mint_production_writer_capability("protected_presentation_mechanism", mechanism_id, _factory_seal=_PRODUCTION_WRITER_FACTORY_SEAL)`. **`HPAC-PRESENTATION-EVIDENCE/2.0` stays outside the certification family — reuse this unchanged (REQ-248).**

### 4.2 The five canonical lifecycle stores (all `*_canonical` methods already exist and already take an `HPACWriterCapability`)

| Role | Store method | `require_writer` role | `require_writer` subject |
|---|---|---|---|
| `hpac_challenge_coordinator` | `HPACLifecycleStore.open_challenge_canonical(writer, *, proof_id, approval_id, invocation_id, attempt_id, principal_id, credential_id, mechanism_id, occurred_at, resolved_presentation, challenge)` | `_GENESIS_WRITER_ROLE` = `hpac_challenge_coordinator` | `proof_id` |
| `hpac_assertion_recorder` | `HPACLifecycleStore.record_assertion_canonical(writer, *, proof_id, assertion_digest, occurred_at)` | `_ASSERTION_WRITER_ROLE` | `proof_id` |
| `human_authentication_proof_verifier` | `HumanAuthenticationProofStore.create_canonical(writer, proof)` **AND** `HPACLifecycleStore.record_verified_canonical(writer, …)` | `human_authentication_proof_verifier` | **⚠ `create_canonical` requires `subject == proof.mechanism_id`; `record_verified_canonical` requires `subject == proof_id`** — see Open Question OQ-1 |
| `hpac_gate5_binder` | `HPACLifecycleStore.bind_gate5_canonical(writer, *, proof_id, approval_digest, occurred_at)` — called **inside** `verify_human_authentication` | `_BOUND_WRITER_ROLE` | `proof_id` |
| `hpac_rhamp_counter_state_verifier` | `HpacRhampCounterStateStore.apply_after_verification(writer, *, credential_id, expected_current, decision, updated_at)` — called **inside** `verify_human_authentication` | `COUNTER_STATE_VERIFIER_ROLE` | `credential_id` |

- `HPACLifecycleStore._TERMINAL_WRITER_ROLE = "hpac_lifecycle_terminator"` (writes only `EXPIRED`/`REVOKED`/`REJECTED`) — **explicitly NOT in the allowlist** (REQ-246).
- `hpac_verifier.verify_human_authentication(*, registry, presentation_store, descriptor_store, proof_store, lifecycle_store, challenge, proof_id, approval_id, now, occurred_at, gate5_writer, verifier_version, require_real_assurance, max_proof_age_seconds, sidecar_store, counter_state_store, counter_state_writer) -> AuthenticatedHumanPrincipal` — expects the lifecycle chain **already at `STATE_PROOF_VERIFIED`** (challenge + assertion + proof + verified written by the coordinator first); it then does the `bind_gate5_canonical` and `apply_after_verification` writes and returns a trusted-construction `AuthenticatedHumanPrincipal` (registered in `_AUTHENTIC_PRINCIPAL_REGISTRY`, the `is_verifier_authenticated_principal` boundary). `require_real_assurance=True` jointly requires every resolved record `authority_class is PRODUCTION` + real auth `mechanism_id ∈ {"hpac.fido2.uv_presence.v2"}` + real presentation `mechanism_id == "pcae-protected-local-presentation"` (HPAC-PPA-REQ-057) — **unrelaxed**.
- `runtime_dispatch_gate5.run_gate5(approval_id, *, approval_store, authenticated_principal, context: InvocationRequestContext, consumption_lookup, lifecycle_store) -> (Gate5Result|None, reasons)` — the **actual** Gate 5; consumes the verifier-issued principal + validated approval + canonical sequence-3 binding; read-mostly, creates only an ephemeral `Gate5Result`. **The certification-authority path terminates at this bounded result (§41 / §68A).**

### 4.3 The H-3 gap (reproduced)

The full canonical `challenge → assertion → proof → verified → gate5-bind → counter` chain composes **only** in test code, obtaining the five writers via `lifecycle_store.fixture_*_writer(...)` (FIXTURE_NON_REAL) or the disclosed test-only production seal (`authority._mint_production_writer_capability(role, subject, _factory_seal=_PRODUCTION_WRITER_FACTORY_SEAL)` reached from a test, or `HPACStoreAuthority._production_test_fixture`). There is **no production entry boundary** that runs the §33 recognition sequence and mints the five lifecycle-writer capabilities for the real N-16-5 chain. `certification_writer` + `hpac_certification_coordinator` + `scripts/hpac_certification_admin.py` fill exactly that.

## 5. Intended production file set (§80 minimization — compared against actual at finalization)

| File | Change |
|---|---|
| `src/pcae/core/hpac_protected_admin_writer.py` | ADD: `CERTIFICATION_FACTORY_CONSUMERS` frozenset (exact: `pcae.core.hpac_certification_coordinator`); `_CERTIFICATION_ROLE_ALLOWLIST` frozenset (exact 5); `certification_writer(role, *, certification_session_id, principal_id, credential_id, proof_id=None, …)`; `CertificationWriterHandle` one-shot; §33A extra checks; parameterize `_run_recognition_sequence` consumer allowlist (§33 step 9 verbatim, only the enumerated set swapped). No change to `production_writer` / `PawaOperation` / `PAWA_FAILURE_CODES` / provisioning. |
| `src/pcae/core/hpac_certification_coordinator.py` | NEW — the sole §38A consumer; bounded coordinator API (`begin_certification_context`, `open_challenge`, `record_assertion`, `verify_authentication_proof`, `bind_and_verify` (→ `verify_human_authentication`), `reach_gate5`); holds writer capabilities internally; no raw-capability leak; non-agent-importable. |
| `scripts/hpac_certification_admin.py` | NEW — standalone bounded admin entry (mirrors `hatp_certification_admin.py`); `--help` + bounded certification lifecycle only; no arbitrary role/subcommand/exec/approval-injection/PIN. |
| `src/pcae/core/human_authentication_proof.py` | POSSIBLE (OQ-1) — additive: accept a certification proof-writer capability bound to `proof_id` in `create_canonical` without weakening the fixture `subject == mechanism_id` path. Recorded as an additive prerequisite if required. |
| `tests/test_phase_<full_id>_n16_5_h3_impl.py` | NEW — the ≥100-item H-3 implementation suite (§99). |
| `docs/PHASE_…_N16_5_H3_IMPL.md` | this doc. |
| `PROJECT_STATUS.md`, `CHANGELOG.md`, `tasks/**`, `.pcae/phase-completion-*` | governed lifecycle. |

**Expected UNCHANGED:** `pyproject.toml` dependency set; `PawaOperation` membership; `PAWA_FAILURE_CODES` (21); RHAMP `terminal_reason_code` (41); all frozen contract bytes; all `hpac_pawa_schemas` / PPA descriptor / current-generation schemas; Gate 5 / Gate 9 / runtime authority; current `PrincipalRecord hp-8cee9b36b6784608ae48261af86289b8`; current `CredentialRecord hpc-2e7bbfa0c1b2480ba84ab5792159179d`; counter state (gen 0); generation-1 protected-presentation deployment.

## 6. Open questions (resolve from primary contract before coding the affected leg)

- **OQ-1 — `human_authentication_proof_verifier` subject. RESOLVED (option a, additive).** `HumanAuthenticationProofStore.create_canonical` bound the canonical proof-writer capability to `proof.mechanism_id`; `HPACLifecycleStore.record_verified_canonical` binds to `proof_id`; §33A REQ-236.4 / §43A REQ-255 fix the certification capability `subject` as `proof_id`. Resolution:
  - The certification proof-verifier capability is minted `_multi_write` bound to `subject == proof_id` (its two writes — `proof.json` + `STATE_PROOF_VERIFIED` — are one §42B / §49A verification transaction; the coordinator spends it once via `authority.complete_multi_write`).
  - `create_canonical` gains one additive keyword `certification_proof_subject` (default `None` → the existing `mechanism_id` path, byte-unchanged and not weakened). When passed (only by the certification coordinator, always the exact `proof_id`) the capability + provenance are checked against `proof_id`.
  - `resolve_canonical` now checks `writer_subject ∈ {proof.mechanism_id, proof.proof_id}` — both are immutable, digest-bound, non-forgeable fields of the resolved proof, so accepting either is not a weakening (a forged provenance must still name one of them, requiring a genuine `human_authentication_proof_verifier` capability bound to it).
  - Verified: `tests/test_hpac_verifier.py` + `tests/test_hpac_lifecycle.py` + `tests/test_hpac_authentication_proof.py` + the two verifier IV suites — 69 passed; the only 2 failures (`test_object_dunder_new_bypasses_trusted_construction_seal`, `test_forged_via_object_new_would_report_real_runtime_eligible`) are **pre-existing at I0** (reproduced identically under `git stash`), unrelated to this phase (a Py3.14 `__slots__`/`object.__new__` interaction), documented in the regression-attribution section.
  - Additive-only, per HPAC-PAWA-REQ-260. No contract change.

## 7. Implementation progress (running)

| Increment | Commit | State |
|---|---|---|
| Phase task open + allowed-file zone | `a22f830e`, `45693ecd` | done |
| I0 + contract identity + CPIPC + delta map | `12bb6d07` | done |
| `certification_writer` factory + §33A + `CertificationWriterHandle` + closed 5-role allowlist (`hpac_protected_admin_writer.py`) | `5519faa4` | done |
| OQ-1 additive proof-writer subject reconciliation (`human_authentication_proof.py`) | `0a194b13` | done |
| Prospective PROJECT_STATUS (`H-3: IMPLEMENTATION IN PROGRESS`) | `af5c5952` | done |
| `pcae.core.hpac_certification_coordinator` (sole §38A consumer / orchestrator; `HpacCertificationCoordinator` + `CertificationSession`; retains capabilities internally; per-role mint→consume→one canonical store call; proof-verifier `_multi_write` + `handle.complete()`; `reach_gate5_assurance` → `verify_human_authentication(require_real_assurance=True)`; hard stop at the bounded assurance result) | _this increment_ | done |
| `scripts/hpac_certification_admin.py` (bounded standalone entry: `describe` / `status` only; no `--approve` / `--yes` / `--pin` / `--fake-real` / arbitrary role / arbitrary subcommand / `--protected-root`; real ceremony explicitly deferred to N16-5-FINAL-CERT) | _this increment_ | done |
| H-3 implementation test suite — part 1 (69 items: contract-identity, §33A factory/recognition, closed 5-role allowlist incl. terminator/wildcard/prefix/near-miss denial, ambient-identity insufficiency, one-shot / wrong-role / wrong-session / wrong-subject, forgery, no-remint/escalation, session/subject binding incl. unresolvable/revoked/unbound principal+credential, §39A import-fence guard, fixture-seam guard, admin-script boundary + `describe`/`status`, host-state preservation) — `tests/test_phase_…_n16_5_h3_impl.py`, 69/0 | _this increment_ | done |
| H-3 test suite — part 2 (`test_100`: deterministic end-to-end chain reachability through the coordinator — `begin_session` → `open_challenge` → `record_assertion` → `record_verified_proof` → `reach_gate5_assurance` → **PRODUCTION `AuthenticatedHumanPrincipal`** (`assurance_class is PRODUCTION`, `is_real_runtime_eligible`, `is_verifier_authenticated_principal`) → `STATE_PROOF_VERIFIED_AND_BOUND` Gate-5 sequence-3 artifact, **with NO `_mint_production_writer_capability` / `_PRODUCTION_WRITER_FACTORY_SEAL` test seal** — the H-3 repair proof; `test_101`: a FIXTURE_NON_REAL authority cannot satisfy §33A; `test_102`: the coordinator never redefines `require_real_assurance` / `assurance_class`; `test_93`: contracts+schemas byte-unchanged since I0) — 73/0 total | _this increment_ | done. Two design fixes: `CertificationSession.open_challenge` now takes bare `presentation_id` + `presentation_digest` and re-resolves the trusted presentation on the freshly-recognized §33A authority (an `HPACResolvedRecord` sealed to another authority instance is rejected); `reach_gate5_assurance` builds every read store on the gate5 writer's authority instance and the counter store on the counter writer's, so no resolved record or store crosses an authority-seal boundary. |
| H-3 test suite — part 3 (deterministic non-elevation matrix, mixed non-real negatives, PB/policy DENY dominance, challenge/proof/counter/principal forgery negatives, restart-dead) | — | pending |
| packaging (`pyproject` wheel inclusion) + clean-install smoke (§54/§55) | — | pending |
| bounded regression + Fast-Green A/B attribution (§100/§101) | — | pending |
| contract / schema / dependency byte-identity checks (§102/§103) | — | pending |
| runtime / host-state preservation verification (§104/§105) | — | pending |
| PROJECT_STATUS + CHANGELOG final; governed finalization; N16-5-H3-IV successor derivation | — | pending |

## 8. Regression attribution (running — §100 / §101)

**Fresh phase suite:** `tests/test_phase_…_n16_5_h3_impl.py` — **73 / 0**.

**Targeted affected band** (`test_hpac_verifier` + `test_hpac_lifecycle` +
`test_hpac_authentication_proof` + `.30R.3.1` + `.30R.3.4` + `.30R.3.5` +
`.30R.5R.1` + `.30R.5R.2` contract-reconciliation + the v1.3 contract IV) —
**466 passed, 6 failed**. All 6 are **point-in-time scope-fence guards from
predecessor verification-only / contract phases** that assert "no `src/pcae`
change / no certification production module exists yet" as of their own
phase-entry SHA. They are **attributable to this phase's sanctioned
implementation**, not regressions, and each is to be reconciled **phase-aware**
(widen the authorized set by *exactly* this phase's file set —
`hpac_protected_admin_writer.py`, `hpac_certification_coordinator.py`,
`human_authentication_proof.py`, `scripts/hpac_certification_admin.py`,
`tests/test_phase_…_n16_5_h3_impl.py` — subset/`==` orientation, NO
wildcard/glob/fnmatch, NO `def test_` renamed/removed; memory trap 11/17):

| Guard | Why it trips | Reconciliation |
|---|---|---|
| `test_hpac_verifier.py::test_runtime_authority_is_the_only_production_consumer_of_hpac_verifier_module` | the §38A coordinator now imports `verify_human_authentication` (contract REQ-247 **requires** the proof path to go through the verifier, never around it) | add `pcae.core.hpac_certification_coordinator` to the authorized-consumer set with an `N16-5-H3-IMPL` comment |
| `.30R.3.1::test_42_no_agent_runtime_gate_plugin_consumer_of_the_factory` | the §38A coordinator imports `certification_writer` from the fence module (v1.3 §38A authorizes exactly this one consumer) | widen by the exact coordinator dotted-path; it is not an agent/runtime/gate/plugin |
| `.30R.5R.2 contract-reconciliation::test_38_no_src_or_scripts_change_since_h0` | that phase was contract-only; H0 = `b2530066` | phase-aware: this implementation phase is the sanctioned src change; widen by the exact file set |
| v1.3 contract IV::`test_01_v0_phase_entry_sha_resolves` | asserts `V0` is HEAD's ancestor with no src delta on that path shape | re-anchor / phase-aware widen |
| v1.3 contract IV::`test_66_this_iv_edits_no_normative_contract_or_source` | the IV phase edited no source; this phase does | phase-aware: scope the guard to the IV phase's own commits |
| v1.3 contract IV::`test_67_no_certification_production_module_exists` | explicitly asserted the module was not yet built | invert to `test_certification_production_module_exists_and_matches_ss38a` once built (this phase) |

**Method for the reconciliation increment:** `git worktree add <wt> 74e52d59`;
run the ~25-file guard band at I0 and at HEAD; `comm -23` the FAILED node lists;
candidate-only = attributable → reconcile; baseline-common = pre-existing (do
not repair). The two `test_hpac_verifier` `object.__new__` forgery failures
(`test_object_dunder_new_bypasses_trusted_construction_seal`,
`test_forged_via_object_new_would_report_real_runtime_eligible`) are
**pre-existing at I0** (Py 3.14 `__slots__` interaction), reproduced under `git
stash` — NOT attributable, NOT repaired here.

## 9. Remaining work (as of commit `df915e32`)

1. Guard reconciliation increment (the 6 attributable guards above; phase-aware; A/B worktree method).
2. Test suite part 3 — deterministic non-elevation matrix (§57/§58), mixed non-real negatives (§59), PB/policy DENY dominance (§71/§72), challenge/proof/counter/principal forgery negatives (§66-§70), restart-dead (§94) — to ≥100 items (§99).
3. Packaging: assert the coordinator ships in the wheel (`src/pcae/core/` — auto-included) and the standalone script is NOT a `console_scripts` entry (matching `scripts/hpac_protected_presentation_admin.py`); a clean-install smoke in a disposable venv (§54/§55).
4. Contract / schema / dependency byte-identity final checks (§102/§103); `pcae runtime inspect` Observed/observe/unavailable, 0/0 (§73/§104/§105); host-state preservation (current principal / credential / counter / gen-1 presentation deployment — repository-only phase, 0 protected-root writes).
5. PROJECT_STATUS + CHANGELOG final; derive (not begin) the `N16-5-H3-IV` successor (`docs/…` + `tasks/DECISIONS.md`).
6. Governed finalization: `.pcae/phase-completion-metadata.json` + `.pcae/phase-completion-report.md` (memory `project-phase-completion-procedure`; implementation-phase metadata shape — `tests_added_or_updated` first token = count; `fast_green` = targeted `N passed, 0 failed`); `pcae phase complete … --stage-pending-report` → `pcae push` (**pushes to origin/main — confirm with the operator**) → re-run `pcae phase complete` (no flag) to promote + fire the Telegram notification; `origin/main..HEAD = 0`.

## 10. Verdicts (to be completed at finalization — §115 verdict block)

_pending._
