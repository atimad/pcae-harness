# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.1 Complete — Independent Verification of the CTAP2 PIN/UV Repair + Mandatory Real-CTAP2-Hardware Verification + N-16-5 Closure

- **Status:** **BLOCKED. N-16-5: NOT CLOSED.** **H-1: INDEPENDENTLY VERIFIED — REAL-CTAP2-HARDWARE VERIFIED.** **New blocking finding H-2: the protected-presentation helper has no interactive human-election surface.**
- **Type:** Governed independent-verification + certification phase (== RHAMP `.1R.33`). Verification/certification only — no production or normative-contract change; no defect repaired inside this phase.
- **Anchors** (re-derived from primary source): `A` = `9f004ea9` (finalized `.1R.30R.5` BLOCKED head, attribution baseline); `R` = `ea40c47e` (finalized `.1R.30R.5R` repair head); `V` = `ea40c47e` (`.1R.30R.5R.1` phase-entry SHA; `V == R`; `origin/main..HEAD = 0` at entry).
- **Contracts changed:** none (`git diff --name-only 9f004ea9 HEAD -- docs/contracts` empty). **`pyproject.toml`:** byte-unchanged. **`src/pcae` / `scripts`:** byte-unchanged this phase.

## 1. Independent verification of the `.1R.30R.5R` repair (finding H-1)

Re-derived from primary source: production diff `A..R` = **exactly one file**
(`src/pcae/core/hpac_rhamp_ctap2.py`); all normative contracts
(RHAMP-001 v1.0, HPAC-PPA-001 v1.0, HPAC-PAWA-001 v1.2, HPAC-001 v2.1,
RIHAC-001 v2.0, RIASC-001 v3.0, HPAC-AUTHORITY-CONSUMPTION/2.1, CPIPC-001 v1.0)
byte-unchanged since `A`; `terminal_reason_code` enum stays at 41; every
referenced `fido2 1.2.0` `CtapError.ERR` / `ClientPin` / `Ctap2` symbol is
valid; `ClientPin.PROTOCOLS == [V2, V1]` so V2 is preferred, V1 is the
valid-only fallback, no mutually supported protocol fails closed
(`ValueError → Ctap2UnavailableError`); the `pinUvAuthToken` is
permission-scoped (`MAKE_CREDENTIAL` / `GET_ASSERTION` per ceremony) and
rp-bound (`_PIN_UV_TOKEN_RP_ID == RP_ID`, never caller-selectable); the
`pinUvAuthParam` is command-scoped (`protocol.authenticate(token,
client_data_hash)`); the PIN is acquired only through a trusted, tty-guarded,
non-logging `getpass` prompt that fails closed when non-interactive and is
dropped with `del pin` / `del token`, never stored on the provider;
`make_credential` sends `options={"rk": False}` (no bare `uv`), `get_assertion`
sends no `options`, neither retries the historical shape, and a `FLAG.UV`-clear
`makeCredential` is rejected (no UP-only downgrade); the new
`_VirtualCtap2Authenticator` is structurally NON_REAL and rejects the exact
`0x2C` / `0x36` / `0x33` shapes; `resolve_production_ctap2_provider()` is
seam-free and env-var-free. **`.1R.30R.5R` repair suite re-run 48/0.**

## 2. Mandatory real-CTAP2-hardware verification (RHAMP-REQ-152) — CTAP2 leg CERTIFIED

Executed once, locally, by the primary operator against a genuine attached
FIDO_2_1 roaming USB security key (`authenticatorGetInfo`: `FIDO_2_1` present;
`aaguid b7d3f68e88a6471e9ecf2df26d041ede`; `clientPin` set; `pinUvAuthToken`
true; `options.uv` absent → PIN path; `pin_uv_protocols [2,1]`; `transports
[nfc, usb]`) through the real `resolve_production_ctap2_provider()` →
`NativeCtap2Provider` (no seam; `DeterministicCtap2Provider` never constructed
on the ceremony path — proven by the persisted sidecar `aaguid` matching live
GetInfo, not the fixture `0x11`×16, and the observed counter `6` then `8`, not
the fixture `0 → 1`):

| RHAMP-REQ-152 requirement | Result |
|---|---|
| roaming USB CTAP2 key used | ✅ AAGUID `b7d3f68e…`, USB-HID, FIDO_2_1 |
| real `makeCredential` → canonical `CredentialRecord` + sidecar + counter-state | ✅ `status=active`, `hpac.fido2.uv_presence.v2`, `{UP, UV}`; sidecar pubkey == registry; `RHAMP-COUNTER-STATE/1.0` initialised; one ACTIVE credential resolves |
| real `getAssertion` → full §37 verifier sequence, `FLAG.UP` + `FLAG.UV` | ✅ two ceremonies; `verify_real_fido2_assertion` accepted both; `up and uv` on both |
| real rpIdHash | ✅ `== SHA-256("hpac.pcae.local")` |
| real COSE signature | ✅ ES256 verified vs canonical stored key |
| real native client context | ✅ `RHAMP-CLIENT-CONTEXT/1.0` reconstructed from trusted state; no browser origin |
| real counter / currentness | ✅ `6 → 8` meaningful, monotonic (RHAMP §20) |
| real UP + real UV | ✅ genuine physical touch + trusted local PIN on every ceremony |
| wrong-challenge rejected | ✅ `client_data_hash_mismatch` (also wrong `invocation_id`) |
| replayed challenge/proof rejected | ✅ `signature_counter_regression` |
| missing / failed UV rejected (§39) | ✅ deterministic no-UV enrollment → `enrollment_ceremony_evidence_invalid` |
| revoked credential rejected | ✅ canonical `revoke_credential` → empty allowlist, verifier `_resolve_credential` raises |
| **presentation-bound approval → Gate 5 → `PRODUCTION` `AuthenticatedHumanPrincipal`, real explicit Approve election** | ❌ **NOT PERFORMABLE — finding H-2** |

No PIN, PIN/UV token, or private key was logged, stored, or transmitted; the
certification credential was canonically revoked at the end; no
attestation / device-identity / MDS claim. Non-secret evidence:
`.pcae/certification/rhamp_hardware_cert_30r5r1.json`.
**H-1: REPAIRED — REAL-CTAP2-HARDWARE VERIFIED.**

## 3. Finding H-2 (BLOCKING) — no interactive human-election surface

`src/pcae/protected_presentation_helper.py::_observe_election` has **no
interactive human-election surface** (no `input()` / `stdin.read` / `readline`
/ `/dev/tty` / `termios` / `tty.` primitive) — it returns `CANCEL` for every
production ceremony unless the disclosed `_test_decision_source` test seam is
supplied. The helper docstring: *"A real interactive local surface is successor
work (the mandatory real-CTAP2-hardware verification phase)"* — this one.
RHAMP-REQ-156 placed *"explicit Approve/Reject (§34)"* in `.1R.32` (==
`.1R.30R.4R.1`), which implemented the protocol / rendering / digest-equivalence
/ election-binding but deferred the interactive input; `.1R.30R.4R.2` IV
recorded *"no interactive surface → fail-closed CANCEL"* as verified behaviour.
RHAMP-REQ-152 bullet 4 (a real explicit Approve election → assertion → proof →
Gate 5 → one `PRODUCTION` `AuthenticatedHumanPrincipal`) is therefore **not
performable**. Adding the surface is a `src/pcae` production change outside this
verification-only phase's authorized scope → **adjudicated, not repaired** (the
`.1R.30R.5` / H-1 precedent). This BLOCKS the phase per the frozen VALID
BLOCKED CONDITIONS (*"protected presentation coupling fails where required"*;
*"N-16-5 requirements remain incomplete"*).

**The rest of the chain composes end-to-end in software** — fresh IV suite
`test_25` mints a `PRODUCTION` `AuthenticatedHumanPrincipal` through
`verify_human_authentication(require_real_assurance=True)` with a real FIDO2
proof + a `PRODUCTION` `pcae-protected-local-presentation/1.0` presentation
evidence record, satisfying HPAC-PPA-REQ-057 and the frozen Gate 5
`assurance_class is HPACAuthorityClass.PRODUCTION` check (an in-process shim
stands in for **only** the launcher's `posix_spawn` boundary, not the CTAP2
authenticator or the human election). H-2 is precisely the missing keystroke.

## 4. Finding F-2 (NON-BLOCKING, environmental)

`_launch_and_exchange`'s `os.posix_spawn(python, [python, "-I", "/dev/fd/N"])`
does not execute the helper on this machine's interpreter (Python 3.9.6 /
macOS) — the child exits 0 having run nothing. ~20 pre-existing
`.1R.30R.4R.1` / `.1R.30R.4R.2` ceremony tests fail for this reason.
**Reproduced identically at the phase-entry SHA `V` (`ea40c47e`) — zero
failures attributable to `.1R.30R.5R.1`** (`comm -23` of the HEAD failure set
against the `V` failure set is empty). Folded into the H-2 successor.

## 5. N-16-5 requirement table + closure adjudication

Rows 1–13, **14a** (CTAP2 PIN/UV repair independently verified) and **14b**
(≥ 1 real-CTAP2 hardware `makeCredential` + `getAssertion` with UP + UV +
rpIdHash + COSE + counter + negatives) **✅ VERIFIED**; **row 14c**
(presentation-bound `PRODUCTION` principal via a real explicit Approve election
→ Gate 5) **❌ finding H-2**; **row 16** (no unresolved blocking finding)
**❌ H-2 open**. Rows 14c + 16 false → **N-16-5 CANNOT CLOSE.** Closure not
forced.

## 6. Carried forward (NOT reconciled — BLOCKED phase kept code-free)

Per the `.1R.30R.5` precedent, this BLOCKED phase changed no `src/pcae` /
`scripts` / `pyproject.toml` / `docs/contracts` byte and reconciled no test
guard. The full phase-aware, widened-not-weakened reconciliation of **F-1**
(`.1R.30R.4R.2` `test_lifecycle_module_diff…` content scan) + the **three
sibling stale `.1R.19R` / `.1R.30R.1` guards** + the `.1R.19R` / `.1R.19R.1` /
`.1R.30R.1` point-in-time guards transitively implicated by the `.1R.30R.5R`
one-file change + the **moving completion-metadata guard** + the
`.1R.30R.4R.2 test_01` "every commit since `5b6b4013` is `.30R.4R.2`" guard
(already stale since `.1R.30R.5`) — all independently reproduced as failing on
`A` / `V` (pre-existing) — folds into the recommended H-2 successor.

## 7. Boundaries

Runtime `not_implemented` / `Observed` / `observe` / `unavailable`; 0 plugins /
0 capabilities; first external effect **ABSENT / UNREACHABLE** (CTAP2 device
I/O and the local presentation helper `posix_spawn` are N-16-5 trust
mechanisms, not the Slice C runtime first external effect). Gate 5 / Gate 9
byte-unchanged since `.1R.30R.4R` (`a727dbf4`). PB DENY / policy DENY still
DENY. N-16-3 / N-16-4 CLOSED; N-16-6 / N-16-7 OPEN / UNTOUCHED (N-16-7 strictly
last); N-23-1 INFO / N-23-2 INFO-DEFERRED carried unchanged. Historical
`.1R.30`, `.1R.30R.3.3`, `.1R.30R.3.5`, `.1R.30R.4`, `.1R.30R.5` remain
immutable BLOCKED records.

`hpac.fido2.uv_presence.v2` = **one VERIFIED SUPPORTED REAL human-authentication
profile (CTAP2 leg real-hardware verified)** — NOT globally mandatory PCAE
authentication, NOT the exclusive mechanism, NOT a mandate for physical FIDO2
hardware in ordinary non-effecting development, NOT a foreclosure of a future
mobile-only path. The *Mechanism-Neutral / Mobile-Only Authentication and
Protected Approval Architecture* is carried INFO / PLANNED — not a current
blocker, MUST NOT block current development.

## 8. Tests

**Fresh `.1R.30R.5R.1` IV suite:**
`tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_1_ctap2_pin_uv_repair_iv.py`
— **32 functions / 48 cases, 0 failed.** Hardware-free and deterministic
(RHAMP-REQ-154). **`.1R.30R.5R` repair suite re-run 48/0. Core non-regression
sweep 231/0** (repair / merged mechanism / merged IV / verifier / `.1R.30R.5`
closure). No pre-existing test file created, modified, removed, renamed,
skipped, skipif'd, or xfailed.

## 9. Recommended next phase

`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2` — repair **H-2** (add the trusted local
interactive human-election surface to the presentation helper — explicit
Approve / Reject from a trusted local TTY, fail-closed, no implicit/timeout
approval, RHAMP-REQ-097/100) and **F-2** (portable helper launch); perform the
presentation-bound leg of the RHAMP-REQ-152 ceremony against a genuine key;
fold the F-1 + sibling + `.1R.19R` / `.1R.19R.1` / `.1R.30R.1` +
moving-metadata + `.30R.4R.2 test_01` point-in-time guard reconciliation
(test-only, widened-not-weakened); and — only if every frozen N-16-5
requirement is then complete and no blocking finding remains — close N-16-5.
Then N-16-6, then N-16-7 (strictly last). Own explicit human authorization +
own protected human approval required; ID recommended, NOT reserved. Do not
begin N-16-6, N-16-7, Slice C, a first external effect, or execution
enablement. `DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` preserved.
