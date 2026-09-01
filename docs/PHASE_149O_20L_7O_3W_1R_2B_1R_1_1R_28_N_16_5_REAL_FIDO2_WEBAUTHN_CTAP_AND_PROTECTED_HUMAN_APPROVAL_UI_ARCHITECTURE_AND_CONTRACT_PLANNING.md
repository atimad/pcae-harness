# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.28 — N-16-5 Real FIDO2/WebAuthn/CTAP and Protected Human-Approval UI Architecture and Contract Planning

**Status: PLANNING COMPLETE — ARCHITECTURE FROZEN FROM PRIMARY SOURCE — IMPLEMENTATION NOT BEGUN.**
**Phase type:** governed planning / primary-source analysis / contract-architecture. No `src/pcae/**`
change, no normative-contract change, no schema package, no CLI, no hardware access, no credential
creation, no runtime capability change, no external effect.
**Phase-entry SHA:** `9901e546` (HEAD at authorization; `git rev-list --count origin/main..HEAD` = 0).
**Authorizing operator:** primary human-authorized operator (this phase's own explicit authorization;
phase ID recommended, NOT reserved).
**Runtime:** `not_implemented` / `Observed` / `observe` / `unavailable`. **First external effect: ABSENT.**

---

## 0. Governing prerequisite state (phase prompt §1), treated as current

| Item | State |
|---|---|
| N-16-3 | **CLOSED** (`.1R.23` IV) — not reopened |
| N-16-4 | **CLOSED** (`.1R.27R` IV, non-blocking findings) — not reopened |
| N-16-5 | **OPEN** — this phase plans it |
| N-16-6 | **OPEN** — not begun |
| N-16-7 | **OPEN** — strictly last; not begun |
| Gate 5 / 6 / 7 / 8 / 9 | CLOSED (coordinator-integrated `.1R.10`–`.1R.15`) |
| Gate 10 pre-effect | structurally closed (`.1R.17`/`.1R.18`); Slice A CLOSED; Slice B CLOSED (`.1R.19R`/`.1R.20`) |
| Runtime | Observed / observe / unavailable; 0 plugins / 0 capabilities |
| First external effect | ABSENT — no `adapter.dispatch(` call site exists in `src/pcae/**` |
| Current human-auth path | deterministic / NON_REAL (`human_authenticator_deterministic.py`), real-authority-ineligible |
| Current protected presentation | NON_REAL (`approval_presentation.py` `verifier_kind == "deterministic-test-fixture"`), real-authority-ineligible |

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved (§34).

---

## 1. Primary sources inspected (phase prompt §3, §78, §99 step 2)

**Contracts (normative, read in full or complete relevant scope):**
`HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md` (**HPAC-001 v2.1**, all 44 sections / HPAC-REQ-001..105);
`RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md` (**RIHAC-001 v2.0**, §3/§5/§12/§14/§16);
`RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md` (**RIASC-001 v3.0**, §2/§3, five-member `subject`,
`approval_scope`, `approval_mechanism` const `trusted_subject_bound_confirmation`);
`HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md` (**HPSE-001 v1.1** — pattern precedent only, per HPAC §6);
`RUNTIME_ENFORCEMENT_POSITIVE_RESULT_CONTRACT.md` (**REPRC-001 v1.0** — companion-contract precedent);
`RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md` (**RDGO-001 v3.1**, §4/§6/§10/§11 — gate 5 / gate 9 timing);
`PERMISSION_BROKER_*` (PBRD-001 v3.0 — no HPAC coupling), `RUNTIME_PROVIDER_ADAPTER_CONTRACT.md`
(**RPAC-001 v1.0**, RPAC-REQ-049/054/084/086/095 — N-16-6 territory, provider-neutral);
the HATP family (`HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md`,
`HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md`, `HATP_REMOTE_ASSERTION_CEREMONY_CONTRACT.md`,
`HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md`, `HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md`,
`HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`) — **separate trust domain**, terminology/pattern precedent (HPAC §6/§31).

**Phase reports:** `PROJECT_STATUS.md` (Current Phase `.1R.27R`); `.1R.27R`, `.1R.26`, `.1R.25`, `.1R.24`
(N-16-4 lineage — planning-phase template); `.1R.16` (Gate-10 architecture; prerequisite ordering, §35
row 15 = the N-16-5 mandate row); `.1R.15.1` §21 (real-authority constraint); `.1R.2A`
(`...RUNTIME_INVOCATION_HUMAN_PRINCIPAL_AUTHENTICATION_AUTHORITY_PROVENANCE_ARCHITECTURE.md`, §29–§70 —
architecture HPAC-001 formalizes); `.1R.2B` (HPAC-001 freeze report); the HPAC-foundation lineage
`.1R.3` / `.1R.3.2` / `.1R.3.2.1` / `.1R.3.2.2` / `.1R.3.2.2.1` (trust root, writer provenance, store
containment, presentation attestation schema), `.1R.4` / `.1R.5` / `.1R.5.1` / `.1R.5.2` / `.1R.5.2.1`
(mechanism-neutral verifier, `AuthenticatedHumanPrincipal` trusted construction), `.1R.6` / `.1R.7` /
`.1R.8` (B1–B7/N1/N2 production authority repair), `.1R.9` (Gate 5 / Gate 9 coordinator planning).

**Production source (read):** `src/pcae/core/human_authenticator.py` (interface + descriptor models);
`human_authenticator_deterministic.py` (`DeterministicTestHumanAuthenticator`, `SIMULATION_ONLY=True`,
`MECHANISM_ID = "hpac.deterministic.test-only.v1"`); `human_principal_registry.py`
(`HumanPrincipalRegistryStore`, `PrincipalRecord` / `CredentialRecord`, `.production()` vs
`HPACStoreAuthority.fixture()`); `approval_presentation.py`
(`CanonicalRuntimeApprovalSubject`, `PresentationMechanismDescriptor`,
`ProtectedApprovalPresentationMechanism` `Protocol`, `TrustedApprovalPresentationStore`,
`verifier_kind == "deterministic-test-fixture"` is the sole accepted kind);
`approval_presentation_deterministic.py` (`DeterministicTestPresentationMechanism`, adversarial faults);
`hpac_verifier.py` (`verify_human_authentication` — full HPAC-REQ-054 sequence,
`_ELIGIBLE_MECHANISM_IDS = {"hpac.deterministic.test-only.v1"}`, `_verify_assertion_material` does **no**
real signature math, `is_verifier_authenticated_principal` identity-registry trust boundary,
`require_real_assurance` "can currently only ever reject"); `hpac_foundation.py` (`HPACStoreAuthority`,
`HPACWriterCapability`, `ProtectedAdminCapability`, `HPACAuthorityClass.{PRODUCTION,FIXTURE_NON_REAL}`);
`hpac_lifecycle.py` (hash-chained `HumanAuthenticationProofLifecycleEvent`, `bind_gate5_canonical`);
`human_authentication_proof.py` (`HPAC-PROOF/2.0` store); `human_approval_trusted_provenance.py`;
`runtime_dispatch_gate5.py` (inherits the NON_REAL hard stop; no production `AuthenticatedHumanPrincipal`
can carry `PRODUCTION` assurance today); `runtime_authority.py` (§424/§1111 interim production hard stop
frozen by `.1R.6` §8); `hatp_fido2_provider.py` (**real CTAP2** `Fido2HardwareProvider`: `make_credential`
enrollment, `get_assertion` signing, `CoseKey`/`AuthenticatorData`/`CollectedClientData` verification,
fixed `_HATP_RP_ID = "hatp.pcae.local"` / `_HATP_ORIGIN = "pcae-hatp://hatp.pcae.local"`,
`attestation_valid=None` non-blocking, `is_user_present()` UP-only); `hatp_providers.py`
(`HardwareProviderCapabilities`, `_PRODUCTION_HARDWARE_PROVIDER_PROFILES`, lazy `fido2` import).
`pyproject.toml` — `fido2>=1.1,<2` + `cryptography>=42,<45` already declared (the `hatp-hardware` extra).

No design was taken from phase reports alone; every load-bearing claim is anchored to a contract
requirement ID or a named production symbol.

---

## 2. Core semantic walls preserved (phase prompt §2)

Every wall below is reproduced verbatim from **HPAC-001 §0 (HPAC-REQ-001)** — it is already normative
contract text, and N-16-5 changes none of it:

```
authenticated human principal != confirmation        confirmation           != approval
credential authentication      != user presence       approval               != PB permission
user presence                  != user verification   PB permission          != runtime capability
user verification              != informed approval   runtime capability     != execution
human principal                != agent identity      FIDO2/WebAuthn assertion != approval
human principal                != OS username         protected presentation != approval
human principal                != Git identity        approval proof         != bearer authority
human principal                != session agent id    valid cryptography     != trusted canonical lifecycle
NON_REAL proof                 != real authentication  real authentication    != permission to dispatch
credential possession          != authorization for this exact effect
```

These are enforced **structurally** in the current code (not merely documented): `SIMULATION_ONLY:
Final[bool]`, a mechanism-id constant outside every real allowlist, `HPACAuthorityClass` propagation,
`_ELIGIBLE_MECHANISM_IDS`, the `is_verifier_authenticated_principal` identity registry, and
`AuthenticatedHumanPrincipal.__reduce__` raising. N-16-5 must **extend** these structural walls to the
real mechanism, never relax them.

---

## 3. Exact N-16-5 mandate, re-derived in normative form (phase prompt §5, §99 step 3)

From `.1R.16` §35 **row 15**: *"Real FIDO2 / WebAuthn / CTAP + protected human-approval UI (PBRD §12
item 3) — NOT SATISFIED"* (evidence: `.1R.15.1` §21; RPAC-REQ-084). From `.1R.15.1` §21: *"Real FIDO2 /
WebAuthn / CTAP is not implemented. A protected human-approval UI is not implemented."* From the
frozen prerequisite ordering (`.1R.16` §48, `.1R.24` §48): **N-16-3 → N-16-4 → N-16-5 → N-16-6 →
N-16-7 (last); N-16-4 before N-16-5; Slice C/D no phase ID.**

**Normative N-16-5 mandate:**

> N-16-5 SHALL replace the deterministic NON_REAL `HumanAuthenticator` and the deterministic NON_REAL
> `ProtectedApprovalPresentationMechanism` with a real, hardware-backed FIDO2/CTAP2 authentication
> mechanism and a real protected approval-presentation mechanism, such that a completed ceremony
> produces a `HumanAuthenticationProof` (`HPAC-PROOF/2.0`) and `TrustedApprovalPresentationEvidence`
> (`HPAC-PRESENTATION-EVIDENCE/2.0`) that pass `hpac_verifier.verify_human_authentication` with
> `require_real_assurance=True` and yield an `AuthenticatedHumanPrincipal` of
> `HPACAuthorityClass.PRODUCTION` and assurance `PRINCIPAL_VERIFIED_INTENT` for **one** exact governed
> runtime-invocation approval — while preserving every §2 wall and every separation between
> authentication, presence, verification, informed intent, approval, PB permission, Runtime
> Enforcement, runtime capability, and execution.
>
> N-16-5 SHALL NOT enable any production positive path to a first external effect on its own; after
> N-16-5 closes, the first external effect SHALL remain unreachable (N-16-6 admission and N-16-7
> capability enablement independently block it).

**Central finding (analogous to N-16-4's):** the architecture and the wire/store schemas for real
human-principal authentication and protected approval presentation are **already frozen** — HPAC-001
v2.1 (comprehensively), RIHAC-001 v2.0 §12 condition 7 / §16, RIASC-001 v3.0 — and the entire
mechanism-neutral consumption path (registry, verifier, proof lifecycle, presentation store, Gates
5/6/7/8/9/10) is **already implemented** against NON_REAL doubles. `fido2>=1.1,<2` is already a
project dependency and `hatp_fido2_provider.py` is already a working real CTAP2 primitive whose reuse
HPAC-REQ-019 / §32 explicitly authorizes. **N-16-5 `.1R.28` is therefore a contract-sufficiency
confirmation + residual-decision freeze + implementation-decomposition phase, not a fresh-architecture
phase.** The residual work is enumerated in §12; it is bounded and freezable, so **no BLOCKED
condition applies** (§30).

---

## 4. Current `HumanPrincipalRegistry` assessment (phase prompt §6)

Reconstructed from `human_principal_registry.py` + HPAC-001 §4–§9.

| Field / property | Meaning | Authority owner | Mutable? | Persistent? | Canonical writer | Trusted reader | Mechanism-neutral? | Real-auth ready? |
|---|---|---|---|---|---|---|---|---|
| `principal_id` (`hp-<hex>`) | opaque, non-display, stable identity | HPAC-001 | no (immutable, never reused; HPAC-REQ-009/011) | yes (`principal-registry.json`) | `human_principal_registry_admin` writer role | any caller (read; HPAC-REQ-021) | yes | **schema yes / bootstrap NO** |
| `PrincipalRecord.status` | `{active, revoked}` monotonic | HPAC-001 §21 | append-only revoke | yes | writer role | verifier | yes | yes |
| `CredentialRecord.credential_id` (`hpc-<hex>`) | stable credential identity, 1 principal → 0..N credentials | HPAC-001 §9 | no (rotation = enroll+revoke, HPAC-REQ-031) | yes | writer role | verifier | yes | yes |
| `CredentialRecord.public_key` | public verification material only — **no private key / PIN / biometric field exists on the dataclass** | HPAC-001 §5 | no | yes | writer role | verifier | mechanism-shaped (COSE for FIDO2) | yes |
| `CredentialRecord.mechanism_id` | binds credential to one mechanism | HPAC-001 §5 | no | yes | writer role | verifier (`_verify_mechanism_eligibility`) | yes | yes |
| registry document | separate physical/logical doc from HATP `registry.json` (HPAC-REQ-018); deployment/user-scoped (HPAC-REQ-021) | HPAC-001 §6/§7 | atomic create/append-only, read-back verified (HPAC-REQ-015) | yes | `HPACStoreAuthority.production()` | canonical resolver | yes | **root resolver + provenance record exist; real ceremony deferred** |

**Assessment:** the registry model is **complete and real-auth-ready at the schema/store/authority
layer**. `HumanPrincipalRegistryStore.production()` exists; `HPACStoreAuthority` distinguishes
`production` from `FIXTURE_NON_REAL`; writes are atomic + read-back verified + writer-provenance
recorded; `principal_generation` / `credential_generation` markers (HPAC-REQ-098a) already fold
whole-record digests. **A real WebAuthn/FIDO2 credential maps to a principal without touching human
identity semantics:** `credential_id` is minted at enrollment (a fresh opaque `hpc-<hex>`, *not* the
raw CTAP2 credential id — the raw credential id and COSE public key are stored inside `public_key` /
an additive field, exactly as `hatp_fido2_provider.EnrolledFido2Credential` already separates
`credential_id_hex` from provider identity). The **only** gap is HPAC-REQ-023's real bootstrap
enrollment ceremony (external deployment-owner protected admin, non-defaultable, UP+UV, verified
`makeCredential` response) — **frozen in HPAC-001, not yet implemented**. No new registry decision is
required (§12 item 11).

---

## 5. Current `HumanAuthenticator` abstraction assessment (phase prompt §7)

Reconstructed from `human_authenticator.py` + `human_authenticator_deterministic.py` + HPAC-001 §10–§17.

| Concern | Current state | Real-mechanism seam |
|---|---|---|
| Interface | `HumanAuthenticator` `Protocol`: `describe` / `status` / `prepare_challenge(subject_digest, presentation_digest)` / `verify_response(challenge, response) -> ProofMaterial` / `resolve_principal` | already minimal + non-collapsible (HPAC-REQ-032); a real `FIDO2HumanAuthenticator` implements the identical `Protocol` |
| Challenge model | `Challenge` dataclass = HPAC-REQ-049's exact closed object (`domain_separator`, `challenge_version` const `HPAC-CHALLENGE/2.0`, `proof_schema_version` const `HPAC-PROOF/2.0`, `principal_id`, `credential_id`, `approval_subject_digest`, `trusted_presentation_digest`, `nonce`, `issued_at`, `expires_at`, `challenge_digest`) | unchanged; the real mechanism binds `challenge_digest` as the CTAP2 `getAssertion` challenge exactly as `hatp_fido2_provider._payload_digest` does |
| Mechanism id | `DETERMINISTIC_MECHANISM_ID = "hpac.deterministic.test-only.v1"` — structurally outside any real allowlist | real: `hpac.fido2.uv_presence.v2` (HPAC-REQ-039), added to `_ELIGIBLE_MECHANISM_IDS` in the implementation phase |
| UP representation | `ProofMaterial.up: bool` | real: `AuthenticatorData.is_user_present()` (`FLAG.UP`) — exactly `hatp_fido2_provider.py:518` |
| UV representation | `ProofMaterial.uv: bool` | real: `AuthenticatorData` `FLAG.UV` (`is_user_verified()`) — **HATP does not check UV; HPAC's real mechanism MUST** (HPAC-REQ-042) |
| Proof output | `ProofMaterial` (untrusted parsed) → canonical `HumanAuthenticationProof` (`HPAC-PROOF/2.0`) minted only after verifier step 2 succeeds | unchanged |
| Verifier input | `hpac_verifier._verify_assertion_material` — **currently categorically rejects every non-deterministic mechanism; no real signature math** | real: `CoseKey.parse(cbor.decode(credential.public_key)).verify(authenticatorData + client_param, signature)` — exactly `hatp_fido2_provider.Fido2HardwareProvider.verify` |
| NON_REAL hard-stop | `SIMULATION_ONLY`, `_ELIGIBLE_MECHANISM_IDS`, `require_real_assurance` gate, `HPACAuthorityClass` | preserved; the deterministic double stays a **test-only** authenticator forever |

**Assessment:** the abstraction **cleanly supports FIDO2/CTAP2**. No interface change is needed. The
implementation adds (a) a `FIDO2HumanAuthenticator` class, (b) real signature verification in
`hpac_verifier`, (c) `hpac.fido2.uv_presence.v2` to `_ELIGIBLE_MECHANISM_IDS`, (d) a UV check
alongside the existing UP check. No contract change is required for the abstraction itself.

---

## 6. Current protected-presentation assessment (phase prompt §8)

Reconstructed from `approval_presentation.py` + `approval_presentation_deterministic.py` + HPAC-001 §38–§39.

| Concern | Current state | Missing for a genuinely protected mechanism |
|---|---|---|
| What is presented | HPAC-REQ-091 closed `human_visible_facts` (13 fields: repository / task / target / operation-effect-scope / prompt / invocation displays + `expires_at` + `one_shot_notice`) | nothing missing in the **schema**; the real renderer must actually render these deterministically |
| Challenge binding | `approval_preview_digest == human_visible_representation_digest`; challenge carries `trusted_presentation_digest`; proof carries `trusted_presentation_ref` (id+digest pair) | unchanged |
| Content digest | `human_visible_representation_digest` = SHA-256 of exact displayed bytes (UTF-8 / NFC / LF) | a real `renderer_profile` that produces deterministic bytes a resolver can re-render and byte-compare |
| Approval-intent representation | closed `election` object (`event_id` `hpevt-<hex>`, `action` const `approve`, `occurred_at >= presented_at`) | a real mechanism that **observes** an explicit human election, not a parameter |
| Presentation attestation | `mechanism_attestation` over the closed `HPAC-PRESENTATION-ATTESTATION/2.0` object, verified under protected `verifier_configuration_digest` | a real `verifier_kind` + real protected verifier configuration + real attestation-signing |
| Verifier / consumer | `TrustedApprovalPresentationStore.resolve_canonical` → `hpac_verifier` step 5 → gate 5 / gate 9 | unchanged |
| Why NON_REAL | descriptor `verifier_kind == "deterministic-test-fixture"`, `verifier_configuration_digest == canonical_digest({"fixture": "deterministic"})`, resolution carries `FIXTURE_NON_REAL` | a real `verifier_kind` + a real, administrator-installed descriptor carrying `PRODUCTION` |
| Why terminal stdout is ineligible | HPAC-REQ-090: *"ordinary terminal stdout/stdin cannot truthfully satisfy `agent_substitution_resistant` and is ineligible"* | a real **process-isolated** presentation surface the requesting agent cannot substitute or observe |

**Assessment:** the **evidence schema, attestation model, digest-equivalence rule, election model,
store, and resolution chain are all frozen and implemented.** The residual is a real
`ProtectedApprovalPresentationMechanism` **implementation** — §12 item 2, the single genuine open
design question for N-16-5.

---

## 7. Real mechanism options (phase prompt §9) — comparison and selection

HPAC-001 §14 **already selected** hardware-backed FIDO2 CTAP2 (`hpac.fido2.uv_presence.v2`,
`offline_capable=true`, `platform_compat = macos, linux`, `presence_support=true`,
`verification_support=required`). This phase **confirms** that selection against the option set and
rejects the alternatives explicitly, because the phase prompt requires it.

| Option | Verdict | Rationale (primary-source anchored) |
|---|---|---|
| **A. WebAuthn platform authenticator via browser/native webview** | **REJECTED** | Requires a browser RP/origin/secure-context, a running desktop+browser on the authority host, and DOM/clickjacking/origin-confusion threat surface. HPAC-REQ-083 deliberately chose "no OS-specific adapter, no platform-specific presence API". A browser is not present on a headless deployment host (§27). |
| **B. Native FIDO2/CTAP2 library + roaming hardware security key** | **SELECTED** | Exactly HPAC-REQ-039/040/082/083. `fido2>=1.1,<2` already a dependency; `hatp_fido2_provider.py` already implements real CTAP2 `makeCredential` + `getAssertion` + `CoseKey` verification. OS-neutral (Mac dev + Linux deploy), fully offline, no browser, no web origin, no TLS. Phishing-resistant by construction (fixed internal RP ID; §11). |
| **C. OS platform APIs directly (Secure Enclave / TPM / Windows Hello)** | **REJECTED** | Non-portable across the Mac/Dell topology; requires a dual OS adapter surface HPAC-REQ-083 explicitly declined; platform authenticators are non-roaming, defeating the "human carries the key to the authority host" model (§27). MAY be added later as an additional `HumanAuthenticator` under HPAC-REQ-068 without lowering the floor. |
| **D. Hybrid: native local presentation helper + WebAuthn/FIDO2 broker** | **PARTIALLY ADOPTED** | The "native local presentation helper" half **is** the selected protected-presentation mechanism (§12 item 2). The "WebAuthn broker" half (a remote/networked assertion transport) is **rejected for N-16-5** and deferred — it overlaps HATP's own `HATP_REMOTE_ASSERTION_CEREMONY` / `HATP_REMOTE_WEBAUTHN_PROVIDER` contracts, which are a separate, separately-governed capability (§27). |
| **E. Another primary-source mechanism** | none identified | HPAC-REQ-066/067: no software-key, UP-only, OS-username, or ordinary-CLI mechanism qualifies for the first real-runtime profile. |

**Selected architecture:** **native CTAP2 roaming hardware FIDO2 key** for authentication +
**PCAE-owned process-isolated local presentation helper** for the protected approval presentation,
both executing **locally on the authority-owning control-plane host**.

---

## 8. FIDO2 / WebAuthn / CTAP role separation (phase prompt §10) — frozen terminology

The phase prompt title says "FIDO2/WebAuthn/CTAP"; the accurate decomposition for the **selected**
architecture (which is **not** a WebAuthn browser ceremony) is:

| Role | Definition | Who plays it in N-16-5 |
|---|---|---|
| **FIDO2** | umbrella: the CTAP + WebAuthn specification family | the standard family the mechanism conforms to |
| **WebAuthn ceremony** | the W3C browser-side JS API (`navigator.credentials.create/get`) | **NOT USED** — N-16-5 has no browser; the ceremony is driven directly via CTAP2 |
| **CTAP2** | the authenticator transport/command protocol (`authenticatorMakeCredential`, `authenticatorGetAssertion`) over USB-HID / NFC | **the real protocol** — driven by `fido2.ctap2.base.Ctap2` over `fido2.hid.CtapHidDevice` |
| **Relying party (RP)** | the entity a credential is scoped to; identified by `rpId` | **PCAE's protected verifier**, `rpId = "hpac.pcae.local"` (fixed internal constant; §11) |
| **Client / platform** | normally the browser/OS that assembles `clientDataJSON` | **the PCAE protected presentation helper process** — it constructs `CollectedClientData` with a non-web origin (§11) |
| **Authenticator** | the roaming hardware key holding the non-exportable private key | the human's physical USB CTAP2 security key |
| **Credential** | `(credential_id, COSE public key)` minted by `makeCredential`; private key never leaves the device | stored in `CredentialRecord` (public half only) |
| **Challenge** | caller byte string embedded in `clientDataJSON` | `Challenge.challenge_digest` (HPAC-REQ-049) |
| **Assertion** | `authenticatorData || sign(authenticatorData ‖ SHA-256(clientDataJSON))` from `getAssertion` | stored as `HumanAuthenticationProof.assertion` (base64url) |
| **Attestation** | a `makeCredential`-time statement about the authenticator model | **not required / not evaluated** for the first profile (§14) — mirrors `hatp_fido2_provider` `attestation_valid=None` |
| **UP (user presence)** | `authenticatorData` `FLAG.UP` — a physical touch occurred | **required** (HPAC-REQ-042) |
| **UV (user verification)** | `authenticatorData` `FLAG.UV` — the authenticator locally verified the user (PIN/biometric) | **required** (HPAC-REQ-042) — stronger than HATP, which does not check UV |

FIDO2, WebAuthn, and CTAP2 are **not** conflated: N-16-5 uses **CTAP2 directly**, adopts the WebAuthn
`clientDataJSON`/assertion **wire shapes** (because `fido2` implements them and they give byte-exact
challenge binding — see the `hatp_fido2_provider` module docstring's own analysis), and performs **no
WebAuthn browser ceremony**.

---

## 9. Relying-party model (phase prompt §11) — frozen, no human deployment decision required

The selected architecture is **not a web ceremony**, so there is no web origin, no `https://`
requirement, no `localhost` port, no ephemeral-port/origin tension (phase prompt §25, §58, §59, §85,
§86, §87 are **MOOT**). CTAP2 still uses an `rpId` string and the client still supplies an `origin`;
both are **fixed internal PCAE constants**, exactly as `hatp_fido2_provider.py` already does
(`_HATP_RP_ID = "hatp.pcae.local"`, `_HATP_ORIGIN = "pcae-hatp://hatp.pcae.local"`, with the module
comment: *"HATP is not a web origin; these are stable, internal constants... exactly as an RP ID
scopes ordinary WebAuthn credentials to a web origin"*).

**Frozen RP/origin strategy for N-16-5:**

| Item | Value | Basis |
|---|---|---|
| `rpId` | `hpac.pcae.local` — **distinct** from HATP's `hatp.pcae.local` | HPAC-REQ-047 domain separation; HPAC-REQ-084 (no HPAC assertion may verify as a HATP assertion) |
| client `origin` | `pcae-hpac://hpac.pcae.local/runtime-invocation-approval.v2` — non-web scheme | HPAC-REQ-047 challenge namespace tag `pcae.hpac.runtime-invocation-approval.v2` |
| RP identity stability | one constant, compiled into the mechanism module; **not** derived from repo, cwd, env, agent id, hostname, or deployment | HPAC-REQ-079/080 (repo/agent state may not select trust-relevant strings); `hatp_fido2_provider` precedent |
| Mac-dev vs Dell-deploy | `rpId` is a **constant string, not a hostname** — it does not vary by machine, so there is **no cross-trust-domain problem** | HPAC-REQ-083 (OS-neutral hardware keys, no platform adapter) |

**This is not a human environment adjudication** (contrast phase prompt §11's BLOCKED condition): the
`rpId`/`origin` are internal constants with an established repo precedent, not a public web identity.
No BLOCKED.

---

## 10. Credential registration lifecycle (phase prompt §12) — already frozen; implementation seam identified

HPAC-001 §8 (HPAC-REQ-025..031) + §14 (HPAC-REQ-041) freeze it; `hatp_fido2_provider.enroll_credential`
already implements the CTAP2 half.

```
protected-admin ceremony launch  (HPAC-REQ-024: never an ordinary pcae CLI / hook / task / stdin / env)
  → protected presentation of the exact registry identity + credential being enrolled (HPAC-REQ-023)
  → authenticator makeCredential  (fido2 Ctap2.make_credential; rp=_HPAC_RP, ES256, UP+UV)
  → PCAE verifies the makeCredential response, extracts (credential_id_bytes, COSE public key)
  → HumanPrincipalRegistryStore.enroll_credential(protected_admin_capability, credential_id=hpc-<hex>,
        principal_id=<existing active principal>, mechanism_id="hpac.fido2.uv_presence.v2",
        public_key=<hex(cbor(COSE key))>, assurance_capabilities=("UP","UV"), ...)   [atomic, read-back]
  → durable provenance/audit entry  (HPAC-REQ-028/069)
  → credential eligible for future authentication
```

| Question (phase prompt §12) | Frozen answer |
|---|---|
| Who may initiate registration | only the external protected deployment-owner administration principal (HPAC-REQ-023/024/029) |
| How the principal is authenticated before adding another credential | a fresh UV-required human act over a protected presentation of the exact operation (HPAC-REQ-028); for the *first* credential, the external OS/equivalent anchor (HPAC-REQ-023) |
| First-credential bootstrap | §13 below — **frozen**, external anchor, not "first to register" |
| Multiple credentials | permitted, 1 principal → 0..N credentials (HPAC-REQ-030) |
| Credential metadata/nickname | **not persisted** (HPAC-REQ-010/013 — no display metadata field exists); a future concern outside this registry |
| Credential status | `{active, revoked}` monotonic (HPAC-REQ-014/062) |
| Credential revocation / replacement | `revoke_credential` + `enroll_credential` — two operations, never in-place overwrite (HPAC-REQ-031) |

No new decision — the implementation phase wires `hatp_fido2_provider.enroll_credential`'s output into
`HumanPrincipalRegistryStore.enroll_credential` under a protected-admin ceremony.

---

## 11. First-credential bootstrap (phase prompt §13) — FROZEN (HPAC-REQ-023)

**Model: external deployment-owner administration anchor (phase prompt §13 option A/D blend), already
frozen by HPAC-001 §7.** Not open.

- Anchored by an **externally established deployment-owner OS/equivalent protected administration
  principal** — "unavailable to ordinary same-user agent execution" (HPAC-REQ-022), owning a protected
  root outside every repository.
- That principal launches a **non-defaultable ceremony**, displays the exact registry identity +
  credential through a protected presentation channel, **requires authenticator UP and UV**, verifies
  the FIDO2 registration response, and **atomically** creates the first `PrincipalRecord` +
  `CredentialRecord` + durable provenance entry (HPAC-REQ-023).
- **"Whoever registers first becomes the principal" is explicitly forbidden** unless the contract
  defines a secure local bootstrap — and it does: the external anchor **is** that definition. There
  is no circular PCAE self-authorization; the trust terminates at the OS/equivalent protected
  administration principal.
- Recovery from total principal loss = **repeat the bootstrap ceremony** (HPAC-REQ-065) — no shortcut,
  because a shortcut would reopen the same-user-agent threat the contract exists to close.

The implementation phase builds the ceremony tool; **N-16-5 planning adds no bootstrap decision.**

---

## 12. Residual decisions this phase FREEZES (the genuine N-16-5 open set)

Everything else in the phase prompt maps to an already-frozen HPAC-001 requirement. The genuine
residual — the decisions HPAC-001 v2.1 deferred to "a future implementation phase" or left silent —
is frozen here, and captured in the companion contract **RHAMP-001 v1.0** (§28):

| # | Decision | Frozen value | Contract basis / delta |
|---|---|---|---|
| 1 | Real `mechanism_id` allowlist entry | `hpac.fido2.uv_presence.v2` (the only real entry); deterministic id stays test-only forever | HPAC-REQ-039; RHAMP-001 §2 enumerates the closed allowlist |
| 2 | **Protected presentation mechanism model** | a **PCAE-owned, process-isolated local presentation helper**: a distinct OS process (not the agent process), launched by the administrator-installed mechanism, that renders the closed `human_visible_facts` via a versioned deterministic `renderer_profile`, observes an explicit election, drives the CTAP2 touch, and produces `mechanism_attestation` under protected verifier configuration. `verifier_kind = "pcae-protected-local-presentation/1.0"`. Terminal stdout/stdin remains ineligible. | HPAC-REQ-090 (schema frozen; `verifier_kind` closed but unenumerated); RHAMP-001 §3 names the kind + its integrity obligations |
| 3 | RP id / client origin | `rpId = "hpac.pcae.local"`; `origin = "pcae-hpac://hpac.pcae.local/runtime-invocation-approval.v2"` — fixed internal constants | HPAC-REQ-047/079/080; RHAMP-001 §4; `hatp_fido2_provider` precedent |
| 4 | Attestation policy | **none / self-attestation accepted; enterprise attestation not required; no MDS; no device-uniqueness claim** for the first profile | HPAC-REQ-039/040 (silent on attestation); RHAMP-001 §5; mirrors `hatp_fido2_provider` `attestation_valid=None` non-blocking |
| 5 | Discoverable vs non-discoverable credentials | **non-discoverable / `allowList`-bound** — the CLI resolves `principal_id → credential_id` from the registry and passes `allow_list=[{id: credential_id}]`; no resident credentials, no usernameless auth in v1 | HPAC-REQ-032 (minimal interface); RHAMP-001 §6; `hatp_fido2_provider.py:439` precedent |
| 6 | Authenticator attachment | **cross-platform (roaming) hardware key only**; no platform authenticator in the first profile | HPAC-REQ-083; RHAMP-001 §7 |
| 7 | Transports | **USB-HID primary; NFC permitted** (same CTAP2 path). **No BLE, no hybrid/caBLE/cross-device** — a remote transport would break the local protected-approval assumption | HPAC-REQ-082; RHAMP-001 §7 |
| 8 | Challenge / proof / presentation TTL | challenge TTL ≤ **120 s**; `max_proof_age_seconds` ≤ **300 s**; presentation `expires_at` == the RIASC approval `expires_at`; a deployment MAY set stricter, never looser | HPAC-REQ-050 ("a future implementation phase sets it"); RHAMP-001 §8 |
| 9 | Signature-counter policy | record `sign_count` as audit evidence in a **protected per-credential counter-state file** under `HPAC_PROTECTED_ROOT`; `0`/absent → accept (modern authenticators); a **nonzero counter that regresses** vs. the last recorded value → **fail closed** (`signature_counter_regression`) + audit + surface for admin review | HPAC-001 silent; RHAMP-001 §9 (new protected artifact, not a `CredentialRecord` schema change) |
| 10 | Failure taxonomy (`terminal_reason_code` vocabulary) | closed set of 25 codes (§18 below) | HPAC-REQ-095 (`terminal_reason_code` "non-empty ID", unenumerated); RHAMP-001 §10 enumerates it |
| 11 | Registry / enrollment / bootstrap | **no new decision** — HPAC-REQ-013/023/026 frozen; implementation wires `hatp_fido2_provider.enroll_credential` → `HumanPrincipalRegistryStore.enroll_credential` | — |
| 12 | Deployment topology | §27 — **local interactive control-plane host; headless/remote approval OUT OF SCOPE for N-16-5, deferred** | HPAC-REQ-021/022/082/083; RHAMP-001 §11 |
| 13 | Dependency | reuse `fido2>=1.1,<2` + `cryptography>=42,<45` (already declared); reuse `hatp_fido2_provider.py` CTAP2 primitives as a **shared library** (not a live HATP trust dependency); **no new dependency, no custom crypto** | HPAC-REQ-019/§32; RHAMP-001 §12 |

---

## 13. Credential record (phase prompt §14) — conceptual schema (already frozen + one additive field)

`CredentialRecord` (HPAC-REQ-013) is **frozen** and already carries every field the phase prompt's
list needs, except two the implementation phase adds **additively** (no MAJOR/MINOR to HPAC-001 —
inside the existing `CredentialRecord` closed set via a companion-defined interpretation, or as a
sidecar; RHAMP-001 §13 fixes the exact location):

| Phase-prompt field | Where it lives |
|---|---|
| `credential_record_schema_version` | registry `schema_version` const `HPAC-REGISTRY/2.0` |
| `principal_id` | `CredentialRecord.principal_id` |
| `credential_id` | `CredentialRecord.credential_id` (opaque `hpc-<hex>`, **not** the raw CTAP2 id) |
| `public_key` / COSE key | `CredentialRecord.public_key` = `hex(cbor(COSE_Key))` — the exact format `CoseKey.parse(cbor.decode(...))` consumes |
| raw CTAP2 `credential_id` bytes | inside `public_key` payload structure (a closed `{cose, raw_credential_id}` object) OR a companion sidecar — RHAMP-001 §13; needed for `allow_list` |
| `aaguid` | **not retained** (attestation not evaluated; §14) |
| `transports` | `assurance_capabilities` may carry `("UP","UV","usb")` markers; RHAMP-001 §7 |
| `sign_count` / authenticator-state | **not in the registry** — protected per-credential counter-state file (§12 item 9) |
| `created_at` | `CredentialRecord.enrolled_at` |
| `status` / `revoked_at` | `CredentialRecord.status` / `revoked_at` |
| `mechanism` | `CredentialRecord.mechanism_id` = `hpac.fido2.uv_presence.v2` |
| `uv capability/requirement` | `assurance_capabilities` = `("UP","UV")`; UV **required** at verify time regardless |
| `rp_id binding` | implicit — the mechanism's fixed `rpId` constant; RHAMP-001 §4 |
| `provenance/writer binding` | `CredentialRecord.enrollment_provenance_ref` + `HPACStoreAuthority` writer-provenance record |
| record digest | `credential_generation` marker (HPAC-REQ-098a) = whole-record canonical digest |

**No private key field exists on the dataclass** (HPAC-REQ-013 — structural, not a runtime check). The
private key remains authenticator-held; CTAP2 never exposes it (`hatp_fido2_provider` module docstring
Root-1 analysis).

---

## 14. Attestation policy (phase prompt §15) — FROZEN: none required

| Item | Frozen |
|---|---|
| Registration attestation | **not required**; `makeCredential` requested with no attestation preference (or `"none"`); a self / packed / none statement is accepted without validation |
| Enterprise attestation | **prohibited** (privacy — would leak a device serial) |
| Metadata service (MDS) | **not used** |
| Device-identity claims | PCAE makes **none** — no `aaguid` allowlist, no model assertion |
| Rationale | mirrors `hatp_fido2_provider` (`device_attestation=False`, `attestation_valid=None`, documented non-blocking limitation); a first local-CLI profile does not need model binding, and requiring it would add an MDS dependency and a privacy leak for no threat-model gain. A future profile MAY add attestation under HPAC-REQ-068 without lowering the UP/UV floor. |

Privacy/security tradeoff frozen: **maximal privacy, no device fingerprint retained**; the security
property that matters (a UV+UP assertion over the exact challenge from the enrolled credential's
private key) does not depend on attestation.

---

## 15. Authentication ceremony (phase prompt §16) — exact runtime flow (frozen; HPAC-REQ-054)

```
1. trusted coordinator reserves approval_id (ria-<hex>) and resolves principal_id → credential_id from registry
2. protected presentation helper renders the closed human_visible_facts (HPAC-REQ-091), byte-hashes them
   → human_visible_representation_digest; canonical_subject.approval_preview_digest MUST equal it
3. human performs the explicit election (action=approve) on the protected surface → election object
4. helper builds Challenge (HPAC-REQ-049) over approval_subject_digest + trusted_presentation_digest +
   fresh CSPRNG nonce + issued_at + expires_at (≤120s) + domain_separator pcae.hpac.runtime-invocation-approval.v2
5. helper drives CTAP2 getAssertion:
     client_data = CollectedClientData.create(type=GET, challenge=challenge_digest, origin="pcae-hpac://hpac.pcae.local/...")
     Ctap2(device).get_assertion(rp_id="hpac.pcae.local", client_data_hash=client_data.hash,
                                 allow_list=[{type:"public-key", id: raw_credential_id}])
   → the human touches the key AND satisfies UV (PIN/biometric on the device)
6. FIDO2HumanAuthenticator.verify_response parses authenticatorData + clientDataJSON + signature → ProofMaterial
   (up = FLAG.UP, uv = FLAG.UV, mechanism_id = hpac.fido2.uv_presence.v2)
7. hpac_verifier.verify_human_authentication (HPAC-REQ-054 steps 1-10, unchanged sequence):
     principal active → credential active & bound → mechanism eligible & ≥ PRINCIPAL_VERIFIED_INTENT →
     recompute challenge_digest → subject + presentation binding → REAL signature verify
     (CoseKey.verify(authenticatorData + SHA256(clientDataJSON), signature)) →
     rp_id_hash == SHA256("hpac.pcae.local") → challenge in clientDataJSON == challenge_digest →
     UP == true AND UV == true → freshness (challenge not expired, proof age ≤ 300s) →
     lifecycle chain resolves, genesis binding matches → append PROOF_VERIFIED_AND_BOUND
   → ephemeral AuthenticatedHumanPrincipal (assurance_class = PRODUCTION, PRINCIPAL_VERIFIED_INTENT)
8. RIHAC-001 §16 ApprovalAuthorityValidator consumes it → RuntimeInvocationApproval trusted
```

All bound inputs are in the `Challenge` object (HPAC-REQ-049); no new binding is introduced.

---

## 16. Challenge construction (phase prompt §17) — frozen (HPAC-REQ-049/050/051)

The `Challenge` object binds `principal_id`, `credential_id`, `approval_subject_digest` (which
transitively binds repository / task / target / prompt / invocation / `approval_scope` / expiry /
one-shot — HPAC-REQ-089), `trusted_presentation_digest`, a CSPRNG `nonce` (generated by the trusted
challenge-construction component, never the authenticator/adapter/caller), `issued_at`, `expires_at`,
plus the const `domain_separator` / `challenge_version` / `proof_schema_version`.

**Authentication is not over-bound into approval:** the challenge binds the presentation *digest* and
the subject *digest*, not the approval decision itself — the explicit election is a **separate**
recorded fact in the presentation `election` object (§19). A valid assertion over an unrelated
challenge cannot satisfy approval (HPAC-REQ-072). No predictable / sequential / timestamp-only /
reusable challenge value is permitted (HPAC-REQ-051).

---

## 17. UP / UV policy (phase prompt §18) — FROZEN

| Question | Frozen answer | Basis |
|---|---|---|
| Require UP? | **YES**, mandatory | HPAC-REQ-042 |
| Require UV? | **YES**, mandatory — immutable contract minimum | HPAC-REQ-042/060 |
| Both? | **YES**; `hpac_verifier._check_up_uv` already rejects unless `up is True and uv is True` | HPAC-REQ-054 step 7 |
| Can UV-less security-key auth ever qualify? | **NO** — UP-only proofs "SHALL NOT authorize real runtime and SHALL NOT yield `AuthenticatedHumanPrincipal`" | HPAC-REQ-042 |
| Can platform biometrics/PIN satisfy UV? | **YES** — UV is satisfied *inside the authenticator* (PIN or biometric); PCAE never sees the PIN/biometric, only the `FLAG.UV` bit | HPAC-REQ-046/§46 |
| Authenticator cannot perform UV? | **fail closed** — no downgrade, no fallback mechanism (HPAC-REQ-066); approval unavailable | HPAC-REQ-060 |

Deployment policy MAY require stronger assurance; **neither repository nor protected administrator may
lower this floor** (HPAC-REQ-042/080).

---

## 18. Failure reason taxonomy (phase prompt §52) — FROZEN `terminal_reason_code` vocabulary

Closed set (RHAMP-001 §10); every `hpac_verifier` rejection path and every lifecycle terminal event
maps to exactly one:

```
principal_not_found            credential_not_found           challenge_digest_mismatch
principal_revoked              credential_revoked             challenge_expired
principal_inactive             credential_principal_mismatch  challenge_replayed
mechanism_unknown              mechanism_below_assurance      subject_digest_mismatch
presentation_unresolved        presentation_digest_mismatch   attestation_verification_failed
election_missing               election_ordering_invalid      signature_invalid
user_presence_missing          user_verification_missing      signature_counter_regression
freshness_stale                lifecycle_fork                 lifecycle_cross_binding
consumption_replay             protected_root_invalid         internal_verification_error
```

Derived from the actual rejection points in `hpac_verifier.verify_human_authentication`,
`approval_presentation._validate_evidence_document` / `resolve_canonical`, `hpac_lifecycle`
fork/gap/chain checks, and HPAC-REQ-054 steps 1–10 — **not** frozen blindly from the phase prompt's
suggested list.

---

## 19. Authentication ≠ approval (phase prompt §19, §20) — one ceremony, two preserved facts

**Hard requirement (HPAC-REQ-001 wall `FIDO2/WebAuthn assertion != approval`):** a successful FIDO2
assertion does **not** by itself create approval.

**One-vs-two ceremony analysis (phase prompt §20):**

| Model | Verdict |
|---|---|
| A. authentication then a separate approval confirmation | rejected — two touches, stale-window risk between them, worse UX for no gain |
| B. one CTAP2 assertion whose challenge includes the exact presentation digest | **SELECTED** — HPAC-001 already mandates this: the challenge binds `trusted_presentation_digest` and the presentation carries its own `election` object; the single touch cryptographically binds *what was shown* to *the assertion*, and the **election is a distinct recorded fact** |
| C. authenticated session + fresh approval assertion | rejected — HPAC-REQ-075/076 forbid an authentication session cache in v2 |
| D. step-up assertion only at approval time | this **is** model B in practice — the assertion happens at approval time, over the approval's presentation |

**The two distinct facts preserved (HPAC-001 §39):**
1. **Informed election** — `TrustedApprovalPresentationEvidence.election` (`action = approve`,
   `occurred_at >= presented_at`), attested by the protected mechanism over the
   `human_visible_representation_digest`. This is "the human saw P and elected to approve P."
2. **Authenticated presence+verification** — the FIDO2 assertion (UP+UV) over the challenge that
   *contains* the presentation digest. This is "an enrolled human principal was present and verified."

Neither implies the other structurally: `hpac_verifier` resolves the presentation (step 5) and the
signature (step 6) as **independent** steps that both must pass. A blind touch with no resolved
`HPAC-REQ-091` evidence "SHALL NOT satisfy `PRINCIPAL_VERIFIED_INTENT`" (HPAC-001 §39 closing line).

---

## 20. Protected approval presentation (phase prompt §21, §22, §26, §27) — frozen content + binding

**Minimum mandatory presentation** = HPAC-REQ-091's closed `human_visible_facts` (13 fields):
repository (identity + human label + fingerprint), task (id + label), runtime target (id + label),
`operation_effect_scope_display` (the **complete** canonical `approval_scope`: requested capability,
local transport, effect class, filesystem/process references, no-network fact, one-dispatch limit),
prompt (hash + fingerprint), invocation (id + label), `expires_at`, `one_shot_notice` const `true`.
No caller-supplied label, no hidden field, no non-attested authority text (HPAC-REQ-092).

**Informed-intent binding (phase prompt §22)** — frozen (HPAC-REQ-092):
`canonical_subject.approval_preview_digest` **SHALL equal** `human_visible_representation_digest`
(SHA-256 of the exact displayed bytes, UTF-8/NFC/LF); the `mechanism_attestation` is verified over the
closed `HPAC-PRESENTATION-ATTESTATION/2.0` object (`presentation_id`, `approval_id`,
`approval_subject_digest`, `human_visible_representation_digest`, `descriptor_digest`, the complete
`election`, `presented_at`). A resolver **re-renders** the same facts under the exact descriptor
version and requires byte/digest equality. "The attested digest identifies what was actually shown,
not merely an abstract data object."

**Canonicalization (phase prompt §26)** — `presentation_payload` = the closed `human_visible_facts`;
`presentation_digest` = HPAC-REQ-089 canonical bytes minus `presentation_digest`; the display bytes
are what the renderer emitted and hashed. `display text A / digest payload B` divergence fails closed
via the re-render equality check.

**Truncation / hidden fields (phase prompt §27)** — frozen: no security-critical field may be omitted
from the digest (the 13 fields are the whole closed set and all are digested); the renderer MUST
display all 13; the `operation_effect_scope_display` MUST render the **complete** `approval_scope`
including the full effect description — HPAC-REQ-091 already requires this. No default-collapsed
expansion of a mandatory field.

**Approval action (phase prompt §28)** — the explicit human election on the protected surface
(`action = approve`) is the intent event; it is recorded as `election.event_id` (`hpevt-<hex>`) with
`occurred_at`. The CTAP2 touch alone is **not** the approval — the election is a separate observed
event, and a `blind_touch` (empty election id) is a modeled adversarial fault the verifier rejects
(`approval_presentation_deterministic.py` `fault="blind_touch"`; HPAC-001 §39 closing line).

---

## 21. Protected UI threat model + architecture (phase prompt §23, §24, §60, §61)

**Threat model (frozen UI trust boundary):**

| Threat | Mitigation (frozen) |
|---|---|
| terminal spoofing / agent-generated text posing as the prompt | terminal stdout/stdin is **structurally ineligible** (HPAC-REQ-090); the helper is a **separate process** with its own surface |
| malicious repository content in the displayed facts | the renderer emits only the closed `human_visible_facts`; repo strings are escaped/encoded; no clickable links from untrusted content |
| terminal escape sequences | the helper does not render into the agent's TTY; if a TTY surface is used it neutralizes escape sequences before display |
| approval-UI substitution by the requesting agent | `agent_substitution_resistant` const `true` in the descriptor; the mechanism is administrator-installed under the protected root; the agent process cannot launch, replace, or observe it |
| approval-text truncation | all 13 mandatory fields rendered; complete `approval_scope`; digest covers exactly the displayed bytes |
| race between presentation and action | the `election.occurred_at >= presented_at` ordering check + challenge `expires_at` (≤120s) + one-shot lifecycle |
| clickjacking / DOM injection / origin confusion | **N/A** — no browser, no DOM, no web origin |
| clipboard/paste manipulation | the election is a deliberate affirmative act on the protected surface, not a paste target |
| accessibility | the renderer profile is versioned; an accessible rendering is a `renderer_profile` version concern, not a security relaxation |

**Selected UI architecture (phase prompt §24):**

| Option | Verdict |
|---|---|
| A. localhost web UI with WebAuthn | rejected — introduces a browser, web origin, TLS/secure-context, CSRF/navigation surface |
| B. OS-native application/window | rejected for the first profile — a GUI toolkit dependency + a dual Mac/Linux surface |
| C. terminal UI + external WebAuthn helper | rejected — terminal surface ineligible (HPAC-REQ-090) |
| **D/E. PCAE-owned process-isolated privileged local presentation helper** | **SELECTED** — a distinct short-lived OS process, launched only by the administrator-installed mechanism under the protected root, that (i) reads the closed facts, (ii) renders them deterministically via `renderer_profile`, (iii) presents on a surface the requesting agent cannot substitute or scrape (a controlled local pane / a dedicated fd not shared with the agent), (iv) observes the explicit election, (v) drives the CTAP2 assertion, (vi) signs the attestation under protected verifier configuration, (vii) exits. No persistent daemon, no network listener. |

`verifier_kind = "pcae-protected-local-presentation/1.0"`. **Process ownership (phase prompt §60):**
the helper is PCAE-owned and administrator-configured; agent-generated HTML/text can never become
trusted presentation; repository strings are escaped/encoded before rendering (phase prompt §61).

---

## 22. Localhost / loopback / network policy (phase prompt §25, §58, §59, §85, §86, §87) — MOOT / frozen

The selected architecture uses **no network, no browser, no loopback socket, no HTTP, no TLS, no
port**. CTAP2 is a **local USB-HID / NFC** transport. Therefore:

- No bind address, ephemeral port, CSRF token, cookie, CSP, or origin-navigation policy is needed.
- HPAC-REQ-082's "no network call is required to produce or verify a proof" is satisfied trivially.
- N-16-3's first-local-CLI network prohibition is **not** engaged — there is no loopback UI transport
  to classify.
- The "WebAuthn generally requires a secure context / HTTPS" concern (phase prompt §87) does **not
  apply** — there is no browser; `fido2.ctap2` talks to the device directly.
- The RP-id / ephemeral-port tension (phase prompt §86) does **not exist** — `rpId` is a fixed
  constant string, not a host:port.

If a future profile ever introduces a browser/loopback path, that requires a **new governed HPAC
version** (HPAC-REQ-067) and a full CSRF/origin/session freeze — explicitly **not** N-16-5.

---

## 23. Sign-counter / cloning signals (phase prompt §32) — FROZEN

- CTAP2 authenticators may report `signCount == 0` permanently (modern / passkey authenticators) or
  non-monotonic values. `signCount` is **not** treated as universally authoritative.
- **Frozen behavior:** a protected per-credential counter-state file
  (`<HPAC_PROTECTED_ROOT>/credentials/<credential_id>/counter.json`, atomic create/replace,
  read-back verified) records the last observed `(signCount, observed_at)`.
  - device reports `0` or omits it → **accept**, record `0`.
  - device reports a value `> last recorded` → **accept**, update.
  - device reports a nonzero value `<= last recorded` (regression) → **fail closed**
    (`signature_counter_regression`), emit an audit record, and mark the credential for
    protected-admin review (not auto-revoked — that is an admin decision).
- This is a **new protected artifact**, not a `CredentialRecord` schema change (the registry is
  create/append-only for revocation only, HPAC-REQ-015). RHAMP-001 §9.

---

## 24. Credential revocation + generation/currentness (phase prompt §33, §34, §67) — FROZEN

**Revocation** is fully frozen (HPAC-REQ-061..065):
- `revoke_credential` / `revoke_principal` — monotonic, first-recorded revocation authoritative,
  later revocation idempotent no-op.
- Revocation **immediately** marks all unused challenges, verified/bound proofs, unmaterialized /
  unconsumed approvals, and derived PB authority projections **invalid** (HPAC-REQ-063).
- An in-flight authentication **cannot** complete after revocation even if the challenge has not
  expired (HPAC-REQ-064).
- Only an approval/proof **already atomically consumed** by the §41 record remains historical
  evidence — never reusable authority.

**Generation / currentness integration (phase prompt §34)** — frozen, **reuse the existing mechanism**
(HPAC-REQ-098a): the five `HPAC-AUTHORITY-GENERATION-SNAPSHOT/1.0` markers
(`principal_generation`, `credential_generation`, `approval_generation`, `lifecycle_generation`,
`consumption_generation`) already fold whole-record registry digests and the full lifecycle chain.
A revoked or replaced credential moves `credential_generation`; a future gate 10 re-reads current
generation state and compares against the durable snapshot (RDGO-001 v3.1 §10/§11). **No parallel
freshness system is introduced.** The per-credential counter-state file (§23) is audit/anti-clone
evidence, **not** a generation input (it uses no wall clock in the marker; it is read at verify time,
not folded into `credential_generation`).

**Propagation (phase prompt §67):** credential revoked → new authentications fail
(`credential_revoked`) → outstanding unconsumed proofs become stale via `credential_generation` and
HPAC-REQ-063 → consumed historical records remain audit evidence only.

---

## 25. Proof lifetime, single-use, writer provenance (phase prompt §35, §36, §37) — FROZEN

| Concern | Frozen |
|---|---|
| Authentication proof lifetime | **operation-specific** — one challenge, one proof, bound to exactly one approval (HPAC-REQ-050/071). No authenticated session (HPAC-REQ-075/076). `max_proof_age_seconds ≤ 300 s`. |
| Approval proof single-use | one exact approval → one authority lifecycle → gate-9 atomic consumption → cannot be replayed (HPAC-REQ-071/098/100/101). Pre-consumption: `PROOF_VERIFIED_AND_BOUND`, revalidatable only for the exact same binding. Post-consumption: `consumption.json` present → replay rejected; retry requires a fresh invocation/attempt/presentation/challenge/proof/approval. |
| Writer provenance | only the trusted verifier/coordinator under the protected root may mint canonical `proof.json` / lifecycle events / `consumption.json` (HPAC-REQ-053/094/098/100). Atomic, create-only, read-back verified. A structurally valid file is **not** trusted authority — `HPACStoreAuthority.verify_record` + the `is_verifier_authenticated_principal` identity registry are the boundary. |

---

## 26. NON_REAL non-upgradeability + mechanism registry (phase prompt §38, §39) — FROZEN, structural

**Non-upgradeability (hard requirement):** existing deterministic NON_REAL proof / presentation
objects can **never** be relabeled, converted, or wrapped into REAL authority. Enforced structurally,
not by prose:
- `DeterministicTestHumanAuthenticator.SIMULATION_ONLY: Final[bool] = True` and `MECHANISM_ID`
  fixed — no constructor override.
- `hpac_verifier._ELIGIBLE_MECHANISM_IDS` — a NON_REAL `mechanism_id` is rejected at step 3.
- `HPACAuthorityClass` propagation — a `FIXTURE_NON_REAL` store record can never yield a `PRODUCTION`
  `AuthenticatedHumanPrincipal`; `require_real_assurance=True` rejects it (`_authority_class_of`).
- `DeterministicTestPresentationMechanism.present_installed` raises if the installed descriptor
  `is_real_runtime_eligible`.
- Mechanism identity is **verifier-owned** (the allowlist), not proof-declared — a NON_REAL proof with
  real-looking fields is still NON_REAL.

Test/model case (feeds §29 matrix): a deterministic authenticator output with `mechanism_id` forged to
`hpac.fido2.uv_presence.v2` → `_verify_mechanism_eligibility` still rejects because the resolved
`CredentialRecord.mechanism_id` won't match a real credential, and even if it did, `_authority_class_of`
returns `FIXTURE_NON_REAL` for a fixture-root credential.

**Mechanism registry:** the current mechanism-neutral verifier supports adding a REAL mechanism by
extending `_ELIGIBLE_MECHANISM_IDS` (a frozenset literal) and adding a real branch to
`_verify_assertion_material`. RHAMP-001 §2 freezes the closed real allowlist (`hpac.fido2.uv_presence.v2`
only); test mechanisms stay isolated by their `hpac.deterministic.*` prefix; duplicate mechanism
registration is a frozenset (no duplicates possible); the registry identity is the compiled module
constant.

---

## 27. Deployment topology: Mac dev / Dell deploy / headless (phase prompt §56, §57, §88) — DECISIVE, FROZEN

**Frozen safe assumption (phase prompt §88 explicitly asks for one, not a BLOCK):**

> **N-16-5's first real profile requires the protected approval presentation and the CTAP2
> authentication touch to occur locally, in an interactive session, on the authority-owning
> control-plane host, with a directly-attached USB CTAP2 hardware key.**

Rationale, primary-source anchored:
- HPAC-REQ-021: the registry is **deployment/user-scoped** — a human enrolls once and reuses across
  repos. This does **not** require the authority host to be the same as any dev host.
- HPAC-REQ-022/082/083: the protected root and the mechanism are **local-only**, **offline**, and
  **OS-neutral** (Mac + Linux both work with the same roaming hardware key).
- The `rpId` is a **constant string** (§9), identical on Mac and Dell — there is **no cross-trust-domain
  problem** and no per-host RP registration.
- The human physically carries the USB key to whichever host owns the authority for a given
  invocation and performs the ceremony there.

**Headless deployment host (phase prompt §57):** if the deployment host (e.g. a headless Dell Ubuntu
box) has **no interactive session and no attached key**, then **N-16-5 does not deliver approval on
that host.** Remote / networked approval — an operator machine presenting + touching and the
deployment host consuming the evidence over a channel — is **explicitly OUT OF SCOPE for N-16-5** and
**deferred** to a separate, separately-authorized architecture. That future work MAY reuse the
patterns in `HATP_REMOTE_ASSERTION_CEREMONY_CONTRACT.md` / `HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md`
(which exist precisely because remote assertion is a distinct capability HATP chose to govern
separately), but it is **not** smuggled into N-16-5 (phase prompt §57: "Do not smuggle in a remote
approval service"). Recorded as an explicit **deployment prerequisite**, RHAMP-001 §11.

**This is not a BLOCKED condition:** HPAC-001 v2.1 already froze a bounded, local model; the safe
assumption is derivable from HPAC-REQ-021/022/082/083; the remote case has a named deferral path.

---

## 28. Contract impact + versioning matrix (phase prompt §68, §69) — companion contract, NO HPAC bump

Each artifact's own versioning rule was read (HPAC-001 §37, RIHAC-001 §-versioning, RIASC-001 §2,
RDGO-001 §21, RPAC-001 §-versioning).

| Artifact | Current | N-16-5 semantic change | Bump | Migration? | IV? | Reason |
|---|---|---|---|---|---|---|
| **HPAC-001** | v2.1 | **none** — every residual decision fits an existing extension point (`mechanism_id` allowlist, `verifier_kind` closed set, `terminal_reason_code` IDs, TTL "future phase sets it", attestation silent) | **NONE** | — | — | avoids a cross-contract reference cascade (RIHAC-001 §12 condition 7 names "HPAC-001 v2.1" literally) |
| **RHAMP-001** *(new companion)* | — → **v1.0** | freezes items 1–13 of §12 as a **profile** under HPAC-001 v2.1's extension points | **new v1.0** | none (no prior artifact) | yes — `.1R.29` freeze + `.1R.31`/`.1R.33` IV | REPRC-001 v1.0 precedent exactly: a companion to avoid a MAJOR/MINOR cascade on the parent |
| RIHAC-001 | v2.0 | none — §12 condition 7 already requires "HPAC-001 v2.x proof verification against current protected state"; a real proof satisfies it | NONE | — | — | consumer, unchanged |
| RIASC-001 | v3.0 | none — `approval_mechanism` already const `trusted_subject_bound_confirmation` | NONE | — | — | wire shape unchanged |
| PBRD-001 | v3.0 | none — PB never receives raw proof material (HPAC-REQ-035); consumes only the RIHAC projection | NONE | — | — | — |
| RDGO-001 | v3.1 | none — gate-5 / gate-9 timing unchanged; the real proof flows through the same steps | NONE | — | — | — |
| RPAC-001 | v1.0 | none — provider-neutral; N-16-5 touches no adapter | NONE | — | — | — |
| REPRC-001 | v1.0 | none — Gate 7 positive result is independent of the auth mechanism | NONE | — | — | — |
| RE No-Go Registry | schema 1.1 | none | NONE | — | — | — |
| HATP contracts | — | none — separate trust domain; N-16-5 reuses `hatp_fido2_provider` **code** as a library, not HATP **state** (HPAC-REQ-019) | NONE | — | — | domain separation preserved |

**No MAJOR bump. No MINOR bump. One new companion contract (RHAMP-001 v1.0).**

**New contract ownership (phase prompt §69):** RHAMP-001 owns — the real `mechanism_id` allowlist, the
`verifier_kind` allowlist + protected-presentation-helper integrity obligations, the RP-id/origin
constants, the attestation policy, the discoverable-credential + attachment + transport profile, the
TTL bounds, the signature-counter policy + counter-state artifact, the `terminal_reason_code`
vocabulary, and the deployment-topology prerequisite. HPAC-001 continues to own the
challenge/proof/presentation/lifecycle/consumption **schemas** and protected resolution.

---

## 29. Contract-freeze sequence + implementation slicing + IV (phase prompt §70, §71, §76, §92, §93)

**Contract-freeze sequence (phase prompt §70):** because a dedicated companion contract is required
and the implementation spans a real mechanism + a real registry writer + a real bootstrap ceremony +
a real presentation helper, the sequence is:

> **planning (`.1R.28`, this phase) → dedicated companion contract freeze (`.1R.29`, RHAMP-001 v1.0)
> → implementation slices with IV → N-16-5 closure.**

**Frozen phase decomposition (IDs recommended, NOT reserved):**

| Phase | Scope |
|---|---|
| `.1R.29` | **RHAMP-001 v1.0 companion contract freeze** — items 1–13 of §12; no `src/pcae` change; own human authorization |
| `.1R.30` | **Real FIDO2 authentication mechanism + registry production writer + bootstrap ceremony** — `FIDO2HumanAuthenticator` (`hpac.fido2.uv_presence.v2`); real signature verification in `hpac_verifier` (`CoseKey.verify`, `rp_id_hash`, `origin`, UV check); `_ELIGIBLE_MECHANISM_IDS += {hpac.fido2.uv_presence.v2}`; `HumanPrincipalRegistryStore` production path exercised; protected-admin enrollment + first-credential bootstrap ceremony tool; counter-state artifact; `terminal_reason_code` wiring; reuse `hatp_fido2_provider` CTAP2 primitives as a shared library |
| `.1R.31` | **Independent Verification of `.1R.30`** — broad fixed-SHA A/B; the §31 IV requirements |
| `.1R.32` | **Real protected approval presentation mechanism + real-assurance wiring** — `verifier_kind = "pcae-protected-local-presentation/1.0"`; process-isolated presentation helper; deterministic `renderer_profile`; real `mechanism_attestation`; administrator-installed `PRODUCTION` descriptor; wire `require_real_assurance=True` through Gate 5 / Gate 9; production `AuthenticatedHumanPrincipal` of class `PRODUCTION` becomes obtainable for one approval |
| `.1R.33` | **Independent Verification of `.1R.32` + N-16-5 closure** — includes the **mandatory** real-hardware manual verification (§31) |

No premature fragmentation beyond this; `.1R.30` deliberately keeps registry + mechanism + bootstrap
together because they share the protected-root resolver and the enrollment ceremony.

**Frozen IV requirements (phase prompt §92) — for `.1R.31` / `.1R.33`:**
real credential cannot be caller-forged; credential maps to exactly one canonical principal; no
private-key storage (structural — no field exists); valid FIDO2/CTAP2 cryptographic verification
(`CoseKey.verify` over `authenticatorData ‖ SHA-256(clientDataJSON)`); `rpId`/origin bound to the PCAE
constants and un-selectable by repo/agent; UP **and** UV enforced, UP-only rejected; authentication ≠
approval (independent verifier steps 5 and 6); presentation digest exactly bound
(`approval_preview_digest == human_visible_representation_digest`); explicit election observed, blind
touch rejected; protected-helper process isolation + content integrity + escaping; challenge
anti-replay (single-use nonce, `challenge_replayed`); credential revocation invalidates outstanding
authority (`credential_generation` + HPAC-REQ-063); NON_REAL cannot upgrade (mechanism-id allowlist +
`HPACAuthorityClass`); proof/consumption writer provenance (protected root + identity registry);
Gate 5 mechanism-neutrality (no FIDO2-specific field leaks into the RIHAC projection); Gate 9
single-use atomic consumption; **N-16-6 still blocks** (no admissible adapter); **runtime still
`unavailable`** (N-16-7 untouched); **first external effect ABSENT**; broad guard A/B clean; **≥ 1
real CTAP2 hardware integration verification** (frozen as **mandatory** before `.1R.33` closes N-16-5,
kept out of `.1R.28`).

**Real-hardware verification strategy (phase prompt §77):** the automated suite uses monkeypatched
`CtapHidDevice.list_devices` / `Ctap2` + a test-only in-memory ES256 key (exactly
`hatp_fido2_provider`'s existing test approach — "REAL HARDWARE NOT EXERCISED in this development
environment"). **At least one** ceremony against a real attached CTAP2 key (enrollment + a UV+UP
assertion + a full verifier pass) is **mandatory for N-16-5 closure** and is performed in `.1R.33`
under explicit controlled conditions.

---

## 30. STOP-condition check (phase prompt "Valid early STOP conditions", §100) — NONE APPLY

| Condition | Applies? | Why not |
|---|---|---|
| HPAC/RIHAC/RIASC/HHCE/HPSE semantics fundamentally conflict with real FIDO2/WebAuthn authority | **NO** | HPAC-001 v2.1 **is** the real-FIDO2 architecture, already frozen and formalized from `.1R.2A` |
| verifier/proof/store model cannot extend without a MAJOR redesign broader than N-16-5 | **NO** | the model was **built** for this — `_ELIGIBLE_MECHANISM_IDS`, `require_real_assurance`, `HPACAuthorityClass` are the seams; a companion contract + additive code suffices |
| no protected presentation model can prove informed intent without becoming bearer authority | **NO** | HPAC-001 §39 already froze one (digest-equivalence + attestation + election + non-serializable ephemeral result) |
| real credential registration cannot bind safely to the canonical human-principal registry | **NO** | `enroll_credential` + `hatp_fido2_provider.enroll_credential` already do exactly this pattern |
| WebAuthn UV semantics cannot be kept distinct from approval intent | **NO** | UV is a `FLAG` bit checked in verifier step 7; the election is a separate observed event in step 5's evidence |
| the mechanism necessarily requires runtime capability enablement / external-effect authorization / N-16-6/7 | **NO** | authentication is upstream of Gate 6 admission and entirely independent of runtime capability |
| production private-key material would need PCAE storage | **NO** | CTAP2 never exposes the private key; no field exists to hold one (structural) |
| a required contract-versioning decision cannot be resolved from primary-source rules | **NO** | resolved: companion RHAMP-001 v1.0, REPRC-001 precedent, no parent bump |
| OS/browser/native-app platform choice cannot be frozen without human environment adjudication | **NO** | native CTAP2, OS-neutral, fixed constant `rpId` — no web identity, no human adjudication (HATP precedent) |
| the design would make NON_REAL proofs upgradeable into real authority | **NO** | structurally impossible (§26) |
| repository evidence requires a prerequisite ordering different from N-16-5 → N-16-6 → N-16-7 | **NO** | `.1R.16` §48 ordering reconfirmed |
| safe UI protection requires capabilities beyond authorized PCAE architecture and no bounded model can be frozen | **NO** | a bounded model **is** frozen: process-isolated local helper (§21); the headless-remote case is explicitly deferred, not blocking |

**No BLOCKED report is returned. Planning proceeds through governed finalization.**

---

## 31. Whole-system authority chain, post-N-16-5 (phase prompt §89) + authority-creation table (§90)

```
registered principal credential                (durable registry record; not authority)
  → real CTAP2 ceremony (UP+UV over challenge)  (produces a fresh assertion; not approval)
  → hpac_verifier §18 (real signature verify)   (produces ephemeral AuthenticatedHumanPrincipal, PRODUCTION)
  → protected presentation + explicit election  (produces TrustedApprovalPresentationEvidence; informed intent)
  → RIHAC-001 §16 ApprovalAuthorityValidator    (produces a trusted RuntimeInvocationApproval)
  → Gate 5 authority validation                 (revalidates; binds PROOF_VERIFIED_AND_BOUND; emits RIHAC projection)
  → Gate 6 PB production consumption             (STILL BLOCKS — no admissible adapter until N-16-6)
  → Gate 7 Runtime Enforcement                   (production still DENYs; positive branch test-seam only, N-16-4)
  → Gate 8 process containment / Shell Gate
  → Gate 9 atomic authority consumption          (writes the single consumption.json; one-shot)
  → Gate 10 pre-effect eligibility               (18-step battery; re-reads current generation state)
  → Slice B durable dispatch lifecycle
  → runtime capability                           (STILL unavailable — N-16-7 untouched)
  → Slice C first concrete effect adapter        (NO phase ID; no adapter.dispatch() call site exists)
```

| Stage | Input | Output | Creates authority? | Consumes authority? | Reusable? | Durable? | Human-visible? | Can cause external effect? |
|---|---|---|---|---|---|---|---|---|
| Enrollment | admin ceremony + makeCredential | `CredentialRecord` | no | no | n/a | yes | at enrollment | no |
| CTAP2 assertion | challenge + touch + UV | `ProofMaterial` | no | no | no | no (transient) | yes (the touch) | no |
| `hpac_verifier` §18 | proof id + approval id + stores | `AuthenticatedHumanPrincipal` (PRODUCTION) | **evidence only** (not PB permission) | no (binds, not consumes) | same-binding revalidation only | no (ephemeral, non-serializable) | no | no |
| Protected presentation | canonical subject + election | `TrustedApprovalPresentationEvidence` | informed-intent evidence | no | no | yes (create-only) | **yes** | no |
| RIHAC §16 | verifier evidence | `RuntimeInvocationApproval` | **approval authority** | no | no | yes | no | no |
| Gate 5 | approval + proof + stores | RIHAC projection + seq-3 event | validated-authority projection | no | same-binding only | seq-3 durable | no | no |
| Gate 9 | projection + PB + RE + all bindings | `consumption.json` | no (consumes) | **yes — the single consumption** | **no (one-shot)** | yes | no | no (gate 10 absent) |

The authentication stage is **never** labeled approval authority.

---

## 32. Positive production path after N-16-5 alone (phase prompt §72) — NONE

After N-16-5 closes:
- Real human authority becomes **satisfiable** — RIHAC-001 §12 condition 7 can pass with a real
  UV+UP+presentation proof of class `PRODUCTION`.
- **Gate 6 (PB) still blocks:** N-16-6's RPAC-REQ-095 generic fixed-argv adapter + supply-chain
  admission is NOT SATISFIED (`.1R.16` §35 row 16) — no adapter is admissible, so no
  `RuntimeInvocationApproval` can name an admissible target.
- **Gate 7 still DENYs in production:** N-16-4 shipped the positive branch as a `pragma: no cover`
  test-seam only; `run_gate7_runtime_enforcement` still returns `Gate7Result(decision="DENY")` on
  every production path.
- **Runtime stays `unavailable`:** N-16-7 (`Observed → Approved/Executable`) is untouched and last.
- **Gate 10 / Slice C:** no `adapter.dispatch(` call site exists anywhere in `src/pcae/**`.

**Production positive path after N-16-5 alone = NONE. The first external effect remains
UNREACHABLE.** (`.1R.16` §35 rows 16–17; `.1R.24` §26.)

---

## 33. N-16-6 / N-16-7 / Slice C relationship (phase prompt §73, §74, §75)

- **N-16-6 (phase prompt §73):** N-16-5 outputs **no** structural dependency for N-16-6 — credential /
  authentication is deliberately **not** coupled to adapter admission (RPAC-REQ-049 forbids
  reinterpreting auth artifacts as generic invocation permission). Keep it decoupled. N-16-5 does not
  implement, reference, or unblock any adapter, mock or real; `RuntimeRegistry` stays empty.
- **N-16-7 (phase prompt §74):** no runtime capability enablement. Even real human approval + a
  future PB admission + a Gate 7 ALLOW would leave the runtime `unavailable` until N-16-7's separate,
  separately-verified `Observed → Approved/Executable` transition.
- **Slice C (phase prompt §75):** **no phase ID assigned.** Slice C cannot begin until N-16-3, N-16-4,
  N-16-5, N-16-6, N-16-7 are all CLOSED. First external effect remains absent.

---

## 34. `.3` governance incident (phase prompt §97, §98) — preserved

```
DELEGATED `.3` FINALIZATION / COMMIT / PUSH: UNAUTHORIZED
```

Preserved exactly. Only the primary human-authorized operator holds `.1R.28` lifecycle authority. No
delegated worker committed, finalized, or pushed. No raw `git commit` / `git push`, no `--no-verify`,
no force push, no history rewrite, no hook bypass — governed `pcae` lifecycle only. This phase's work
was performed by the `claude-local` documentation/default agent under the primary operator's explicit
authorization for `.1R.28`.

---

## 35. Findings summary (all non-blocking; feed `.1R.29`)

| ID | Finding | Disposition |
|---|---|---|
| **N-16-5-1** | HPAC-001 §14 is silent on attestation policy; §16 explicitly defers challenge/proof TTL numbers; §40 leaves `terminal_reason_code` unenumerated; §14 does not state a discoverable-credential / attachment / transport profile. | RHAMP-001 v1.0 (`.1R.29`) freezes all four as a profile under HPAC-001's existing extension points — **no HPAC bump**. |
| **N-16-5-2** | `hpac_verifier._verify_assertion_material` does no real signature math and `_ELIGIBLE_MECHANISM_IDS` excludes every real mechanism — correct for the NON_REAL phase, but the real branch must be added carefully so a fixture-root credential can never reach it. | `.1R.30` adds the real branch behind `_authority_class_of == PRODUCTION` + the real allowlist; IV `.1R.31` proves fixture-root credentials cannot reach it. |
| **N-16-5-3** | HATP's real CTAP2 provider checks UP but **not** UV (`hatp_fido2_provider.py:518` `is_user_present()` only). Reusing it as a library requires HPAC's mechanism to add the UV check itself. | `.1R.30` reuses only the CTAP2 transport + `CoseKey` verification primitives and adds `AuthenticatorData` `FLAG.UV` enforcement in HPAC's own verifier path. |
| **N-16-5-4** | Sign-counter handling has no home in the frozen schemas (registry is create/append-only). | RHAMP-001 §9 defines a **new** protected per-credential counter-state artifact under `HPAC_PROTECTED_ROOT`; not a `CredentialRecord` change. |
| **N-16-5-5** (deployment) | If the deployment host is headless with no attached key, N-16-5 delivers no approval there; remote approval overlaps HATP's separately-governed remote-assertion contracts. | Frozen safe assumption: local interactive control-plane host + attached USB key (§27). Remote/headless approval **deferred** to a separate authorized architecture — **not** N-16-5, **not** BLOCKED. |
| **N-16-5-6** (observation) | `.1R.16` §35 row 15 labels N-16-5 "PBRD §12 item 3"; PBRD is now v3.0 and §12 was superseded. | Non-blocking cross-reference imprecision; frame N-16-5 as "real `hpac.fido2.uv_presence.v2` mechanism + real protected presentation satisfying HPAC-001 v2.1 §14/§18/§39 with `PRINCIPAL_VERIFIED_INTENT` / `PRODUCTION` assurance", not "PBRD §12 item 3". |

**No new blocking finding. N-16-3 and N-16-4 are not reopened.**

---

## 36. Test strategy (phase prompt §76, §78) — for the implementation phases

**Layered (phase prompt §76):** deterministic fake CTAP2 fixtures (monkeypatch `CtapHidDevice`/`Ctap2`
+ in-memory ES256 key — the `hatp_fido2_provider` pattern); real WebAuthn/CTAP2 protocol test vectors
for `AuthenticatorData` / `clientDataJSON` parsing; a virtual authenticator where available; **no
browser automation** (no browser); a manual hardware-key integration test (mandatory for closure,
`.1R.33`); negative protocol cases; UI content-integrity cases; proof-lifecycle cases;
restart/replay; credential revoke; multi-credential; wrong principal; wrong challenge; wrong
`rpId`/origin; missing UV; stale presentation; cancelled election. The automated suite **never**
requires real hardware.

**Defensive test matrix (phase prompt §78) — ≥ 55 cases frozen for `.1R.30`–`.1R.33`:**

1 first-credential bootstrap success · 2 unauthorized (same-UID agent) registration rejected · 3
duplicate `credential_id` rejected · 4 revoked credential rejected · 5 wrong principal rejected · 6
wrong `rpId` (`hatp.pcae.local` instead of `hpac.pcae.local`) rejected · 7 wrong origin rejected · 8
wrong challenge digest rejected · 9 expired challenge (`>120s`) rejected · 10 replayed challenge/nonce
rejected · 11 invalid signature rejected · 12 missing UP rejected · 13 missing UV rejected · 14
authenticator cancel → no approval, no proof · 15 authenticator timeout → fail closed · 16 unknown
credential rejected · 17 credential/principal mismatch rejected · 18 malformed `authenticatorData`
rejected · 19 malformed `clientDataJSON` rejected · 20 wrong `clientData.type` (not `GET`) rejected ·
21 presentation-digest mismatch rejected · 22 invisible-field mutation (any of the 13 facts) → digest
changes → rejected · 23 stale presentation (`now >= expires_at`) rejected · 24 election rejected /
absent (`blind_touch`) → no `PRINCIPAL_VERIFIED_INTENT` · 25 auth success without election → not
approval · 26 election without a valid assertion → not authenticated · 27 NON_REAL proof upgrade
attempt (fixture mechanism id) rejected · 28 forged real `mechanism_id` on a fixture-root credential
rejected · 29 forged canonical `proof.json` (identity-registry check fails) rejected · 30 invalid
writer provenance rejected · 31 credential revoked after auth, before Gate 5 → seq-3 fails · 32
credential revoked after Gate 5, before Gate 9 → consumption fails closed · 33 principal disabled →
rejected · 34 multi-credential: correct credential selected via `allow_list` · 35 wrong credential for
principal rejected · 36 sign-count regression (nonzero, decreasing) → `signature_counter_regression` ·
37 sign-count `0`/absent → accepted · 38 process restart mid-ceremony → challenge unconsumed, resume
only same-binding · 39 concurrent approvals → one-challenge/attempt ownership · 40 double election
submit → idempotent or rejected · 41 stale helper instance approving after a newer challenge rejected
· 42 (N/A — no CSRF; asserted absent) · 43 (N/A — no origin navigation; asserted absent) · 44
injected HTML/escape sequence in a repo-derived fact → escaped, digest stable · 45 terminal-escape
content neutralized · 46 (N/A — no loopback bind; asserted absent) · 47 (N/A — no external
script/resource; asserted absent) · 48 authenticator private key never stored (no field exists —
structural) · 49 no biometric/PIN stored (verified — only `FLAG.UV` bit) · 50 proof single-use
(second consumption rejected) · 51 Gate 9 replay rejected (`consumption.json` present) · 52 N-16-6
still blocks (no admissible adapter) · 53 runtime `unavailable` after N-16-5 · 54 no `adapter.dispatch(`
call site anywhere · 55 real-hardware manual positive case (`.1R.33`) · 56 recovery path (total
principal loss → repeat bootstrap; no shortcut).

---

## 37. Guard-impact inventory (phase prompt §79, §80) — predicted, for the implementation phases

**This planning phase changes no `src/pcae/**` and no `tests/**` — it trips no guard.** The table
below is a **prediction** for `.1R.30` / `.1R.32`:

| Guard family | Predicted impact when the real mechanism lands |
|---|---|
| `NON_REAL` / `SIMULATION_ONLY` assertions | preserved — the deterministic double stays test-only; `.1R.30` adds a **real** mechanism alongside, does not relabel the fixture |
| `human_authenticator` / `hpac_verifier` `_ELIGIBLE_MECHANISM_IDS` guards | evolve — widen the allowlist by exactly `{hpac.fido2.uv_presence.v2}` with a `.1R.30` citation; subset/`==` orientation; no wildcard |
| `approval_presentation` `verifier_kind == "deterministic-test-fixture"` guards | evolve — add `"pcae-protected-local-presentation/1.0"` as a second accepted kind (`.1R.32`) |
| `require_real_assurance` "can only reject" guards | evolve — after `.1R.32` a production descriptor exists; the guard becomes "rejects unless a `PRODUCTION` descriptor + `PRODUCTION` registry records are resolved" |
| `HPACAuthorityClass.PRODUCTION` unreachability guards | evolve — `.1R.32` makes it reachable for exactly one approval; the guard becomes "reachable only via the full real ceremony" |
| gate 5 / gate 9 "no production `AuthenticatedHumanPrincipal`" guards (`runtime_dispatch_gate5.py:34`) | evolve carefully in `.1R.32` — the point-in-time "no real assurance mechanism exists" assertions become "real assurance requires the full HPAC-REQ-054 chain + a `PRODUCTION` descriptor" |
| "no real FIDO2 / hardware / network" no-go assertions (many IV suites `.1R.3`..`.1R.20`) | phase-aware reconciliation in `.1R.30`/`.1R.32` — each widened by exactly the new module set with an explicit citation; **no `def test_` renamed/removed**; broad fixed-SHA A/B in a worktree (the `.1R.26` method) |
| `.1R.16` §35 row 15 "N-16-5 NOT SATISFIED" | flips to SATISFIED only at `.1R.33` closure |
| runtime-posture guards (`Observed`/`unavailable`) | **unchanged** — N-16-5 touches neither |
| `first external effect ABSENT` guards | **unchanged** |

**Historical vs current strategy (phase prompt §80):** historical NON_REAL phases (`.1R.3`..`.1R.20`)
are **not** rewritten as if real FIDO2 existed then — they are preserved; `.1R.30`/`.1R.32` add
companion current-canonical assertions and reconcile point-in-time scope fences phase-aware, exactly
as `.1R.26` did for Gate 7.

**Supply-chain / dependency guards (phase prompt §81):** `fido2>=1.1,<2` + `cryptography>=42,<45` are
already pinned and provenance-reviewed for HATP; N-16-5 adds **no new dependency**. If `.1R.30`
promotes `fido2` from the `hatp-hardware` extra to a base dependency, that is a pinned, reviewed,
non-vendored change with its own guard note. No custom cryptography — `CoseKey.verify` is the library's.

**Platform / browser test matrix (phase prompt §82):** macOS (dev) + Ubuntu (deploy), USB CTAP2
hardware key, NFC optional. **No browser.** No platform-authenticator claim. No unsupported
combination asserted.

---

## 38. Observability + error handling + UI lifecycle (phase prompt §83, §84, §85)

- **Observability (phase prompt §83):** `pcae` MAY expose *mechanism availability* (`healthy` /
  `unavailable`) and *principal enrollment readiness* (boolean) — **not** credential IDs, not public
  keys, not counts that leak enrollment size unnecessarily. **No `pcae runtime inspect` schema change**
  is required by N-16-5.
- **Error handling (phase prompt §84):** no stack traces carrying protocol material in the normal
  helper output; a `terminal_reason_code` (§18) plus a safe human string; cryptographic verification
  failure is **fail-closed** (`hpac_verifier` already raises, never returns a partial trust).
- **UI process lifetime (phase prompt §85):** the presentation helper starts only for one challenge,
  exits after success / cancel / timeout, holds **no** persistent listener, binds **no** socket, and
  uses **no** port. There is no RP-id/ephemeral-port tension because there is no port.

---

## 39. Runtime / no-effect verdict (phase prompt §95)

- Runtime: `not_implemented` / `Observed` / `observe` / `unavailable`; 0 plugins / 0 capabilities —
  **unchanged** (`pcae runtime inspect` re-run at finalization).
- First external effect: **ABSENT** — no `adapter.dispatch(` call site; `RuntimeRegistry` empty.
- No credential, secret, FIDO2/CTAP2, hardware, or protected UI was accessed, created, or referenced.
- No approval / proof / presentation / challenge / nonce consumed; no `consumption.json` written.
- No subprocess, network, socket, or provider SDK call — only read-only `git` inspection and `pcae`
  governance CLI checks.

---

## 40. Planning verdict (phase prompt §95)

**N-16-5 ARCHITECTURE / CONTRACT PLAN: COMPLETE.**

- **REAL HUMAN AUTHENTICATION: ARCHITECTURE FROZEN — IMPLEMENTATION NOT BEGUN.**
  Native CTAP2 roaming hardware FIDO2 (`hpac.fido2.uv_presence.v2`), UP+UV mandatory, offline,
  OS-neutral, fixed internal `rpId` `hpac.pcae.local`. No browser, no WebAuthn ceremony, no web
  origin, no TLS, no loopback. HPAC-001 v2.1 §14/§16/§17/§18 already froze the schemas and sequence;
  `hatp_fido2_provider.py` is the reusable CTAP2 primitive (HPAC-REQ-019).
- **PROTECTED HUMAN APPROVAL UI: ARCHITECTURE FROZEN — IMPLEMENTATION NOT BEGUN.**
  PCAE-owned, process-isolated local presentation helper; `verifier_kind =
  "pcae-protected-local-presentation/1.0"`; deterministic `renderer_profile`; real
  `mechanism_attestation`; administrator-installed `PRODUCTION` descriptor. HPAC-001 §39 already froze
  the evidence schema, digest-equivalence rule, attestation object, and election model.
- **REAL APPROVAL PROOF: ARCHITECTURE FROZEN — IMPLEMENTATION NOT BEGUN.**
  `HPAC-PROOF/2.0` + hash-chained `HPAC-PROOF-LIFECYCLE-EVENT/2.0` + `HPAC-AUTHORITY-CONSUMPTION/2.1`
  — all frozen; single-use; writer-provenance-bound; generation/currentness via the existing
  `HPAC-AUTHORITY-GENERATION-SNAPSHOT/1.0` markers.
- **Contract ownership:** **new companion RHAMP-001 v1.0** (Real Human Authentication Mechanism &
  Protected Presentation Profile) — **no HPAC-001 bump, no MAJOR, no MINOR** to any existing contract
  (REPRC-001 v1.0 precedent).
- **Deployment topology:** frozen safe assumption — local interactive control-plane host + attached
  USB CTAP2 key; headless/remote approval **explicitly deferred**, not N-16-5, not BLOCKED.
- **NON_REAL non-upgradeability:** preserved structurally (§26).
- **N-16-6 / N-16-7 / Slice C boundaries:** preserved — authentication decoupled from admission;
  runtime stays `unavailable`; Slice C keeps no phase ID.
- **Production positive path after N-16-5 alone: NONE. First external effect: UNREACHABLE.**
- No production / contract / schema / runtime / effect change by this phase.

**Runtime: Observed / observe / unavailable. First external effect: ABSENT.**

---

## 41. Recommended next phase (phase prompt §96)

**Requires its own separate explicit human authorization; ID recommended, NOT reserved.**

`149O.20L.7O.3W.1R.2B.1R.1.1R.29` — **N-16-5 Real Human Authentication Mechanism & Protected
Presentation Profile Contract Freeze (RHAMP-001 v1.0)** — scope frozen in §12 / §28 / §29: author
RHAMP-001 v1.0 as a companion under HPAC-001 v2.1's existing extension points (real `mechanism_id`
allowlist; `verifier_kind` allowlist + protected-helper integrity obligations; `rpId`/origin
constants; attestation policy; discoverable-credential / attachment / transport profile; challenge /
proof / presentation TTL bounds; signature-counter policy + counter-state artifact;
`terminal_reason_code` vocabulary; deployment-topology prerequisite). **No `src/pcae/**` change, no
HPAC-001 bump, no implementation, no hardware.** Then `.1R.30` (implementation) → `.1R.31` (IV) →
`.1R.32` (protected presentation + real-assurance wiring) → `.1R.33` (IV + N-16-5 closure incl.
mandatory real-hardware verification). Then N-16-6 → N-16-7 (strictly last). Slice C / Slice D keep no
phase ID until N-16-3..7 all close.

**Do not begin `.1R.29`.**

---

## 42. N-16-5 closure criteria (phase prompt §94) — frozen

N-16-5 is CLOSED only when **all** hold (verified by `.1R.33` IV):
real credential registration via the protected-admin ceremony; real CTAP2 authentication assertion;
real UV policy enforced (UP-only rejected); real protected presentation with deterministic rendering +
attestation; explicit election observed (blind touch rejected); cryptographic challenge/presentation
binding (`approval_preview_digest == human_visible_representation_digest`); a trusted real approval
proof of class `PRODUCTION` / assurance `PRINCIPAL_VERIFIED_INTENT`; canonical lifecycle +
generation/currentness integration; NON_REAL isolation proven; Gate 5 mechanism-neutral integration;
Gate 9 single-use consumption compatible; the ≥ 55-case automated negative suite green; **≥ 1 real
CTAP2 hardware verification** performed; **production first external effect still ABSENT**; runtime
still `unavailable`; N-16-6 still blocking.

---

## 43. No-go confirmations

- No `src/pcae` file was created, modified, or deleted; `git diff --name-only 9901e546 HEAD -- src/pcae` is empty.
- No normative contract file was edited; HPAC-001, RIHAC-001, RIASC-001, HPSE-001, HHCE, PBRD-001, RDGO-001, RPAC-001, REPRC-001, the RE No-Go Registry, and every HATP contract are byte-unchanged.
- No new contract file (`RHAMP-001`) was created; it is a conceptual deliverable for `.1R.29`, not authored now.
- No schema package under `src/pcae/schema_resources/**`, no enrollment CLI, no registry writer, no `HumanAuthenticator` implementation, no `ProtectedApprovalPresentationMechanism` implementation was created.
- No FIDO2 / WebAuthn / CTAP / hardware authenticator was accessed; no `fido2` device call, no `Ctap2`, no `CtapHidDevice` enumeration; no credential was registered or minted; deterministic authentication remains NON_REAL.
- No `HumanPrincipalRegistry` was created or mutated; no principal or credential enrolled or revoked; no `principal-registry.json` written.
- No protected root was created, resolved, or written; no proof, presentation, challenge, nonce, lifecycle event, or `consumption.json` was created or consumed on any path.
- No real assurance mechanism was enabled; `_ELIGIBLE_MECHANISM_IDS` is byte-unchanged; `require_real_assurance` still can only reject.
- No `AuthenticatedHumanPrincipal` of class `PRODUCTION` was produced anywhere.
- No execution was enabled; runtime remains `not_implemented` / `Observed` / `observe` / `unavailable`; 0 plugins / 0 capabilities.
- No runtime capability was elevated or promoted; no `Observed -> Approved/Executable` transition; N-16-7 remains untouched and last.
- No Slice C was implemented; no `adapter.dispatch(` call site exists anywhere in `src/pcae`; Slice C / Slice D keep no phase ID.
- No N-16-5 implementation, and no N-16-6 / N-16-7 work was begun; each remains its own separately authorized implementation + IV pair.
- No adapter (mock or real) was registered, implemented, activated, or called; `RuntimeRegistry` remains empty; no supply-chain admission store or resolver was created or called.
- No MAJOR or MINOR contract version was bumped, forced, or overridden; RHAMP-001 v1.0 is a conceptual delta for `.1R.29`, not applied; HPAC-001 stays v2.1.
- No subprocess, process spawn, `os.system` / `popen` / `spawn` / `exec*`, `pty`, provider SDK, HTTP client, socket, or network path was created or invoked; only read-only `git` history inspection and `pcae` governance CLI checks were run.
- No third-party system, unrelated account, provider API, external network, or deployment target was accessed or mutated.
- No test was added, removed, weakened, skipped, xfailed, or renamed; no planning-traceability test was manufactured; no functional-suite evidence was fabricated for a planning-only phase.
- No reopening of a closed gate boundary (Gate 5, 6, 7, 8, 9), the Slice-A / Slice-B verdicts, or the N-16-3 / N-16-4 closures.
- No human approval was treated as a policy or enforcement override.
- No raw `git commit` / `git push`, no `--no-verify`, no force push, no history rewrite, no hook bypass; governed `pcae` lifecycle only.
- No delegated worker committed, finalized, or pushed; only the primary human-authorized operator holds `.1R.28` lifecycle authority; `DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` is preserved.
- No STOP or BLOCKED condition was reached; every valid early-STOP condition in the phase prompt was checked (§30) and none applies.
- No "Remaining" section is presented; all authorized planning work is complete.

---

*Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.28 — canonical planning artifact. Planning only; no implementation.*
