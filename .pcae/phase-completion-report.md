# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5 Complete — Mandatory Real-CTAP2-Hardware Verification and N-16-5 Closure

- **Status:** **BLOCKED.** N-16-5: **NOT CLOSED.**
- **Type:** Governed certification / verification phase (== RHAMP `.1R.33`). VERIFICATION / CERTIFICATION ONLY — no production source, script, `pyproject.toml`, or normative contract byte changed; no defect repaired inside this phase.
- **Phase-entry SHA `A`** (finalized `.1R.30R.4R.2` head): `0b973e2e1a433dd8983a17fc320f2bee55c430b8`; `origin/main..HEAD = 0` at entry.
- **Contracts changed:** none (`git diff --name-only A HEAD -- docs/contracts` empty). **`src/pcae` / `scripts` / `pyproject.toml` changed:** none.

## Why BLOCKED — finding H-1

A genuine CTAP2 roaming USB security key (Yubico `vid=0x1050 pid=0x0402`;
`authenticatorGetInfo` `versions=[U2F_V2, FIDO_2_0, FIDO_2_1_PRE, FIDO_2_1]`;
`clientPin` set; `pinUvAuthToken` true; `options.uv` **absent** — no on-device
biometric UV; `pin_uv_protocols=[2,1]`; `transports=[nfc,usb]`; ES256 in
`algorithms`) was attached and exercised through the **production native
provider path** — `resolve_production_ctap2_provider()` → `NativeCtap2Provider`
(`PROVIDER_KIND = "native-ctap2"`), the deterministic NON_REAL fixture
(`DeterministicCtap2Provider`, `SIMULATION_ONLY = True`) never involved. The
device enumerated and the USB-HID transport was healthy, but **both** mandatory
RHAMP-REQ-152 ceremonies were rejected by the authenticator with
`CTAP error 0x2C — CTAP2_ERR_INVALID_OPTION`, **upstream of any user gesture**:

| Ceremony | Production call | Device response |
|---|---|---|
| `authenticatorMakeCredential` | `NativeCtap2Provider.make_credential(...)` → `ctap2.make_credential(..., options={"rk": False, "uv": True})` | `0x2C — INVALID_OPTION` |
| `authenticatorGetAssertion` | `NativeCtap2Provider.get_assertion(...)` → `ctap2.get_assertion(..., options={"uv": True})` | `0x2C — INVALID_OPTION` |

**Finding H-1 (BLOCKING).** `NativeCtap2Provider`
(`src/pcae/core/hpac_rhamp_ctap2.py`) requests user verification with a bare
`"uv"` **option**. CTAP 2.1 removed the `uv` option from
`authenticatorMakeCredential` and requires a PIN/UV-protocol `pinUvAuthParam`
(or a built-in-UV authenticator advertising `options.uv`) for
`authenticatorGetAssertion`; every `FIDO_2_1` authenticator therefore rejects
the request as malformed. The production provider has consequently **never
successfully communicated with real CTAP 2.1 hardware** — the automated suite
is green only because `DeterministicCtap2Provider` honours the bare `uv` option
and returns `up=True, uv=True` (verified: the identical call on the fixture
succeeds). This is exactly the gap **RHAMP-INV-018** exists to catch: N-16-5
closure requires **both** the automated negative suite green **and** ≥ 1
real-CTAP2-hardware verification — neither substitutes for the other.

Repairing the provider (add the `ClientPin` / `PinProtocolV2` →
`pinUvAuthToken` → `pinUvAuthParam` handshake to both ceremonies + a trusted
non-logging PIN flow + CTAP-version-aware automated coverage) is a
`src/pcae/core/` change **outside this certification phase's scope** (governing
prompt §55: *"Any production change: STOP and adjudicate whether a defect was
found. Do not silently repair."*). The defect is adjudicated here; the repair
belongs to a dedicated successor phase.

No credential was created on the device. No PIN was requested, entered, logged,
or stored. No canonical RHAMP registry / sidecar / counter-state record was
written. No deterministic fixture was substituted for certification; no
hardware evidence was fabricated; **no hardware certification is claimed**; no
production code was changed. This BLOCKS the phase per multiple frozen VALID
BLOCKED CONDITIONS (the production provider path cannot complete a spec-valid
exchange with the authenticator; real `makeCredential` / `getAssertion` cannot
complete; an unresolved blocking software defect appeared; N-16-5 requirements
are incomplete after the hardware exercise).

## Software trust chain — independently preserved (re-verified at `A`)

`docs/contracts` and all of `src/pcae` byte-unchanged since `A`. The merged
RHAMP real FIDO2 software mechanism (`.30R.3.4` + `.3.6` / `.3.6.1`), the
protected human-approval presentation (`.30R.4R.1`, IV'd by `.30R.4R.2`),
real-assurance consumption through the frozen `assurance_class is PRODUCTION`
Gate 5 / Gate 9 check, and PB / policy / runtime independence all unchanged and
independently re-verified. N-16-3 / N-16-4 CLOSED. N-16-6 / N-16-7 OPEN /
UNTOUCHED. N-23-1 INFO / N-23-2 INFO-DEFERRED carried unchanged. Runtime
`not_implemented` / `Observed` / `observe` / `unavailable`, 0 plugins /
0 capabilities; first external effect ABSENT / UNREACHABLE. Historical BLOCKED
phases (`.1R.30`, `.30R.3.3`, `.30R.3.5`, `.30R.4`) remain immutable
repaired-and-verified records, not current blockers.

## N-16-5 complete-requirement table

Rows 1–13 and 15 (all software prerequisites, the ≥ 55-case negative matrix,
no unresolved BLOCKED descendants) **✅ VERIFIED**. **Row 14** (≥ 1 mandatory
real-CTAP2 hardware verification) **❌ — finding H-1**. **Row 16** (no
unresolved blocking finding) **❌ — H-1 open**. Rows 14 and 16 false →
**N-16-5 CANNOT CLOSE. NOT CLOSED.** Closure not forced. The frozen 15-point
closure test (governing prompt §49) items 1, 2, 4, 6, 7, 8, 9, 13 are not
satisfied.

## Findings carried forward (test-only, not repaired in this BLOCKED phase)

Same discipline `.30R.3.5` applied to its own uncorrected finding — keeping the
BLOCKED phase code-change-free:

- **F-1 (NON-BLOCKING, from `.30R.4R.2`)** —
  `.1R.19R::test_lifecycle_module_diff_since_r20_head_is_only_the_n20_4_remap`;
  its `assert not any("subprocess" in l or "socket" in l or ".dispatch(" in l
  for l in added)` scan matches two purely descriptive disclaimer lines in the
  authorized `.30R.4R.1` launcher module (`protected_presentation.py`).
  Narrow fix: restrict the `added` scan to the one file `.1R.19R` actually
  repaired (`runtime_dispatch_attempt_lifecycle.py`).
- **Three sibling stale guards — independently reproduced as FAILING on `A`
  (`0b973e2e`) with zero working-tree changes → pre-existing, not attributable
  to this phase:**
  `.1R.19R::test_no_contract_change_since_r20_head` and
  `.30R.1::test_no_contract_change_since_b30` (authorized-contract sets predate
  the `.1R.29` RHAMP + `.30R.3.1` / `.30R.4R.1` PPA/PAWA-anchor contract
  additions; fix: extend by the exact filenames, no wildcard); and
  `.30R.1::test_phase_id_discrepancy_present_and_resolution_recorded` (asserts
  `"1R.30R.2"` in the moving live `.pcae/phase-completion-metadata.json`; fix:
  pin to the historical `.30R.1`-era metadata blob by SHA).

All four deferred to the successor repair phase — widened-not-weakened, no
`def test_` renamed/removed, no `skip` / `skipif` / `xfail` / `fnmatch` /
wildcard added.

## Fresh `.30R.5` suite

`tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5_hardware_cert_closure.py`
— **13 test functions / 15 cases, 0 failed.** Hardware-free and deterministic
(RHAMP-REQ-154): pins `A`; proves `docs/contracts` and `src/pcae`
byte-unchanged since `A`; proves `resolve_production_ctap2_provider()` yields
the real `NativeCtap2Provider` and `DeterministicCtap2Provider.SIMULATION_ONLY`
is permanently `True`; pins the exact source locus of finding H-1; asserts the
phase doc records BLOCKED + the `0x2C` finding + the carried-forward
F-1 / sibling guards; asserts `PROJECT_STATUS.md` names `.30R.5` BLOCKED with
N-16-5 NOT CLOSED; and asserts the runtime posture, the "nothing changed in
`src/pcae`" boundary, and the doc/test/status-only change footprint. The
real-hardware observations are recorded in the canonical phase document, not as
CI assertions.

## Verdict

**BLOCKED — MANDATORY REAL-CTAP2 HARDWARE VERIFICATION COULD NOT COMPLETE
(finding H-1). N-16-5: NOT CLOSED.** No production source, script, or normative
contract changed. No deterministic fixture substituted. No hardware
certification claimed. Runtime `Observed` / `observe` / `unavailable`; first
external effect ABSENT; N-16-6 / N-16-7 OPEN / UNTOUCHED.

## Successor (not begun; own explicit human authorization + protected human approval required)

**`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R`** — repair finding H-1 in
`hpac_rhamp_ctap2.py` (CTAP 2.1 PIN/UV auth-protocol handshake + trusted PIN
flow + CTAP-version-aware automated coverage); perform the full mandatory
RHAMP-REQ-152 real hardware ceremony; fold the F-1 + three sibling stale
`.1R.19R` / `.30R.1` guard reconciliations; and — only if every frozen N-16-5
requirement is then complete and no blocking finding remains — close N-16-5.
Then N-16-6, then N-16-7 (strictly last). ID recommended NOT reserved. Do not
begin N-16-6, N-16-7, Slice C, a first external effect, or execution
enablement.

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` preserved — this
phase's governed lifecycle was performed only by the primary human-authorized
operator session.
