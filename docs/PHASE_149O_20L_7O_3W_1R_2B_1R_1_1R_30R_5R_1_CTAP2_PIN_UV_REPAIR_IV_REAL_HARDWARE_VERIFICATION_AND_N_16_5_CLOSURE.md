# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.1 — Independent Verification of the CTAP2 PIN/UV Repair + Mandatory Real-CTAP2-Hardware Verification + N-16-5 Closure

**Phase ID:** 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.1
**Type:** governed independent-verification + certification phase (== RHAMP `.1R.33`) — verification only; no production or normative-contract change
**Status:** **BLOCKED.** N-16-5: **NOT CLOSED.**
**H-1 (CTAP2 PIN/UV interoperability repair): INDEPENDENTLY VERIFIED — REAL-CTAP2-HARDWARE VERIFIED.**
**New blocking finding H-2: the protected-presentation helper has no interactive human-election surface.**

**Anchors (re-derived from primary source, not inherited from prose):**

| Anchor | SHA | Meaning |
|---|---|---|
| `A` | `9f004ea9` | finalized `.1R.30R.5` BLOCKED head (fixed-SHA attribution baseline) |
| `R` | `ea40c47e` | finalized `.1R.30R.5R` repair head |
| `V` | `ea40c47e` | `.1R.30R.5R.1` phase-entry SHA (`git rev-parse HEAD` + `git rev-list --count origin/main..HEAD` = 0 at entry) |

`V == R` — this IV phase entered directly on the finalized repair head.

---

## 1. Verdict

The narrow CTAP2 PIN/UV interoperability repair implemented by
`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R` (finding **H-1**) is **independently
verified from primary source** and **certified against genuine FIDO_2_1
hardware**. The repaired production `NativeCtap2Provider` successfully
completed real `authenticatorMakeCredential` and real
`authenticatorGetAssertion` ceremonies against an attached roaming USB CTAP 2.1
security key — the exact interaction that failed with `CTAP2_ERR_INVALID_OPTION`
(`0x2C`) before the repair.

**N-16-5 does not close.** RHAMP-REQ-152's mandatory real-hardware evidence
requires (bullet 4) *"a presentation-bound approval [that] succeeded end-to-end
(real helper render → explicit Approve election → assertion → proof → Gate 5)
and yielded a `PRODUCTION` `AuthenticatedHumanPrincipal` for exactly one
approval."* This cannot be performed: the production protected-presentation
helper (`src/pcae/protected_presentation_helper.py`, `_observe_election`) has
**no interactive human-election surface** — it returns `CANCEL` for every
production ceremony unless the disclosed `_test_decision_source` test seam is
used. `.1R.30R.4R.1` (== RHAMP `.1R.32`) implemented the presentation protocol,
the deterministic rendering, the digest-equivalence check, and the
election *binding*, but deferred the actual interactive input to *"the mandatory
real-CTAP2-hardware verification phase"* (this one). This phase is
**verification only** (governing prompt, STRICT AUTHORIZED SCOPE: *"This phase
MUST NOT repair production defects found during this IV"*), so the missing
surface is **adjudicated as finding H-2, not repaired** — exactly as `.1R.30R.5`
adjudicated H-1.

This matches the frozen **VALID BLOCKED CONDITIONS** verbatim: *"protected
presentation coupling fails where required"*; *"N-16-5 requirements remain
incomplete"*.

No production code was changed, no deterministic fixture was substituted for
the CTAP2 authenticator, no hardware evidence was fabricated, and — because
bullet 4 is unsatisfiable — no N-16-5 closure is claimed.

---

## 2. Independent verification of the `.1R.30R.5R` repair (primary source)

### 2.1 Production diff — exactly one file

`git diff 9f004ea9 ea40c47e -- src/pcae scripts pyproject.toml` touches
**exactly one file**: `src/pcae/core/hpac_rhamp_ctap2.py`. `git diff 9f004ea9
ea40c47e -- docs/contracts` is **empty**. `pyproject.toml` byte-unchanged — no
new dependency (`fido2 1.2.0` / `cryptography` were already declared).

### 2.2 Contract byte identity (re-derived at HEAD)

`git diff 9f004ea9 HEAD -- docs/contracts` is empty. RHAMP-001 v1.0,
HPAC-PPA-001 v1.0, HPAC-PAWA-001 v1.2, HPAC-001 v2.1, RIHAC-001 v2.0,
RIASC-001 v3.0, HPAC-AUTHORITY-CONSUMPTION/2.1, CPIPC-001 v1.0 all frozen.

### 2.3 H-1 root-cause reconstruction (from the immutable `.1R.30R.5` record)

Pre-repair, `NativeCtap2Provider.make_credential` sent
`options={"rk": False, "uv": True}` and `.get_assertion` sent
`options={"uv": True}`. CTAP 2.1 removed the `uv` **option** from
`authenticatorMakeCredential` and requires a PIN/UV-protocol `pinUvAuthParam`
for `authenticatorGetAssertion` on a `clientPin`-based roaming key → every
`FIDO_2_1` authenticator rejects with `0x2C` **before any user gesture**. The
automated suite stayed green only because `DeterministicCtap2Provider`
(`SIMULATION_ONLY = True`) honoured the invalid shape — the RHAMP-INV-018 gap.

### 2.4 Repair mechanics — verified against the pinned `fido2 1.2.0` API

| Property | Evidence (primary source) | Verdict |
|---|---|---|
| GetInfo-driven capability negotiation | `_obtain_pin_uv` reads `ctap2.info.options` (`uv`, `clientPin`); `ClientPin(ctap2)` negotiates from `info.pin_uv_protocols` | VERIFIED |
| PinProtocolV2 preferred, V1 fallback | `fido2.ctap2.ClientPin.PROTOCOLS == [V2, V1]`; `ClientPin.__init__` iterates and picks the first supported; no mutually-supported protocol → `ValueError` → `Ctap2UnavailableError` (fail closed) | VERIFIED |
| No UV downgrade / no bare-`uv` fallback | `make_credential` sends `options={"rk": False}` (no `uv`); `get_assertion` sends no `options`; both raise `Ctap2UnavailableError` on `CtapError` with **no** bare-`uv` retry; `make_credential` additionally rejects a `FLAG.UV`-clear response | VERIFIED |
| Built-in UV vs PIN | `if builtin_uv: client_pin.get_uv_token(...)` else trusted PIN → `client_pin.get_pin_token(...)` | VERIFIED |
| Permission-scoped token | `permission = {make_credential: PERMISSION.MAKE_CREDENTIAL, get_assertion: PERMISSION.GET_ASSERTION}[permission_name]` — each ceremony gets only its own permission | VERIFIED |
| rp-id-bound token | `_PIN_UV_TOKEN_RP_ID = RP_ID` (`"hpac.pcae.local"`), passed as `permissions_rpid`; never caller-selectable | VERIFIED |
| Command-scoped `pinUvAuthParam` | `protocol.authenticate(token, client_data_hash)` — derived over the per-ceremony `client_data_hash`; distinct token + permission per ceremony | VERIFIED |
| Trusted, non-logging, non-persisted PIN | `_default_pin_prompt` — `getpass`, `sys.stdin.isatty()`-guarded, non-interactive → fail closed; `EOFError`/`KeyboardInterrupt` → `Ctap2CancelledError`; `del pin` in `finally`; PIN never stored on the provider, never on an exception message (`_map_pin_uv_ctap_error` is PIN-free), never on a RHAMP artifact | VERIFIED |
| Error mapping — no new `terminal_reason_code` | `_map_pin_uv_ctap_error` maps `ClientPin` / PIN-UV `CtapError` codes onto **existing** reasons; all referenced `CtapError.ERR.*` constants (`USER_ACTION_TIMEOUT`, `KEEPALIVE_CANCEL`, `PIN_AUTH_INVALID`, `UV_INVALID`, `PIN_AUTH_BLOCKED`, `UV_BLOCKED`, `PIN_NOT_SET`, `PUAT_REQUIRED`, `INVALID_OPTION`) exist in `fido2 1.2.0`; the enum stays at 41 | VERIFIED |
| Deterministic-provider realism | `_VirtualCtap2Authenticator` rejects: bare `uv` → `INVALID_OPTION` (0x2C); missing `pinUvAuthParam` → `PUAT_REQUIRED` (0x36); wrong protocol → `INVALID_PARAMETER`; wrong param / permission / rp_id → `PIN_AUTH_INVALID` (0x33). `SIMULATION_ONLY = True`, `PROVIDER_KIND_IS_REAL = False` | VERIFIED |
| Production / test provider separation | `resolve_production_ctap2_provider()` → `NativeCtap2Provider()` with no seam, no env var, no flag; `build_virtual_ctap2_test_seam` is test-only and unreachable from the resolver; the three `_connection_factory` / `_client_pin_factory` / `_pin_prompt` params are keyword-only, underscore-prefixed, default `None` | VERIFIED |
| `DeterministicCtap2Provider` byte-unchanged | still the `Ctap2Provider`-level NON_REAL fixture; `SIMULATION_ONLY` is the class constant `True` with no constructor override | VERIFIED |

### 2.5 `.1R.30R.5R` repair suite

`tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_ctap2_pin_uv_repair.py`
re-run unchanged: **48 passed**.

### 2.6 Fresh `.1R.30R.5R.1` IV suite

`tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_1_ctap2_pin_uv_repair_iv.py`
— hardware-free and deterministic (RHAMP-REQ-154). Covers: anchor derivation;
one-file production diff; contracts byte-unchanged; H-1 locus repaired (no
bare-`uv` shape, `ClientPin` / `pin_uv_param` / `pin_uv_protocol` /
`_obtain_pin_uv` present); GetInfo negotiation; V2-preferred / V1-fallback /
no-compatible-protocol fail-closed; permission scoping; rp-id binding;
command-scoped `pinUvAuthParam`; PIN non-logging / non-persistence / tty-guard /
cancellation; `_map_pin_uv_ctap_error` uses only extant `CtapError.ERR`
constants and mints no new `terminal_reason_code`; deterministic-fixture
realism (rejects the historical shape); deterministic provider stays NON_REAL;
production resolver seam-free; registration / counter / verifier / presentation
/ Gate 5-9 modules byte-unchanged; the `require_real_assurance` PRODUCTION chain
composes in software (in-process helper shim, downstream-only — **not** a
substitute for the real helper, whose absence is finding H-2); H-2 pinned;
runtime posture unchanged; N-16-6 / N-16-7 untouched; FIDO2 profile is
supported-not-exclusive; the mobile-only future path stays architecturally
open.

---

## 3. Mandatory real-CTAP2-hardware verification (RHAMP-REQ-152)

Performed with the harness
`scratchpad/rhamp_hw_cert.py` (NOT a pytest module — RHAMP-REQ-154), run once
locally against a genuine attached security key. Non-secret evidence:
`.pcae/certification/rhamp_hardware_cert_30r5r1.json`.

### 3.1 Genuine hardware (deterministic fixture never involved)

- **Provider:** `resolve_production_ctap2_provider()` → `NativeCtap2Provider`
  (`PROVIDER_KIND = "native-ctap2"`); no seam populated.
- **Authenticator (`authenticatorGetInfo`):** `versions = [U2F_V2, FIDO_2_0,
  FIDO_2_1_PRE, FIDO_2_1]`; `aaguid = b7d3f68e88a6471e9ecf2df26d041ede`;
  `options` include `clientPin: true`, `pinUvAuthToken: true`,
  `makeCredUvNotRqd: true`, `alwaysUv: false`, `options.uv` **absent** (no
  on-device biometric UV → the PIN path); `pin_uv_protocols = [2, 1]`;
  `transports = [nfc, usb]`; ES256 among the algorithms.
- **Transport:** USB-HID (frozen-allowed). No browser WebAuthn, no platform
  authenticator, no network/proxy, no BLE/hybrid.
- **Genuineness proof:** the persisted canonical sidecar `aaguid` is
  `b7d3f68e88a6471e9ecf2df26d041ede` — identical to the live GetInfo `aaguid`
  and **not** the deterministic fixture's `0x11`×16; the observed
  signature-counter was **6** then **8** — **not** the fixture's `0 → 1`. The
  `DeterministicCtap2Provider` was never constructed on the ceremony path.

### 3.2 RHAMP-REQ-152 evidence obtained

| RHAMP-REQ-152 requirement | Result | Verdict |
|---|---|---|
| supported roaming USB CTAP2 key used | AAGUID `b7d3f68e…`, USB-HID, FIDO_2_1 | ✅ VERIFIED |
| real `makeCredential` → canonical `CredentialRecord` + sidecar + counter-state | `credential_id hpc-50ca429c…`; registry record `status=active`, `mechanism_id=hpac.fido2.uv_presence.v2`, `assurance_capabilities ⊇ {UP, UV}`; sidecar `cose_public_key == registry.public_key`, `transports=('usb',)`, real `aaguid`; `RHAMP-COUNTER-STATE/1.0` initialised; exactly one ACTIVE canonical credential resolves | ✅ VERIFIED |
| real `getAssertion` → passes the full §37 verifier sequence with `FLAG.UP` + `FLAG.UV` | two real assertions; `verify_real_fido2_assertion` accepted both; `env.up and env.uv` True on both | ✅ VERIFIED |
| real rpIdHash | §37 step 2 — `authenticatorData.rpIdHash == SHA-256("hpac.pcae.local")` verified through production code | ✅ VERIFIED |
| real COSE signature | §37 step 3 — ES256 assertion signature verified against the canonical stored COSE public key; no test bypass | ✅ VERIFIED |
| real native client context | §37 step 4 — `RHAMP-CLIENT-CONTEXT/1.0` reconstructed from trusted state and matched; no browser origin | ✅ VERIFIED |
| real counter / currentness | observed sign-count `6 → 8` across two ceremonies — meaningful and monotonic (RHAMP §20 advance) | ✅ VERIFIED |
| real user presence (UP) + real user verification (UV) | genuine physical touch on every ceremony; PIN entered in the trusted local `getpass` prompt; `FLAG.UV` observed on every assertion; no UP-only downgrade | ✅ VERIFIED |
| wrong-challenge rejected | verifying assertion #1 against challenge #2 → `client_data_hash_mismatch`; wrong `invocation_id` → `client_data_hash_mismatch` | ✅ VERIFIED |
| replayed challenge/proof rejected | re-verifying assertion #1 against a counter-state advanced past it → `signature_counter_regression` (RHAMP §20 currentness) | ✅ VERIFIED |
| missing / failed UV rejected (where testable — §39) | deterministic no-UV enrollment → `enrollment_ceremony_evidence_invalid`; the real-hardware requirement is the genuine positive UV path (§39) | ✅ VERIFIED |
| revoked credential rejected | canonical `revoke_credential(...)` → `resolve_active_credentials` returns `()`, `resolve_authentication_allowlist` returns `()`, verifier `_resolve_credential` raises `HPACVerificationError` (`credential_not_active`) | ✅ VERIFIED |
| **presentation-bound approval end-to-end → Gate 5 → `PRODUCTION` `AuthenticatedHumanPrincipal` for exactly one approval** | **NOT PERFORMABLE — finding H-2** (see §4) | ❌ **NOT VERIFIED** |

No PIN, PIN/UV token, or private key appears in the evidence record. Attestation
was not consulted; no device-identity / manufacturer / MDS claim is made
(RHAMP keeps attestation non-authoritative). The one certification credential
was canonically revoked at the end of the ceremony (§49).

---

## 4. Finding H-2 (BLOCKING) — protected-presentation helper has no interactive election surface

`src/pcae/protected_presentation_helper.py`, `_observe_election` (lines
217–244):

```python
directive = request.get("test_decision_directive")
if directive is not None:
    ...  # the disclosed _test_decision_source test seam
# No interactive surface available this phase → explicit cancel.
return "CANCEL"
```

The helper docstring states it plainly: *"A real interactive local surface is
successor work (the mandatory real-CTAP2-hardware verification phase). When no
interactive surface is available and the launcher has not supplied the
disclosed test-only decision seam, the helper fails closed with `CANCEL`."*

RHAMP-REQ-156's sequencing table places *"explicit Approve/Reject (§34)"* in
`.1R.32` (== `.1R.30R.4R.1`). That phase implemented the protocol, the
deterministic neutralized rendering, the display/digest-equivalence check, and
the election *binding*, but deferred the actual human keystroke input;
`.1R.30R.4R.2` IV recorded *"no interactive surface → fail-closed `CANCEL`"* as
verified behaviour rather than flagging the gap. From this phase's chair, a
genuine *"explicit Approve election"* by a real human (RHAMP-REQ-152 bullet 4)
therefore cannot be performed, and **N-16-5 cannot close.**

**Disposition — adjudicated, not repaired.** Implementing the interactive local
election surface is a `src/pcae` production change, outside this
verification-only phase's authorized scope (STRICT AUTHORIZED SCOPE). The
successor repair phase must add the interactive surface (a trusted local TTY
election read, fail-closed, no implicit/timeout approval — RHAMP-REQ-097/100),
then perform the presentation-bound leg of the RHAMP-REQ-152 ceremony.

### The rest of the chain composes (software, downstream-only)

To scope H-2 precisely, the full `require_real_assurance = True` path was
exercised end-to-end with an in-process shim standing in for **only** the
launcher's `posix_spawn` boundary (not the CTAP2 authenticator): a real
`hpac.fido2.uv_presence.v2` proof (`DeterministicCtap2Provider` in the software
probe) + a `PRODUCTION` `pcae-protected-local-presentation/1.0` presentation
evidence record → `verify_human_authentication(require_real_assurance=True)` →
a `PRODUCTION` `AuthenticatedHumanPrincipal` with `is_real_runtime_eligible`
True, resolving through the frozen
`principal.assurance_class is HPACAuthorityClass.PRODUCTION` Gate 5 check.
HPAC-PPA-REQ-057's joint requirement (real auth mechanism **and** real
presentation mechanism id) held. **H-2 is exactly the missing interactive
input — nothing downstream is broken.** This probe is not a substitute for the
real helper and is recorded as an IV observation, not a certification.

## 5. Finding F-2 (NON-BLOCKING, environmental) — `/dev/fd/N` helper launch inoperative on this interpreter

`src/pcae/core/protected_presentation.py`, `_launch_and_exchange`:
`os.posix_spawn(sys.executable, [sys.executable, "-I", "/dev/fd/N"], ...)` does
not execute the helper script on this machine's interpreter (Python 3.9.6 /
macOS): the child exits 0 having run nothing. Every protected-presentation
ceremony consequently fails closed with `ceremony_cancelled`. Reproduced at the
`.1R.30R.4R.2` finalized head `0b973e2e` with this phase's changes removed —
**pre-existing, zero attributable regression** (the `.1R.30R.4R.1` /
`.1R.30R.4R.2` suites were finalized on an environment where `/proc/self/fd/N`
or `/dev/fd/N` script execution works). ~20 `.1R.30R.4R.1` / `.1R.30R.4R.2`
ceremony tests fail in this environment for this reason. Test-only /
environmental; folded into the H-2 successor together with the carried guard
debt.

---

## 6. Findings carried forward (not repaired in this BLOCKED phase)

Following the `.1R.30R.5` precedent, this BLOCKED phase changes **no code and
no test guard**; it carries the full point-in-time guard set forward to the
successor that also repairs H-2:

- **F-1** (`.1R.30R.4R.2`) — `..._1r19r.py::
  test_lifecycle_module_diff_since_r20_head_is_only_the_n20_4_remap` matches two
  descriptive disclaimer lines in `protected_presentation.py`.
- **Three sibling stale guards** —
  `..._1r19r.py::test_no_contract_change_since_r20_head`;
  `..._1r_30r_1_...::test_no_contract_change_since_b30`;
  `..._1r_30r_1_...::test_phase_id_discrepancy_present_and_resolution_recorded`.
- **`.1R.19R` / `.1R.19R.1` and `.1R.30R.1` point-in-time guards** transitively
  implicated by the `.1R.30R.5R` one-file `src/pcae` change.
- **The moving completion-metadata guard** (`.1R.30R.1`
  `"1R.30R.2" in <live .pcae/phase-completion-metadata.json>`).

Independently reproduced as failing on `A` (`9f004ea9`) with zero changes
applied — **pre-existing**. Per the governing prompt's BLOCKED discipline
(*"do not repair; do not weaken requirements"*) and the `.1R.30R.5` precedent
(BLOCKED phase kept code-free for clean attribution), the full phase-aware,
widened-not-weakened reconciliation is folded into the successor phase.

---

## 7. N-16-5 complete-requirement table

| # | Requirement / prerequisite | Phase(s) | Current status | Blocking? |
|---|---|---|---|---|
| 1 | N-16-3 closure | `.1R.22` / `.1R.22R` / `.1R.22R.1` | CLOSED, unchanged | no |
| 2 | N-16-4 closure | `.1R.26` / `.1R.26R…` | CLOSED, unchanged | no |
| 3 | PAWA production protected-admin writer anchor | `.30R.3.1` | IMPLEMENTED | no |
| 4 | PAWA writer-anchor independent verification | `.30R.3.2` | VERIFIED | no |
| 5 | RHAMP-001 v1.0 contract freeze | `.1R.29` | frozen, byte-unchanged | no |
| 6 | HPAC-PAWA-001 v1.2 / HPAC-PPA-001 v1.0 reconciliation | `.30R.4R` | frozen, byte-unchanged | no |
| 7 | Real RHAMP credential registration path (software) | `.30R.3.4` | IMPLEMENTED + IV'd | no |
| 8 | Real FIDO2 software authentication mechanism | `.30R.3.4` | IMPLEMENTED + IV'd | no |
| 9 | Merged RHAMP mechanism independent verification | `.30R.3.5` / `.3.6` / `.3.6.1` | VERIFIED | no |
| 10 | Protected human-approval presentation implementation | `.30R.4R.1` | IMPLEMENTED **except the interactive election surface** | **see H-2** |
| 11 | Protected presentation independent verification | `.30R.4R.2` | VERIFIED (software); F-1 non-blocking | no |
| 12 | Real-assurance consumption (Gate 5 / Gate 9) | `.30R.4R.1` / `.2` | VERIFIED (software) + **composition proven end-to-end this phase** | no |
| 13 | ≥ 55-case automated negative matrix green | `.1R.28` §36 / `.30R.3.4` | green | no |
| 14a | CTAP2 PIN/UV interoperability repair (H-1) | `.30R.5R` | IMPLEMENTED + **independently verified this phase** | no |
| 14b | **≥ 1 real-CTAP2 hardware `makeCredential` + `getAssertion` (UP+UV, rpIdHash, COSE, counter, negatives)** | **`.30R.5R.1` (this phase)** | **REAL-HARDWARE VERIFIED** | no |
| 14c | **presentation-bound `PRODUCTION` `AuthenticatedHumanPrincipal` end-to-end → Gate 5, real explicit Approve election** | **`.30R.5R.1` (this phase)** | **NOT PERFORMABLE — finding H-2** | **YES** |
| 15 | No unresolved BLOCKED descendants | — | historical BLOCKEDs repaired + IV'd | no |
| 16 | No unresolved blocking finding | — | **H-2 open** | **YES** |

**Rows 14c and 16 are false → N-16-5 CANNOT CLOSE.**

Row 14a's CTAP2 automated portion and row 14b's real-hardware CTAP2 portion —
false at the end of `.1R.30R.5` — are now **true**.

---

## 8. N-16-5 closure adjudication

The frozen closure test (governing prompt §59): items 4–13, 20–22 are
satisfied; items **17–19** (protected presentation VERIFIED end-to-end + real
hardware coupled to the protected presentation + Gate 5 consumption verified
*with a real approval*) and **24** (no current blocking finding) are **not**.

> **N-16-5: NOT CLOSED.**

Closure is not forced. Every software prerequisite and the entire CTAP2
hardware ceremony are complete and independently verified; the sole remaining
gate is the presentation-bound approval leg, blocked on finding H-2.

---

## 9. Boundary preservation (re-verified at HEAD)

- **Runtime:** `pcae runtime inspect` → `not_implemented` / `Observed` /
  `observe` / `unavailable`; 0 plugins / 0 capabilities;
  `execution_unavailable`; `non-executing`. Unchanged.
- **First external effect:** **ABSENT / UNREACHABLE.** No `adapter.dispatch(`,
  no `DispatchEnvelope`, no effect adapter, no `os.fork` / `subprocess` /
  network. Local CTAP2 security-key I/O and the local protected-presentation
  helper `posix_spawn` are N-16-5 trust mechanisms, not the governed runtime
  first external effect (Slice C).
- **No `src/pcae`, `scripts/`, `pyproject.toml`, or `docs/contracts` change**
  in this phase.
- **Gate 5 / Gate 9 source byte-unchanged** since `.1R.30R.4R` (`a727dbf4`);
  they consume real assurance only via the existing frozen
  `assurance_class is HPACAuthorityClass.PRODUCTION` check.
- **PB / policy independence:** a `PRODUCTION` `AuthenticatedHumanPrincipal`
  carries no PB `ALLOW`, policy override, runtime capability,
  `DispatchEnvelope`, or execution authority. Valid REAL assurance + PB DENY →
  DENY; valid REAL assurance + policy DENY → DENY.
- **N-16-3 / N-16-4:** CLOSED (unchanged). **N-16-6 / N-16-7:** OPEN /
  UNTOUCHED (N-16-7 strictly last). **N-23-1** INFO / **N-23-2** INFO-DEFERRED
  carried unchanged.
- Historical BLOCKED phases (`.1R.30`, `.30R.3.3`, `.30R.3.5`, `.30R.4`,
  `.30R.5`) remain immutable historical records; a successful `.1R.30R.5R.1`
  does not rewrite history.

---

## 10. Authentication-architecture distinction (preserved)

Certification of the CTAP2 PIN/UV mechanism establishes:

> `hpac.fido2.uv_presence.v2` = **one VERIFIED SUPPORTED REAL
> HUMAN-AUTHENTICATION PROFILE** (CTAP2 leg real-hardware verified this phase).

It does **not** establish FIDO2 as globally mandatory PCAE authentication, a
physical security key as mandatory for ordinary PCAE development, desktop-local
key/PIN as a permanent UX requirement, mobile-only PCAE interaction as
unsupported, or all future protected approval as tied to FIDO2. This phase adds
no architecture, contract, status rule, source guard, or product assumption
that permanently requires a Mac-attached key, USB-only auth, desktop-local PIN,
desktop-only protected presentation, possession of a roaming key for ordinary
development, or `hpac.fido2.uv_presence.v2` as the sole real mechanism.

**FIDO2 availability is not a prerequisite for unrelated PCAE development** —
repository inspection, architecture / planning / documentation phases,
deterministic testing, non-effecting governed development, and ordinary
Observed-mode workflows do not require physical FIDO2 hardware. Only operations
whose currently frozen trust contract specifically requires real human
authentication / protected approval depend on the certified profile.

**Carried forward (INFO / PLANNED, not a current blocker):**
*Mechanism-Neutral Human Authentication Profiles / Mobile-Only Authentication
and Protected Approval Architecture* — to evaluate, under separate architecture
/ contract / implementation / IV work: mobile platform authenticator; device
biometrics (Face ID / fingerprint) through a governed platform trust boundary;
device credential / platform authenticator; NFC roaming key mediated by a
mobile platform; an assurance-level abstraction independent of mechanism;
mobile protected presentation; mechanism selection / policy; compatibility with
the existing `hpac.fido2.uv_presence.v2`. **MUST NOT** be treated as required
before N-16-6 unless canonical project priorities later place it there, and
**MUST NOT** block current development.

---

## 11. Product / certification verdicts

| Property | Verdict |
|---|---|
| CTAP2 PIN/UV repair — independent verification | **VERIFIED** |
| GetInfo capability negotiation | **VERIFIED** |
| PIN/UV protocol selection (V2 preferred, V1 valid-only, no-compat fail-closed) | **VERIFIED** |
| Trusted, non-logging, non-persisted PIN handling | **VERIFIED** |
| Permission-scoped, rp-bound PIN/UV token | **VERIFIED** |
| Command-scoped `pinUvAuthParam` (both ceremonies) | **VERIFIED** |
| No bare-`uv` production path; no UV downgrade; incompatible authenticator rejected | **VERIFIED** |
| Deterministic-provider / virtual-authenticator realism | **VERIFIED** |
| Production-provider ↔ test-provider authority separation | **VERIFIED** |
| **Real `makeCredential`** (genuine hardware, canonical records) | **VERIFIED** |
| **Real credential registration** (registry + sidecar + counter-state) | **VERIFIED** |
| **Real `getAssertion`** (genuine hardware, ×2) | **VERIFIED** |
| **Real UP** | **VERIFIED** |
| **Real UV** | **VERIFIED** |
| **Real rpIdHash** | **VERIFIED** |
| **Real COSE signature** | **VERIFIED** |
| **Real counter / currentness** (`6 → 8`, meaningful, monotonic) | **VERIFIED** |
| Wrong-challenge / replay / revoked-credential rejection | **VERIFIED** |
| Deterministic provider excluded from the ceremony | **VERIFIED** |
| Protected-presentation coupling (real explicit Approve election) | **NOT VERIFIED — finding H-2** |
| Gate 5 end-to-end with a real approval | **NOT VERIFIED — finding H-2** |
| Gate 5 consumption chain composes to `PRODUCTION` assurance (software, this phase) | **VERIFIED** |
| Guard reconciliation | **DEFERRED to the H-2 successor** (BLOCKED phase kept code-free) |
| Mobile / future-mechanism flexibility | **PRESERVED** |
| Runtime `Observed` / `observe` / `unavailable`; first effect ABSENT | **VERIFIED** |
| **H-1** | **REPAIRED — REAL-CTAP2-HARDWARE VERIFIED** |
| **N-16-5** | **NOT CLOSED** (finding H-2) |

---

## 12. Recommended next phase (recommended, NOT reserved; own explicit human authorization + own protected human approval required — do not begin)

**`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2` — N-16-5 Protected-Presentation
Interactive Election Surface Repair, Presentation-Bound Real-Hardware Ceremony,
Stale-Guard Reconciliation, and N-16-5 Closure.** Scope: repair finding **H-2**
in `src/pcae/protected_presentation_helper.py` — add the trusted local
interactive human-election surface (explicit Approve / Reject read from a
trusted local TTY; fail-closed; no implicit / timeout / touch-alone approval —
RHAMP-REQ-097/100); address finding **F-2** so `_launch_and_exchange` runs the
helper portably; then perform the presentation-bound leg of the RHAMP-REQ-152
ceremony against a genuine attached key (real helper render → real explicit
Approve election → real `getAssertion` → proof → Gate 5 → one `PRODUCTION`
`AuthenticatedHumanPrincipal`; PB DENY / policy DENY still DENY); fold the full
phase-aware reconciliation of the F-1 + three-sibling + `.1R.19R` / `.1R.19R.1`
/ `.1R.30R.1` + moving-completion-metadata point-in-time guard set (test-only,
widened-not-weakened, no `def test_` renamed / removed); and — only if every
frozen N-16-5 requirement is then complete and no blocking finding remains —
close N-16-5. Then N-16-6, then N-16-7 (strictly last). The exact CPIPC-valid
successor ID/title is to be confirmed from canonical project state by the phase
that drafts it. **Do not begin N-16-6, N-16-7, Slice C, a first external
effect, or execution enablement.**

---

## Governance

- **`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED`** — preserved.
  This applies to delegated workers / subagents. The primary human-authorized
  operator session performed the governed lifecycle for `.1R.30R.5R.1` under
  the explicit authorization in the phase prompt.
- Governed PCAE lifecycle only — no raw `git commit` / `git push`,
  `--no-verify`, force push, history rewrite, or hook bypass.
- Historical `.1R.30`, `.1R.30R.3.3`, `.1R.30R.3.5`, `.1R.30R.4`, `.1R.30R.5`
  remain immutable BLOCKED records, not rewritten.
- Real hardware interaction was operator input, not new phase authorization.
  No PIN, PIN/UV token, or private key was logged, stored, or transmitted.

*Canonical artifact — Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.1.*
