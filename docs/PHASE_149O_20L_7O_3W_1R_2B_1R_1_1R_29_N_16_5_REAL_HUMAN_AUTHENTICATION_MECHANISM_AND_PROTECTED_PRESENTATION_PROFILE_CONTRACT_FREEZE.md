# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.29 — N-16-5 Real Human Authentication Mechanism & Protected Presentation Profile Contract Freeze (RHAMP-001 v1.0)

**Status: CONTRACT FREEZE COMPLETE — RHAMP-001 v1.0 FROZEN AS THE SOLE NORMATIVE DELTA — IMPLEMENTATION NOT BEGUN.**
**Phase type:** governed contract freeze. New companion contract only. No `src/pcae/**` change, no existing-contract change, no HPAC-001 bump, no schema package, no CLI, no hardware access, no credential creation, no runtime capability change, no external effect.
**Phase-entry SHA:** `4ae0a025` (HEAD at authorization; `git rev-list --count origin/main..HEAD` = 0).
**Authorizing operator:** primary human-authorized operator (this phase's own explicit authorization; phase ID recommended, NOT reserved).
**Runtime:** `not_implemented` / `Observed` / `observe` / `unavailable`. **First external effect: ABSENT.**
**Deliverable:** `docs/contracts/REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md` — **RHAMP-001 v1.0**, RHAMP-REQ-001..169, RHAMP-INV-001..018.

---

## 1. Current verified state (phase prompt §1) — treated as current, not reopened

| Item | State |
|---|---|
| N-16-3 | **CLOSED** (`.1R.23` IV) — not reopened |
| N-16-4 | **CLOSED** (`.1R.27R` IV, non-blocking findings) — not reopened |
| N-16-5 | **PLAN COMPLETE / IMPLEMENTATION PENDING** — this phase freezes its companion contract |
| N-16-6 | **OPEN** — not begun |
| N-16-7 | **OPEN** — strictly last; not begun |
| Current human-auth path | deterministic / NON_REAL (`human_authenticator_deterministic.py`), real-authority-ineligible |
| Current protected presentation | deterministic / NON_REAL (`approval_presentation.py` `verifier_kind == "deterministic-test-fixture"`), real-authority-ineligible |
| Runtime | `not_implemented` / `Observed` / `observe` / `unavailable`; 0 plugins / 0 capabilities |
| First external effect | ABSENT — no `adapter.dispatch(` call site in `src/pcae/**` |

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved (§20).

## 2. Governing planning baseline (phase prompt §2)

`.1R.28` (`docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_28_N_16_5_REAL_FIDO2_WEBAUTHN_CTAP_AND_PROTECTED_HUMAN_APPROVAL_UI_ARCHITECTURE_AND_CONTRACT_PLANNING.md`)
read in full. Every frozen item of `.1R.28` §12 / §28 / §29 is carried into RHAMP-001
v1.0 as normative text; none was disproved by primary source. The one figure
`.1R.28` got wrong — the `terminal_reason_code` count (it says "25" in §12 item 10
and its summary; its §18 block actually enumerates 27 tokens) — is re-derived and
corrected to **41** in RHAMP-001 §49 (RHAMP-REQ-130), exactly as phase prompt §84
directs.

## 3. Primary sources inspected (phase prompt §3, §98 step 2)

**Contracts (normative, read to complete relevant scope):**
`HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md` (**HPAC-001 v2.1** — §0 walls, §6
HPAC-REQ-019 (library reuse), §7 HPAC-REQ-021/022/023/024 (bootstrap anchor),
§8–§9 HPAC-REQ-025..031 (enrollment/multiplicity), §10–§11 HPAC-REQ-032..035
(interface), §14 HPAC-REQ-039..046 (mechanism descriptor, UP/UV), §15
HPAC-REQ-047/048 (domain separation), §16 HPAC-REQ-049..051 (challenge/nonce/TTL
deferral), §18 HPAC-REQ-054/055 (verification sequence), §19 HPAC-REQ-056..058
(trusted construction), §20 HPAC-REQ-059/060 (assurance floor), §21
HPAC-REQ-061..065 (revocation/recovery), §22 HPAC-REQ-066..068 (no fallback),
§23 HPAC-REQ-069/070 (audit/privacy), §30 HPAC-REQ-082/083 (offline/portable),
§31 HPAC-REQ-084 (HATP separation), §32 (reuse map), §34 HPAC-REQ-086
(same-user-agent), §37 (versioning), §38 HPAC-REQ-089 (canonical subject), §39
HPAC-REQ-090/091/092/093 (presentation mechanism / evidence / attestation), §40
HPAC-REQ-094/095/096/097 (proof lifecycle, `terminal_reason_code`), §41
HPAC-REQ-098/098a/099 (consumption, authority-generation snapshot));
`RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md` (**RIHAC-001 v2.0** — §12
condition 7, §16 consumer);
`RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md` (**RIASC-001 v3.0** — five-member
`subject`, `approval_scope`, `approval_mechanism` const);
`RUNTIME_ENFORCEMENT_POSITIVE_RESULT_CONTRACT.md` (**REPRC-001 v1.0** — the
companion-contract shape RHAMP-001 follows; §0/§1/§18/§23/§24 pattern);
`RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md` (**RDGO-001 v3.1** — Gate 5 / Gate 9
timing);
`HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md` (**HPSE-001 v1.1** — separate
namespace precedent, enrollment-vs-approval framing);
`RUNTIME_PROVIDER_ADAPTER_CONTRACT.md` (**RPAC-001 v1.0** — provider-neutral,
N-16-6 territory, untouched);
the HATP family (`HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md`,
`HATP_REMOTE_ASSERTION_CEREMONY_CONTRACT.md`,
`HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md` — separate trust domain; terminology
and remote-deferral precedent).

**Phase reports:** `PROJECT_STATUS.md`; `.1R.28` (governing plan, in full);
`.1R.27R` / `.1R.26` / `.1R.24` (N-16-4 lineage — companion-contract precedent);
`.1R.2B` (HPAC-001 freeze).

**Production source (read as evidence only — not modified):**
`src/pcae/core/hpac_verifier.py` (`_ELIGIBLE_MECHANISM_IDS =
frozenset({"hpac.deterministic.test-only.v1"})` line 128; `_verify_assertion_material`
line 429 — `proof.mechanism_id not in _ELIGIBLE_MECHANISM_IDS` reject at line 460,
**no real signature math**; `_check_up_uv` line 467; `_authority_class_of` line
485; `verify_human_authentication` line 494, `require_real_assurance` at 508 /
705 — "rejects unless PRODUCTION"; `is_verifier_authenticated_principal` line 306
— the trust boundary);
`src/pcae/core/human_principal_registry.py` (`REGISTRY_SCHEMA_VERSION =
"HPAC-REGISTRY/2.0"` line 36; `CredentialRecord` line 99 — closed fields
`credential_id, principal_id, mechanism_id, public_key, assurance_capabilities,
status, enrollment_provenance_ref, enrolled_at, revoked_at` — **no private-key /
PIN / biometric field exists**; `HumanPrincipalRegistryStore.production()` line
264; `enroll_principal` line 428, `enroll_credential`);
`src/pcae/core/approval_presentation.py` (`PresentationMechanismDescriptor` line
118 with `verifier_kind` / `renderer_profile`; `verifier_kind !=
"deterministic-test-fixture"` reject at line 658;
`ProtectedApprovalPresentationMechanism` Protocol line 373;
`TrustedApprovalPresentationStore` line 440);
`src/pcae/core/hatp_fido2_provider.py` (`_HATP_RP_ID = "hatp.pcae.local"` line
102, `_HATP_ORIGIN = "pcae-hatp://hatp.pcae.local"` line 103, `_RP_ID_HASH` line
104; `CoseKey.parse(cbor.decode(record.public_key))` line 513;
`cose_key.verify(bytes(authenticator_data) + client_data.hash, signature)` line
514; `is_user_present()` line 518 — **UP only, no UV check** (finding N-16-5-3);
`CollectedClientData.create(type=GET, challenge=…, origin=_HATP_ORIGIN)` line
429; `allow_list=[{"type": "public-key", "id": credential_id}]` line 439;
`CtapHidDevice.list_devices()` — monkeypatched in tests, "REAL HARDWARE NOT
EXERCISED");
`pyproject.toml` — `fido2>=1.1,<2` + `cryptography>=42,<45` already declared.

Every load-bearing RHAMP-001 clause is anchored to an HPAC-REQ-### id or a named
production symbol; no design is taken from a phase report alone.

## 4. Initial repository inspection (phase prompt §4)

```
git status --branch --short   → ## main...origin/main   (clean at entry)
git rev-list --count origin/main..HEAD  → 0
pcae health     → Session continuity: verified / enforcement: strict / Git status: clean
pcae check      → PCAE check passed
pcae status coherence → coherent
pcae doctor task-memory → warnings only (pre-existing tasks/done/ entries not listed in tasks/DONE.md — carried, not introduced by this phase)
pcae push check → Check: passed / Phase report trust: passed / Phase report identity: passed / Mode: nothing_to_push
pcae runtime inspect → Runtime status: not_implemented / state: Observed / capability: unavailable / plugins 0 / capabilities 0 / Permission Broker: execution_unavailable / governance posture: non-executing
pcae notify status → Telegram configured, enabled, ready
pcae phase-report show --latest → .1R.28 (completed, report complete, pushed, origin/main..HEAD 0)
```

Confirmed: `.1R.28` is the latest completed phase; no active governed phase
before startup (idle task); `origin/main..HEAD` = 0; runtime Observed / observe
/ unavailable; first external effect absent.

## 5. Native CTAP2 terminology verdict (phase prompt §7) — FROZEN in RHAMP-001 §3

**Verdict:** RHAMP-001 v1.0 is a **native CTAP2** mechanism. FIDO2 (umbrella),
CTAP2 (the protocol used, over USB-HID / NFC via `fido2.ctap2`), and WebAuthn
(the browser client API — **not used**) are frozen distinct (RHAMP-REQ-008).
RHAMP-001 adopts the WebAuthn/CTAP2 **wire shapes** (`authenticatorData`, COSE
keys, the `sign(authenticatorData ‖ clientDataHash)` assertion form) because
`fido2` implements them and they give byte-exact binding (RHAMP-REQ-009) — this
is **not** "running a WebAuthn ceremony" and SHALL not be described as one
(RHAMP-REQ-010).

**WebAuthn / browser-origin exclusion (phase prompt §62):** RHAMP-001 §56
(RHAMP-REQ-141/142) — no browser ceremony, no web origin, no TLS, no
secure-context, no localhost HTTP service, no ephemeral port, no CSRF/cookie/
session model, no web UI. A future browser/loopback profile requires a new
governed HPAC-001 version, not a RHAMP-001 MINOR.

## 6. RP ID semantics (phase prompt §8) — FROZEN in RHAMP-001 §6

`rp_id = "hpac.pcae.local"` — a compiled-in PCAE constant, distinct from HATP's
`hatp.pcae.local` (RHAMP-REQ-017). `authenticatorData.rpIdHash` SHALL equal
`SHA-256(UTF-8("hpac.pcae.local"))`, recomputed from the constant at verify time
(RHAMP-REQ-018). Not derived from repo / cwd / env / agent / hostname /
deployment / task / caller (RHAMP-REQ-019). **Not a web origin, no browser
origin claim** (RHAMP-REQ-020). Credentials are permanently bound to it; a
future `rp_id` change needs an explicit migration path (RHAMP-REQ-021).
Identical string on macOS and Linux → no per-host RP registration, no
cross-trust-domain problem.

## 7. PCAE client-data schema / hash semantics (phase prompt §9) — FROZEN in RHAMP-001 §7

RHAMP-001 does **not** use a browser `clientDataJSON` and does **not** treat any
string as a browser security origin. It defines `RHAMP-CLIENT-CONTEXT/1.0`
(RHAMP-REQ-023): a closed object of `client_context_schema`, `ceremony_kind`
(const `runtime-invocation-approval` / `credential-enrollment`),
`context_identifier` (const `pcae-hpac://hpac.pcae.local/runtime-invocation-approval.v2`
— classified as a **PCAE-internal domain-separation constant, NOT a browser
security origin**, RHAMP-REQ-028), `domain_separator`, `challenge_digest`,
`approval_subject_digest`, `trusted_presentation_digest`, `principal_id`,
`credential_id`, `invocation_id`, `attempt_id`, `nonce`, `issued_at`,
`expires_at`, `mechanism_id`. `client_data_bytes` = HPAC-REQ-089 canonical
serialization; `client_data_hash = SHA-256(client_data_bytes)`; the CTAP2 call
signs `authenticatorData ‖ client_data_hash` (RHAMP-REQ-024). Verification
reconstructs the object from trusted state, recomputes the hash, and rejects any
mismatch (`client_data_hash_mismatch`) or a non-constant `ceremony_kind` /
`context_identifier` (`client_data_context_mismatch`) (RHAMP-REQ-025). No field
is caller-selectable (RHAMP-REQ-026).

**No false phishing-resistance claim (phase prompt §10):** RHAMP-001 §8
(RHAMP-REQ-027) states exactly the true posture — the `rpIdHash` + canonical
`client_data_hash` bind the assertion to PCAE's ceremony context; the native
profile does **not** claim browser / WebAuthn origin enforcement. The
anti-substitution property provided is a **local helper-integrity** property
(RHAMP-REQ-029), not a network-origin one.

## 8. Mechanism ID (phase prompt §11) — FROZEN in RHAMP-001 §4

Real allowlist = exactly `{hpac.fido2.uv_presence.v2}` — one entry, no wildcard,
no `fido2.*`, no `fnmatch` (RHAMP-REQ-011). Verifier-owned — resolved from
`CredentialRecord.mechanism_id`, never caller-declared (RHAMP-REQ-012).
`hpac.deterministic.test-only.v1` stays permanently non-real (RHAMP-REQ-013).
`_ELIGIBLE_MECHANISM_IDS` widens by exactly `{"hpac.fido2.uv_presence.v2"}` in
`.1R.30`, `frozenset` literal, with a citation (RHAMP-REQ-109).

## 9. Verifier kind (phase prompt §12) — FROZEN in RHAMP-001 §5

Real allowlist = exactly `{pcae-protected-local-presentation/1.0}`
(RHAMP-REQ-014). It is presentation assurance **only** with an
administrator-installed `active` `PRODUCTION`-class descriptor, a verified
`mechanism_attestation`, helper integrity (§30), and byte/digest re-render
equality (RHAMP-REQ-015). A caller / repository / agent SHALL NEVER mint or
attest it; only HPAC-REQ-080's protected administrator may create or revoke the
descriptor (RHAMP-REQ-016).

## 10. Authenticator profile / UP-UV / auth≠approval / ceremony order

| Concern | Frozen (RHAMP-001) |
|---|---|
| Authenticator profile (§13) | roaming / cross-platform, CTAP2, non-discoverable, `allowList`-bound, USB-HID or NFC, UP + UV — §9 RHAMP-REQ-030; unsupported: BLE, hybrid/cross-device, synced passkey, platform authenticator, discoverable/resident, usernameless — RHAMP-REQ-031/032 |
| UP / UV policy (§14, §18) | UP required, UV required, immutable minimum; UP-only never yields `AuthenticatedHumanPrincipal`; UV satisfied inside the authenticator (PCAE sees only `FLAG.UV`); no downgrade / no fallback — §10 RHAMP-REQ-033..036; **RHAMP adds the UV check HATP omits** (finding N-16-5-3) |
| Authentication ≠ approval (§15, §19, §20) | assertion / `AuthenticatedHumanPrincipal` / touch are each **not** approval; presentation resolution (HPAC-REQ-054 step 5) and signature (step 6) are independent verifier steps; blind touch → `election_missing` — §11 RHAMP-REQ-037/038 |
| Ceremony model (§16) | single step-up assertion at approval time whose canonical client-data carries the presentation digest; no session, no cache — §12 RHAMP-REQ-039 |
| Ceremony order (§65) | reserve `approval_id` → render + hash facts → **explicit `approve` election** → **then** build challenge + client-data + drive CTAP2 assertion → verify (HPAC-REQ-054) → mint proof; reject → no assertion, no proof — §12 RHAMP-REQ-040/041 |

## 11. Registration lifecycle / first-credential bootstrap / bootstrap evidence

| Concern | Frozen (RHAMP-001) |
|---|---|
| Registration flow (§17) | protected-admin ceremony (never ordinary CLI/hook/task/stdin/env; same-UID agent denied) → protected presentation of the exact identity + credential → protected-admin election → CTAP2 `makeCredential` (ES256, UP+UV, non-discoverable, no attestation) → verify → `enroll_credential` (opaque `hpc-<hex>` id, not the raw CTAP2 id) [atomic, read-back] → sidecar + counter-state create → durable provenance — §13 RHAMP-REQ-043..046 |
| First-credential bootstrap authority (§18) | **HPAC-REQ-023's external deployment-owner protected administration principal** — owns the protected root outside every repo, unavailable to ordinary same-user agent execution. **Never** an arbitrary CLI caller, OS username, first registrant, agent identity, repo identity, Git identity, session id, env var, or stdin. Unprovable anchor → `bootstrap_authority_unproven` / BLOCK — §14 RHAMP-REQ-047..050 |
| Bootstrap evidence (§19) | operation id, `principal_id`, `credential_id`, raw-credential-id digest, `mechanism_id`, challenge/nonce id, registrar authority provenance, timestamp, `credential_generation` before/after, result digest — audit evidence, **not** reusable authority — §15 RHAMP-REQ-051/052 |
| Multi-credential policy (§20) | 1 principal → 0..N `active` credentials; unique credential ids; no credential under two principals; `allowList` from all active credentials; authenticator selects — §16 RHAMP-REQ-053/054 |
| Discoverable-credential policy (§21) | non-discoverable only; `allowList`-bound; no usernameless / principal-discovery in v1 — §9 RHAMP-REQ-030/032 |

## 12. Credential schema / private-key boundary / attestation / counter

| Concern | Frozen (RHAMP-001) |
|---|---|
| Credential schema (§22) | `CredentialRecord` **byte-unchanged**; `public_key = hex(cbor(COSE_Key))`; `assurance_capabilities` = `("UP","UV",<"usb"|"nfc">)`. Raw CTAP2 credential id + `rp_id` + transports + advisory AAGUID → **new protected sidecar** `RHAMP-FIDO2-CREDENTIAL/1.0` at `<HPAC_PROTECTED_ROOT>/credentials/<credential_id>/fido2-credential.json` (immutable, create-only, read-back verified) — §17 RHAMP-REQ-055..058 |
| Private-key / biometric / PIN boundary (§23) | PCAE stores **no** private key (structural — no field), **no** biometric template, **no** PIN; only `FLAG.UV` observed — §18 RHAMP-REQ-059/060 |
| Attestation policy (§24) | not required for authority; `none`/`self`/`packed` accepted unvalidated; enterprise attestation prohibited; no MDS; no AAGUID security classification; no device-uniqueness claim — §19 RHAMP-REQ-061..064; §52 RHAMP-REQ-134 |
| Signature-counter policy (§25) | not "always monotonic"; `0`/absent → accept; `> last` → accept + update; non-zero `<= last` → **fail closed** `signature_counter_regression` + audit + admin-review flag; **never auto-revoke**; anomaly is a signal, not proof of cloning — §20 RHAMP-REQ-065..067 |
| Counter-state artifact (§26) | **new protected** `RHAMP-COUNTER-STATE/1.0` at `<HPAC_PROTECTED_ROOT>/credentials/<credential_id>/counter-state.json`: `last_accepted_meaningful`, `last_observed_raw`, `generation`, `updated_at`, `writer_provenance_ref`, `review_flag`; atomic replace + read-back; corruption / missing for an active credential → fail closed (never silently "counter 0"); **not** a `CredentialRecord` change, **not** an authority-generation input — §21 RHAMP-REQ-068..070 |
| Counter update ordering (§27) | verify (incl. counter check) → step-10 proof mint → **then** atomic counter-state update, before the `AuthenticatedHumanPrincipal` is returned; a crash between mint and counter update does not create replay authority (challenge/nonce one-use); non-atomic store → BLOCK — §22 RHAMP-REQ-071..073 |

## 13. TTL / freshness / replay

| Concern | Frozen (RHAMP-001) |
|---|---|
| Challenge TTL (§28) | ≤ **120 s**; trusted coordinator clock; expired → `challenge_expired`; expiry ≠ revocation ≠ currentness — §23 RHAMP-REQ-074/075 |
| Proof age (§29) | `max_proof_age_seconds` ≤ **300 s**; older → ineligible even if cryptographically valid (`proof_age_exceeded`); generation currentness separately required — §24 RHAMP-REQ-076 |
| Presentation / approval expiry (§30) | presentation `expires_at` == RIASC approval `expires_at`; `approval_preview_digest == human_visible_representation_digest` binds the exact presentation to the exact approval — §25 RHAMP-REQ-077/078 |
| Challenge entropy (§31) | CSPRNG ≥ 256 bits, trusted component only; no predictable/sequential/timestamp-only/reusable value; NON_REAL fixtures may stay deterministic and stay structurally NON_REAL — §26 RHAMP-REQ-079 |
| Replay (§32) | registration challenge one-use; auth/approval challenge + nonce one-use (`challenge_replayed`); approval proof one authority lifecycle; Gate-9 `consumption.json` final single-use (`consumption_replay`); replay at any layer fails closed — §27 RHAMP-REQ-080/081 |

## 14. Protected presentation helper (phase prompt §33, §34, §35, §63, §64)

| Concern | Frozen (RHAMP-001) |
|---|---|
| Helper trust model (§33) | PCAE-owned fixed implementation (identity + version); administrator-installed `active` descriptor; **helper integrity evidence per §30**; canonical payload over a PCAE-owned channel the agent cannot write; no substitution/mutation/reorder/suppression of the 13 facts; agent cannot launch/replace/observe/scrape/feed it; **caller-nominated executable/helper prohibited** — §28 RHAMP-REQ-082/083 |
| Helper process model (§34) | local process only; no agent-owned helper; no repo-provided executable; no arbitrary shell; no remote endpoint; no listener / socket / port; short-lived; one approval challenge per lifecycle where practical; terminates on success/reject/cancel/timeout/error; renders on a dedicated surface, not the agent TTY — §29 RHAMP-REQ-084..086 |
| Helper integrity evidence (§35) | pinned executable digest in a protected installation record (verified pre-launch) + descriptor digest + `verifier_configuration_digest` (+ supply-chain-admitted package / signed descriptor where the architecture provides it); **not path/name alone**; unprovable → BLOCK; failure → `helper_integrity_unverified`; **separate from N-16-6 adapter admission** — §30 RHAMP-REQ-087..090 |
| Canonical presentation payload (§36) | exactly HPAC-REQ-091's 13 closed `human_visible_facts`; RHAMP adds/removes none; all 13 rendered; `operation_effect_scope_display` renders the **complete** `approval_scope`, no truncation/collapse of a mandatory field; no caller label / hidden field / non-attested authority text — §31 RHAMP-REQ-091/092 |
| Display / digest equivalence (§37) | closed facts → deterministic `renderer_profile` → displayed bytes (UTF-8/NFC/LF) → SHA-256 → `human_visible_representation_digest`; resolver re-renders and requires byte/digest equality; `approval_preview_digest` equality; inequality → `presentation_digest_mismatch` / `subject_digest_mismatch` — §32 RHAMP-REQ-093/094 |
| Untrusted-content escaping (§38) | repo/task/path/prompt/scope strings are untrusted; strip C0/C1, neutralize ANSI/terminal escapes, escape native-UI markup, prevent line-truncation / RTL-override ambiguity, delimit untrusted strings; no repo text can alter a trusted label/control; digest is over the neutralized displayed bytes — §33 RHAMP-REQ-095/096 |
| Approve / Reject action (§39) | explicit Approve + explicit Reject controls; **no implicit approval, no timeout-as-approval, no touch-alone-as-approval**; touch only after a distinct Approve election that the ceremony binds; reject → no assertion, no proof — §34 RHAMP-REQ-097..099 |
| No accidental approval (§40) | no default affirmative control; no ambiguous Enter-submits-Approve; clear PCAE identity; consequential wording where the effect class warrants; expired presentation visibly invalid + Approve disabled; explicit post-approval confirmation state — §35 RHAMP-REQ-100 |
| Helper IPC (§63) | provenance-bound local invocation; canonical payload transmitted **without shell interpretation**; one-shot request/response; response bound to challenge id + presentation digest + decision; unbound response → `helper_response_untrusted` — §57 RHAMP-REQ-143 |
| Helper response (§64) | closed object: schema/version, `challenge_id`/`approval_id`, `presentation_digest`, `decision`, `renderer_profile`/`verifier_kind`, integrity/provenance binding, timestamp, self-excluding digest; structure alone ≠ trust — §58 RHAMP-REQ-144/145 |

## 15. Client-data approval binding & assertion verification (phase prompt §41, §42)

**Approval client-data binding (§41):** RHAMP-001 §36 RHAMP-REQ-101 — the
canonical client-data binds `ceremony_kind`, the domain-separation
`context_identifier` + `domain_separator`, the challenge `nonce`, `principal_id`
+ `credential_id`, `trusted_presentation_digest`, `approval_subject_digest`,
`invocation_id` + `attempt_id`, `issued_at` + `expires_at`, and
`mechanism_id`/profile version — digests are the binding; no redundant raw
payload.

**Assertion verification requirements (§42):** RHAMP-001 §37 RHAMP-REQ-102/103 —
credential lookup + principal ownership; `rpIdHash` equality; COSE signature via
`CoseKey.parse(cbor.decode(public_key)).verify(authenticatorData ‖
client_data_hash, sig)`; `client_data_hash` equality + context constants; UP
**and** UV; §20 counter policy; credential + principal `active`; challenge
active/unconsumed + `challenge_digest` recompute; mechanism eligible + ≥
`PRINCIPAL_VERIFIED_INTENT`; HPAC-REQ-054 step 5 presentation + step 9 lifecycle/
consumption; proof age + authority-generation currentness. **No custom
cryptography — the library's `CoseKey.verify`.** The real branch is reachable
only when `_authority_class_of(...)` is `PRODUCTION` for every resolved record
and the resolved mechanism is in the real allowlist — a `FIXTURE_NON_REAL`
credential never reaches real signature verification (finding N-16-5-2).

## 16. HATP FIDO2 reuse boundary (phase prompt §43) — FROZEN in RHAMP-001 §38

`hatp_fido2_provider.py` primitives are reusable **as a shared library only**
(HPAC-REQ-019), never as a live HATP trust dependency, never against HATP state.
**Reusable:** CTAP2 device enumeration, `makeCredential`/`getAssertion`
invocation, `CoseKey` parse+verify, `CollectedClientData` construction as a
wire-shape helper, `allow_list` construction, cancellation/timeout handling.
**NOT reusable as-is:** the UP-only presence check (RHAMP adds `FLAG.UV`,
finding N-16-5-3). **NOT reusable:** `_HATP_RP_ID` / `_HATP_ORIGIN`, HATP
registry / `SignerRecord` semantics (separate trust domain, HPAC-REQ-084).
Future implementation SHOULD extract shared primitives into a library module
only if needed — blind code copying is not frozen and is discouraged
(RHAMP-REQ-104/105).

## 17. Dependency policy / mechanism-registry evolution (phase prompt §44, §45)

**Dependency (§44):** reuse the already-declared `fido2>=1.1,<2` +
`cryptography>=42,<45`; **no new dependency**; pins not loosened; no custom
signature algorithm; no opaque binary vendoring; no dependency install in
`.1R.29` — §39 RHAMP-REQ-106..108.

**Real verifier / mechanism registry (§45):** `_ELIGIBLE_MECHANISM_IDS` gains
exactly `{hpac.fido2.uv_presence.v2}` (frozenset literal, `.1R.30` citation, no
wildcard); `approval_presentation.py` gains exactly
`pcae-protected-local-presentation/1.0` as a second accepted kind (`.1R.32`,
`PRODUCTION`-descriptor-gated); `deterministic-test-fixture` stays
`FIXTURE_NON_REAL`-only — §40 RHAMP-REQ-109/110.

## 18. NON_REAL non-upgradeability / ownership / revocation / currentness / proofs

| Concern | Frozen (RHAMP-001) |
|---|---|
| NON_REAL non-upgradeability (§46) | `NON_REAL + real-looking mechanism_id + copied fields != REAL authority`; REAL eligibility requires the full structural conjunction (real mechanism impl + verifier-owned registry identity + canonical `PRODUCTION`-root credential + crypto verification + real presentation assurance + lifecycle/currentness); enforced by `SIMULATION_ONLY`, the frozenset, `HPACAuthorityClass`, `_authority_class_of`, the identity registry, `__reduce__` raising — none weakened — §41 RHAMP-REQ-111..113 |
| Principal / credential ownership (§47) | the canonical `CredentialRecord` determines `principal_id`; caller cannot override; duplicate credential id under another principal invalid — §42 RHAMP-REQ-114/115 |
| Revocation / deactivation (§48, §49) | revoked credential / revoked-or-disabled principal cannot authenticate; revocation invalidates outstanding challenges, bound proofs, unconsumed approvals, PB projections (HPAC-REQ-063/064) — even within challenge TTL; only an already-consumed `consumption.json` remains audit evidence — §43 RHAMP-REQ-116/117 |
| Credential generation / currentness (§50) | **reuse** the existing `credential_generation` marker (HPAC-REQ-098a, whole-`CredentialRecord` digest); **no parallel freshness system**; moved generation → `authority_generation_stale`; if the existing contract can't accommodate it → BLOCK (not anticipated) — §44 RHAMP-REQ-118..120 |
| Real authentication proof (§51) | **no new artifact** — existing `HPAC-PROOF/2.0` already carries `mechanism_id`, `assertion`, `up`, `uv`, digests, `trusted_presentation_ref`; real branch populates them with real CTAP2 values; schema byte-unchanged — §45 RHAMP-REQ-121/122 |
| Real approval proof (§52) | verified CTAP2 auth (UP+UV) + resolved presentation digest + explicit approve election + exact challenge/subject/client-data binding + lifecycle/generation currentness → a `PRODUCTION` / `PRINCIPAL_VERIFIED_INTENT` proof for exactly one approval; still `approval proof != PB permission != RE approval != runtime capability != execution` — §46 RHAMP-REQ-123/124 |
| Proof writer (§53) | only the trusted verifier/proof writer under the protected root (`is_verifier_authenticated_principal` boundary) mints `proof.json` / lifecycle / sidecar / counter-state / `consumption.json`; atomic, create-only (atomic-replace for counter-state), read-back verified; a structurally valid file is not authority; reuse the existing writer; no second authority-artifact constructor — §47 RHAMP-REQ-125/126 |
| Raw-artifact retention / privacy (§54) | retain opaque ids, COSE public key, raw credential id (sidecar only), transports, advisory AAGUID, UP/UV audit booleans, digests; retain the existing base64url `assertion` blob only (no *additional* raw-blob field); **never** PIN / biometric / private key / device serial — §48 RHAMP-REQ-127/128 |

## 19. Terminal reason vocabulary (phase prompt §55, §56, §84) — RE-DERIVED, 41 codes

**Count discrepancy disclosed (RHAMP-REQ-130):** `.1R.28` §12 item 10 and its
summary say "25 codes"; its §18 enumerated block actually lists **27** tokens
and omits enrollment/bootstrap, helper-integrity, explicit-human-rejection,
cancellation, and timeout codes. RHAMP-001 §49 re-derives the closed set from
**every** rejection point across the real ceremony and freezes **41** codes
(RHAMP-INV-010). The full table (code / stage / trigger / human-visible category
/ retryable / audit significance / authority result) is RHAMP-001 §49.1.

**Terminal-reason semantics (§56):** five distinct human-visible categories —
`enrollment_error`, `not_authenticated`, `presentation_integrity_error`,
`approval_declined` (human reject / cancel / timeout), `authority_stale`,
`internal_error` — all yield **no approval authority** but carry distinct audit
meaning; a human rejection is never reported as an authentication failure and
vice versa (RHAMP-001 §50 RHAMP-REQ-131).

## 20. Transport / topology / deferral (phase prompt §57–§61)

| Concern | Frozen (RHAMP-001) |
|---|---|
| Transport policy (§57) | USB-HID + NFC supported; BLE, hybrid/cross-device, remote phone/passkey, platform authenticators **not supported** in v1.0 (each needs a future contract) — §51 RHAMP-REQ-132/133 |
| Device-identity / attestation claims (§58) | credential validity ≠ unique physical device identity; no MDS, no model trust, no AAGUID classification; a future device claim needs a new contract version — §52 RHAMP-REQ-134 |
| Local interactive control-plane requirement (§59) | REAL approval requires a local interactive control-plane host that can launch the helper, reach the roaming CTAP2 key, collect the election, run the CTAP2 ceremony locally; headless-only host **ineligible**; derivable from HPAC-REQ-021/022/082/083; **not BLOCKED** — §53 RHAMP-REQ-135/136 |
| Dell / Mac topology consequence (§60) | if the deployment host is headless with no key, RHAMP-001 v1.0 REAL approval cannot run there directly; the human carries the USB key to whichever local interactive control-plane host owns the authority; `rp_id` constant is identical on Mac + Linux; **no remote Mac→Dell transport added**; deployment host ≠ authority-UI host — §54 RHAMP-REQ-137/138 |
| Remote approval deferred (§61) | remote approval, controller→deployment challenge transport, networked relay, headless approval service — **OUT OF SCOPE**, deferred to a separate authorized architecture (may reuse HATP remote-assertion patterns); **no network authority transport authorized by this contract** — §55 RHAMP-REQ-139/140 |

## 21. Cancel / timeout / concurrency / restart / recovery (phase prompt §66, §67, §68, §69)

RHAMP-001 §59 RHAMP-REQ-146..148: helper close/cancel → `ceremony_cancelled`;
timeout → `ceremony_timed_out`; challenge past TTL → `challenge_expired`; each →
no proof, no authority. **Concurrency:** exactly one active
protected-approval ceremony per `(invocation_id, attempt_id)`; concurrent
*unrelated* approvals allowed only with unique challenge + helper lifecycle +
presentation digest + independent assertion; a stale window/response for A
cannot satisfy B → `ceremony_superseded`. **Restart:** pending ceremony trust
lost, new challenge required; no stale-helper continuation; no durable
pending-ceremony store; the durable truth is the canonical proof/lifecycle/
consumption records, re-verified from scratch (HPAC-REQ-058).

**Recovery (§69):** RHAMP-001 §60 RHAMP-REQ-149 — lost/compromised credential →
`revoke_credential` + `enroll_credential` of a replacement under the same
principal; loss of **all** credentials for the sole principal → REAL approval
unavailable until a protected administrative re-bootstrap; **no silent bypass,
no fallback to NON_REAL** under any recovery condition; full automated recovery
beyond re-bootstrap deferred.

**Protected admin enrollment / audit (§70, §71):** RHAMP-001 §61 RHAMP-REQ-150/151
— local interactive mode; canonical principal selection by the protected admin;
explicit protected-administrative confirmation; presence + UV; no agent-delegated
enrollment authority; durable audit for enrollment / revocation / replacement /
recovery (the §15 field set); audit records do not authenticate future approvals.

## 22. Real-hardware verification requirement (phase prompt §72, §73, §74)

RHAMP-001 §62 RHAMP-REQ-152/153 — **before N-16-5 closes (in `.1R.33`)**, ≥ 1
real CTAP2 hardware verification with minimum evidence: supported roaming USB
key; real `makeCredential` enrollment → canonical records; real `getAssertion` →
assertion passing the full §37 sequence with UP + UV observed; a
presentation-bound approval end-to-end → `PRODUCTION` `AuthenticatedHumanPrincipal`
for exactly one approval; wrong-challenge rejected; missing/failed UV rejected
where testable; replay rejected; revoked credential rejected. **No hardware
accessed in `.1R.29` or any phase before `.1R.33`.**

**Automated-fixture policy (§73, §74):** RHAMP-001 §63 RHAMP-REQ-154/155 —
deterministic virtual/synthetic authenticator fixture, explicitly TEST /
NON_PRODUCTION (monkeypatched `CtapHidDevice`/`Ctap2` + in-memory ES256 key —
the `hatp_fido2_provider` pattern); protocol test vectors; crypto negative
cases; mocked CTAP transport; the ≥ 55-case matrix from `.1R.28` §36. **No
synthetic object ever becomes REAL authority in a production registry.** N-16-5
closure requires **both** the automated suite green **and** the real-hardware
evidence — not substitutes.

## 23. Existing-contract versioning re-derivation (phase prompt §6, §86, §87, §100)

Each artifact's own versioning rule was re-read (HPAC-001 §37; RIHAC-001 /
RIASC-001 / RDGO-001 §21 / RPAC-001 / REPRC-001 §24 versioning sections; PBRD-001).

| Artifact | Current | RHAMP-001 dependency | Semantic change? | Bump required? | Reason |
|---|---|---|---|---|---|
| **HPAC-001** | v2.1 | RHAMP-001 profiles its `mechanism_id` allowlist, `verifier_kind` closed set, `terminal_reason_code` id, TTL ("a future implementation phase sets it"), attestation-silence extension points | **NO** | **NONE** | every residual decision fits an existing extension point; RIHAC-001 §12 condition 7 names "HPAC-001 v2.1" literally — a bump would cascade |
| **RHAMP-001** *(new companion)* | — → **v1.0** | is the contract | new artifact | **new v1.0 initial freeze** | REPRC-001 v1.0 precedent exactly — a companion to avoid a MAJOR/MINOR cascade on the parent |
| RIHAC-001 | v2.0 | consumer — §12 condition 7 already requires "HPAC-001 v2.x proof verification against current protected state"; a real proof satisfies it | NO | NONE | unchanged |
| RIASC-001 | v3.0 | `approval_mechanism` already const `trusted_subject_bound_confirmation`; wire shape unchanged | NO | NONE | unchanged |
| HPSE-001 | v1.1 | pattern precedent only | NO | NONE | unchanged |
| HHCE-001 | current | pattern precedent only | NO | NONE | unchanged |
| HPAC-AUTHORITY-CONSUMPTION | /2.1 | Gate 9 consumption schema unchanged; `credential_generation` already folds the whole `CredentialRecord` | NO | NONE | unchanged |
| PBRD-001 | v3.0 | PB never receives raw proof material (HPAC-REQ-035); consumes only the RIHAC projection | NO | NONE | unchanged |
| RDGO-001 | v3.1 | Gate-5 / Gate-9 timing unchanged; the real proof flows the same steps | NO | NONE | unchanged |
| RPAC-001 | v1.0 | provider-neutral; RHAMP-001 touches no adapter | NO | NONE | unchanged |
| REPRC-001 | v1.0 | Gate-7 positive result independent of the auth mechanism | NO | NONE | unchanged |
| RE No-Go Registry | schema 1.1 | none | NO | NONE | unchanged |
| HATP contracts | — | RHAMP-001 reuses `hatp_fido2_provider` **code** as a library, not HATP **state** (HPAC-REQ-019/084) | NO | NONE | domain separation preserved |

**Expected result confirmed: no existing contract version movement.** The only
normative delta of the entire N-16-5 track through `.1R.29` is **RHAMP-001 v1.0**
(RHAMP-INV-016). No existing contract requires a MINOR or MAJOR — the phase
proceeds to finalization (phase prompt §6/§87).

**RHAMP-001 versioning rules (phase prompt §86):** RHAMP-001 §70
RHAMP-REQ-166..169 — MAJOR for: browser/WebAuthn web-origin ceremony; remote/
headless approval or any network authority transport; discoverable/resident/
usernameless credentials; relaxing UP or UV; changing the election ceremony or
its ordering; changing the bootstrap authority model; making attestation or a
device claim authoritative; a transport outside `{USB-HID, NFC}`; making
NON_REAL upgradeable. MINOR for: re-stating verified behaviour; an additional
authenticator model within the frozen profile; tightening (never loosening) a
TTL; adding a `terminal_reason_code` for a new terminal path without
removing/re-meaning an existing one; a test-fixture clarification. No version
may retrospectively widen an issued proof's or enrolled credential's assurance.

## 24. Guard-impact inventory (phase prompt §75, §76) — predicted, for `.1R.30` / `.1R.32`

**This contract-freeze phase changes no `src/pcae/**` and no `tests/**` — it
trips no guard.** Broad `tests/` needle search performed for the phase-prompt
§75 term set (`NON_REAL`, `real_assurance` / `require_real_assurance`,
`hpac.fido2`, `human_authenticator`, `protected_presentation` /
`approval_presentation`, `mechanism_id`, `verifier_kind`,
`HumanPrincipalRegistry`, `_ELIGIBLE_MECHANISM_IDS`, `user_presence` /
`user_verification`, proof writer, `mechanism_attestation`, `PRODUCTION`
descriptor, `Gate5` / `Gate6` / `Gate7` / `Gate9`, authority generation, "no
hardware", "no real mechanism", contract hashes, consumer inventories,
meta-guards) to build the predicted impact table — recorded in RHAMP-001 §67
RHAMP-REQ-162/163:

| Guard family | Predicted impact when the real mechanism lands (`.1R.30`/`.1R.32`) |
|---|---|
| `_ELIGIBLE_MECHANISM_IDS` guards | widen by exactly `{hpac.fido2.uv_presence.v2}`; subset/`==` orientation; no wildcard; `.1R.30` citation |
| `verifier_kind == "deterministic-test-fixture"` guards | add `pcae-protected-local-presentation/1.0` as a second accepted kind; `.1R.32` |
| `require_real_assurance` "can only reject" guards | evolve → "rejects unless a `PRODUCTION` descriptor + `PRODUCTION` registry records resolve" |
| `HPACAuthorityClass.PRODUCTION` unreachability guards | evolve → "reachable only via the full real ceremony" |
| Gate 5 / Gate 9 "no production `AuthenticatedHumanPrincipal`" guards | evolve carefully in `.1R.32` → "real assurance requires the full HPAC-REQ-054 chain + a `PRODUCTION` descriptor" |
| "no real FIDO2 / hardware / network" no-go assertions (`.1R.3`..`.1R.20` IV suites) | phase-aware reconciliation, each widened by exactly the new module set with an explicit citation; **no `def test_` renamed or removed** (`.1R.19R.1` / `.1R.22R` `test_no_test_weakening` scanners); broad fixed-SHA A/B in a worktree (the `.1R.26` method) |
| `.1R.16` §35 row 15 "N-16-5 NOT SATISFIED" | flips to SATISFIED only at `.1R.33` closure |
| runtime-posture (`Observed`/`unavailable`) guards | **unchanged** — RHAMP-001 touches neither |
| `first external effect ABSENT` guards | **unchanged** |

**Historical vs current guard strategy (phase prompt §76):** historical NON_REAL
phases (`.1R.3`..`.1R.20`) are **not** rewritten as if real FIDO2 existed then —
they are preserved; `.1R.30` / `.1R.32` add companion current-canonical
assertions and reconcile point-in-time scope fences phase-aware, exactly as
`.1R.26` did for Gate 7 (RHAMP-REQ-163).

**Contract-production equivalence plan (phase prompt §77):** RHAMP-001 §68
RHAMP-REQ-164 — every RHAMP-001 requirement mapped by `.1R.30` / `.1R.32` and
re-derived by `.1R.31` / `.1R.33` to exact production-source + test evidence; no
prose-only security guarantee.

## 25. Implementation / IV sequence (phase prompt §78, §79) — FROZEN in RHAMP-001 §64

| Phase | Scope (IDs recommended, NOT reserved; each its own human auth + IV pair) |
|---|---|
| `.1R.30` | Real FIDO2 credential registry + authentication mechanism: production `HumanPrincipalRegistryStore` writer path; §17 sidecar + §21 counter-state stores; protected-admin enrollment + first-credential bootstrap tool; `FIDO2HumanAuthenticator`; real CTAP2 assertion verification in `hpac_verifier` (§37) incl. the `FLAG.UV` check; `_ELIGIBLE_MECHANISM_IDS += {hpac.fido2.uv_presence.v2}`; `terminal_reason_code` wiring; reuse `hatp_fido2_provider` CTAP2 primitives as a shared library. **No protected UI. No real approval-authority production path yet.** |
| `.1R.31` | Independent verification of `.1R.30`. |
| `.1R.32` | Protected human-approval presentation + real approval-proof integration: process-isolated helper; deterministic `renderer_profile`; helper integrity/provenance; explicit Approve/Reject; presentation-digest binding; real `mechanism_attestation`; `verifier_kind = pcae-protected-local-presentation/1.0`; wire `require_real_assurance=True` through Gate 5 / Gate 9; a `PRODUCTION` `AuthenticatedHumanPrincipal` becomes obtainable for exactly one bound approval. |
| `.1R.33` | Independent verification of `.1R.32` + mandatory real-CTAP2-hardware verification (§62) + N-16-5 closure. |

**Phase ordering (phase prompt §79):** N-16-5 → N-16-6 → N-16-7, **N-16-7
strictly last**; **no Slice C** until N-16-3..7 all close (RHAMP-REQ-157). Do not
implement any of the above.

## 26. Post-N-16-5 production reachability (phase prompt §80) — NONE

RHAMP-001 §65 RHAMP-REQ-158..160. After N-16-5 closes:
- Real human authority becomes **satisfiable** — RIHAC-001 §12 condition 7 can
  pass with a real UV+UP+presentation proof of class `PRODUCTION`.
- **Gate 6 still blocks:** N-16-6's RPAC-REQ-095 fixed-argv adapter +
  supply-chain admission NOT SATISFIED — no admissible adapter.
- **Gate 7 still DENYs in production:** N-16-4 shipped the positive branch as a
  `pragma: no cover` test-seam only.
- **Runtime stays `unavailable`:** N-16-7 untouched and last.
- **No `adapter.dispatch(` call site** anywhere in `src/pcae/**`.

**Production positive path after N-16-5 alone = NONE. First external effect
UNREACHABLE.**

**N-16-6 relationship (§81):** RHAMP-001 does **not** govern runtime
effect-adapter admission; the protected-UI helper trust model is separate from
N-16-6 supply-chain admission; human credential identity SHALL NOT influence
adapter admission (RHAMP-REQ-090/158). **N-16-7 relationship (§82):** real
approval does **not** enable runtime capability; the runtime stays `Observed` /
`observe` / `unavailable` until the separately-authorized N-16-7 transition
(RHAMP-REQ-159).

**N-23-1 / N-23-2 (§83):** carried unchanged (N-23-1 INFO; N-23-2 INFO /
DEFERRED NORMALIZATION DEBT); RHAMP-001 does not normalize PBRD / PBNDE
(RHAMP-REQ-161).

## 27. STOP-condition check (phase prompt "Valid early stop conditions") — NONE APPLY

| Condition | Applies? | Why not |
|---|---|---|
| native CTAP2 cannot satisfy the HPAC extension points without changing HPAC-001 | **NO** | every residual decision fits an existing extension point (`mechanism_id`, `verifier_kind`, `terminal_reason_code`, TTL deferral, attestation silence); RHAMP-001 §1 RHAMP-REQ-001..003 |
| native CTAP2 profile cannot define an RP/client-data binding without falsely claiming WebAuthn/browser-origin semantics | **NO** | RHAMP-001 §7/§8 define a PCAE-owned canonical client-data context and §8 RHAMP-REQ-027/028 explicitly disclaim origin enforcement |
| first-credential bootstrap authority root cannot be frozen safely from existing canonical governance | **NO** | HPAC-REQ-022/023's external deployment-owner protected administration principal **is** that root; RHAMP-001 §14 |
| credential registry / counter-state model requires PCAE to store private-key material | **NO** | structural — no private-key field exists; RHAMP-001 §18 RHAMP-REQ-059 |
| the process-isolated helper cannot be made provably canonical/integrity-bound without broader architecture changes | **NO** | RHAMP-001 §30 freezes the intended integrity evidence (pinned digest + descriptor + installation record); the implementing phase confirms against then-current architecture and BLOCKS only if none can be established — a `.1R.32` gate, not a `.1R.29` blocker |
| UP/UV semantics cannot be kept distinct from approval intent | **NO** | UV is a `FLAG` bit checked in verifier step 7; the election is a separate observed event in step 5's evidence; RHAMP-001 §10/§11/§36 |
| NON_REAL objects could become upgradeable into REAL authority | **NO** | structurally impossible — RHAMP-001 §41 RHAMP-REQ-111..113 |
| a contract-versioning rule requires an existing-contract MAJOR/MINOR contrary to "companion-only" | **NO** | §23 above — no existing contract moves; REPRC-001 precedent |
| local-interactive-only deployment cannot be frozen without contradicting the current Dell topology | **NO** | RHAMP-001 §53/§54 records it as a deployment prerequisite; the headless case is a named deferral, not a contradiction |
| real mechanism closure would require remote/headless approval architecture inside N-16-5 | **NO** | RHAMP-001 §55 defers it entirely; no network authority transport authorized |
| the selected transport/authenticator profile cannot be specified portably enough | **NO** | USB-HID + NFC, OS-neutral roaming keys, constant `rp_id` — RHAMP-001 §51; HPAC-REQ-082/083 |
| repository evidence shows RHAMP must modify PBRD/RDGO/HPAC/RIHAC/RIASC semantics rather than profile extension points | **NO** | §3 / §23 — RHAMP-001 profiles only; every existing contract byte-unchanged |

**No BLOCKED report is returned. The phase proceeds through governed
finalization.**

## 28. Contract-freeze verdict (phase prompt §94)

```
RHAMP-001 v1.0:                 FROZEN  (sole normative delta of the N-16-5 track through .1R.29)
N-16-5:                         CONTRACT PROFILE FROZEN — IMPLEMENTATION NOT BEGUN
REAL HUMAN AUTHENTICATION:      CONTRACT FROZEN — NOT IMPLEMENTED
PROTECTED HUMAN APPROVAL:       CONTRACT FROZEN — NOT IMPLEMENTED
REAL APPROVAL PROOF:            CONTRACT FROZEN — NOT IMPLEMENTED
Native CTAP2 vs WebAuthn:       SEPARATED — native CTAP2 only, no browser, no web origin, no TLS, no loopback
First-credential bootstrap:     FROZEN — HPAC-REQ-023 external deployment-owner protected administration principal
Credential / counter-state / sidecar schemas:  FROZEN (CredentialRecord byte-unchanged; two new protected artifacts)
Presentation-helper integrity model:           FROZEN (pinned digest + descriptor + installation record; not path)
NON_REAL non-upgradeability:                    PRESERVED (structural)
Local-interactive-only deployment prerequisite: FROZEN; headless/remote deferred
Real-hardware verification requirement:         FROZEN (mandatory before .1R.33 closes N-16-5)
Implementation / IV sequence:                   FROZEN (.1R.30 → .1R.31 → .1R.32 → .1R.33)
HPAC-001:                       v2.1 (NO bump)
Every other existing contract:  byte-unchanged
src/pcae/**:                    unchanged
Runtime:                        not_implemented / Observed / observe / unavailable
First external effect:          ABSENT
```

## 29. Recommended next phase (phase prompt §95) — requires its own explicit human authorization

`149O.20L.7O.3W.1R.2B.1R.1.1R.30` — **N-16-5 Real FIDO2 Credential Registry and
Authentication Mechanism Implementation** — scope frozen in RHAMP-001 §64
(RHAMP-REQ-156 `.1R.30` row): production `HumanPrincipalRegistryStore` writer
path; the FIDO2-credential sidecar and counter-state stores; protected-admin
enrollment + first-credential bootstrap ceremony tool; `FIDO2HumanAuthenticator`
for `hpac.fido2.uv_presence.v2`; real CTAP2 assertion verification in
`hpac_verifier` (COSE verify + `rp_id_hash` + client-data hash + the added
`FLAG.UV` check); `_ELIGIBLE_MECHANISM_IDS += {hpac.fido2.uv_presence.v2}`;
`terminal_reason_code` wiring; `hatp_fido2_provider` CTAP2 primitives reused as a
shared library. **No protected approval UI, no real approval-authority
production path, no N-16-6/N-16-7, no Slice C.** Then `.1R.31` (IV) → `.1R.32`
(protected presentation + real-assurance wiring) → `.1R.33` (IV + mandatory
real-CTAP2-hardware verification + N-16-5 closure). **Do not begin `.1R.30`.**

## 30. `.3` governance incident (phase prompt §96, §97) — preserved

```
DELEGATED `.3` FINALIZATION / COMMIT / PUSH: UNAUTHORIZED
```

Preserved exactly. Only the primary human-authorized operator holds `.1R.29`
lifecycle authority. No delegated worker committed, finalized, or pushed. No raw
`git commit` / `git push`, no `--no-verify`, no force push, no history rewrite,
no hook bypass — governed `pcae` lifecycle only. This phase's work was performed
by the `claude-local` documentation/default agent under the primary operator's
explicit authorization for `.1R.29`.

## 31. Files changed / tests / analysis

- **Added:** `docs/contracts/REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md`
  (RHAMP-001 v1.0).
- **Added:** this canonical phase report.
- **Updated:** `PROJECT_STATUS.md` (new Current Phase entry), `CHANGELOG.md`
  (new bullet), task lifecycle artifacts, `.pcae/phase-completion-metadata.json`
  / `.pcae/phase-completion-report.md`.
- `git diff --name-only 4ae0a025 HEAD -- docs/contracts` → exactly the RHAMP-001
  file (phase prompt §89).
- `git diff 4ae0a025 HEAD -- src/pcae` → empty (phase prompt §88).
- **Tests:** none added, removed, weakened, skipped, xfailed, or renamed — this
  is a contract-freeze phase with zero code change. `fast_green` recorded as
  `0 passed, 0 failed (contract-freeze-only phase, no test changes)`.
- **Analysis run:** read-only `git` history inspection; `pcae health` / `check` /
  `status coherence` / `doctor task-memory` / `push check` / `runtime inspect` /
  `notify status` / `phase-report show`; a read-only `tests/` needle grep for the
  §75 guard-term set (no mutation).

## 32. No-go confirmations

- No `src/pcae` file was created, modified, or deleted; `git diff --name-only 4ae0a025 HEAD -- src/pcae` is empty.
- No existing normative contract file was edited; HPAC-001, RIHAC-001, RIASC-001, HPSE-001, HHCE, PBRD-001, RDGO-001, RPAC-001, REPRC-001, the RE No-Go Registry, and every HATP contract are byte-unchanged.
- No MAJOR or MINOR version was bumped, forced, or overridden on any existing contract; HPAC-001 stays v2.1; `HPAC-AUTHORITY-CONSUMPTION` stays `/2.1`; only RHAMP-001 v1.0 (initial freeze) is new.
- No schema package under `src/pcae/schema_resources/**`, no enrollment CLI, no registry writer, no `HumanAuthenticator` implementation, no `ProtectedApprovalPresentationMechanism` implementation, no presentation helper, and no protected descriptor was created.
- No FIDO2 / WebAuthn / CTAP / hardware authenticator was accessed; no `fido2` device call, no `Ctap2`, no `CtapHidDevice` enumeration; no credential was registered, minted, or enumerated; no authenticator was touched.
- No `HumanPrincipalRegistry` was created or mutated; no principal or credential enrolled or revoked; no `principal-registry.json`, sidecar, or counter-state file written.
- No protected root was created, resolved, or written; no proof, presentation, challenge, nonce, lifecycle event, or `consumption.json` was created or consumed on any path.
- No real assurance mechanism was enabled; `_ELIGIBLE_MECHANISM_IDS` is byte-unchanged; `require_real_assurance` still can only reject; no `verifier_kind` was added to any acceptance set.
- No `AuthenticatedHumanPrincipal` of class `PRODUCTION` was produced anywhere.
- No execution was enabled; runtime remains `not_implemented` / `Observed` / `observe` / `unavailable`; 0 plugins / 0 capabilities.
- No runtime capability was elevated or promoted; no `Observed -> Approved/Executable` transition; N-16-7 remains untouched and last.
- No Slice C was implemented; no `adapter.dispatch(` call site exists anywhere in `src/pcae`; Slice C / Slice D keep no phase ID.
- No N-16-5 implementation, and no N-16-6 / N-16-7 work, was begun; each remains its own separately authorized implementation + IV pair.
- No adapter (mock or real) was registered, implemented, activated, or called; `RuntimeRegistry` remains empty; no supply-chain admission store or resolver was created or called.
- No dependency was installed, upgraded, vendored, or unpinned; `fido2>=1.1,<2` + `cryptography>=42,<45` remain as already declared; no custom cryptography was written.
- No subprocess, process spawn, `os.system` / `popen` / `spawn` / `exec*`, `pty`, provider SDK, HTTP client, socket, or network path was created or invoked; only read-only `git` inspection and `pcae` governance CLI checks were run.
- No third-party system, unrelated account, provider API, external network, or deployment target was accessed or mutated.
- No test was added, removed, weakened, skipped, xfailed, or renamed; no traceability test was manufactured; no functional-suite evidence was fabricated for a contract-freeze-only phase.
- No reopening of a closed gate boundary (Gate 5, 6, 7, 8, 9), the Slice-A / Slice-B verdicts, or the N-16-3 / N-16-4 closures.
- No human approval was treated as a policy or enforcement override.
- No raw `git commit` / `git push`, no `--no-verify`, no force push, no history rewrite, no hook bypass; governed `pcae` lifecycle only.
- No delegated worker committed, finalized, or pushed; only the primary human-authorized operator holds `.1R.29` lifecycle authority; `DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` is preserved.
- No STOP or BLOCKED condition was reached; every valid early-STOP condition in the phase prompt was checked (§27) and none applies.
- No "Remaining" section is presented; all authorized `.1R.29` work is complete.

---

*Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.29 — canonical contract-freeze artifact. RHAMP-001 v1.0 frozen; no implementation.*
