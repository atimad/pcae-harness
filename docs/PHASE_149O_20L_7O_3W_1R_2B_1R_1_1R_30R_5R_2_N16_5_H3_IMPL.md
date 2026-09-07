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

- **OQ-1 — `human_authentication_proof_verifier` subject.** `HumanAuthenticationProofStore.create_canonical` calls `require_writer(writer, role, subject=proof.mechanism_id)`; `HPACLifecycleStore.record_verified_canonical` calls `require_writer(writer, role, subject=proof_id)`. §33A REQ-236.4 / §43A REQ-255 fix the certification capability `subject` as `proof_id` for all four lifecycle roles. Options: (a) mint the proof-verifier role capability bound to `proof_id` and make `create_canonical` accept a `proof_id`-subject capability additively (no fixture-path weakening); (b) BLOCK + reconciliation successor. Preferred: (a) — a narrow additive change; the contract's §96 is "specialized, not redefined" for exactly this family and REQ-260 explicitly permits an additive prerequisite change. Decision to be recorded in `tasks/DECISIONS.md` + this doc §6 before implementation of that leg.

## 7. Verdicts (to be completed at finalization)

_pending — see the canonical Phase Report and §115 verdict block._
