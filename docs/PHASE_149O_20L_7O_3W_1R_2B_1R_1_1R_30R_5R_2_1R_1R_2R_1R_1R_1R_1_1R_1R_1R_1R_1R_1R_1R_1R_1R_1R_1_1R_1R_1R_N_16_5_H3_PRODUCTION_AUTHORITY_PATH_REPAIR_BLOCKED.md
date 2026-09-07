# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R — N-16-5 Production Authority-Path Repair for Real-Human / Genuine-YubiKey Certification — H-3 Challenge / Proof / Lifecycle / Counter / Gate-5 Reachability

## Status: BLOCKED. H-3: NOT REPAIRED. N-16-5: NOT CLOSED.

## Summary

This phase was authorized to repair blocking finding **H-3** (raised by the
predecessor certification-retry phase): the real end-to-end N-16-5
certification chain has **no production authority path** — it composes only
in test code through disclosed test-only seals.

The primary-source investigation was completed and **independently reproduced
H-3**. It then established that **the smallest correct repair requires a
normative `HPAC-PAWA-001` contract change** (v1.2 → v1.3): a new authorized
`PRODUCTION` writer-factory-consumer category for a certification coordinator,
plus a production mint path for the five certification-chain lifecycle roles.
Frozen `HPAC-PAWA-REQ-087 / 088 / 223 / 224` enumerate a **closed** set of
authorized consumer categories and state explicitly that *"the launcher,
helper, presentation store, verifier, Gates, runtime, agent, CLI, and plugins
remain unauthorized."* A certification coordinator is exactly a
verifier/Gate-adjacent consumer.

Per this phase's own **FROZEN CONTRACT PRESERVATION** directive — *"If the
repair cannot be made without contract change: STOP. Finalize BLOCKED.
Recommend a contract-reconciliation phase."* — the phase is **finalized
BLOCKED through canonical completion, not aborted**. No `src/pcae`, `scripts`,
`tests`, `docs/contracts`, `pyproject.toml`, or dependency change. No
ceremony. Zero writes to the protected root. Counter state untouched
(generation 0). Runtime unchanged (`not_implemented` / `Observed` / `observe`
/ `unavailable`, 0 plugins / 0 capabilities). No first governed runtime
external effect. N-16-6 / N-16-7 remain OPEN / UNTOUCHED (N-16-7 strictly
last).

## Anchors

- **H0 (phase-entry SHA):** `3d1965b3d962e337bb016c61b956a6c5ea2e5017`
- **Predecessor:** `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1` — Final Real-Human / Genuine-YubiKey Protected-Presentation N-16-5 Certification and Closure Adjudication (BLOCKED, finding H-3; latest canonical completed phase — confirmed via `pcae session bootstrap` + `pcae phase-report show --latest`).
- **CPIPC successor validation:** the canonical parser (`pcae.core.phase_id`) confirms the operator-supplied ID `…1.1R.1R.1R` is valid, `same_series` and `same_branch` with the predecessor, and strictly greater (`compare` → `less` predecessor→candidate). It is the established `R`-suffix repair-successor of a completed phase (final subphase token `1` → `1R`), is absent from `tasks/done/`, matches the predecessor report's own "Successor" recommendation, does not reopen or reuse a completed phase ID, and introduces no parallel numbering scheme. No mechanical discrepancy — the operator-supplied ID is used exactly as given.
- **`origin/main..HEAD` at entry:** 0. **At exit:** 0.

## 1. Governed orientation (§1)

| Check | Result |
|---|---|
| `git status` | clean; branch `main` even with `origin/main` |
| `pcae health` | healthy |
| `pcae check` | passed |
| `pcae status coherence` | coherent |
| `pcae push check` | `nothing_to_push` (phase-report trust + identity passed) |
| `pcae runtime inspect` | `not_implemented` / `Observed` / `observe` / `unavailable`; registry empty; 0 plugins / 0 capabilities; PB `execution_unavailable`; posture `non-executing` |
| `pcae notify status` | Telegram configured, enabled, outbound-ready |
| `pcae phase-report show --latest` | predecessor H-3 BLOCKED report; N-16-5 NOT CLOSED |
| Predecessor is latest canonical completed phase | ✅ |
| C-1 | RESOLVED (predecessor bootstrap) |
| Canonical principal `hp-8cee9b36b6784608ae48261af86289b8` | present, active, mechanism-neutral (per predecessor's revalidation) |
| Canonical credential `hpc-2e7bbfa0c1b2480ba84ab5792159179d` | present, active, not revoked, bound (per predecessor's revalidation) |
| Counter state | generation 0 — unchanged |
| Generation-1 protected-presentation deployment | current / trusted (per predecessor's revalidation) |
| No conflicting active phase | ✅ (active task was the post-predecessor idle placeholder) |

No `git reset` / `stash` / `revert` / `clean` was performed.

## 2. H-3 independently reproduced from primary source (§5)

Modules read in full or in the relevant part: `hpac_verifier.py`,
`hpac_protected_admin_writer.py`, `hpac_foundation.py`, `hpac_lifecycle.py`,
`human_authentication_proof.py`, `hpac_rhamp_counter_state.py`,
`protected_presentation.py`, and
`docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`.

**Positive certification chain and its production writer needs:**

```
run_protected_presentation_ceremony(authority: HPACStoreAuthority)
  → real helper render → real /dev/tty APPROVE
  → HPAC-PRESENTATION-EVIDENCE/2.0        [mint_protected_presentation_evidence_writer — EXISTS]
HumanAuthenticationProofStore.create_canonical(writer, proof)  [role human_authentication_proof_verifier]
HPACLifecycleStore.open_challenge_canonical(writer, …)         [role hpac_challenge_coordinator]
HPACLifecycleStore.record_assertion_canonical(writer, …)       [role hpac_assertion_recorder]
HPACLifecycleStore.record_verified_canonical(writer, …)        [role human_authentication_proof_verifier]
verify_human_authentication(require_real_assurance=True,
        gate5_writer, counter_state_writer)
  → HPACLifecycleStore.bind_gate5_canonical(gate5_writer, …)   [role hpac_gate5_binder]
  → counter_state_store.apply_after_verification(counter_state_writer, …)  [role hpac_rhamp_counter_state_verifier]
  → PRODUCTION AuthenticatedHumanPrincipal
Gate 5 consumption
```

**The five missing production lifecycle roles** — each currently mintable
only for a `FIXTURE_NON_REAL` authority via `HPACStoreAuthority.writer(role)`:

| # | Role | Required by |
|---|---|---|
| 1 | `hpac_challenge_coordinator` | `HPACLifecycleStore._GENESIS_WRITER_ROLE` — `open_challenge_canonical` |
| 2 | `hpac_assertion_recorder` | `HPACLifecycleStore._ASSERTION_WRITER_ROLE` — `record_assertion_canonical` |
| 3 | `human_authentication_proof_verifier` | `HPACLifecycleStore._VERIFIED_WRITER_ROLE` — `record_verified_canonical`; and `HumanAuthenticationProofStore._WRITER_ROLE` — `create_canonical` |
| 4 | `hpac_gate5_binder` | `HPACLifecycleStore._BOUND_WRITER_ROLE` — `bind_gate5_canonical` (invoked inside `verify_human_authentication`) |
| 5 | `hpac_rhamp_counter_state_verifier` | `hpac_rhamp_counter_state.COUNTER_STATE_VERIFIER_ROLE` — `apply_after_verification` (invoked inside `verify_human_authentication`) |

**Blockers (verified line-by-line):**

1. `HPACStoreAuthority.writer(role)` raises *"no production HPAC writer is
   implemented in this foundation phase"* for any `authority_class` that is
   not `FIXTURE_NON_REAL` (`hpac_foundation.py:748-749`).
2. `HPACStoreAuthority._mint_production_writer_capability` requires
   `_PRODUCTION_WRITER_FACTORY_SEAL`, held only by
   `hpac_protected_admin_writer` (`hpac_foundation.py:773`).
3. Inside `hpac_protected_admin_writer`, the two production mint sites are:
   - `production_writer()` — closed `PawaOperation` set
     (`ENROLL_PRINCIPAL`, `REVOKE_PRINCIPAL`, `ENROLL_CREDENTIAL`,
     `REVOKE_CREDENTIAL`, `INITIALIZE_CREDENTIAL_SIDECAR_STATE`,
     `CONFIGURE_PRESENTATION_MECHANISM`); mints only roles
     `human_principal_registry_admin` / `presentation_mechanism_installer`;
     callers restricted by `_detect_caller_module` to
     `AUTHORIZED_FACTORY_CONSUMERS` = {`pcae.core.hpac_protected_admin_writer`,
     `pcae.core.hpac_rhamp_enrollment`,
     `pcae.core.hpac_protected_presentation_admin`}.
   - `mint_protected_presentation_evidence_writer()` — role
     `protected_presentation_mechanism` only; caller restricted to
     `pcae.core.protected_presentation`; and it **requires the caller to
     already hold a recognized `PRODUCTION` `HPACStoreAuthority`**.
   Neither covers any of the five certification-chain roles.
4. `HPACStoreAuthority.production()` alone fails
   `_validate_production_boundary` when run as the deployment owner
   (predecessor finding **F-11**): with `_configured_agent_identity is None`
   the negative boundary keys off `_current_agent_identity()` (the live
   euid), which owns the `0700` root. `_configured_agent_identity` is bound
   only inside `production_writer()`'s §33 recognition sequence, via the
   factory seal (`_bind_configured_agent_identity`,
   `hpac_foundation.py:599-611`).
5. `run_protected_presentation_ceremony(authority=…)` and the proof /
   lifecycle / counter stores all accept a **caller-supplied** `PRODUCTION`
   `HPACStoreAuthority` / `HPACWriterCapability`. No production caller
   legitimately holds one for the certification purpose. The only place the
   full chain composes is test code — e.g.
   `tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_1_ctap2_pin_uv_repair_iv.py::test_25`,
   which uses `HPACStoreAuthority._production_test_fixture` (guarded by
   `_PRODUCTION_TEST_FIXTURE_SEAL`), a directly-imported
   `_PRODUCTION_WRITER_FACTORY_SEAL`, an in-process `_launch_and_exchange`
   shim, the structurally-`NON_REAL` `DeterministicCtap2Provider`, and the
   `_test_decision_source` seam — its own docstring: *"an IV observation,
   not a certification."*

**Verdict:** `H-3 ROOT CAUSE — VERIFIED`. `PRE-REPAIR PRODUCTION
CERTIFICATION AUTHORITY PATH — ABSENT`. `TEST-ONLY CERTIFICATION PATH —
PRESENT`.

## 3. Authority-graph table (§6)

| Object / action | Current creator | Current recognizer | Trust anchor | Production reachable? | Test-only? | Missing production boundary |
|---|---|---|---|---|---|---|
| certification operation / context | — (none) | — | — | **NO** | n/a | a recognized certification-coordinator entry point |
| authentication challenge (`open_challenge_canonical`) | `HPACLifecycleStore` + `hpac_challenge_coordinator` writer | `resolve_canonical_chain` provenance | authority `_seal` + issuance registry | **NO** (FIXTURE only) | yes (`fixture_genesis_writer`) | production mint for `hpac_challenge_coordinator` |
| protected-presentation request / evidence | `protected_presentation` + `mint_protected_presentation_evidence_writer` | `verify_protected_presentation_evidence` | authority `_seal` | **partial** — mint fn EXISTS, but needs a recognized PRODUCTION authority handed in | no | a way for the coordinator to obtain the recognized authority |
| FIDO2 assertion result | `NativeCtap2Provider` (real) via `verify_real_fido2_assertion` | `hpac_verifier._verify_assertion_material` | real CTAP2 signature math | yes (provider certified `.1R.30R.5R.1`) | no | — |
| authentication proof (`create_canonical`) | `HumanAuthenticationProofStore` + `human_authentication_proof_verifier` writer | `proof_store.resolve_canonical` | authority `_seal` + issuance registry | **NO** (FIXTURE only) | yes | production mint for `human_authentication_proof_verifier` |
| counter-state decision (`apply_after_verification`) | `HpacRhampCounterStateStore` + `hpac_rhamp_counter_state_verifier` writer | `counter_state_store.resolve` | authority `_seal` | **NO** (FIXTURE only) | yes | production mint for `hpac_rhamp_counter_state_verifier` |
| `AuthenticatedHumanPrincipal` | `verify_human_authentication` return path only | `is_verifier_authenticated_principal` (identity registry) | process-local identity registry | yes (function exists) — but unreachable without all writers above | no | (unblocks once writers exist) |
| Gate 5 consumption | `runtime_dispatch_gate5` | existing `assurance_class is PRODUCTION` + `is_verifier_authenticated_principal` | verifier identity registry | yes (consumer exists) — but unreachable without a real principal | no | (unblocks once principal reachable) |

## 4. Minimal H-3 repair set (§7) — specified, NOT implemented

1. **`HPAC-PAWA-001` v1.2 → v1.3 amendment** — add exactly one authorized
   `PRODUCTION` writer-factory-consumer category: the bounded **N-16-5
   real-human-authentication certification coordinator**. Exact dotted path
   (recommended `pcae.core.hpac_certification_coordinator`), reached only
   from a standalone `scripts/` entry point (recommended
   `scripts/hpac_certification_admin.py`, mirroring the existing
   `hatp_certification_admin.py` pattern named in the contract's §36 area).
   No wildcard / prefix / glob (PAWA-INV-9).
2. **A production mint authority for the five certification-chain lifecycle
   roles** (`hpac_challenge_coordinator`, `hpac_assertion_recorder`,
   `human_authentication_proof_verifier`, `hpac_gate5_binder`,
   `hpac_rhamp_counter_state_verifier`): non-bearer, single-use per
   authentication ceremony, process-local, restart-dead; bound to
   `principal_id` / `credential_id` / challenge / operation / consumer.
   **Not** a new §42 `PawaOperation` — these are per-authentication
   `<root>/proofs/v2/…` lifecycle records, not protected
   principal-administration mutations.
3. **A dedicated recognition sequence** for that consumer, reusing the
   existing §33 machinery (root topology + `HPAC-PAWA-AGENT-EXCLUSION/1.0`
   resolution + configured-agent identity binding + exact factory-consumer
   check).
4. **Explicit continued prohibition** (restate `HPAC-PAWA-REQ-088` / `224`
   in spirit): launcher, helper, presentation store, runtime, agent, CLI,
   plugins, and generic Gate consumers remain unauthorized; ordinary agent
   authority does not grow.
5. The existing `mint_protected_presentation_evidence_writer` path is
   reused unchanged; only its caller (the coordinator) must be able to
   obtain a recognized `PRODUCTION` authority to pass in.

## 5. Why BLOCKED, not implemented (§40 / FROZEN CONTRACT PRESERVATION)

`HPAC-PAWA-REQ-087` establishes the closed authorized-consumer categories;
`HPAC-PAWA-REQ-088` and `HPAC-PAWA-REQ-224` explicitly list *verifier,
Gates, runtime, agent, CLI, plugins* as **unauthorized**; `HPAC-PAWA-REQ-223`
shows the precedented amendment form (*"The exact future production factory
consumer added by v1.2 is …"*). Authorizing a certification coordinator and
adding a five-role production mint path is therefore a **normative
`HPAC-PAWA-001` change**, in the same class as v1.0 → v1.1 (agent exclusion,
phase `.2A`) and v1.1 → v1.2 (presentation-mechanism configuration, phase
`.1R.30R.4R.1`).

This phase's directive is unambiguous for that case: *STOP, finalize BLOCKED,
recommend a contract-reconciliation phase.* The phase is completed BLOCKED
through the full governed lifecycle, preserving the derived H-3 root cause,
the exact five missing production lifecycle roles, the current closed
factory-consumer set, and the minimal required contract delta.

## 6. Required final verdicts (§53)

```
H-3 ROOT CAUSE:                                  VERIFIED
PRE-REPAIR PRODUCTION CERTIFICATION AUTHORITY PATH: ABSENT
TEST-ONLY CERTIFICATION PATH:                    PRESENT
MINIMAL H-3 REPAIR SET:                          DERIVED — requires HPAC-PAWA-001 v1.3 (new factory-consumer category + five-role production mint path + dedicated recognition sequence)
PRODUCTION CERTIFICATION ENTRY BOUNDARY:         NOT ESTABLISHED (contract change required first)
PRODUCTION CHALLENGE ISSUANCE:                   NOT IMPLEMENTED
PRODUCTION AUTHENTICATION-PROOF ISSUANCE:        NOT IMPLEMENTED
PRODUCTION COUNTER-VERIFICATION LIFECYCLE:       NOT IMPLEMENTED
PRODUCTION require_real_assurance REACHABILITY:  NOT IMPLEMENTED
PRODUCTION GATE-5 CERTIFICATION REACHABILITY:    NOT IMPLEMENTED
TEST-ONLY SEAL REQUIRED AFTER REPAIR:            N/A (no repair performed)
ORDINARY AGENT CAN ISSUE TRUSTED CERTIFICATION AUTHORITY: NO
DETERMINISTIC INPUT CAN ELEVATE TO PRODUCTION ASSURANCE:  NO
CERTIFICATION PATH EXTERNAL EFFECT:              UNREACHABLE
PACKAGE / CLEAN-INSTALL PRODUCTION PATH:         N/A (no repair performed)
CANONICAL PRINCIPAL:                             UNCHANGED
CANONICAL CREDENTIAL:                            UNCHANGED
COUNTER STATE:                                   UNCHANGED (generation 0)
GENERATION-1 PRESENTATION DEPLOYMENT:            UNCHANGED
REAL CEREMONY PERFORMED:                         NO
H-3:                                            NOT REPAIRED / BLOCKED
F-5:                                            DEPLOYMENT VERIFIED — CERTIFICATION BLOCKED
N-16-5:                                         NOT CLOSED
RUNTIME:                                        not_implemented / Observed / observe / unavailable (0 plugins / 0 capabilities)
FIRST GOVERNED RUNTIME EXTERNAL EFFECT:         ABSENT / UNREACHABLE
```

## 7. No-ceremony / no-mutation attestation (§49 / §50)

`makeCredential` 0; real `getAssertion` 0; YubiKey touch 0; FIDO2 PIN prompt
0; protected APPROVE 0; protected REJECT 0; real presentation evidence 0;
challenges opened 0; proofs created 0; Gate 5 certifications 0; principals
minted 0; authorized protected host mutation 0; unauthorized protected host
mutation 0; counter-state generation before 0 / after 0; secrets
requested / echoed / logged 0.

## 8. Boundaries preserved

- No `src/pcae`, `scripts`, `tests`, `pyproject.toml`, `docs/contracts`, or
  dependency change. `git diff --name-only H0 HEAD` touches only `.pcae/**`,
  `docs/PHASE_…`, `PROJECT_STATUS.md`, `CHANGELOG.md`, `tasks/**`.
- No principal / credential / counter / protected-root / helper / generation
  / PPA-registration state created, recreated, reset, rotated, or repaired.
- Runtime `not_implemented` / `Observed` / `observe` / `unavailable`, 0 / 0 —
  unchanged. No `adapter.dispatch`, no `DispatchEnvelope`, no plugin, no
  first governed runtime external effect.
- Human principal remains mechanism-neutral; `hpac.fido2.uv_presence.v2` and
  `pcae-protected-local-presentation/1.0` remain supported / non-exclusive;
  the mobile-only future path stays open. YubiKey and local TTY are not
  globally mandatory for PCAE development.
- `DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` preserved. No
  delegated worker used; the primary human-authorized session performed all
  read-only investigation, primary-source study, evidence authoring, task
  lifecycle, commits, and push.
- Durable Telegram Acceptance Receipt / Phase-Notification Auditability
  Repair: preserved. No historical notification re-dispatch. This phase's
  normal completion notification is authorized.

## 9. Ordinary-development non-regression

`pcae health` (healthy), `pcae check` (passed), `pcae status coherence`
(coherent), `pcae runtime inspect` (`not_implemented` / `Observed` /
`observe` / `unavailable`, 0 / 0). Focused sanity: `pytest
tests/test_hpac_verifier.py
tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_1_ctap2_pin_uv_repair_iv.py`
→ **75 passed** (byte-identical tree to the pushed-green `3d1965b3`; no code
or test change).

## 10. Evidence

`.pcae/certification/n16_5_h3_production_authority_repair_30r5r2_1r1r1r.json`
(schema `PCAE-N16-5-H3-AUTHORITY-PATH-REPAIR/1.0`) records H0, the CPIPC
successor validation, the orientation snapshot, the reproduced H-3 root-cause
chain, the five missing production lifecycle roles, the current closed
factory-consumer set, the exact minimal contract delta, the derived successor
chain, and the all-zero ceremony / mutation audit.

## 11. Successor phases (derived — NOT begun)

1. **`HPAC-PAWA-001` v1.3 Certification-Coordinator Authority Contract
   Reconciliation / Freeze** (next). Decides and freezes the smallest new
   authorized factory-consumer category, its recognition sequence, the exact
   five-role mint authority, caller / consumer restrictions, non-bearer /
   single-use properties, and the explicit continued prohibition on ordinary
   launcher / helper / runtime / agent / CLI / plugin authority.
2. Then a **dedicated production implementation phase** for the H-3
   authority path.
3. Then a **dedicated independent verification phase**.
4. Then a **fresh final real-human / genuine-YubiKey N-16-5 certification
   phase** (re-run the predecessor certification phase unchanged against the
   unchanged canonical principal / credential / counter / generation-1
   deployment; do not reuse a completed phase ID).

None of these is bundled into this phase. N-16-6 and N-16-7 remain OPEN /
UNTOUCHED and strictly out of scope; N-16-7 remains strictly last.
