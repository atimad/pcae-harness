# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5 — Mandatory Real-CTAP2-Hardware Verification and N-16-5 Closure

**Phase ID:** 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5
**Type:** governed certification / verification phase (== RHAMP `.1R.33`) — verification only; no production or normative-contract change
**Status:** **BLOCKED.** N-16-5: **NOT CLOSED.**
**A (phase-entry SHA — finalized `.1R.30R.4R.2` head):** `0b973e2e1a433dd8983a17fc320f2bee55c430b8`
(re-derived via `git rev-parse HEAD` + `git rev-list --count origin/main..HEAD` = 0 at entry)

---

## 1. Verdict

The mandatory real-CTAP2 hardware ceremony required by **RHAMP-REQ-152** and
**RHAMP-INV-018** before N-16-5 can close **cannot be completed with the
current production code**. A genuine CTAP2 roaming USB security key was
attached and used through the production native provider path
(`resolve_production_ctap2_provider()` → `NativeCtap2Provider`); the device
enumerated, the transport was healthy, and the deterministic NON_REAL fixture
was never involved. **Both** required ceremonies were rejected by the
authenticator:

| Ceremony | Production call | Device response |
|---|---|---|
| `authenticatorMakeCredential` | `NativeCtap2Provider.make_credential(...)` → `ctap2.make_credential(..., options={"rk": False, "uv": True})` | `CTAP error 0x2C — CTAP2_ERR_INVALID_OPTION` |
| `authenticatorGetAssertion` | `NativeCtap2Provider.get_assertion(...)` → `ctap2.get_assertion(..., options={"uv": True})` | `CTAP error 0x2C — CTAP2_ERR_INVALID_OPTION` |

**Root cause (BLOCKING finding H-1).** `NativeCtap2Provider`
(`src/pcae/core/hpac_rhamp_ctap2.py`) requests user verification by passing a
bare `"uv": true` **option** to `authenticatorMakeCredential` and
`authenticatorGetAssertion`. In **CTAP 2.1** the `uv` option key was removed
from `authenticatorMakeCredential` entirely, and for `authenticatorGetAssertion`
a PIN/UV-protocol `pinUvAuthParam` (or a built-in-UV authenticator advertising
`options.uv`) is required — a bare `uv` option on a `clientPin`-based
authenticator is invalid. Every attached authenticator that advertises
`FIDO_2_1` therefore rejects the request as malformed **before any user
gesture**. The production provider has, as a consequence, **never successfully
communicated with real CTAP 2.1 hardware**; the entire automated suite is green
only because `DeterministicCtap2Provider` (`SIMULATION_ONLY = True`) honours the
bare `uv` option and returns `up=True, uv=True`. This is exactly the gap that
RHAMP-INV-018 exists to catch: *"N-16-5 closure requires both the ≥ 55-case
automated negative suite green and ≥ 1 real-CTAP2-hardware verification; neither
substitutes for the other."*

Repairing `NativeCtap2Provider` to run the CTAP 2.1 PIN/UV auth-protocol
handshake (acquire a `pinUvAuthToken` via `ClientPin` / `PinProtocolV2`, derive
`pinUvAuthParam`, thread it through both ceremonies, and prompt for the PIN via
a trusted non-logging flow) is a **non-trivial change to `src/pcae/core/`**.
The governing prompt (§55) scopes this phase to "verification / certification
plus narrow historical guard reconciliation" and directs: *"Any production
change: STOP and adjudicate whether a defect was found. Do not silently
repair."* The defect is real and adjudicated here; the repair belongs to a
dedicated successor phase. **N-16-5 remains NOT CLOSED.**

This matches the following frozen **VALID BLOCKED CONDITIONS** verbatim:
the production provider path cannot complete a spec-valid exchange with the
authenticator; real `makeCredential` cannot complete; real `getAssertion`
cannot complete; an unresolved blocking software defect appeared; N-16-5
requirements are incomplete after the hardware exercise.

No deterministic fixture was substituted, no hardware evidence was fabricated,
no hardware certification is claimed, and no production code was changed.

---

## 2. Hardware exercised (genuine, non-deterministic)

- **Provider selected:** `resolve_production_ctap2_provider()` →
  `NativeCtap2Provider` (`PROVIDER_KIND = "native-ctap2"`). The resolver
  accepts no environment variable or flag that could swap in
  `DeterministicCtap2Provider`; `DeterministicCtap2Provider.SIMULATION_ONLY` is
  the class constant `True` with no constructor override.
- **Authenticator observed:** USB-HID roaming security key, `vid=0x1050`
  (Yubico), `pid=0x0402` ("YubiKey FIDO"), `product_name="YubiKey FIDO"`,
  `aaguid=b7d3f68e88a6471e9ecf2df26d041ede`.
- **`authenticatorGetInfo`:** `versions = [U2F_V2, FIDO_2_0, FIDO_2_1_PRE,
  FIDO_2_1]`; `options` includes `clientPin: true` (a PIN is set),
  `pinUvAuthToken: true`, `alwaysUv: false`, `makeCredUvNotRqd: true`;
  `options.uv` **absent** (no on-device biometric UV); `pin_uv_protocols =
  [2, 1]`; `transports = [nfc, usb]`; `algorithms` include ES256 (`alg -7`).
- **Transport:** USB-HID (frozen-allowed). No browser WebAuthn, no platform
  authenticator, no network/proxy, no BLE/hybrid.
- **Profile compatibility:** the device *is* capable of satisfying the frozen
  RHAMP profile (CTAP2, roaming, USB-HID, non-discoverable credentials, ES256,
  `allowList`, UP, and UV via `clientPin`). The blocker is the production
  provider's CTAP-version-invalid UV request, **not** a device-capability gap.
- **Deterministic-provider contrast (recorded):**
  `DeterministicCtap2Provider().make_credential(...)` returns
  `up=True, uv=True, transport="usb"` for the identical bare-`uv`-option call
  that the real device rejects with `0x2C`. The fixture is structurally
  incapable of exposing H-1.

No credential was created on the device (both ceremonies failed at option
validation, before the user-presence / user-verification step). No PIN was
requested, entered, logged, or stored. No canonical RHAMP registry, sidecar,
or counter-state record was written. Attestation was never consulted; no
device-identity / manufacturer / MDS claim is made (RHAMP keeps attestation
non-authoritative).

---

## 3. Independent preservation of the already-verified software trust chain

Re-verified from primary source at `A` (no change introduced by this phase):

- **Contracts byte-unchanged since `A`:** `git diff --name-only A HEAD --
  docs/contracts` is empty. RHAMP-001 v1.0, HPAC-PPA-001 v1.0, HPAC-PAWA-001
  v1.2, HPAC-001 v2.1, RIHAC-001 v2.0, RIASC-001 v3.0, HPAC-AUTHORITY-
  CONSUMPTION/2.1, CPIPC-001 v1.0 all frozen.
- **Production source unchanged since `A`:** `git diff --name-only A HEAD --
  src/pcae scripts pyproject.toml` is empty.
- **Merged RHAMP real FIDO2 software mechanism** (`.30R.3.4` + `.30R.3.6` /
  `.3.6.1` repair, IV'd) — unchanged: `RHAMP-FIDO2-CREDENTIAL/1.0` sidecar,
  `RHAMP-COUNTER-STATE/1.0`, protected-admin bootstrap, `FIDO2HumanAuthenticator`,
  the pure RHAMP-REQ-102 assertion-verification core, `hpac_verifier`
  real-mechanism branch, exact `hpac.fido2.uv_presence.v2` eligibility, the
  deterministic NON_REAL seam.
- **Protected-presentation authority** (`.30R.4R.1`, IV'd by `.30R.4R.2`) —
  unchanged: pinned helper digest / current generation, installer ≠ launcher ≠
  evidence-writer, process-local non-bearer single-use evidence writer,
  create-only `HPAC-PRESENTATION-EVIDENCE/2.0`, explicit informed approval,
  REAL-auth + REAL-presentation coupling, `require_real_assurance`, Gate 5 /
  Gate 9 consumption via the frozen `assurance_class is PRODUCTION` check.
- **PB / policy independence:** valid REAL assurance + PB DENY → DENY; valid
  REAL assurance + policy DENY → DENY. Hardware certification would grant no
  override. Unchanged.
- **Runtime / effect independence:** `pcae runtime inspect` →
  `not_implemented` / `Observed` / `observe` / `unavailable`, 0 plugins,
  0 capabilities, `execution_unavailable`. No `adapter.dispatch(`, no
  `DispatchEnvelope`, no effect adapter. First external effect **ABSENT /
  UNREACHABLE**. Local CTAP2 security-key I/O is an authentication mechanism,
  not the governed runtime "first external effect" (Slice C).
- **N-16-3, N-16-4:** CLOSED (unchanged). **N-16-6, N-16-7:** OPEN /
  UNTOUCHED. **N-23-1** INFO / **N-23-2** INFO-DEFERRED carried unchanged.
- Historical BLOCKED phases (`.1R.30`, `.30R.3.3`, `.30R.3.5`, `.30R.4`)
  remain immutable historical records; their defects were subsequently
  repaired and independently verified and are **not** current blockers.

---

## 4. Findings carried forward (not repaired in this BLOCKED phase)

### H-1 (BLOCKING) — `NativeCtap2Provider` UV request is not CTAP 2.1-valid

`src/pcae/core/hpac_rhamp_ctap2.py`, `NativeCtap2Provider.make_credential`
(`options={"rk": False, "uv": True}`) and `.get_assertion`
(`options={"uv": True}`). Against any `FIDO_2_1` authenticator both calls fail
with `CTAP2_ERR_INVALID_OPTION (0x2C)`. The successor repair phase must add the
PIN/UV auth-protocol handshake (`ClientPin` / `PinProtocolV2` →
`pinUvAuthToken` → `pinUvAuthParam` on both ceremonies), a trusted
non-logging PIN-entry flow, and then re-run the full mandatory hardware
ceremony. Automated coverage must add a real-CTAP2.1 protocol fixture (or a
CTAP-version-aware negative case) so that "bare `uv` option accepted" can never
again pass only because the deterministic fixture is lenient.

### F-1 (NON-BLOCKING, carried from `.30R.4R.2`) — stale `.1R.19R` content-scan guard

`tests/test_dispatch_attempt_durable_lifecycle_reconciliation_3w1r2b1r1_1r19r.py::
test_lifecycle_module_diff_since_r20_head_is_only_the_n20_4_remap` — its
`assert not any("subprocess" in l or "socket" in l or ".dispatch(" in l for l
in added)` scans **every** added `src/pcae` diff line since `e05f0ea3` and now
matches two purely descriptive disclaimer lines in `.30R.4R.1`'s authorized
launcher module (`protected_presentation.py`): the docstring fragment
`"generic subprocess API (HPAC-PPA-REQ-031)"` and the comment
`"# subprocess API. posix_spawn avoids fork() in a possibly multi-threaded"`.
The launcher has zero functional `subprocess` / `socket` / `adapter.dispatch`
use. The narrow reconciliation (for the successor phase) is to restrict that
`added` scan to the one file `.1R.19R` actually repaired
(`runtime_dispatch_attempt_lifecycle.py`), matching the guard's own stated
intent, so genuine subprocess/effect detection for `.1R.19R`'s change is
preserved and later authorized modules (which carry their own dedicated guards
in the `.30R.4R.1` / `.30R.4R.2` suites) are not policed by it.

### Sibling stale guards specifically identified (carried forward)

Independently reproduced as failing on `A` (`0b973e2e`) with zero changes
applied — i.e. **pre-existing**, not attributable to this phase:

1. `..._1r19r.py::test_no_contract_change_since_r20_head` — its authorized set
   `{PB extension, PB policy applicability, PB narrow eligibility, REPRC-001}`
   does not yet include the contracts authorizedly added since `e05f0ea3`:
   `REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md`
   (`.1R.29`), `HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md` and
   `HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md` (`.30R.3.1` /
   `.30R.4R` / `.30R.4R.1`). Reconciliation: extend the authorized set by those
   exact filenames (no wildcard).
2. `tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_1_writer_anchor_adjudication_iv.py::
   test_no_contract_change_since_b30` — same class: the
   `changed <= {writer-anchor contract only}` bound predates the RHAMP / PPA
   contract additions. Reconciliation: extend by the exact additional
   filenames.
3. `..._1r_30r_1_...::test_phase_id_discrepancy_present_and_resolution_recorded`
   — asserts `"1R.30R.2" in <live .pcae/phase-completion-metadata.json>`; that
   file now legitimately reflects `.30R.4R.2`. Reconciliation: pin the check to
   the historical `.30R.1`-era metadata blob by SHA rather than the moving
   live file.

All four are test-only reconciliations deferred to the successor phase so this
BLOCKED phase changes no code and keeps regression attribution clean (the same
discipline `.30R.3.5` applied to its own uncorrected finding). They must be
reconciled **without** weakening: no `def test_` renamed/removed, no
`skip`/`skipif`/`xfail`/`fnmatch`/wildcard added, guards made *more* precise.

---

## 5. N-16-5 complete-requirement table

| # | Requirement / prerequisite | Phase(s) | Current evidence | Status | Blocking? |
|---|---|---|---|---|---|
| 1 | N-16-3 closure | `.1R.22` / `.1R.22R` / `.1R.22R.1` | CLOSED, unchanged | ✅ | no |
| 2 | N-16-4 closure | `.1R.26` / `.1R.26R…` | CLOSED, unchanged | ✅ | no |
| 3 | PAWA production protected-admin writer anchor | `.30R.3.1` | IMPLEMENTED | ✅ | no |
| 4 | PAWA writer-anchor independent verification | `.30R.3.2` | VERIFIED | ✅ | no |
| 5 | RHAMP-001 v1.0 contract freeze | `.1R.29` | frozen, byte-unchanged | ✅ | no |
| 6 | HPAC-PAWA-001 v1.2 / HPAC-PPA-001 v1.0 reconciliation | `.30R.4R` | frozen, byte-unchanged | ✅ | no |
| 7 | Real RHAMP credential registration path (software) | `.30R.3.4` | IMPLEMENTED | ✅ | no |
| 8 | Real FIDO2 software authentication mechanism | `.30R.3.4` | IMPLEMENTED | ✅ | no |
| 9 | Merged RHAMP mechanism independent verification | `.30R.3.5` / `.3.6` / `.3.6.1` | VERIFIED (after re-entry-guard repair) | ✅ | no |
| 10 | Protected human-approval presentation implementation | `.30R.4R.1` | IMPLEMENTED | ✅ | no |
| 11 | Protected presentation independent verification | `.30R.4R.2` | VERIFIED (software); 1 non-blocking finding F-1 | ✅ | no |
| 12 | Real-assurance consumption (Gate 5 / Gate 9) | `.30R.4R.1` / `.30R.4R.2` | VERIFIED (software) | ✅ | no |
| 13 | ≥ 55-case automated negative matrix green | `.1R.28` §36 / `.30R.3.4` | green | ✅ | no |
| 14 | **≥ 1 mandatory real-CTAP2 hardware verification** | **`.30R.5` (this phase)** | **attempted; production provider not CTAP 2.1-valid — finding H-1** | ❌ | **YES** |
| 15 | No unresolved BLOCKED descendants | — | historical BLOCKEDs repaired + IV'd | ✅ | no |
| 16 | No unresolved blocking security finding | — | **H-1 open** | ❌ | **YES** |

**Rows 14 and 16 are false → N-16-5 CANNOT CLOSE.**

---

## 6. N-16-5 closure adjudication

The frozen 15-point closure test (governing prompt §49): items 1 (genuine
CTAP2 hardware *used*), 4 (real UV verified), 6 (COSE signature verified),
7 (canonical credential/currentness state), 8 (counter semantics), 9
(production provider *proven to complete*), and 13 (F-1 / sibling guard debt
reconciled) are **not satisfied**. Item 2 (a real human gesture) never
occurred because the ceremonies failed at CTAP option validation upstream of
the presence/verification step.

> **N-16-5: NOT CLOSED.**

Closure is not forced. Software prerequisites (rows 1–13, 15) are complete and
independently verified; the sole remaining gate is the mandatory real-hardware
ceremony, which is blocked on finding H-1.

---

## 7. Fresh `.30R.5` suite

`tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5_hardware_cert_closure.py`
— **13 test functions / 15 cases, 0 failed.** Hardware-free and deterministic
(RHAMP-REQ-154: the automated suite never requires real hardware): pins the
phase-entry SHA `A`; proves `docs/contracts` and `src/pcae` byte-unchanged
since `A`; proves `resolve_production_ctap2_provider()` yields the real
`NativeCtap2Provider` and `DeterministicCtap2Provider.SIMULATION_ONLY` is a
permanent `True`; pins the exact source locus of finding **H-1** (the bare
`uv` option in both ceremonies, and the absence of any `ClientPin` /
`pinUvAuthParam` handshake); asserts the phase document records BLOCKED + the
`0x2C` finding + the carried-forward F-1 / sibling guards; asserts
`PROJECT_STATUS.md` names `.30R.5` as BLOCKED with N-16-5 NOT CLOSED; and
asserts the runtime posture, the "nothing changed in `src/pcae`" boundary, and
the doc/test/status-only change footprint. The real-hardware observations of
§2 are recorded in this document, not as CI assertions.

---

## 8. Scope discipline preserved

- No `src/pcae`, `scripts/`, `pyproject.toml`, or `docs/contracts` change.
- No deterministic fixture used for certification; no fabricated hardware
  evidence; no hardware-certification claim.
- No N-16-6 work (no fixed-argv effect adapter, no RPAC-REQ-095 implementation,
  no pre-authorization). No N-16-7 work. No Slice C. No first external effect.
  No execution enablement. No `Observed → Approved/Executable` transition.
- Runtime posture, Gate 5 / Gate 9 source, `runtime_authority`,
  `hpac_foundation`, `permission_broker`, and every RHAMP/FIDO2/PPA/PAWA
  module byte-unchanged since `A`.
- `DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` preserved for
  delegated workers/subagents; only the primary human-authorized operator
  session executed this governed lifecycle under this explicit authorization.

---

## 9. Recommended next phase (not begun; requires its own explicit human authorization)

**`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R`** — *N-16-5 Real-CTAP2 Provider CTAP 2.1
PIN/UV Auth-Protocol Repair, Mandatory Hardware Ceremony, Stale-Guard
Reconciliation, and N-16-5 Closure.* Scope: repair finding **H-1** in
`hpac_rhamp_ctap2.py` (add the `ClientPin` / `PinProtocolV2` → `pinUvAuthToken`
→ `pinUvAuthParam` handshake to both ceremonies + a trusted non-logging PIN
flow; add CTAP-version-aware automated coverage); then perform the full
mandatory RHAMP-REQ-152 real hardware ceremony (real `makeCredential`, real
human gesture, canonical registration, real `getAssertion`, rpIdHash / UP / UV
/ COSE / native-client-context / counter / currentness verification,
wrong-challenge + replay + revoked-credential rejection, presentation-bound
approval end-to-end → Gate 5); fold the **F-1** and the three sibling stale
`.1R.19R` / `.30R.1` guard reconciliations (test-only, widened-not-weakened);
and — only if every frozen N-16-5 requirement is then complete and no blocking
finding remains — close N-16-5. Then N-16-6, then N-16-7 (strictly last). The
exact CPIPC-valid successor ID/title is to be confirmed from canonical project
state by the phase that drafts it; it is **recommended, not reserved**, and it
must carry its own explicit human authorization and its own protected human
approval. **Do not begin N-16-6, N-16-7, Slice C, a first external effect, or
execution enablement.**

---

*Canonical artifact — Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5.*
