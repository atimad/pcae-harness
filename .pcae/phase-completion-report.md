# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.28 Complete — N-16-5 Real FIDO2/WebAuthn/CTAP and Protected Human-Approval UI Architecture and Contract Planning

**Phase ID:** 149O.20L.7O.3W.1R.2B.1R.1.1R.28
**Type:** planning / primary-source analysis / contract-impact analysis / threat-modeling / decision-freezing only
**Status:** N-16-5 ARCHITECTURE / CONTRACT PLAN COMPLETE — IMPLEMENTATION NOT BEGUN — REAL HUMAN AUTHENTICATION + PROTECTED HUMAN APPROVAL UI + REAL APPROVAL PROOF: ARCHITECTURE FROZEN FROM PRIMARY SOURCE
**Phase-entry SHA:** `9901e546` (`origin/main` synced; `origin/main..HEAD = 0` at entry)
**Production source changed:** none (`git diff --name-only 9901e546 HEAD -- src/pcae` empty; the deterministic NON_REAL `human_authenticator` / protected-presentation doubles are byte-identical)
**Normative contracts changed:** none (`git diff --name-only 9901e546 HEAD -- docs/contracts` empty)
**Runtime:** `not_implemented / Observed / observe / unavailable`; 0 plugins / 0 capabilities; FIRST EXTERNAL EFFECT ABSENT; execution NOT enabled

## Summary

Planning / primary-source analysis / contract-impact analysis / threat-modeling / decision-freezing only. Re-derived N-16-5 from primary source (HPAC-001 v2.1 all 44 sections / HPAC-REQ-001..105 **read in full**; RIHAC-001 v2.0 §3/§5/§12/§16 incl. condition 7; RIASC-001 v3.0 §2/§3; RDGO-001 v3.1 §4/§6/§10/§11; REPRC-001 v1.0 companion-contract precedent; the HATP contract family and `hatp_fido2_provider.py` (528 lines) / `hatp_providers.py` **read**; `src/pcae/core/` `human_authenticator.py` + `human_authenticator_deterministic.py` + `human_principal_registry.py` (577 lines) + `approval_presentation.py` + `approval_presentation_deterministic.py` + `hpac_verifier.py` (746 lines) + `hpac_foundation.py` + `hpac_lifecycle.py` + `human_authentication_proof.py` + `runtime_dispatch_gate5.py` + `runtime_authority.py` **read**; `pyproject.toml` (`fido2>=1.1,<2` + `cryptography>=42,<45`); `.1R.16` §35 row 15 = the N-16-5 mandate; `.1R.15.1` §21; `.1R.2A` / `.1R.2B`; the `.1R.3`..`.1R.20` HPAC-foundation + gate lineage; `.1R.24` planning-phase structure), not from phase summaries.

**Central finding (frozen).** The architecture and the wire/store schemas for real human-principal authentication and protected approval presentation are **already frozen** — HPAC-001 v2.1 comprehensively (mechanism descriptor `hpac.fido2.uv_presence.v2`; `HPAC-CHALLENGE/2.0`; `HPAC-PROOF/2.0`; `HPAC-PRESENTATION-EVIDENCE/2.0`; `HPAC-PROOF-LIFECYCLE-EVENT/2.0`; `HPAC-AUTHORITY-CONSUMPTION/2.1`; the UP+UV floor; the `PRINCIPAL_VERIFIED_INTENT` minimum; the protected root; the external deployment-owner bootstrap anchor; domain separation from HATP; NON_REAL non-upgradeability), RIHAC-001 v2.0 §12 condition 7 / §16, RIASC-001 v3.0 — and the mechanism-neutral consumption path (`HumanPrincipalRegistryStore`, `hpac_verifier`, the proof lifecycle, `TrustedApprovalPresentationStore`, Gates 5/6/7/8/9/10) is **already implemented** against deterministic NON_REAL doubles. `fido2>=1.1,<2` is already a project dependency and `hatp_fido2_provider.py` is a working **real CTAP2 primitive** whose reuse HPAC-REQ-019 / §32 explicitly authorizes. **N-16-5 `.1R.28` is therefore a contract-sufficiency confirmation + residual-decision freeze + implementation-decomposition phase, not a fresh-architecture phase** — directly analogous to the N-16-4 `.1R.24` central finding.

## Frozen architecture

- **Real mechanism (§7, §8):** **native CTAP2 roaming hardware FIDO2** (`hpac.fido2.uv_presence.v2`) — OS-neutral, fully offline, **no browser, no WebAuthn ceremony, no web origin, no TLS, no loopback socket, no port**. The RP/origin/HTTPS/ephemeral-port questions in the phase prompt (§25, §58, §59, §85–§87) are **MOOT**. Options A (browser WebAuthn), C (OS platform APIs), and the remote-broker half of D are **rejected explicitly**.
- **RP / origin (§9):** fixed internal constants — `rpId = "hpac.pcae.local"`, client `origin = "pcae-hpac://hpac.pcae.local/runtime-invocation-approval.v2"` — distinct from HATP's `hatp.pcae.local` (HPAC-REQ-047/084). A constant string, not a hostname → **no Mac/Dell cross-trust-domain problem**, **no human environment adjudication**, exactly the `hatp_fido2_provider.py` precedent.
- **Protected presentation (§6, §21):** a **PCAE-owned, process-isolated local presentation helper** — a distinct short-lived OS process (not the agent process), launched only by the administrator-installed mechanism under the protected root, that renders the closed `human_visible_facts` via a versioned deterministic `renderer_profile`, observes an explicit election, drives the CTAP2 touch, signs the `mechanism_attestation` under protected verifier configuration, and exits. `verifier_kind = "pcae-protected-local-presentation/1.0"`. Terminal stdout/stdin remains structurally ineligible (HPAC-REQ-090).
- **Authentication ≠ approval (§19, §20):** one CTAP2 ceremony over a challenge that includes the presentation digest, **plus** a distinct recorded `election` object — `hpac_verifier` steps 5 (presentation) and 6 (signature) are independent; a blind touch with no resolved `HPAC-REQ-091` evidence is rejected.
- **UP / UV (§17):** both mandatory (HPAC-REQ-042/060); `hpac_verifier._check_up_uv` already rejects unless `up is True and uv is True`; UV is satisfied inside the authenticator (PIN/biometric) and PCAE never sees it. `hatp_fido2_provider` checks UP only — HPAC's real mechanism adds the `FLAG.UV` check itself (finding N-16-5-3).
- **Attestation (§14):** **none required** — self/none accepted, enterprise prohibited, no MDS, no device-uniqueness claim (mirrors `hatp_fido2_provider` `attestation_valid=None` non-blocking). Maximal privacy, no device fingerprint retained.
- **Credentials (§10, §13):** non-discoverable / `allowList`-bound; no resident credentials; no usernameless auth in v1 (the `hatp_fido2_provider.py:439` pattern). 1 principal → 0..N credentials (HPAC-REQ-030). Rotation = enroll + revoke (HPAC-REQ-031). No private-key field exists on `CredentialRecord` (structural).
- **Transports (§12):** USB-HID primary, NFC permitted; **no BLE, no hybrid/caBLE/cross-device** (would break the local protected-approval assumption).
- **TTL bounds (§12, §16):** challenge TTL ≤ 120 s; `max_proof_age_seconds` ≤ 300 s; presentation `expires_at` == the RIASC approval `expires_at`. Resolves HPAC-REQ-050's explicit deferral of the numeric bound.
- **Signature counter (§23):** recorded in a **new protected per-credential counter-state artifact** under `HPAC_PROTECTED_ROOT`; `0`/absent → accept; a nonzero regression → **fail closed** (`signature_counter_regression`) + audit + admin review. Not a `CredentialRecord` schema change.
- **Failure taxonomy (§18):** a closed 25-code `terminal_reason_code` vocabulary, derived from the actual rejection points in `hpac_verifier` / `approval_presentation` / `hpac_lifecycle`.
- **Bootstrap / revocation / recovery (§11, §24):** **already frozen** (HPAC-REQ-023 external deployment-owner anchor — not "first to register"; HPAC-REQ-061..065 monotonic revocation + repeat-bootstrap recovery). No new decision.
- **Generation / currentness (§24):** **reuse the existing mechanism** — the five `HPAC-AUTHORITY-GENERATION-SNAPSHOT/1.0` markers (HPAC-REQ-098a). No parallel freshness system.
- **NON_REAL non-upgradeability (§26):** preserved **structurally** — `SIMULATION_ONLY: Final[bool]`, `hpac_verifier._ELIGIBLE_MECHANISM_IDS`, `HPACAuthorityClass` propagation, the `require_real_assurance` gate, the `is_verifier_authenticated_principal` identity registry, `AuthenticatedHumanPrincipal.__reduce__` raising.

## Deployment topology (decisive; frozen safe assumption — not BLOCKED)

**N-16-5's first real profile requires the protected approval presentation and the CTAP2 authentication touch to occur locally, in an interactive session, on the authority-owning control-plane host, with a directly-attached USB CTAP2 hardware key** (derivable from HPAC-REQ-021/022/082/083; the `rpId` is a constant string identical on Mac and Dell). If the deployment host is headless with no attached key, **remote / networked approval is explicitly OUT OF SCOPE for N-16-5 and DEFERRED** to a separate, separately-authorized architecture (which MAY reuse the patterns in `HATP_REMOTE_ASSERTION_CEREMONY_CONTRACT.md` / `HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md` — remote assertion is a distinct capability HATP already governs separately). It is **not** smuggled into N-16-5. HPAC-001 v2.1 already froze a bounded local model, so a safe assumption **can** be frozen → **no BLOCKED condition applies**.

## Contract ownership and versioning

**Frozen: a new companion contract `RHAMP-001` v1.0** (Real Human Authentication Mechanism & Protected Presentation Profile) — directly analogous to how REPRC-001 v1.0 was born for N-16-4 — freezing the residual decisions (real `mechanism_id` allowlist; `verifier_kind` allowlist + presentation-helper integrity obligations; the `rpId`/origin constants; the attestation policy; the discoverable-credential / attachment / transport profile; the TTL bounds; the signature-counter policy + counter-state artifact; the `terminal_reason_code` vocabulary; the deployment-topology prerequisite) as a **profile under HPAC-001 v2.1's existing extension points** (`mechanism_id` allowlist, `verifier_kind` closed set, `terminal_reason_code` IDs, TTL "a future implementation phase sets it", attestation silent).

**No HPAC-001 bump. No MAJOR bump. No MINOR bump to any existing contract.** HPAC-001 v2.1, RIHAC-001 v2.0, RIASC-001 v3.0, HPSE-001 v1.1, PBRD-001 v3.0, PBNDE-001 v1.0, RDGO-001 v3.1, RPAC-001 v1.0, REPRC-001 v1.0, the RE No-Go Registry, and every HATP contract are byte-unchanged. The versioning matrix reads each contract's own rules first (HPAC-001 §37 MINOR criteria; REPRC-001's initial-freeze / PBNDE-001 companion precedent) — deliberately avoiding a cross-contract reference cascade (RIHAC-001 §12 condition 7 names "HPAC-001 v2.1" literally).

## Production positive path after N-16-5 alone: NONE

After N-16-5 closes, real human authority becomes **satisfiable** (RIHAC-001 §12 condition 7 can pass with a real UV+UP+presentation proof of class `PRODUCTION`). But: **Gate 6 (PB) still blocks** — N-16-6's RPAC-REQ-095 adapter + supply-chain admission is NOT SATISFIED, so no adapter is admissible; **production Gate 7 still DENYs** — N-16-4 shipped the positive branch as a `pragma: no cover` test-seam only; **runtime stays `unavailable`** — N-16-7 is untouched and last; **Gate 10 / Slice C** — no `adapter.dispatch(` call site exists anywhere in `src/pcae`. **Production positive path after N-16-5 alone = NONE. The first external effect remains UNREACHABLE.**

## Non-blocking findings (feed the recommended contract-freeze phase)

- **N-16-5-1** — HPAC-001 is silent on attestation policy, defers challenge/proof TTL numbers, leaves `terminal_reason_code` unenumerated, and states no discoverable-credential / attachment / transport profile → RHAMP-001 v1.0 freezes all four as a profile under HPAC-001's existing extension points (no HPAC bump).
- **N-16-5-2** — `hpac_verifier._verify_assertion_material` does no real signature math and `_ELIGIBLE_MECHANISM_IDS` excludes every real mechanism → the implementation phase adds the real branch behind `_authority_class_of == PRODUCTION` + the real allowlist; IV proves a fixture-root credential cannot reach it.
- **N-16-5-3** — HATP's real CTAP2 provider checks UP but **not** UV (`hatp_fido2_provider.py:518`) → HPAC's real mechanism reuses only the CTAP2 transport + `CoseKey` verification primitives and adds `FLAG.UV` enforcement itself.
- **N-16-5-4** — sign-counter handling has no home in the frozen schemas (the registry is create/append-only for revocation only) → RHAMP-001 §9 defines a **new** protected per-credential counter-state artifact under `HPAC_PROTECTED_ROOT`.
- **N-16-5-5** (deployment) — a headless deployment host with no attached key → the frozen safe assumption (local interactive control-plane host + attached USB key) + an explicit deferral of remote approval — **not** N-16-5, **not** BLOCKED.
- **N-16-5-6** (observation) — `.1R.16` §35 row 15's "PBRD §12 item 3" label predates PBRD-001 v3.0 → frame N-16-5 as "a real `hpac.fido2.uv_presence.v2` mechanism + real protected presentation satisfying HPAC-001 v2.1 §14/§18/§39 with `PRINCIPAL_VERIFIED_INTENT` / `PRODUCTION` assurance".

**No new blocker. N-16-3 and N-16-4 are CLOSED and not reopened. N-23-2 carried (INFO / DEFERRED); N-23-1 carried.**

## Implementation decomposition (frozen; IDs recommended, NOT reserved)

1. **`.1R.29`** — **RHAMP-001 v1.0 companion contract freeze** (no `src/pcae` change, no HPAC bump, no implementation, no hardware).
2. **`.1R.30`** — real FIDO2 authentication mechanism + registry production writer + bootstrap ceremony (`FIDO2HumanAuthenticator`; real signature verification in `hpac_verifier` via `CoseKey.verify` + `rp_id_hash` + origin + `FLAG.UV`; `_ELIGIBLE_MECHANISM_IDS` widened by exactly `{hpac.fido2.uv_presence.v2}`; production registry path; protected-admin enrollment + first-credential bootstrap tool; the counter-state artifact; `terminal_reason_code` wiring; reuse `hatp_fido2_provider` CTAP2 primitives as a shared library).
3. **`.1R.31`** — Independent Verification of `.1R.30`.
4. **`.1R.32`** — real protected approval presentation mechanism (`verifier_kind = "pcae-protected-local-presentation/1.0"`; process-isolated helper; deterministic `renderer_profile`; real `mechanism_attestation`; administrator-installed `PRODUCTION` descriptor) + wire `require_real_assurance=True` through Gate 5 / Gate 9; a production `AuthenticatedHumanPrincipal` of class `PRODUCTION` becomes obtainable for exactly one approval.
5. **`.1R.33`** — Independent Verification of `.1R.32` + N-16-5 closure, including a **mandatory** real-CTAP2-hardware manual verification (kept out of `.1R.28`).

Then N-16-6 → N-16-7 (strictly last). Slice C (first concrete effect adapter) and Slice D (end-to-end IV) keep **no phase ID** until N-16-3..7 all independently close. The ≥ 55-case defensive test matrix (canonical doc §36), the frozen IV requirements (§29), and the predicted guard-impact inventory (§37) are specifications for those phases, not tests authored now.

## Whole-system authority chain (post-N-16-5)

registered principal credential (durable record; not authority) → real CTAP2 ceremony UP+UV (fresh assertion; not approval) → `hpac_verifier` §18 real signature verify (ephemeral `AuthenticatedHumanPrincipal`, `PRODUCTION` / `PRINCIPAL_VERIFIED_INTENT`; evidence only) → protected presentation + explicit election (`TrustedApprovalPresentationEvidence`; informed intent) → RIHAC-001 §16 (`RuntimeInvocationApproval`; approval authority) → Gate 5 (revalidates; binds `PROOF_VERIFIED_AND_BOUND`; emits RIHAC projection) → **Gate 6 PB (STILL BLOCKS — no admissible adapter until N-16-6)** → **Gate 7 (production still DENYs)** → Gate 8 → Gate 9 atomic consumption (one-shot `consumption.json`) → Gate 10 pre-effect eligibility (18-step battery; re-reads current generation state) → Slice B → **runtime capability (STILL unavailable — N-16-7)** → Slice C first concrete effect adapter (NO phase ID). The authentication stage is **never** labelled approval authority.

## Governance

- `pcae health` healthy · `pcae check` passed · `pcae status coherence` coherent · `pcae push check` `nothing_to_push` (pre-push) · `pcae doctor task-memory` warning-only historical `DONE.md` omissions (pre-existing hygiene debt; no current-phase error) · `pcae runtime inspect` `not_implemented / Observed / observe / unavailable`, 0/0.
- **DELEGATED `.3` FINALIZATION / COMMIT / PUSH: UNAUTHORIZED** — preserved. Only the primary human-authorized operator holds `.1R.28` lifecycle authority. Governed `pcae` lifecycle only — no raw `git commit`/`git push`, no `--no-verify`, no force push, no history rewrite, no hook bypass.
- No STOP / BLOCKED condition reached — every valid early-STOP condition in the phase prompt was checked (canonical doc §30) and none applies.

## Verdict

**N-16-5 REAL FIDO2/WEBAUTHN/CTAP AND PROTECTED HUMAN-APPROVAL UI ARCHITECTURE AND CONTRACT PLAN COMPLETE — PLANNING ONLY.** N-16-5 NOT implemented; the deterministic NON_REAL human-authentication and protected-presentation path is unchanged; FIRST EXTERNAL EFFECT still ABSENT; execution NOT enabled.

- **REAL HUMAN AUTHENTICATION: ARCHITECTURE FROZEN — IMPLEMENTATION NOT BEGUN.**
- **PROTECTED HUMAN APPROVAL UI: ARCHITECTURE FROZEN — IMPLEMENTATION NOT BEGUN.**
- **REAL APPROVAL PROOF: ARCHITECTURE FROZEN — IMPLEMENTATION NOT BEGUN.**

**Runtime: Observed / observe / unavailable. First external effect: ABSENT. Execution enabled: NO.**

## Recommended next phase

`149O.20L.7O.3W.1R.2B.1R.1.1R.29` — **N-16-5 Real Human Authentication Mechanism & Protected Presentation Profile Contract Freeze (RHAMP-001 v1.0)** → then `.1R.30` (implementation) → `.1R.31` (IV) → `.1R.32` (protected presentation + real-assurance wiring) → `.1R.33` (IV + N-16-5 closure incl. mandatory real-hardware verification). Each requires its own separate explicit human authorization; IDs recommended, NOT reserved. **Do not begin `.1R.29`.** Do not implement N-16-5. Do not modify `src/pcae`. Do not modify normative contracts. Do not implement real FIDO2/WebAuthn/CTAP. Do not implement the protected UI. Do not begin N-16-6..7. Do not begin Slice C. Do not implement or call the first external effect. Do not enable execution.

See `docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_28_N_16_5_REAL_FIDO2_WEBAUTHN_CTAP_AND_PROTECTED_HUMAN_APPROVAL_UI_ARCHITECTURE_AND_CONTRACT_PLANNING.md`.
