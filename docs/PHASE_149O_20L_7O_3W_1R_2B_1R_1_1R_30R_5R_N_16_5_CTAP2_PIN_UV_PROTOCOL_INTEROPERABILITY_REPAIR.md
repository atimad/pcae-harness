# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R — N-16-5 CTAP2 PIN/UV Protocol Interoperability Repair

**Phase ID:** 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R
**Type:** governed narrow production repair (finding H-1)
**Status:** COMPLETE. **H-1: REPAIRED — FRESH REAL-HARDWARE CERTIFICATION REQUIRED.**
**N-16-5: NOT CLOSED.**
**R0 (phase-entry SHA — finalized `.1R.30R.5` BLOCKED head):** `9f004ea9` (`origin/main..HEAD = 0` at entry).
**A (fixed-SHA attribution baseline):** `9f004ea9`.

---

## 1. Verdict

Finding **H-1**, raised by the mandatory real-hardware certification phase
`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5` (BLOCKED, immutable), is **repaired**.

The production native CTAP2 provider (`src/pcae/core/hpac_rhamp_ctap2.py`,
`NativeCtap2Provider`) previously requested user verification by passing a
bare `"uv": true` **option** to `authenticatorMakeCredential` and
`authenticatorGetAssertion`. CTAP 2.1 removed the `uv` option from
`authenticatorMakeCredential` and requires a PIN/UV-protocol `pinUvAuthParam`
for `authenticatorGetAssertion` on a `clientPin`-based roaming key; every
attached `FIDO_2_1` authenticator therefore rejected both ceremonies with
`CTAP2_ERR_INVALID_OPTION` (`0x2C`) before any user gesture. The production
provider had consequently never successfully communicated with real CTAP 2.1
hardware; the automated suite was green only because the deterministic
NON_REAL fixture (`DeterministicCtap2Provider`, `SIMULATION_ONLY = True`)
honoured the invalid shape — exactly the gap `RHAMP-INV-018` exists to catch.

`NativeCtap2Provider` now:

1. reads `authenticatorGetInfo` and negotiates the authenticator's supported
   PIN/UV protocol via the pinned `fido2` library's `ClientPin`
   (`PinProtocolV2` preferred, `PinProtocolV1` fallback where valid);
2. acquires a **permission-scoped** (`makeCredential` / `getAssertion` only),
   **rp-bound** (`hpac.pcae.local`) `pinUvAuthToken` — via built-in UV where
   the authenticator advertises it, otherwise via a **trusted, non-logging,
   non-persisted local PIN entry** (`getpass`; never a CLI argument,
   environment variable, repository / config value, or chat prompt; a
   non-interactive environment fails closed);
3. derives a **command-scoped** `pinUvAuthParam` over the canonical
   `client_data_hash` and threads `pin_uv_param` + `pin_uv_protocol` through
   both ceremonies;
4. sends **no bare `"uv"` option** and performs **no bare-`uv` fallback** on
   failure — it fails closed with an existing frozen `terminal_reason_code`;
5. rejects as incompatible any authenticator that cannot perform UV (no
   built-in UV and no configured PIN) and any `makeCredential` that returns
   with `FLAG.UV` clear — **no UP-only downgrade** (RHAMP-REQ-034/035).

The PIN is held only long enough to obtain the token, then dropped
(`del pin`); it is never stored on `NativeCtap2Provider`, never placed on an
exception message, and never written to any RHAMP artifact, completion
metadata, or phase report. `RHAMP-INV-006` / §18 / §54 are intact —
structurally, no RHAMP-001 artifact has a PIN field, and this repair adds
none.

**No normative contract byte changed.** RHAMP-001 v1.0, HPAC-PPA-001 v1.0,
HPAC-PAWA-001 v1.2, HPAC-001 v2.1 are byte-identical to `R0`. The client-side
`ClientPin` handshake is a pinned-library wire detail (like `CoseKey.verify`
in the same module), not a normative delta; RHAMP-REQ-035 already names "PIN"
as the UV factor and the recommended-next-phase text for `.1R.30R.5R`
explicitly scoped "the CTAP 2.1 ClientPin / PinProtocolV2 → pinUvAuthToken →
pinUvAuthParam handshake on both ceremonies + trusted non-logging PIN flow"
as in-scope for this repair.

## 2. Production change (narrow)

`git diff 9f004ea9 HEAD -- src/pcae scripts pyproject.toml` touches **exactly
one file**: `src/pcae/core/hpac_rhamp_ctap2.py`.

Added / changed inside that file:

- `_default_pin_prompt()` — `getpass`, tty-guarded, fail-closed, no logging.
- `_map_pin_uv_ctap_error()` — maps `ClientPin` / PIN-UV `CtapError` codes
  onto **existing** frozen terminal reasons (invalid/blocked PIN, PIN-auth
  invalid, UV invalid/blocked, PIN-not-set, timeout, cancel). **No new
  `terminal_reason_code`** — the enum stays at 41.
- `NativeCtap2Provider.__init__` — three keyword-only, underscore-prefixed,
  **test-only** seams (`_connection_factory`, `_client_pin_factory`,
  `_pin_prompt`), each defaulting to `None` / real hardware / `getpass`.
  `resolve_production_ctap2_provider()` is unchanged (`return
  NativeCtap2Provider()` — no seam, no env var, no flag).
- `NativeCtap2Provider._open_ctap2` / `_client_pin` / `_obtain_pin_uv` — the
  negotiation + token acquisition + command-scoped `pinUvAuthParam` derivation.
- `NativeCtap2Provider.make_credential` / `get_assertion` — pass
  `options={"rk": False}` (no bare `"uv"`) + `pin_uv_param` + `pin_uv_protocol`;
  `make_credential` additionally rejects a UV-clear response.
- `_DeterministicPinUvProtocol` / `_VirtualInfo` / `_VirtualClientPin` /
  `_VirtualCtap2Authenticator` / `_VirtualAttestation` / `_VirtualAssertion` /
  `build_virtual_ctap2_test_seam()` — a **structurally NON_REAL**
  (`SIMULATION_ONLY = True`, `PROVIDER_KIND_IS_REAL = False`) protocol-faithful
  in-memory model of a CTAP 2.1 roaming key. It rejects the exact shapes real
  FIDO_2_1 hardware rejects (bare `uv` → `0x2C`; missing `pinUvAuthParam` →
  `0x36`; wrong protocol → `0x02`; wrong `pinUvAuthParam` / permission / rp_id
  → `0x33`). It is reachable **only** through the test seams and can never be
  returned by `resolve_production_ctap2_provider()`.

`DeterministicCtap2Provider` is **byte-unchanged** (still the `Ctap2Provider`-
level NON_REAL fixture for the enrollment / authentication rig). §20/§21
design: the `Ctap2Provider` protocol boundary abstracts away the CTAP2 wire;
the bare-`uv` shape lives *below* it, so wire-shape enforcement belongs in the
new wire-level `_VirtualCtap2Authenticator`, which `NativeCtap2Provider`'s real
CTAP 2.1 code now drives in automated tests. Production and test provider
authorities remain distinct: `resolve_production_ctap2_provider()` accepts no
seam; the virtual model is a test-only construction.

## 3. Contract / boundary preservation (re-verified at HEAD)

- `git diff 9f004ea9 HEAD -- docs/contracts` is **empty**.
- `git diff 9f004ea9 HEAD -- pyproject.toml` is **empty** — no new dependency;
  `fido2` / `cryptography` were already declared (the `hatp-hardware` extra).
- RHAMP credential registration, `RHAMP-FIDO2-CREDENTIAL/1.0` sidecar,
  `RHAMP-COUNTER-STATE/1.0`, `FIDO2HumanAuthenticator`, the pure
  RHAMP-REQ-102 assertion-verification core, `hpac_verifier` REAL branch,
  protected presentation, Gate 5 / Gate 9, PAWA, PPA, policy / PB, and the
  runtime capability model are **byte-unchanged** (`git diff --stat` empty for
  each — see the repair suite's `test_46`).
- Runtime: `not_implemented` / `Observed` / `observe` / `unavailable`;
  0 plugins / 0 capabilities. First external effect **ABSENT / UNREACHABLE**.
  CTAP2 device I/O is N-16-5 authentication activity, not Slice C.
- N-16-3 / N-16-4 CLOSED. N-16-6 / N-16-7 OPEN / UNTOUCHED (N-16-7 strictly
  last). N-23-1 INFO / N-23-2 INFO-DEFERRED carried unchanged.

## 4. Fresh `.1R.30R.5R` repair suite

`tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_ctap2_pin_uv_repair.py`
— **48 tests, all passing**. Covers: historical `.30R.5` BLOCKED preservation;
H-1 source shape removed; no bare-`uv` path; GetInfo capability negotiation;
protocol V2 selection / V1 fallback / no-compatible-protocol rejection;
built-in-UV path takes no PIN prompt; trusted `getpass` PIN flow with
non-interactive fail-closed; no env / CLI / repo PIN; PIN not stored on the
provider; PIN absent from exception text; cancellation fails closed; empty PIN
rejected; permission-scoped + rp-bound tokens; command-scoped `pinUvAuthParam`
differs per `client_data_hash`; wrong permission / rp_id / protocol / auth
param rejected; makeCredential + getAssertion positive fixtures through the
full signature-material check; counter increments; wrong-challenge rejected;
UV-clear makeCredential rejected; PIN-blocked maps to an existing reason; 41
terminal reasons unchanged; virtual authenticator + virtual ClientPin
structurally NON_REAL; `DeterministicCtap2Provider` still NON_REAL; production
resolver distinct and seam-free; no new dependency; no normative contract
change; production diff confined to the one module; no first-effect primitive;
registration / counter / verifier / presentation / Gate 5-9 modules unchanged;
runtime boundary unchanged; N-16-6 / N-16-7 untouched.

Re-run software baselines (unchanged, all green with this change):
`.1R.30R.3.4` merged-mechanism suite (now 148 tests, `test_33` reconciled),
`.1R.30R.3.5` merged IV suite (0 failures).

## 5. Test reconciliations (widened, not weakened)

The point-in-time guards that this repair's one-file production change
directly trips are reconciled here (exact filenames, `.1R.30R.5R` comments,
no wildcard / fnmatch, no `def test_` renamed / removed / skipped / xfailed):

| Guard | Reconciliation |
|---|---|
| `.1R.30R.3.4::test_33_non_discoverable_and_uv_options_requested` | Was `assert '"rk": False' in text and '"uv": True' in text` — it encoded the H-1 bug. Now asserts the repaired reality: `rk=False` present, the bare-`uv` shape (`"rk": False, "uv": True`) **gone**, and `pin_uv_param` / `pin_uv_protocol` / `_obtain_pin_uv` threaded. Strictly stronger. |
| `.1R.30R.4R.2::test_70_iv_suite_touches_no_production_source_or_contract` | Open-ended `git diff 5b6b4013 --` (working-tree-inclusive). Upper bound pinned to the `.1R.30R.4R.2` finalized head `0b973e2e` — through that head the IV phase changed no `src/pcae` / `docs/contracts` / `scripts` file. |
| `.1R.30R.5::test_h1_locus_native_provider_requests_uv_as_a_bare_option` | Anchored the pre-repair invalid shape. Now anchors the **same locus** in its repaired state: bare-`uv` shapes **gone**, `ClientPin` / `pin_uv_param` / `pin_uv_protocol` / `_obtain_pin_uv` present. Same `def` name; widened, not weakened. |
| `.1R.30R.5::test_no_production_or_script_or_pyproject_change_since_A`, `::test_no_effect_adapter_or_dispatch_introduced_since_A`, `::test_this_phase_touched_only_doc_test_and_status_files` | Open-ended `git diff A(0b973e2e) HEAD` guards from the BLOCKED certification phase. Each keeps the byte-unchanged assertion through the `.1R.30R.5` finalized head `9f004ea9` (its own window) and adds a not-weakened check that `.1R.30R.5R` changes **exactly** `src/pcae/core/hpac_rhamp_ctap2.py`, with no `adapter.dispatch(` / `DispatchEnvelope` / `subprocess` / `os.fork` / `posix_spawn` primitive in the added lines. |

The historical `.1R.30R.5` **document** is byte-unchanged and immutable (§42);
only its forward-looking point-in-time *test* guards are reconciled, per the
established repo pattern (trap 11 / `.1R.26`).

## 6. Regression attribution (fixed-SHA A/B, A = `9f004ea9`)

**Repair-attributable functional regressions: 0.** The `Ctap2Provider`
protocol boundary is unchanged; `DeterministicCtap2Provider` and every
consuming module (enrollment, `human_authenticator_fido2`,
`hpac_rhamp_assertion_verify`, `hpac_verifier`, Gate 5 / Gate 9, protected
presentation) are byte-unchanged and green. A targeted A/B sweep of the ~2000
tests touching rhamp / hpac / ctap / fido2 / gate5 / gate9 / verifier /
presentation / authenticator / `.1R.19R` / `.1R.30R.1` / HMIC surfaces shows
**no new functional failure** with the change applied.

**Attributable-but-non-functional (point-in-time / working-tree guards):**
consistent with the established repo pattern (trap 11; `.1R.26` session), a
one-file `src/pcae` change trips several "nothing but X changed in `src/pcae`
since fixed baseline Y" and "working tree clean" guards from unrelated earlier
phases. Those observed here:

- 3 "working tree dirty / `git status` touches no `src/pcae`" guards
  (`149O.20h`, `149O.20k`, `149O.20k.1` HMIC) — clear once the change is
  committed.
- The `.1R.19R` / `.1R.19R.1` "since `R20_HEAD`" production / contract-scope
  and no-test-weakening guards, and the `.1R.30R.1` "since `B30`" guards
  (`test_no_contract_change_since_r20_head`,
  `test_lifecycle_module_diff_since_r20_head_is_only_the_n20_4_remap`,
  `test_no_contract_change_since_b30`,
  `test_phase_id_discrepancy_present_and_resolution_recorded`, and the four
  `.1R.19R.1` meta-guards) — **these were already failing at `R0`** (the
  pre-existing F-1 + three-sibling carried debt documented since `.1R.30R.3.5`
  / `.1R.30R.5`), plus the same guards are now transitively implicated by this
  repair's one-file change. Per prompt §29 ("if primary-source lifecycle says
  these belong in a separate IV, leave them for that successor") and §36
  (Option A — repair only, followed by a fresh hardware-certification IV), the
  full phase-aware reconciliation of this guard set is folded into the
  dedicated successor IV, which re-baselines all point-in-time guards for the
  N-16-5 track. This repair reconciles only the two guards its own change
  *directly and cleanly* trips (§5).

## 7. Certification placement (§36) — Option A

Per CPIPC-001 and RHAMP-REQ-152/153/155/156, `.1R.33`'s "independent
verification + mandatory real-CTAP2-hardware verification + N-16-5 closure" is
a **distinct dedicated phase** — RHAMP-REQ-153 forbids hardware access "in any
phase before `.1R.33`'s controlled hardware session", and RHAMP-INV-018 keeps
the automated suite and the hardware evidence non-substitutable. This repair
phase is **repair-only**. No real hardware ceremony was performed here; a
passing protocol-faithful fixture is **not** a hardware certification, and a
single command getting past `0x2C` is **not** a certification.

**H-1: REPAIRED — IV / REAL-HARDWARE CERTIFICATION PENDING.**
**N-16-5: NOT CLOSED** (row 14 — ≥ 1 real-CTAP2 hardware verification — still
false; row 16 clears once the hardware IV finds no blocking finding).

## 8. Product verdicts

| Property | Verdict |
|---|---|
| CTAP2 capability negotiation (`authenticatorGetInfo` driven) | VERIFIED |
| PIN/UV protocol selection (V2 preferred, V1 fallback, no-compat rejected) | VERIFIED |
| Trusted, non-logging, non-persisted PIN handling | VERIFIED |
| Permission-scoped, rp-bound PIN/UV token flow | VERIFIED |
| `makeCredential` PIN/UV authorization (command-scoped `pinUvAuthParam`) | VERIFIED |
| `getAssertion` PIN/UV authorization (command-scoped `pinUvAuthParam`) | VERIFIED |
| Mandatory UV never downgraded; incompatible authenticator rejected | VERIFIED |
| Deterministic-provider / virtual-authenticator realism (rejects the invalid shape) | VERIFIED |
| Production-provider ↔ test-provider authority separation | VERIFIED |
| **H-1** | **REPAIRED** (on evidence; real-hardware certification pending) |
| Real FIDO2 software mechanism baseline | VERIFIED — PRESERVED |
| Protected presentation baseline | VERIFIED — PRESERVED |
| Runtime `Observed` / `observe` / `unavailable`; first effect ABSENT | VERIFIED |

## 9. Recommended next phase (recommended, NOT reserved; own explicit human authorization + own protected human approval required — do not begin)

**`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.1` — Independent Verification of the
CTAP2 PIN/UV Repair + Mandatory Real-CTAP2-Hardware Verification + N-16-5
Closure** (== RHAMP `.1R.33`). It shall: independently verify this repair from
primary source; perform the full frozen RHAMP-REQ-152 real-hardware ceremony
against a genuine attached key (real `makeCredential` → canonical records;
real `getAssertion` passing the full §37 sequence with UP + UV; a
presentation-bound `PRODUCTION` approval end-to-end through Gate 5;
wrong-challenge / missing-UV / replay / revoked-credential all rejected);
fold the full phase-aware reconciliation of the F-1 + three-sibling +
`.1R.19R` / `.1R.19R.1` / `.1R.30R.1` point-in-time guard set (test-only,
widened-not-weakened); and — only if every frozen N-16-5 requirement is then
complete and no blocking finding remains — close N-16-5. Then N-16-6, then
N-16-7 (strictly last). Do not begin N-16-6 / N-16-7 / Slice C; do not
implement or call the first external effect; do not enable execution.

---

## Governance

- **`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED`** — preserved.
  This applies to delegated workers / subagents. The primary human-authorized
  operator session performed the governed lifecycle for `.1R.30R.5R` under the
  explicit authorization in the phase prompt.
- Governed PCAE lifecycle only — no raw `git commit` / `git push`,
  `--no-verify`, force push, history rewrite, or hook bypass.
- Historical `.1R.30R.5` (and `.1R.30`, `.1R.30R.3.3`, `.1R.30R.3.5`,
  `.1R.30R.4`) remain immutable BLOCKED records, not rewritten.

*Canonical artifact — Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.*
