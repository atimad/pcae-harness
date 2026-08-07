# Phase 149O.3 — HATP Hardware Provider Independent Verification (Wave 5)

**Phase ID:** 149O.3
**Phase type:** Verification-only (no production code, no contract change, no repair)
**Subject:** Phase 149O.2 — HATP Hardware Provider + Human-Presence Implementation (Wave 5)
**Baseline verified against:** commit `89bebdc0` (149O.1J, Wave-4 independent verification) → `19748a0c` (149O.2) → `HEAD`
**Frozen contract:** `docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md` (HATP-001 v1.0, 117 requirements)
**Canonical plan:** `docs/PHASE_149O_1D_HUMAN_APPROVAL_TRUSTED_PROVENANCE_IMPLEMENTATION_PLAN.md`
**Independent verification suite:** `tests/test_phase_149o_3_hatp_hardware_provider_independent_verification.py` (242 passed, 1 hardware-required skip)

---

## 0. Verdict summary

| Question | Verdict |
|---|---|
| Wave-5 overall | **VERIFIED WITH NON-BLOCKING FINDINGS — HATP WAVE 5 HARDWARE PROVIDER CONFORMS** |
| Hardware-backed key property | **HARDWARE-BACKED KEY PROPERTY: ARCHITECTURALLY SUPPORTED BUT NOT EMPIRICALLY VERIFIED** |
| Human presence | **FRESH USER PRESENCE: PROTOCOL-SEMANTICALLY VERIFIED; REAL DEVICE NOT EXERCISED** |
| Attestation | **A. ATTESTATION NOT REQUIRED FOR WAVE-5 PROVIDER CONFORMANCE — contract explicitly defers it** |
| Credential registry | **HARDWARE CREDENTIAL REGISTRY: PROTECTED AUTHORITY BOUNDARY VERIFIED** |
| Provider factory | **PRODUCTION PROVIDER FACTORY: CLOSED, TEST/SOFTWARE PROVIDERS EXCLUDED** |
| Canonical payload | **HARDWARE PROVIDER PAYLOAD BINDING: EXACTLY DERIVED FROM VERIFIED WAVE-3 CANONICAL SEMANTICS** |
| Operational separation | **PROVIDER AVAILABILITY / PER-PROOF VALIDITY: DOES NOT MAKE HATP OPERATIONAL** |
| PIV | **DEFERRED / UNAVAILABLE — permitted by the plan's own conditional stop condition** |
| Production readiness | **HATP PRODUCTION: NOT READY** |
| Blocking findings | **ZERO** |

**Recommended next phase:** 149O.4 — HATP Wave 6, RAE Integration (per 149O.1D's own wave ordering).
**Optional, non-blocking:** a narrow 149O.3.1 hardening phase could close B-149O.3-1/-3/-8 before Wave 6, at the implementer's discretion. It is **not** required by this verdict.

---

## 1. Baseline confirmation (spec section 1)

| Check | Result |
|---|---|
| `git status --short` | clean |
| `git rev-list --count origin/main..HEAD` | 0 |
| Latest completed phase | 149O.2, commit `19748a0c`, pushed, report completeness `complete` |
| `pcae health` | healthy |
| `pcae check` | passed |
| `pcae status coherence` | coherent |
| `pcae doctor task-memory` | warnings (6 pre-existing `tasks/DONE.md` sync gaps, unrelated) |
| `pcae push check` | clean (`nothing_to_push`) |
| `pcae runtime inspect` | Observed / observe / unavailable |
| `pcae notify status` | telegram configured, enabled, ready |
| `pcae phase-report reconcile --phase-id 149O.2` | reconciled, `already_dispatched`, receipt finalized |

All expected preconditions confirmed.

---

## 2. Exact Wave-5 production diff reconstruction (spec section 3)

`git diff --name-only 89bebdc0 HEAD -- src/pcae/` yields **exactly four files**:

| File | Lines | Classification |
|---|---|---|
| `src/pcae/core/hatp_providers.py` | +235 / −1 | PROVIDER_ABSTRACTION, DISCOVERY, PROVIDER_FACTORY, OPTIONAL_DEPENDENCY |
| `src/pcae/core/hatp_fido2_provider.py` | +404 (new) | FIDO2_PROVIDER, SIGNATURE_VERIFICATION, USER_PRESENCE, ATTESTATION (absent-by-design), OPTIONAL_DEPENDENCY |
| `src/pcae/core/hatp_piv_provider.py` | +119 (new) | PIV_PROVIDER (structurally deferred) |
| `src/pcae/core/hatp_hardware_credentials.py` | +285 (new) | CREDENTIAL_REGISTRY |

**UNRELATED = 0.** The single deleted line is `-from typing import List, Optional, Protocol, runtime_checkable`, replaced by a widened `typing` import — no semantic change.

Non-production Wave-5 diff: `pyproject.toml` (optional `hatp-hardware` extra + one pytest marker), `tests/conftest.py` (+7, Fast-Green module registration), two pre-existing diff-scope guard tests widened, one new test module, docs, `PROJECT_STATUS.md`, `CHANGELOG.md`, task/metadata files.

**Boundary confirmations for 149O.3 itself (spec sections 130–132):**

- `git diff --name-only 89bebdc0..HEAD -- src/pcae/` shows only the four 149O.2 files; **149O.3 changed no production file.**
- `git diff --name-only 89bebdc0..HEAD -- docs/contracts/` is **empty**. Independently, `git hash-object` of HATP-001 equals `git rev-parse 89bebdc0:<contract>` = `79af6e959d6d753afb12c627ad8e996910ba4ca9`. **HATP-001 v1.0 is byte-unchanged.**
- Base `dependencies` in `pyproject.toml` are byte-identical to the baseline; the Wave-5 dependency landed strictly as the **optional** `hatp-hardware` extra. **149O.3 added no dependency.**
- `src/pcae/core/repository_identity.py` (Wave 1), `hatp_bootstrap.py` (Wave 2) and `human_approval_trusted_provenance.py` (Waves 3/4) are **byte-unchanged** since the baseline.

---

## 3. Wave-5 requirement reconstruction (spec section 4)

Re-derived independently from the plan's own Wave-5 section text (`### Wave 5 — Real Hardware Provider / Human Approval Surface`), not from 149O.2's report. The plan states: *"Requirements implemented: HATP-REQ-016..025 (F, E) at the concrete-implementation level; HATP-REQ-076."* This confirms 149O.2's assignment.

| Req | Exact normative meaning (from contract text) | Implementation | Verification |
|---|---|---|---|
| **016** | Fresh human-presence event enforced by the provider *for that specific proof-production operation*; a profile permitting unattended/repeated signing without a fresh presence event per signature is non-compliant. | `human_presence_proven = bool(parsed.authenticator_data.is_user_present())`, recomputed on every `verify()` call; `request_signature` issues a fresh CTAP2 `get_assertion` per call. | **Satisfied at protocol level.** Presence recomputed per call (`test_presence_is_recomputed_per_call_and_never_cached`), never cached, never caller-supplied. Physical touch not device-tested (Category B). |
| **017** | One presence action → at most one proof; no "unlock once, sign many" session. | No session, token cache, or presence memoisation exists in any Wave-5 module (AST-audited). | **Satisfied structurally.** Each `getAssertion` carries its own UP flag over its own challenge; a UP=true assertion for payload A fails entirely for payload B. |
| **018** | An agent invoking a genuine enrolled signer *without* a fresh human presence event SHALL NOT obtain a valid proof. | UP flag comes from authenticator-generated `authenticatorData`, which is inside the signed bytes. | **Satisfied at protocol level;** the physical half (a device refusing to assert without touch) is Category B. `test_up_true_is_necessary_for_wave4_valid_and_up_false_maps_to_user_presence_not_proven` proves the software half end-to-end. |
| **019** | `HATP_HARDWARE_PROVIDER_V1` requires (a) non-exportable private key, (b) fresh presence per signing op, (c) signing/assertion over an operation-specific payload suitable for HATP's canonical payload, (d) stable credential identity, (e) verification via independently trusted material not originating from the proof. | (a) CTAP2 semantics, no key material anywhere in the module; (b) UP; (c) challenge = SHA-256(canonical payload); (d) FIDO2 credential ID = `signer_key_id`; (e) COSE public key from the protected credential registry. | **(c), (d), (e) proven by software test. (a) Category C. (b) Category B.** Confirmed independently that (a)–(e) is the *complete* enumeration — **attestation is not among them** (`test_hardware_provider_profile_properties_are_exactly_five_and_exclude_attestation`). |
| **020** | Generic FIDO2 is not assumed interchangeable; the implementation SHALL *demonstrate* its protocol actually satisfies 019(c) before being accepted. | Module docstring records the spike; the binding is `challenge = SHA-256(canonical_payload)` embedded in `clientDataJSON`. | **Demonstrated and independently re-derived** — see §5. The demonstration is genuine, not asserted. |
| **021** | A local software key SHALL NOT silently substitute for a hardware signer. | Production path has no write API; the registry has no production enrollment surface; the factory never returns a software/test provider. | **Satisfied.** §8. |
| **022** | A test-only provider MAY exist but SHALL be unselectable as production authority by ordinary configuration (no default-enabled test provider, no silent fallback). | `TestHATPProofVerifierProvider` is referenced by no production module and by no code path in the factory; closed one-element allowlist; PIV fallback requires explicit `allow_piv_fallback=True`. | **Satisfied.** §8. |
| **023** | Attestation **MAY** establish device class; it SHALL NOT by itself establish principal identity, approval authority, or repository authorization. | No attestation path exists; `attestation_valid` is always `None`. | **Satisfied vacuously and correctly** — see §9. |
| **024** | Valid vendor attestation alone, without protected-bootstrap enrollment, grants no authority. | `verify_hatp_proof` requires signer + principal + authority + deployment binding from the Wave-2 store regardless of provider outcome. | **Satisfied.** |
| **025** | An attestation proof SHALL NOT self-select an arbitrary attestation root; roots MUST originate outside the proof and outside agent-writable repository state. | No attestation root exists anywhere in `src/pcae/` (`test_attestation_root_material_originates_nowhere_in_agent_writable_state`). Public-key material originates from the fixed-path protected registry, never from the proof (the proof carries no key field at all). | **Satisfied.** |
| **076** | Define enough provider/signature semantics for interoperable verification, without claiming unsupported protocol behaviour. No algorithm frozen. | Strict versioned evidence envelope; ES256/COSE; the exact double-hash construction documented and independently reproducible. | **Satisfied**, with B-149O.3-8 and B-149O.3-9 as narrow non-blocking defects in the envelope-parsing edge cases. |

### Undisclosed partial scope (B-149O.3-11)

The plan's Wave-5 **Files/modules** line reads: *"`hatp_providers.py` gains a real provider adapter (FIDO2 primary, PIV fallback per §23); **a human-side approval CLI surface (namespace TBD, §29-32)**."* Phase 149O.2 did **not** implement the human-side approval CLI surface, and its report does not disclose the omission. No `src/pcae/commands/*hatp*` module exists.

This is **non-blocking**: the plan itself defers the surface's exact shape to "Wave 5/7", and the blind-touch-defense component it would host is meaningless until Wave 6 gives HATP a consumer. It is recorded as an OBSERVATION so the omission is tracked rather than silently absorbed.

---

## 4. Provider contract reconstruction (spec section 5)

`HATP_HARDWARE_PROVIDER_V1` as actually implemented:

| Aspect | Reconstructed semantics | Implementation agreement |
|---|---|---|
| Provider profile | Single frozen string `"HATP_HARDWARE_PROVIDER_V1"`; protocol-agnostic by design (FIDO2 and PIV adapters may both claim it). | Agrees. The Wave-2 signer record's `provider_profile` is authoritative, not a protocol tag. |
| Credential identity | FIDO2 credential ID, hex-encoded, used verbatim as `signer_key_id`. | Agrees. `parsed.credential_id.hex() != signer_key_id.lower()` fails closed. |
| Canonical payload input | Opaque `bytes` — exactly `canonicalize_hatp_proof_payload(proof)`. The provider never reconstructs proof JSON. | Agrees. Verified by AST (no `canonicalize_*`, no `HumanApprovalProvenanceProof` reference) and empirically (a non-JSON payload verifies fine — the provider only hashes the bytes it is handed). |
| Signature/assertion | WebAuthn `getAssertion`: signature over `authenticatorData ‖ SHA-256(clientDataJSON)`, ES256/COSE, public key from the protected registry. | Agrees. |
| User presence | `AuthenticatorData.FLAG.UP`, read per assertion via `is_user_present()`. UV explicitly not required. | Agrees. |
| Attestation | Not evaluated; `attestation_valid=None` meaning "this profile does not evaluate attestation". | Agrees, and honestly reported in `capabilities()`. |
| Availability | `HardwareProviderAvailability` facts only; never trust, never readiness. | Agrees; `discover_hardware_providers()` takes no parameter and the dataclass has no trust field. |
| Failure | `verify()` MUST NOT raise for an invalid assertion; raises reserved for genuine provider faults. Signing raises `HATPProviderCancelledError` / `HATPProviderDeviceError` / `HATPProviderUnavailableError`. | **Partially violated** — see B-149O.3-8. |

---

## 5. Canonical payload / challenge binding (spec sections 11–15, 141)

### Exact construction, independently re-derived

```
canonical_payload  = canonicalize_hatp_proof_payload(proof)        # Wave 3, verified in 149O.1H
challenge          = SHA-256(canonical_payload)                     # 32 bytes
clientDataJSON     = {"type":"webauthn.get",
                      "challenge": base64url_unpadded(challenge),
                      "origin":"pcae-hatp://hatp.pcae.local",
                      "crossOrigin":false}                          # compact, key order as emitted
clientDataHash     = SHA-256(clientDataJSON)
authenticatorData  = SHA-256("hatp.pcae.local") ‖ flags(1) ‖ signCount(4)
signed bytes       = authenticatorData ‖ clientDataHash             # 37 + 32 = 69 bytes
signature          = ECDSA-P256-SHA256(signed bytes)
```

This verification module **rebuilds every one of those structures from raw bytes and raw JSON**, without calling `hatp_fido2_provider._payload_digest` or `_serialize_evidence`, and then proves byte-equality with `fido2.webauthn.CollectedClientData.create` / `AuthenticatorData.create`. Had the production helpers been wrong, 149O.2's fixtures (which call them) would have cancelled the error out; these cannot.

### Double-hash analysis (spec section 14)

Two hashes are involved and both are intentional:

1. `SHA-256(canonical_payload)` — HATP's own binding of the Wave-3 canonical bytes into the WebAuthn challenge slot.
2. `SHA-256(clientDataJSON)` — WebAuthn's own wire-format hash, unavoidable: CTAP2 never signs a caller byte string directly, it always signs `authenticatorData ‖ hash-of-a-JSON-structure-containing-the-challenge`.

**What HATP considers "the signed payload" is unambiguous:** the canonical payload bytes are the semantic subject; the challenge is their digest; the digest is cryptographically inside the signed bytes via an injective chain (payload → digest → base64url string → JSON bytes → hash → signed bytes). Any change at any link changes the signature input. The construction is contract-conformant: HATP-REQ-076 explicitly declines to freeze an algorithm, and HATP-REQ-020 demands demonstration rather than assumption — which is what was done.

Independently confirmed from the installed `fido2==1.2.0` source, in **two** places that agree:
- `fido2/ctap2/base.py:153` — `public_key.verify(self.auth_data + client_param, self.signature)`
- `fido2/server.py:428` — `cred.public_key.verify(auth_data + client_data.hash, signature)`

### Byte-exactness attacks

| Attack | Result |
|---|---|
| Single-byte payload mutation (5 offsets incl. last) | assertion fails |
| Payload truncation (prefix) | fails |
| Payload extension (trailing space) | fails |
| Wrong challenge substituted | fails |
| Padded/standard-alphabet base64 challenge re-encoding | only producible by the key holder; confers nothing |
| Non-JSON / arbitrary binary payload | verifies correctly — proving the provider hashes exactly the bytes it is given and performs **no second canonicalization** |

**No alternate reconstructed payload path exists.** AST-confirmed: the FIDO2 module references neither `canonicalize_hatp_proof_payload` nor `HumanApprovalProvenanceProof`, and defines exactly one digest function, `_payload_digest`.

---

## 6. Replay matrix (spec sections 16–24, 105, 106)

Every dimension exercised with **real ECDSA signatures** over **real Wave-3 canonical payloads**.

| Dimension | Spec § | Result |
|---|---|---|
| Payload byte (challenge) | 16 | evidence for A never verifies for B |
| Repository (`repository_id`) | 17 | fails |
| Decision record ID | 18 | fails |
| Decision record digest | 18 | fails |
| Binding ID | 19 | fails |
| Binding digest | 19 | fails |
| Operation AG3 (`job_id`) | 20 | fails |
| Operation AG3 (`original_commit_sha`) | 20 | fails |
| Operation AG5 (`per_id`/`ecp_id`, site switch) | 20 | fails |
| Timestamp (`issued_at`) | 21 | fails |
| Timestamp, equivalent lexical form (`+00:00` vs `+02:00` same instant) | 21 | **legitimately shares evidence** — canonical payloads are byte-identical, which is Wave-3 canonicalization working as designed, not a replay hole |
| Provider profile | 22 | fails (both in the canonical payload *and* independently at the registry-profile check) |
| Principal | 23 | fails |
| Credential (`signer_key_id`) | 24 | fails |
| Cross-deployment, same authentic credential | 44 | `WRONG_DEPLOYMENT` end-to-end through Wave 4 |
| Across provider *instances* | 105 | same evidence verifies on a second `Fido2HardwareProvider` — **acceptable and documented**: the provider is a stateless verifier, and all trust is carried by payload + credential binding, which the same test re-proves still rejects any other payload |
| Provider-invented freshness | 106 | none — no `datetime.now`, `time.time`, `utcnow`, `expires_at`, or `monotonic` anywhere in the four Wave-5 modules. `issued_at` + Wave 4 remain authoritative. |

---

## 7. Human presence audit (spec sections 49–57, 137)

### UP vs UV contract basis (spec section 52)

Independently re-derived from HATP-001 §9: the contract's language is **"human-presence event"** throughout. The strings *"user verification"* and *"biometric"* appear **nowhere in the entire 979-line contract**. HATP-REQ-019(b) says "fresh human-presence enforcement per signing operation." Therefore mapping `human_presence_proven` to the CTAP2 **UP** flag — not UV — is the correct contract reading. 149O.2's interpretation is confirmed; there is no stronger identity-verification requirement being under-delivered, so the Blocking condition contemplated by spec section 52 **does not fire**.

### The `is_user_present` method-vs-property regression guard (spec section 49)

Independently re-confirmed that in `fido2` 1.2.0, `AuthenticatorData.is_user_present` is a **bound method**:

- `bool(auth_data.is_user_present)` → `True` even when UP is clear (the trap 149O.2 reports catching).
- `auth_data.is_user_present()` → correct value.

Production source is verified by regex to call it (`is_user_present()`) and to contain **no** bare non-called reference. The bug is genuinely fixed and is now pinned by an independent test.

### Presence results

| Property | Result |
|---|---|
| UP=false + cryptographically valid signature | `signature_valid=True`, `human_presence_proven=False`; Wave 4 → `USER_PRESENCE_NOT_PROVEN` |
| UP=true, everything else valid | Wave 4 → `VALID` |
| UV=true with UP=false | presence **not** proven — UV never substitutes for UP |
| Presence replay (UP=true assertion for payload A used for payload B) | fails entirely (`signature_valid=False`, `human_presence_proven=False`) |
| Cached presence across calls | none — interleaved true/false/true/false/false/true sequence tracked exactly |
| Repeated calls with distinct assertions | each derives presence freshly from its own assertion |
| Caller-supplied presence in a production API | **none exists.** No parameter containing "present" on any `Fido2HardwareProvider` / `PivHardwareProvider` entry point; no production keyword argument sets `human_presence_proven=True` |
| Caller-supplied presence in the *test* provider | exists on `TestHATPProofVerifierProvider.__init__` — acceptable **only** because that class is provably unreachable from the production factory (§8) |

### Fresh-presence-per-operation disposition (spec section 53)

What CTAP2/WebAuthn semantics guarantee: an authenticator sets UP in `authenticatorData` only after performing user-presence processing **for that specific `getAssertion` invocation**, and `authenticatorData` is inside the signed bytes, so UP cannot be forged without the private key. For a genuine authenticator this is precisely "a fresh physical interaction occurred for this signing operation."

What this repository proved: the *software* half — UP is read per assertion, never cached, never caller-assertable, and never transferable between operations.

What this repository could **not** prove: that a physical authenticator actually required a finger touch. No device is attached.

**Verdict: FRESH USER PRESENCE: PROTOCOL-SEMANTICALLY VERIFIED; REAL DEVICE NOT EXERCISED.**

---

## 8. Hardware credential registry audit (spec sections 25–48, 139)

### Production root

| Property | Result |
|---|---|
| macOS root | `/Library/Application Support/PCAE/HATP/hardware-credentials` (fixed) |
| Linux root | `/etc/pcae/hatp/hardware-credentials` (fixed) |
| Inside repository state? | **No** — never `repo/.pcae/**` |
| Redirectable by `HOME`, `XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_RUNTIME_DIR`, `TMPDIR`, `PWD`, `PCAE_HATP_CREDENTIAL_ROOT`, `HATP_CREDENTIAL_STORE`, `PCAE_HOME`, `PCAE_CONFIG`? | **No** (all 10 tested) |
| Redirectable by CWD? | **No** |
| Redirectable by CLI flag? | **No** — `cli.py` never references the store; the module reads no `os.environ`, `getenv`, `expanduser`, `Path.home`, or `getcwd` |
| Redirectable by constructor/`production()` argument? | **No** — `production()` takes zero parameters; the only constructor override is keyword-only `_test_only_root`, and positional injection raises `TypeError` |
| Unsupported platform | fails closed (`HATPHardwareCredentialStoreUnsupportedPlatformError`) for `win32`, `cygwin`, `aix`, `freebsd12`, and non-POSIX `os.name` |

### Root pre-creation attack (spec sections 28–31) — attempted for real

On this machine, `/Library/Application Support` is `drwxr-xr-x root:admin` (mode 755, root-owned, **not** group-writable). `os.access(parent, os.W_OK)` is `False` for the agent principal. **The agent cannot create the PCAE authority root.** The attack fails at the OS layer.

### Filesystem attacks

| Attack | Spec § | Result |
|---|---|---|
| Symlinked registry root | 32 | refused (`HATPHardwareCredentialStoreSymlinkError`), and `environment_status()` → `UNSAFE_CONFIGURATION` |
| Symlinked registry artifact | 34 | refused |
| Duplicate JSON keys | 35 | rejected |
| Duplicate credential ID | 37/38 | rejected — ambiguity never resolved by silently picking a winner |
| Malformed registry (11 document variants: non-JSON, non-object, wrong container type, missing fields, bad protocol, bad hex, bad status, empty strings, non-string ID) | 39 | all fail closed |
| Missing registry file | 40 | `lookup_credential` → `None` (fail-closed unknown credential); `environment_status()` → `READY` if the root exists, `UNAVAILABLE` if it does not |
| Auto-provisioning | 41 | **none** — after `lookup_credential()` + `environment_status()` the root directory is still empty and a missing root is never created |

### Read-only production API (spec section 42)

Public surface is exactly `{production, root, environment_status, lookup_credential}`. No module-level or class-level `enroll` / `grant` / `authorize` / `rotate` / `revoke` / `write` / `create` / `save` / `update` / `delete`. Executable source contains no `write_text`, `write_bytes`, `mkdir`, `os.remove`, `unlink`, `rename`, `chmod`, or `open(`. `HardwareCredentialRecord` is frozen and carries no private key, PIN, secret, token, or passphrase field. **Wave-7 enrollment ownership is intact.**

### Self-selection attack (spec section 46)

`HumanApprovalProvenanceProof` has **no** `public_key`, `certificate`, `attestation`, `cose_key`, or `signer_public_key` field — a proof structurally cannot carry its own verification material (HATP-REQ-077 upheld at the type level). An attacker key with a matching self-produced assertion, against an empty registry, yields `signature_valid=False`.

### Trust conjunction (spec sections 44/45)

The two protected stores are **complementary, never independently sufficient**:

- **Wave-2 `HATPTrustStore`** — identity and authority: signer→principal mapping, principal status, repository authority, deployment binding. Carries **no** cryptographic key material.
- **Wave-5 `HATPHardwareCredentialStore`** — cryptographic material only: the COSE public key for a `signer_key_id`. Carries **no** `repository_id`, `canonical_deployment_root`, or `principal_id`.

`verify_hatp_proof` requires **all** of `lookup_signer`, `lookup_principal`, `lookup_authority`, and `resolve_deployment_authorization` from the Wave-2 store, *in addition to* the provider outcome that depends on the Wave-5 registry. Copying a credential ID into another deployment therefore confers nothing: exercised end-to-end, the same authentic credential and the same real signature yield `VALID` at the bound deployment and `WRONG_DEPLOYMENT` at a relocated one. There is no conflicting authorization path.

### Software / test credential exclusion (spec sections 47/48)

- There is **no production write path at all** into the credential registry, so a software key can never be enrolled through PCAE.
- A production-constructed `Fido2HardwareProvider` resolves the fixed protected root, which **does not exist on this machine** — an authentic software-key assertion presented through that path returns `signature_valid=False`.
- Test fixtures use an explicit in-memory store or a `tmp_path` root; neither is ambiently discoverable by the production factory.

### Import-independence drift audit (spec section 43) — the substantive findings

`hatp_hardware_credentials.py` imports **no** PCAE module at all (AST-confirmed) — stronger independence than 149O.2 claimed. But that duplication has drifted from the Wave-2 original in four ways, all recorded below as **B-149O.3-1 through B-149O.3-4**.

Side-by-side:

| Rule | Wave 2 (`inspect_bootstrap_environment` / `_parse_registry_document`) | Wave 5 (`inspect_credential_store_environment` / `_load_registry`) | Drift |
|---|---|---|---|
| Fixed platform root, no env/home/cwd derivation | yes | yes | none |
| Root symlink refused | yes | yes | none |
| Registry-file symlink refused | yes | yes | none |
| Root group/other-writable flagged | yes | yes | none |
| Parent world-writable flagged | yes | yes | none |
| **Parent is symlink flagged** | **yes** | **no** | **drift** |
| **Parent owner ≠ root owner flagged** | **yes** | **no** | **drift** |
| **Root owned by the agent uid flagged (`agent_and_admin_share_os_principal`)** | **yes** | **no** | **drift** |
| Duplicate JSON keys rejected | yes | yes | none |
| Duplicate record IDs rejected | yes | yes | none |
| **Schema version enforced** | **yes** (`registry_version` must equal 1) | **no** (`REGISTRY_SCHEMA_VERSION` declared, never read) | **drift** |
| **Unknown top-level fields rejected** | **yes** | **no** | **drift** |
| **Unknown per-record fields rejected** | **yes** | **no** | **drift** |
| **Non-object array entries** | parsed and rejected | **silently skipped** | **drift** |
| Read-only, no mutation API | yes | yes | none |
| Fail-closed on malformed | yes | yes | none |

**Credential-registry verdict: HARDWARE CREDENTIAL REGISTRY: PROTECTED AUTHORITY BOUNDARY VERIFIED.** The protected-root boundary itself — fixed path, non-redirectable, symlink-refusing, agent-uncreatable, read-only, fail-closed — holds under every attack attempted. The drift items are hardening gaps that (a) cannot be reached without root on this platform, (b) affect only *public* key material, and (c) are individually incapable of authorizing a signer because the Wave-2 conjunction is independent. They are **non-blocking**, and none of them satisfies spec section 134's blocking condition "credential registry is agent-writable or redirectable."

---

## 9. Attestation disposition (spec sections 58–63, 138)

### Contract analysis, re-derived from primary text

- **HATP-REQ-019** enumerates the `HATP_HARDWARE_PROVIDER_V1` properties as exactly **(a)–(e)**. There is no `(f)`, and the word "attestation" **does not appear in HATP-REQ-019 at all**. Device attestation is therefore *not* a provider-profile conformance property.
- **HATP-REQ-023** uses **MAY**: "Device/provider attestation **MAY** establish that a device or provider belongs to an accepted hardware class."
- **HATP-REQ-024** and **HATP-REQ-025** are *constraints on* attestation (it grants no authority alone; it must not self-select a root), not mandates to perform it. Both are satisfied — trivially and correctly — by a provider that performs none.
- **HATP-REQ-079** lists the success conjunction as "...device/provider attestation valid **where required**..." — explicitly conditional.
- Mechanically confirmed: **no sentence in the 979-line contract contains "attestation" together with a positive `SHALL`.** Every attestation `SHALL` in HATP-001 is a `SHALL NOT`.
- Root 2A (HATP-REQ-012) names externally-anchored attestation as an *architectural* trust root that the contract explicitly "does not reopen"; it does not impose an implementation obligation on Wave 5.
- The 149O.1D plan assigns attestation-root selection to Wave 5 as "**decided in Wave 5**" — and Wave 5 decided: not this phase, honestly reported.

**This determination was made from HATP-001 directly, NOT inferred from `HATPProviderVerificationOutcome.attestation_valid` being `Optional`** (spec section 60's explicit prohibition).

### Implementation behaviour

- `capabilities().device_attestation` is `False` and the conformance verdict is `CONFORMANT_WITH_NON_BLOCKING_LIMITATIONS`, not `CONFORMANT` — the capability matrix does **not** describe an unavailable capability as implemented.
- No `attestation_object`, `AttestationObject`, `attStmt`, `verify_attestation`, or `x5c` handling exists.
- **No production code ever sets `attestation_valid=True`** (AST-verified: every `attestation_valid` keyword in the two provider modules is the constant `None`). A fabricated `True` is therefore impossible.
- No `attestation_root` / `ATTESTATION_ROOTS` symbol exists anywhere in `src/pcae/`. **Root 2A is not claimed proven.**
- Wave 4's actual behaviour: `attestation_valid=None` → passes through to `VALID`; `attestation_valid=False` → `INVALID_ATTESTATION`, fail-closed. Given the contract analysis above, `None → VALID` for `HATP_HARDWARE_PROVIDER_V1` is **contract-correct**, and the Blocking condition contemplated by spec section 61 does not fire.

**ATTESTATION VERDICT: A. ATTESTATION NOT REQUIRED FOR WAVE-5 PROVIDER CONFORMANCE — contract explicitly defers it.**

---

## 10. PIV disposition (spec sections 76–79)

`hatp_piv_provider.py` (119 lines) is a **structural placeholder**, not a conformant provider:

- Imports only `pcae.core.hatp_providers` (plus `__future__`). No `pkcs11`, `pyscard`, or `smartcard`.
- `capabilities()` reports `NOT_CONFORMANT` with every property `False` — no approximation of missing properties.
- `credential_identity()` and `request_signature()` raise `HATPProviderUnavailableError` unconditionally.
- `verify()` returns `signature_valid=False, human_presence_proven=False` unconditionally (fail-closed, correctly not raising).
- The source contains no `signature_valid=True` and no `human_presence_proven=True`.
- `discover_piv()` always reports `library_installed=False, device_detected=False`.
- The production factory instantiates it **only** on explicit `allow_piv_fallback=True`; the default is `False` and the guard `if not allow_piv_fallback:` precedes the import.

**Is deferral permitted?** Re-derived from the plan's own conditional stop condition: *"if the FIDO2 spike (§23) cannot bind HATP's exact canonical payload as the signed challenge, switch to the PIV fallback strategy before continuing."* PIV is a **contingent** fallback, triggered only by FIDO2 failure. §5 above independently demonstrates that the FIDO2 binding *does* work. The trigger condition never fired, so the contract/plan does not require both provider profiles to exist.

**PIV VERDICT: DEFERRED / UNAVAILABLE — permitted, honestly reported, non-blocking.** No weak PIV fallback can be silently instantiated, and the placeholder cannot produce success without the mandatory properties.

---

## 11. Hardware-backed key and non-exportability (spec sections 7, 8, 9, 136)

### Real hardware availability (spec section 9)

Independently probed — **not** taken from 149O.2's environment statement:

- `fido2.hid.CtapHidDevice.list_devices()` → `[]` (zero devices).
- `discover_hardware_providers()` → FIDO2 `library_installed=True, device_detected=False`; PIV `library_installed=False, device_detected=False`.

**REAL HARDWARE EXECUTION: NOT EXERCISED.**

### What a software EC P-256 key actually proves

The verification fixtures in this phase use a software P-256 key to construct genuine WebAuthn-shaped assertions. That proves: protocol correctness, ECDSA/COSE signature verification, byte-exact payload binding, credential binding, presence-flag handling, and evidence-envelope strictness. It proves **nothing at all** about hardware key generation, hardware key storage, or key non-exportability — a software key structurally cannot exhibit those properties.

### Non-exportability basis (spec section 8)

What *would* legitimately establish a non-exportable private key for a real provider:

1. **Authenticator-generated credential** — the key pair is created inside the device during `makeCredential` and never leaves it.
2. **CTAP2/WebAuthn protocol semantics** — the CTAP2 command set exposes no documented private-key export operation.
3. **FIDO Alliance certification** of the authenticator model.
4. **Device attestation** binding the credential to a certified hardware class — **not implemented this phase**, which is precisely why basis (4) is unavailable and the property cannot be certified per-device.

The implementation's basis is (2), correctly stated in `capabilities().notes`: *"CTAP2 authenticators never expose the private key over any documented command."* Crucially, the accompanying note **also** says *"REAL HARDWARE NOT EXERCISED in this development environment"* — the claim is explicitly scoped, not passed off as empirical.

**"PCAE does not expose an export API" is NOT accepted as proof** (spec section 8's explicit prohibition). It is verified here as a *necessary* hygiene property only: the module handles no `private_key` / `private_bytes` / `PrivateKey` / `export_key` symbol on either side, and `request_signature` accepts no key parameter — signing happens entirely inside the device via `Ctap2.get_assertion`. Necessary, nowhere near sufficient.

**Did 149O.2 overclaim?** No. `capabilities().non_exportable_key` is `True` as a *design* property of the profile, the note scopes it to CTAP2 semantics, an explicit "REAL HARDWARE NOT EXERCISED" disclaimer is attached, and the conformance verdict is deliberately downgraded to `CONFORMANT_WITH_NON_BLOCKING_LIMITATIONS`. The blocking condition "non-exportable-key property is falsely claimed as proven" **does not fire**.

**VERDICT: HARDWARE-BACKED KEY PROPERTY: ARCHITECTURALLY SUPPORTED BUT NOT EMPIRICALLY VERIFIED.**

---

## 12. Security-property evidence classification (spec section 6)

**Category A — PROVEN BY SOFTWARE TEST**

- Challenge ≡ SHA-256 of the exact Wave-3 canonical payload; no second canonicalizer exists.
- Byte-exact payload binding; single-byte mutation, truncation, and extension all invalidate.
- Full replay rejection across all 14 signed semantic dimensions.
- Credential-ID ↔ public-key binding; wrong key, wrong credential, substituted registry key all fail.
- Public-key type confusion (RSA / Ed25519 / P-384) and malformed COSE material fail closed.
- Origin and RP-ID-hash validation are enforced predicates, not decorative fields.
- WebAuthn client-data type validation.
- Evidence-envelope strictness for unknown field, missing field, unknown version, duplicate key, non-UTF-8, non-object.
- UP-flag derivation, non-caching, per-call freshness, non-transferability between operations; UV never substitutes for UP.
- No caller-supplied presence anywhere in a production API.
- Credential-registry protected-root discipline: fixed path, env/CWD/CLI/constructor non-redirectability, unsupported-platform fail-closed, symlink refusal, duplicate/malformed fail-closed, no auto-provisioning, read-only API.
- Production factory closed allowlist (14 hostile profile strings rejected); test-provider unreachability; PIV opt-in-only.
- Optional-dependency behaviour with `fido2` and/or `cryptography` masked; no import-time device probe.
- Operational hard ceiling: `operational=False` under maximal health, with 7 environment-variable override attempts.
- No approval derivation, no RAE/Permission-Broker/agent integration in either direction.
- Trust conjunction: cross-deployment credential reuse → `WRONG_DEPLOYMENT`.

**Category B — SUPPORTED BY PROVIDER/API SEMANTICS BUT NOT PHYSICALLY EXERCISED**

- Fresh physical human presence per signing operation (CTAP2 re-evaluates UP per `getAssertion`; UP is inside the signed bytes).
- HATP-REQ-018's legitimate-signer-abuse defence in its physical half (a real authenticator refusing to assert without touch).
- Cancellation / timeout mapping to `HATPProviderCancelledError` from real `CtapError` codes.
- Real device I/O failure mapping to `HATPProviderDeviceError`.
- Multi-device deterministic selection behaviour.

**Category C — REQUIRES REAL HARDWARE AND IS CURRENTLY UNVERIFIED**

- Private key generated inside hardware.
- Private key non-exportable in fact.
- Credential hardware provenance (would require device attestation, itself not implemented).
- End-to-end `request_signature` against a live CTAP2 authenticator.
- HATP-001 §44 acceptance attacks #6 and #20 in their hardware-in-the-loop form.

---

## 13. Operational hard ceiling (spec sections 107–110, 142)

Re-attacked independently with the most favourable possible substrate: `fido2` installed, `cryptography` installed, a fully-populated and structurally valid Wave-2 trust store (principal + signer + deployment binding + authority, all `active`), a real `Fido2HardwareProvider` successfully constructible from the production factory, and a real cryptographically `VALID` Wave-4 verification result in hand.

| Probe | Result |
|---|---|
| `inspect_hatp_verification_substrate_readiness(...).operational` | **`False`** |
| `.status` | `NOT_READY` |
| `provider_profile_available` | `False` (hardcoded) |
| `provider_attestation_trusted` | `False` (hardcoded) |
| `HATP_FORCE_OPERATIONAL`, `HATP_TRUSTED_OPERATIONAL`, `PCAE_HATP_OPERATIONAL`, `HATP_HARDWARE_PROVIDER_V1`, `HATP_OPERATIONAL`, `PCAE_HATP_FORCE`, `HATP_PROVIDER_ATTESTATION_TRUSTED` set to `1` | **no effect** |
| Function signature | `(trust_store, *, current_repository_id)` — no override parameter |
| Internal guard | `assert operational is False` still present |
| Any Wave-5 module able to reach the readiness function | **none** — the string `inspect_hatp_verification_substrate_readiness` and the token `operational` appear in no Wave-5 module |

**Provider availability ≠ operational.** **A cryptographically valid, presence-proven, Wave-4 `VALID` hardware proof ≠ operational.** Wave 5 did not touch `inspect_hatp_verification_substrate_readiness`, and the ceiling is enforced by hardcoded `False` terms plus an assertion, not by prose.

**VERDICT: PROVIDER AVAILABILITY / PER-PROOF VALIDITY: DOES NOT MAKE HATP OPERATIONAL.**

---

## 14. Integration-boundary audit (spec sections 111–117)

| Check | Result |
|---|---|
| `approval_present` / `approved` / `authorized` / `can_execute` / `permission_granted` / `allow` / `decision` assigned anywhere in the four Wave-5 modules (AST over `Assign`, `AnnAssign`, and keyword arguments) | **zero matches** |
| RAE call sites (`rollback_approval_evidence`, `RollbackApprovalEvidence`) | **none** |
| Permission Broker call sites (`permission_broker`, `PermissionBroker`, `permission_broker_foundation`) | **none** |
| Agent call sites (`from pcae.core.agent`, `import agent`, `AgentInvocation`) | **none** |
| Prompt generation / prompt dispatch / runtime enforcement | **none** |
| Reverse direction: `rollback_approval_evidence.py`, `permission_broker.py`, `permission_broker_foundation.py`, `core/agent.py`, `commands/agent.py` referencing any Wave-5 module or symbol | **none** |
| Filesystem/process mutation (`subprocess`, `os.system`, `shutil`, `write_text`, `write_bytes`, `mkdir`, `unlink`) in Wave-5 modules | **none** — no rollback-execution effect is reachable |
| `pcae runtime inspect` | Observed / observe / unavailable — **unchanged** |

---

## 15. Optional dependency behaviour (spec sections 71–75)

Exercised in real subprocesses with a `sys.meta_path` import blocker, for three configurations: `fido2` absent, `cryptography` absent, both absent.

| Configuration | `import pcae` + core HATP modules | `discover_hardware_providers()` | `create_production_hardware_provider(...)` |
|---|---|---|---|
| `fido2` blocked | OK | FIDO2 `(False, False)`, PIV `(False, False)` — no raise | `HATPProviderUnavailableError` |
| `cryptography` blocked | OK | same | `HATPProviderUnavailableError` |
| both blocked | OK | same | (not applicable) |

Additionally corroborated by a **genuinely independent second interpreter** present on this machine: Homebrew Python 3.14.5 has `pcae` importable but **no** `fido2` installed. `import pcae` succeeds, discovery reports `fido2_library_not_installed:ModuleNotFoundError`, and the factory raises `HATPProviderUnavailableError`. This is a real-environment confirmation, not only a mocked one.

- **No import-time device probe**: AST-confirmed that no module-level statement in any Wave-5 module calls `list_devices`; every such call is inside a function body.
- **No import-time hardware failure**: `Fido2HardwareProvider()` construction touches neither hardware nor the registry.
- **`pcae health` and `pcae check` both exit 0** with no device attached.
- Only `hatp_fido2_provider.py` imports `fido2`/`cryptography` at module level, and `hatp_providers.py` imports it **lazily** — the concrete provider modules appear in no module-level import statement of `hatp_providers.py`.

---

## 16. Regression results

Two interpreters exist on this machine and the distinction is material (see B-149O.3-10):

- **`.venv/bin/python` — CPython 3.9.6**, has `fido2==1.2.0` + `cryptography==44.0.3`. This is the environment in which Wave 5 is actually exercisable, and the one Phase 149O.2 used.
- **`python` on `PATH` — Homebrew CPython 3.14.5**, has `pcae` but no `fido2`.

Unless noted, results below are from `.venv/bin/python` (pytest 8.4.2).

| Suite | Command | Result | Assessment |
|---|---|---|---|
| **149O.3 own suite** | `pytest tests/test_phase_149o_3_...py -q` | **242 passed, 1 skipped** | new; the skip is the hardware-required placeholder |
| **Wave 5 (149O.2's own)** | `pytest tests/test_phase_149o_2_...py -q` | **62 passed, 1 skipped** | exact match to entering baseline |
| **Wave 4** | `pytest tests/test_hatp_verification_engine.py tests/test_phase_149o_1j_...py -q` | **136 passed** | exact match to 59 + 77 |
| **Waves 1–2** | `pytest tests/test_repository_identity.py tests/test_hatp_bootstrap_foundation.py -q` | **40 passed** | exact match |
| **Combined HATP** | `pytest tests/ -k 'hatp or 149o_1 or 149o_2 or 149o_3' -q` | **1617 passed, 4 skipped, 91 failed** | 1617 = 1376 + 241 new. The 91 failures reproduce 149O.2's count exactly, **and are now root-caused** — see B-149O.3-10 |
| **Combined HATP, Python 3.14** | same selection, Homebrew 3.14.5 | **1405 passed, 4 skipped, 0 failed** | the 91 failures **vanish entirely** on a newer interpreter |
| **Report trust** | `pytest tests/test_phase_reports.py tests/test_phase_reports_cli.py tests/test_phase_report_trust_hard_fail.py -q` | **186 passed, 1 failed** | exact match; `test_public_reconciliation_requires_report_marker_checkpoint_and_receipt` is the known pre-existing live-`.pcae/`-state failure |
| **Permission Broker** | `pytest -k permission_broker -n auto -q` | **990 passed, 1 failed** | the +12 over 149O.2's 978 is this phase's own parametrized boundary tests matching the keyword. Under Python 3.14 the same selection gives **978 passed, 1 failed**, exactly matching 149O.2. The one failure is the known `test_permission_broker_consumer_scope_inventory` docstring-prose false positive |
| **RAE canonical provenance** | `pytest tests/test_phase_149o_rollback_approval_evidence_...py -q` | **1 passed, 16 failed** (3.9) / **13 passed, 4 failed** (3.14) | B-149O-1..4 remain OPEN. **The 149O.2-vs-149O.1J discrepancy 149O.2 declined to investigate is resolved here**: it is purely the interpreter version |
| **Fast Green** | `pytest -m fast_green -n auto -q` | **4652 passed, 1 skipped, 0 failed** | exact match to entering baseline. This phase's verification suite is deliberately **not** registered into Fast Green (149O.1J precedent), so the count is unchanged |
| **Agent** | `pytest tests/test_agent.py -q` | not re-run this phase (671 s single-process; 149O.1J/149O.2 both recorded 4236 passed) | **Independently confirmed instead by source audit**: `core/agent.py` and `commands/agent.py` reference no Wave-5 module or symbol, in either direction |
| **Full suite** | see §16.1 | see §16.1 | |

### 16.1 Full suite (spec section 129)

The full suite **cannot be run under `-n auto` at all**, and this is **pre-existing and unrelated to Phase 149O.3** — see B-149O.3-13. `tests/test_phase_149o_1h_hatp_proof_models_canonical_serialization_independent_verification.py` (landed in Phase 149O.1H) evaluates `str(uuid.uuid4())` inside `@pytest.mark.parametrize` data, which is executed at **collection** time. Each `pytest-xdist` worker therefore collects a different test ID and the run aborts with `Different tests were collected between gw0 and gwN`.

Proven pre-existing: with all of Phase 149O.3's changes stashed (`git stash push -u`), `pytest tests/test_phase_149o_1h_...py -n 4` on unmodified `main` fails with the identical error, then restored. This is the same class of xdist collection-nondeterminism gotcha this repository has already recorded once before (enum-frozenset parametrization).

The full suite was therefore executed in the only configuration available: `-n auto` with that one module and `tests/test_agent.py` excluded, plus those two modules single-process. Results are recorded in the phase-completion metadata. All failures classify into the four already-known pre-existing buckets (Python-3.9 ISO-8601 parsing, the RAE B-149O-1..4 findings, the report-trust live-state test, and the Permission Broker docstring-prose inventory test). **No new failure is attributable to Phase 149O.2 or 149O.3.**

---

## 17. Findings

No finding is repaired by this phase. **Zero BLOCKING.**

### B-149O.3-1 — NON-BLOCKING — Credential-registry readiness check is weaker than the Wave-2 trust store

`inspect_credential_store_environment` duplicates `inspect_bootstrap_environment` but omits three checks: **root owned by the agent uid** (`agent_and_admin_share_os_principal`), **parent is a symlink**, and **parent owner mismatch**. Reproduced directly: an agent-owned root reports `READY` from the Wave-5 inspector while the identical root reports `UNSAFE_CONFIGURATION` from the Wave-2 inspector.

*Why non-blocking:* the production root is a fixed, root-owned platform path the agent principal provably cannot create on this machine; the registry holds only **public** key material and grants no authority by itself; and `verify_hatp_proof` still independently requires the Wave-2 store to authorize signer, principal, authority, and deployment binding. Exploitation requires host-root write access, which is **Threat B** and out of HATP-001 scope per HATP-REQ-009. The registry is neither agent-writable nor redirectable, so spec section 134's blocking condition does not fire.

*Recommended disposition:* fold into an optional 149O.3.1 hardening phase, or into Wave 7's deployment-provisioning work where the Class-B ownership model is established anyway.

### B-149O.3-2 — OBSERVATION — Credential-registry readiness is consumed by nothing

`HATPHardwareCredentialStore.environment_status()` / `inspect_credential_store_environment` is called by no production caller: not by `Fido2HardwareProvider.verify`, not by `verify_hatp_proof`, not by `inspect_hatp_verification_substrate_readiness` (which Wave 5 did not modify). The registry's readiness posture therefore has **no effect on any verification outcome today**. Harmless while the hard ceiling keeps `operational=False` unconditionally, but the term will need wiring when Wave 5/6 makes `provider_profile_available` a real conjunction term — otherwise B-149O.3-1 becomes load-bearing.

### B-149O.3-3 — NON-BLOCKING — Credential-registry schema is open where Wave 2's is closed

`REGISTRY_SCHEMA_VERSION = 1` is declared but never read by `_load_registry`, `lookup_credential`, or `_parse_credential`. A registry document declaring `"registry_version": 99` plus an arbitrary unknown top-level object, and a credential record carrying an unknown field, is **accepted**. The Wave-2 trust store rejects the equivalent document on both counts. This forfeits forward-compatibility safety (a future schema-2 registry would be silently misread as schema 1).

### B-149O.3-4 — OBSERVATION — Non-object credential entries are silently skipped

`lookup_credential` filters with `isinstance(raw, dict)`, so `{"credentials": ["garbage", 17, null]}` yields a clean `None` rather than a malformed-registry error. Conservative in effect (it can only cause a lookup to fail closed), but it is a parse relaxation Wave 2 does not share — Wave 2 parses and rejects every array element.

### B-149O.3-5 — OBSERVATION — First-enumerated-device selection

`request_signature` uses `device = devices[0]` with no deterministic ordering across multiple attached authenticators. Materially mitigated: the CTAP2 `allow_list` carries the exact credential ID, so a device that does not hold the credential fails closed rather than substituting its own. Unexercisable without hardware (Category B).

### B-149O.3-6 — OBSERVATION — WebAuthn signature counter ignored

`signCount` is neither read nor validated. Independently confirmed that HATP-001 contains no "signature counter" or "signCount" requirement, so this is **not** a contract violation. Recorded because the contract is silent rather than permissive, and cloned-authenticator detection is a property a future profile revision may want.

### B-149O.3-7 — OBSERVATION — Registry `algorithm` field is advisory and uncross-checked

`HardwareCredentialRecord.algorithm` is stored but never compared against the stored COSE key; `record.algorithm` appears nowhere in the FIDO2 provider. Safe in practice — verification uses the COSE key itself, whose own `alg` label is authoritative — so an inconsistent `algorithm` string can neither downgrade nor confuse verification (demonstrated: `"RS256-nonsense"` changes nothing). Recorded as unused state that could mislead a future reader.

### B-149O.3-8 — NON-BLOCKING — `Fido2HardwareProvider.verify()` raises for structurally malformed evidence

The frozen `HATPProofVerifierProvider.verify` contract states: *"MUST NOT raise for an invalid/unrecognized assertion — return `signature_valid=False` instead; raising is reserved for genuine provider-level failure."* It does raise. `_parse_fido2_evidence` performs `bytes.fromhex(...)`, `AuthenticatorData(...)`, and `CollectedClientData(...)` **outside** the `HATPFido2EvidenceMalformedError` boundary, while `verify()` catches only that one exception type. Reproduced for 12 inputs:

| Input | Escaping exception |
|---|---|
| non-hex `signature_hex` (`"zz"`), odd-length (`"0"`) | `ValueError` |
| non-hex `credential_id_hex`, `authenticator_data_hex`, `client_data_json_hex` | `ValueError` |
| truncated / empty / 36-byte `authenticator_data_hex` | `ValueError` |
| non-JSON or empty `client_data_json_hex` | `json.JSONDecodeError` (a `ValueError`) |
| `clientDataJSON` missing `challenge` (`{}` or `{"type":"webauthn.get"}`) | `KeyError` |

This **narrows the scope of Phase 149O.2's own `evidence_format_strictness` claim** that malformed evidence "never raises": that claim holds only for the five envelope-level cases 149O.2 exercised (unknown field, missing field, unknown version, duplicate key, non-UTF-8 garbage), not for malformed hex or malformed inner WebAuthn structures. One malformed-signature case (`signature_hex: ""`) *is* handled correctly, so the finding is scoped precisely and not overstated.

*Why non-blocking:* `verify_hatp_proof` (Wave 4, unmodified) wraps the provider call in `except Exception` and maps it to `INVALID_SIGNATURE`. Verified end-to-end: a proof with `"signature_hex": "zz"` returns `INVALID_SIGNATURE`, never `VALID`. **HATP fails closed in every case.** The defect is confined to the provider layer's own reusability contract — it would matter to any future non-Wave-4 caller of `provider.verify`, and to Wave 6's error-classification granularity.

### B-149O.3-9 — OBSERVATION — Evidence `version` check is numerically loose

`document["version"] != _EVIDENCE_SCHEMA_VERSION` uses Python numeric equality, so JSON `true` and `1.0` are both accepted as schema version 1. Semantically harmless (both *are* numerically 1), but type-loose where the rest of the envelope parsing is strict.

### B-149O.3-10 — OBSERVATION (PRE-EXISTING, WAVE-3, OUT OF SCOPE) — The 91-failure HATP baseline is interpreter-version-dependent, not "timezone-dependent"

Phase 149O.2 characterised its 91 combined-HATP failures as "environment/timezone-dependent (ISO-8601 fraction/offset parsing edge cases)" and explicitly declined to investigate the related RAE 16/1-vs-4/13 discrepancy. **Both are root-caused here.**

`_parse_iso_timestamp` delegates to `datetime.fromisoformat`, whose accepted lexical set widened substantially in **Python 3.11**. Directly demonstrated:

| Lexical form | CPython 3.9.6 | CPython 3.14.5 |
|---|---|---|
| `2026-01-01T12:00:00Z` | `ValueError` | accepted |
| `2026-01-01T12:00:00.123+0000` | `ValueError` | accepted |
| `2026-01-01T12:00:00,123Z` | `ValueError` | accepted |
| `2026-01-01T13:00:00.123+01` | `ValueError` | accepted |

Consequently the identical selection yields **91 failed** under 3.9.6 and **0 failed** under 3.14.5, and the RAE suite yields 16-failed vs 4-failed on the same two interpreters.

This matters because `pyproject.toml` declares `requires-python = ">=3.9"`. Under the project's own **declared minimum supported interpreter**, HATP's accepted timestamp lexical set is materially narrower than the Wave-3 tests assert. That is a genuine cross-interpreter portability divergence in **Wave 3**, not an "environmental" artifact — and it is **out of Phase 149O.3's verification-only scope**, unrelated to Wave 5, and unaffected by the `fido2`/`cryptography` installation (which touches no timestamp code).

*Recommended disposition:* route to a dedicated Wave-3 timestamp-portability phase, which should decide between raising `requires-python` and making `_parse_iso_timestamp` interpreter-independent. Not a Wave-5 blocker.

### B-149O.3-11 — OBSERVATION — Undisclosed Wave-5 partial scope: human-side approval CLI surface

The 149O.1D plan's Wave-5 Files/modules line names *"a human-side approval CLI surface (namespace TBD, §29-32)"*. Phase 149O.2 did not implement it (no `src/pcae/commands/*hatp*` module exists) and its report does not disclose the omission. Non-blocking — the plan itself defers the namespace to "Wave 5/7", and the blind-touch-defense component it would host has no consumer until Wave 6 — but the omission should be tracked rather than silently absorbed, and Wave 6/7 planning must account for it.

### B-149O.3-12 — OBSERVATION — Production factory docstring overclaims device detection

`create_production_hardware_provider`'s docstring claims it raises `HATPProviderUnavailableError` for *"any unrecognized profile string, missing optional dependency, or absent device"*. It performs no device check — no `device_detected` and no `list_devices` in its body — and returns a `Fido2HardwareProvider` whenever the library imports, as demonstrated on this device-free machine. Harmless (a verify-only provider legitimately needs no device, and every device-requiring operation fails closed), but the docstring is inaccurate.

### B-149O.3-13 — OBSERVATION (PRE-EXISTING, OUT OF SCOPE) — Full suite is unrunnable under `pytest-xdist`

`tests/test_phase_149o_1h_hatp_proof_models_canonical_serialization_independent_verification.py` evaluates `str(uuid.uuid4())` inside `@pytest.mark.parametrize` data, which runs at collection time, so each xdist worker collects different test IDs and any `-n auto` run spanning that module aborts with `Different tests were collected between gw0 and gwN`. Proven pre-existing by stashing all of Phase 149O.3's changes and reproducing on unmodified `main`. Landed in Phase 149O.1H; means no full-suite `-n auto` run has been possible since. Trivially repaired by using fixed UUID literals in the parametrize data.

### Retained findings from earlier phases

| Finding | Status |
|---|---|
| B-149O.1H-1 | independently re-confirmed **CLOSED** (Wave-3 suites pass unchanged; Wave-3 source byte-unchanged) |
| B-149O.1H.4-1 | independently re-confirmed **CLOSED** |
| B-149O.1H-2 | independently re-confirmed **CLOSED** |
| B-149O.1F-1 | **CLOSED** — re-verified: the credential registry independently avoids the agent-home trap (fixed platform path, no `Path.home`, no `expanduser`, no env read) |
| B-149O.1R-1 | **CLOSED** |
| B-149O.1R-2 | **CLOSED** |
| B-149O-1 … B-149O-4 | **OPEN**, unchanged, unaffected by Waves 4/5 |

---

## 18. Blocking-condition checklist (spec section 134)

Every named blocking condition, evaluated:

| Condition | Fires? |
|---|---|
| Software-exportable key can enter the production hardware path | **No** — no production write path exists |
| Non-exportable-key property falsely claimed as proven | **No** — claim is explicitly scoped and disclaimed |
| Caller can assert user presence | **No** |
| UP check is bypassable | **No** |
| Presence from operation A can satisfy operation B | **No** |
| Provider verifies evidence over noncanonical proof semantics | **No** — exact Wave-3 bytes, no second canonicalizer |
| Challenge construction allows payload substitution | **No** |
| Wrong credential / public key can succeed | **No** |
| Proof or provider can self-select trust | **No** — the proof carries no key field at all |
| Credential registry is agent-writable or redirectable | **No** |
| Credential registry has weaker protected-root semantics than required | **No** — weaker than Wave 2 (B-149O.3-1/-3), but the *required* boundary holds |
| Duplicate / malformed credential state can be selected | **No** |
| Test or software provider reachable through the production factory | **No** |
| Missing optional dependency crashes normal PCAE | **No** |
| Device absence crashes import or core commands | **No** |
| Attestation normatively required but absent | **No** — not normatively required (§9) |
| PIV placeholder can produce success without mandatory properties | **No** |
| Provider availability makes HATP operational | **No** |
| Wave 5 derives `approval_present=True` | **No** |
| Wave 5 wires RAE / Permission Broker / agent execution | **No** |
| Wave-3 canonicalization changed | **No** — byte-unchanged |
| Wave-4 verification semantics changed improperly | **No** — byte-unchanged |
| HATP-001 changed | **No** — byte-identical hash |

**Zero blocking conditions fire.**

---

## 19. Verdicts

- **HARDWARE-BACKED KEY PROPERTY: ARCHITECTURALLY SUPPORTED BUT NOT EMPIRICALLY VERIFIED**
- **FRESH USER PRESENCE: PROTOCOL-SEMANTICALLY VERIFIED; REAL DEVICE NOT EXERCISED**
- **ATTESTATION: A. ATTESTATION NOT REQUIRED FOR WAVE-5 PROVIDER CONFORMANCE — contract explicitly defers it**
- **HARDWARE CREDENTIAL REGISTRY: PROTECTED AUTHORITY BOUNDARY VERIFIED**
- **PRODUCTION PROVIDER FACTORY: CLOSED, TEST/SOFTWARE PROVIDERS EXCLUDED**
- **HARDWARE PROVIDER PAYLOAD BINDING: EXACTLY DERIVED FROM VERIFIED WAVE-3 CANONICAL SEMANTICS**
- **PROVIDER AVAILABILITY / PER-PROOF VALIDITY: DOES NOT MAKE HATP OPERATIONAL**
- **OVERALL: VERIFIED WITH NON-BLOCKING FINDINGS — HATP WAVE 5 HARDWARE PROVIDER CONFORMS**

---

## 20. Production readiness

**HATP PRODUCTION: NOT READY.**

Wave 6 (RAE integration) and Wave 7 (Class-B deployment provisioning, credential enrollment, deployment verification) remain outstanding. HATP-REQ-029/§37's frozen statement stands: this deployment runs the Agent and Human/Admin functions under the same OS principal and is therefore **NOT READY** regardless of proof validity. `inspect_hatp_verification_substrate_readiness` enforces this mechanically.

Runtime remains **Observed / observe / unavailable**.

---

## 21. Recommended next phase

Per the 149O.1D plan's own wave ordering, and because Wave 5 verifies with no Blocking findings, the next phase is **Wave 6 — RAE Integration** (`HATP-REQ-095..096`, `HATP-REQ-101..104`): extend `src/pcae/core/rollback_approval_evidence.py` so `approval_present` derivation conditions on **both** RAE-001's own pass **and** a `VALID` HATP result, under Wave 4's activation-conjunction discipline — which means `approval_present` still cannot become `True` in this deployment even after that wave lands, because Wave 7's Class-B provisioning does not exist.

The plan defines no intermediate certification/readiness phase between Waves 5 and 6, so Wave 6 may be entered directly.

**Optional and explicitly not required by this verdict:** a narrow **149O.3.1** hardening phase closing B-149O.3-1 (registry ownership-check drift), B-149O.3-3 (registry schema closure), and B-149O.3-8 (provider `verify()` fail-closed-without-raising). B-149O.3-10 and B-149O.3-13 are pre-existing, out-of-scope, and belong to separate Wave-3 / test-infrastructure phases.

**Phase 149O.3 stops here.** Wave 6 is not started and not authorized by this phase.

---

## 22. Explicit no-go confirmations

- HATP-001 v1.0 remained byte-unchanged (hash-verified).
- No production code was modified by Phase 149O.3.
- Wave-1 repository identity remained unchanged.
- Wave-2 trust-store semantics remained unchanged.
- Wave-3 proof/canonicalization semantics remained unchanged.
- Wave-4 verification-state semantics remained unchanged.
- B-149O.1H-1 remains independently confirmed closed.
- B-149O.1H.4-1 remains independently confirmed closed.
- B-149O.1H-2 remains independently confirmed closed.
- B-149O.1F-1 remains closed.
- B-149O.1R-1 remains closed.
- B-149O.1R-2 remains closed.
- No `approval_present=True` derivation exists.
- No RAE production integration exists.
- No AG3/AG5 Permission Broker integration exists.
- No rollback execution behavior changed.
- No Runtime Enforcement behavior changed.
- No Prompt Generation, Prompt Dispatch, or agent-invocation capability was implemented.
- Provider-level cryptographic validity remains distinct from signer trust.
- Human presence remains distinct from approval.
- Wave-4 `VALID` remains distinct from approval, permission, capability, execution, and operational readiness.
- B-149O-1 through B-149O-4 remain OPEN.
- HATP production remains NOT READY.
- Runtime remains Observed / observe / unavailable.
- No governance bypass, `--no-verify` flag, or force push was used.
- No Blocking defect was found; no finding was repaired.
