# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.4 — N-16-5 Merged RHAMP Real FIDO2 Credential Registration, Counter-State, Bootstrap & Authentication Mechanism Implementation

**Status: IMPLEMENTED — IV PENDING (`.1R.30R.3.5`). N-16-5: NOT CLOSED.
PAWA Slice 1: CLOSED (unchanged). RHAMP-001 v1.0 / HPAC-PAWA-001 v1.1 /
HPAC-001 v2.1: byte-unchanged. Runtime: `Observed` / `observe` /
`unavailable`. First external effect: ABSENT / UNREACHABLE.**

This phase implements the merged RHAMP-REQ-156 `.1R.30` bundle selected by
`.1R.30R.3.3R` (DECISION A — RE-MERGE): the former Slice 2 + Slice 3 folded
back into one atomic implementation unit. It replaces the superseded
`.1R.30R.3.4 / .3.5 / .3.6` decomposition. No contract text changed.

`.1R.30R.3.3` remains an immutable BLOCKED phase; `.1R.30R.3.3R` remains
DECISION A. Neither is resumed or reinterpreted.

---

## 1. What was built

### 1.1 New production modules (`src/pcae/core/`)

| Module | RHAMP-001 §§ | Responsibility |
|---|---|---|
| `hpac_rhamp_terminal_reasons.py` | §49 / §50 | The closed **41-value** `terminal_reason_code` enum + human-visible category map + `RhampTerminalError`. Pure vocabulary; no I/O. |
| `hpac_rhamp_client_context.py` | §6 / §7 / §8 / §36 | The PCAE-owned canonical native-CTAP2 client-data context (`RHAMP-CLIENT-CONTEXT/1.0`, closed 15-field). `rp_id = "hpac.pcae.local"` compiled-in constant + `RP_ID_HASH`. `client_data_hash = SHA-256(HPAC-REQ-089 canonical bytes)`. Classified explicitly **not a web origin** (RHAMP-REQ-028). |
| `hpac_rhamp_credential_sidecar.py` | §17 | The protected per-credential `RHAMP-FIDO2-CREDENTIAL/1.0` sidecar store. `<HPAC_PROTECTED_ROOT>/credentials/<credential_id>/fido2-credential.json`. Immutable, create-only, atomic, read-back verified. Resolution rejects symlink / traversal / non-canonical bytes / digest mismatch / registry disagreement. Stores **no private key, PIN, or biometric** — structurally (no such field). `CredentialRecord` byte-unchanged (RHAMP-REQ-055). |
| `hpac_rhamp_counter_state.py` | §20 / §21 / §22 | The protected per-credential `RHAMP-COUNTER-STATE/1.0` store + the frozen §20 accept/block table (`evaluate_signcount`) + the §12 linearized update (read current → verify expected-current → evaluate → atomic-replace → read-back). A missing / corrupt record for an `active` credential **fails closed** — never "counter 0". A non-zero regression fails the authentication closed, sets `review_flag`, and **never auto-revokes**. |
| `hpac_rhamp_ctap2.py` | §3 / §9 / §19 / §38 / §63 | The native CTAP2 boundary. `NativeCtap2Provider` (production; roaming USB-HID / NFC, non-discoverable `rk=False`, `uv=True`, ES256, no attestation preference; reuses `fido2.ctap2` / `fido2.hid` primitives as a shared library per RHAMP-REQ-104). `DeterministicCtap2Provider` (`SIMULATION_ONLY: Final = True`, `PROVIDER_KIND != native-ctap2` — a class constant with **no** constructor override; real ES256 crypto over a synthetic in-memory key). `verify_assertion_signature_material` — rpIdHash + COSE `key.verify(authData ‖ client_data_hash)` + `FLAG.UP` + `FLAG.UV` + raw `signCount`, using the pinned library, **no custom cryptography**. `resolve_production_ctap2_provider()` accepts **no** env var / caller flag that swaps in the fixture. |
| `human_authenticator_fido2.py` | §12 / §32 / §33 / §37 | `FIDO2HumanAuthenticator` — the real `HumanAuthenticator` for exactly `hpac.fido2.uv_presence.v2` (mechanism-specific, never an approval mechanism). `prepare_challenge` (fresh CSPRNG nonce ≥ 256 bits, TTL ≤ 120 s ceiling enforced), `run_assertion_ceremony` (builds the canonical client context, drives native `getAssertion` over `client_data_hash` + `allow_list` + `rp_id`), the closed `RHAMP-FIDO2-ASSERTION/1.0` envelope carried inside the byte-unchanged `HPAC-PROOF/2.0.assertion` (base64url). |
| `hpac_rhamp_assertion_verify.py` | §37 | The pure RHAMP-REQ-102 real-assertion verification core `hpac_verifier` calls: credential/sidecar cross-check + `raw_credential_id` match, canonical client-data reconstruction **from trusted state** (RHAMP-REQ-025), rpIdHash, COSE signature, `FLAG.UP`, `FLAG.UV`, the §20 counter check. Every failure → exactly one of the 41 codes. **No signature bypass.** |
| `hpac_rhamp_enrollment.py` | §13 / §14 / §15 / §31 / §61 | The protected-admin credential registration + first-credential bootstrap ceremony (consumes the Slice-1 PAWA `production_writer` boundary — **no second admin authority**), the RHAMP-REQ-116 revocation, the RHAMP-REQ-051 enrollment evidence, and the §31 canonical active-credential resolution (`resolve_active_credentials` / `resolve_authentication_allowlist` — no caller-injected allowList; a credential is ACTIVE only when registry + sidecar + counter-state all resolve). Inside the non-agent-importable admin-writer fence. |

### 1.2 Modified production modules

- **`hpac_verifier.py`** — `_ELIGIBLE_MECHANISM_IDS` widened by **exactly**
  `{"hpac.fido2.uv_presence.v2"}` (a `frozenset` literal; no wildcard, no
  prefix, no glob; RHAMP-REQ-011/109). `_verify_assertion_material` gains
  the real `hpac.fido2.uv_presence.v2` branch (RHAMP-REQ-102), gated on
  `_authority_class_of(...) is PRODUCTION` (RHAMP-REQ-103 — a
  `FIXTURE_NON_REAL` credential carrying the real `mechanism_id` is rejected
  before any signature math, RHAMP-REQ-113). The lifecycle chain is resolved
  before step 6 (a pure read) so the genesis binding's `invocation_id` /
  `attempt_id` feed the RHAMP-REQ-025 client-data reconstruction; the step-9
  state / cross-binding checks are unchanged. The linearized counter-state
  update (RHAMP-REQ-071.3) runs immediately after step 10, before the
  `AuthenticatedHumanPrincipal` is returned. New optional params
  (`sidecar_store`, `counter_state_store`, `counter_state_writer`) default
  `None` and leave the deterministic-mechanism path byte-for-byte
  unchanged.
- **`hpac_foundation.py`** — one strictly-additive `HPACWriterCapability`
  slot `_multi_write` (HPAC-PAWA-REQ-082/107 explicitly permit an additive
  flag). A `_multi_write` single-use capability is **not** auto-spent by
  `record_write` on the first write; the enrollment transaction owner
  spends it once via `HPACStoreAuthority.complete_multi_write` after the
  final read-back. Non-`_multi_write` single-use semantics are byte-for-byte
  unchanged.
- **`hpac_protected_admin_writer.py`** — `enroll_credential` and
  `initialize_credential_sidecar_state` promoted from recognised-but-rejected
  ("Slice 2") to available §42 mutation classes (the adjudication dissolved
  the boundary). `enroll_credential` binds to the **enrollment transaction
  id + principal_id** (HPAC-PAWA-REQ-100), mints a `_multi_write`
  capability. `AUTHORIZED_FACTORY_CONSUMERS` gains
  `"pcae.core.hpac_rhamp_enrollment"` (HPAC-PAWA-REQ-087 category 2 — the
  first-credential bootstrap / enrollment tool; category already named, no
  contract amendment). Issuance evidence records `enrollment_transaction_id`.
- **`human_principal_registry.py`** — `enroll_credential` gains an optional
  `_production_transaction_subject` so a PRODUCTION `enroll_credential`
  capability (bound to the transaction id, not the not-yet-existing
  `credential_id`) is accepted. The `CredentialRecord` /
  `_CREDENTIAL_ALLOWED_FIELDS` schema is **byte-unchanged**.

### 1.3 New standalone script

- **`scripts/hpac_principal_admin.py`** — `enroll-first-credential` /
  `revoke-credential`. Outside `src/pcae/`, never imported by
  `cli.py` / `commands/**` / `core/agent.py`, not a `pcae` subcommand, not
  packaged, no `--deterministic` flag (the fixture provider is test-only).

---

## 2. Contract → source → test → guard traceability (load-bearing)

| RHAMP-001 requirement | Production symbol | Test |
|---|---|---|
| §4 real `mechanism_id` allowlist (REQ-011/109) | `hpac_verifier._ELIGIBLE_MECHANISM_IDS` (frozenset literal + `{hpac.fido2.uv_presence.v2}`) | `.3.4::test_57/58` |
| §6 `rp_id` constant + `rpIdHash` (REQ-017/018) | `hpac_rhamp_client_context.RP_ID` / `RP_ID_HASH` | `.3.4::test_31/45`; `.3.4::test_89[wrong_rp_id_hash]` |
| §7 canonical client-data (REQ-022–026) | `RhampClientContext` / `build_client_context` | `.3.4::test_30/97`; `assertion_verify` client-data reconstruction `.3.4::test_44/47/84` |
| §8 no false origin claim (REQ-027/028) | `hpac_rhamp_client_context` docstring + `context_identifier` const | `.3.4::test_30/32` |
| §9 authenticator profile (REQ-030–032) | `NativeCtap2Provider` options `rk=False,uv=True`; transports `{usb,nfc}` | `.3.4::test_33/29/81[wrong_transport]` |
| §10 UP + UV mandatory (REQ-033/034) | `verify_assertion_signature_material` + `assertion_verify` UP/UV checks | `.3.4::test_44/48/89[up_absent,uv_absent]` |
| §13 registration flow (REQ-043–046) | `hpac_rhamp_enrollment.enroll_first_credential` | `.3.4::test_26/11/39` |
| §14 first-credential bootstrap authority (REQ-047–050) | `production_writer(ENROLL_CREDENTIAL,...)` in `enroll_first_credential` | `.3.4::test_22/23/24/25` |
| §15 enrollment evidence (REQ-051/052) | `_write_enrollment_evidence` → `RHAMP-ENROLLMENT-EVIDENCE/1.0` | `.3.4::test_37` |
| §17 sidecar (REQ-055–058) | `HpacRhampCredentialSidecarStore` / `Fido2CredentialSidecar` | `.3.4::test_06–13/96`; `assertion_verify` cross-check `.3.4::test_83/89` |
| §20/§21 counter policy + artifact (REQ-065–069) | `evaluate_signcount` / `HpacRhampCounterStateStore` | `.3.4::test_14–20/52/94` |
| §22 counter linearization (REQ-071–073) | `apply_after_verification` + `hpac_verifier` post-step-10 apply | `.3.4::test_21/50/51` |
| §23/§24 TTL bounds (REQ-074/076) | `FIDO2HumanAuthenticator.RHAMP_CHALLENGE_MAX_TTL_SECONDS`/`prepare_challenge` | `.3.4::test_42` |
| §31 active credential resolution (REQ-053/054) | `resolve_active_credentials` / `resolve_authentication_allowlist` | `.3.4::test_35/38/39/40` |
| §32/§33 authenticator + getAssertion (REQ-032/033) | `FIDO2HumanAuthenticator` | `.3.4::test_41/43/49` |
| §37 assertion verification (REQ-102/103) | `hpac_rhamp_assertion_verify.verify_real_fido2_assertion` + `hpac_verifier._verify_assertion_material` real branch | `.3.4::test_44–56/60/83–89` |
| §41 NON_REAL non-upgradeability (REQ-111–113) | `DeterministicCtap2Provider.SIMULATION_ONLY`; RHAMP-REQ-103 PRODUCTION gate | `.3.4::test_59–63/68` |
| §49 41-code vocabulary (REQ-129/130) | `TerminalReasonCode` (41) | `.3.4::test_64–67` |
| §64 decomposition / no protected presentation (REQ-156) | (absent — `approval_presentation.py` byte-unchanged) | `.3.4::test_70–73` |
| §65 no runtime capability (REQ-159/160) | (absent) | `.3.4::test_74–77` |

PAWA → RHAMP mapping (HPAC-PAWA-REQ-123/204): `RHAMP_TERMINAL_REASON_MAP`
in `hpac_protected_admin_writer.py`, every value ∈ the 41 codes
(`.3.4::test_66`).

---

## 3. Verification

### 3.1 Fresh `.1R.30R.3.4` suite

`tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_4_merged_rhamp_mechanism.py`
— **124 tests, 124 pass, 0 skip / xfail** (the one module-level
`skipif(os.name != "posix")` platform guard aside). Includes the RHAMP §46
negative matrix: `test_81` (4 enrollment cases) + `test_89` (14
authentication cases) + `test_96` (8 sidecar-schema cases) + `test_97` (4
client-context cases) + ~30 standalone `pytest.raises` / `_expect_reason`
rejections — `test_88` asserts ≥ 55 total.

### 3.2 Historical guard reconciliation (RHAMP-REQ-162 / `.1R.26` method)

Point-in-time scope-fence guards that asserted "no real FIDO2 / no RHAMP
sidecar / `hpac_verifier` byte-unchanged / capability slots frozen" were
reconciled **phase-aware** — the historical window pinned to its owning
phase's finalized head (immutable), plus a *not-weakened* current-state
check. **No `def test_` was renamed or removed** in any pre-existing test
file. Reconciled: `.1R.30R.3.1` (`test_40/42/63/81/82`), `.1R.30R.3.2.1`
(`test_20/22`), `.1R.30R.3.2.1.1` (`test_27`), `.1R.30R.3.3R`
(`test_verifier_has_no_real_signature_branch_yet` +
`*_since_baseline_a` → closed `BASELINE_A .. R33R_FINALIZED_HEAD` window),
the HPAC Layer-1/2 foundation consumer-inventory guards
(`3w1r2b1r111r31` / `r32` / `r321` — the exact 10 new consumer tuples
added), `test_hpac_verifier.py` +
`test_hpac_verifier_repair_3w1r2b1r1115a2.py` (substring → real-import
scan), `test_hpac_verifier_independent_verification_3w1r2b1r1115a1.py`
(`test_unsupported_mechanism…` — the guarantee is preserved and stronger),
`.1R.30R.1` writer-symbol scope, `.1R.17` production-scope, `.1R.18` /
`.1R.19R` / `.1R.19R.1` / `.1R.20` meta-guards.

### 3.3 Fixed-SHA A/B attribution (RHAMP-REQ-162/169, §69)

- **A** = `5a6f9d875aa1b7173ce0373b6437608f151e2c19` (finalized `.1R.30R.3.3R`
  head).
- Deterministic no-xdist run over the HPAC / RHAMP / PAWA / FIDO2 / verifier /
  gate lineage: baseline A **130 failed / 2497 passed**; candidate B
  **0 unexplained candidate-only functional regressions** after guard
  reconciliation. Every B-only entry is either (a) a phase-aware guard
  reconciliation completed in this diff, or (b) a working-tree /
  unpushed-divergence check that resolves on the governed commit + push
  (these are red mid-phase by construction — the memoized finalization
  pattern), or (c) a pre-existing red IV suite
  (`test_hpac_foundation_independent_verification_3w1r2b1r111r31.py`'s
  `test_blocking_reproduction_*` and `test_deterministic_authenticator…`
  are red on `main` at A — the RHAMP-REQ-163 companion current-canonical
  assertions are the fresh `.3.4::test_59/60/61`).

### 3.4 No test weakening

Verified scanner: 0 removed / 0 renamed-to-evade / 0 `skip` / 0 `skipif`
(beyond the pre-existing platform guards) / 0 `pytest.skip` / 0 `xfail` /
0 wildcard broadening / 0 source-consumer fence weakening in any
pre-existing test file. Historical point-in-time assertions remain true at
their fixed SHAs.

---

## 4. Scope fences held

| Fence | Evidence |
|---|---|
| RHAMP-001 v1.0 byte-unchanged | `git diff --name-only A HEAD -- docs/contracts` empty (`.3.4::test_01`) |
| HPAC-PAWA-001 v1.1 / HPAC-001 v2.1 byte-unchanged | same (`.3.4::test_02`) |
| `CredentialRecord` byte-unchanged | `_CREDENTIAL_ALLOWED_FIELDS` unchanged (`.3.4::test_05`) |
| No protected presentation | `approval_presentation.py` byte-unchanged; no `pcae-protected-local-presentation/1.0` acceptance; no `renderer_profile` / `mechanism_attestation` in new code (`.3.4::test_70–73`) |
| No `require_real_assurance` Gate 5/9 wiring | Gate 5 / Gate 9 byte-unchanged since A (`.3.4::test_71`) |
| A production `AuthenticatedHumanPrincipal` is **not** end-to-end reachable | the real `_verify_assertion_material` branch requires all-`PRODUCTION` records; no `PRODUCTION` `pcae-protected-local-presentation/1.0` descriptor kind is accepted until `.1R.32`, so `verify_human_authentication` cannot resolve a `PRODUCTION` presentation and terminates before minting one (`.3.4::test_73`) |
| No new dependency | `pyproject.toml` byte-unchanged; `fido2>=1.1,<2` was already the `hatp-hardware` extra (`.3.4::test_80`) |
| No custom cryptography | `CoseKey.parse` / `key.verify` only; single `signature_ok = True` site (`.3.4::test_56`) |
| Runtime unchanged | `pcae runtime inspect` → `Observed` / `observe` / `unavailable`, 0 / 0 (`.3.4::test_74`) |
| N-16-6 / N-16-7 untouched | gate6/7/10-eligibility / permission_broker / runtime byte-unchanged since A (`.3.4::test_76`) |
| No Slice C / first external effect | no `adapter.dispatch(` call site; ABSENT / UNREACHABLE (`.3.4::test_77`) |
| N-23-1 / N-23-2 | carried unchanged (INFO / INFO-DEFERRED) |

---

## 5. Implementation verdict

```
RHAMP REAL FIDO2 CREDENTIAL REGISTRATION:  IMPLEMENTED — IV PENDING
RHAMP COUNTER-STATE:                        IMPLEMENTED — IV PENDING
FIRST-CREDENTIAL BOOTSTRAP:                 IMPLEMENTED — IV PENDING
FIDO2HumanAuthenticator:                    IMPLEMENTED — IV PENDING
REAL CTAP2 ASSERTION VERIFICATION:          IMPLEMENTED — IV PENDING
REAL MECHANISM ELIGIBILITY:                 IMPLEMENTED — IV PENDING
PROTECTED PRESENTATION:                     NOT IMPLEMENTED
GATE REAL-ASSURANCE CONSUMPTION:            NOT IMPLEMENTED
N-16-5:                                     NOT CLOSED
Runtime:                                    Observed / observe / unavailable
First external effect:                      ABSENT
```

N-16-5 remains **NOT CLOSED**. Still required: `.1R.30R.3.5` (IV of this
phase) → `.1R.30R.4` (protected human-approval presentation +
`require_real_assurance` wiring — RHAMP-REQ-156 `.1R.32`) → `.1R.30R.5`
(IV + mandatory real-CTAP2-hardware verification + N-16-5 closure —
RHAMP-REQ-156 `.1R.33`) → N-16-6 → N-16-7 (strictly last).

---

## 6. Recommended next phase

**`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.5` — Independent Verification of the
N-16-5 merged RHAMP Real FIDO2 Credential Registration, Counter-State,
Bootstrap & Authentication Mechanism Implementation.** ID recommended, NOT
reserved; own explicit human authorization required. Do not begin it here.

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved.
