# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R Complete — N-16-5 CTAP2 PIN/UV Protocol Interoperability Repair

- **Status:** COMPLETE. **H-1: REPAIRED — fresh real-hardware certification required. N-16-5: NOT CLOSED.**
- **Type:** Narrow governed production repair (finding H-1). Option A per governing prompt §36 — repair only; the mandatory RHAMP-REQ-152 hardware ceremony and N-16-5 closure are the dedicated successor.
- **Phase-entry SHA `R0`** (finalized `.1R.30R.5` BLOCKED head): `9f004ea9`; `origin/main..HEAD = 0` at entry. `R0` is also the fixed-SHA attribution baseline `A`.
- **Contracts changed:** none (`git diff --name-only 9f004ea9 HEAD -- docs/contracts` empty). **New dependency:** none (`pyproject.toml` byte-unchanged). **Production diff:** exactly `src/pcae/core/hpac_rhamp_ctap2.py`.

## What was repaired — finding H-1

`NativeCtap2Provider` (`src/pcae/core/hpac_rhamp_ctap2.py`) requested user
verification with a bare `"uv"` **option** — removed in CTAP 2.1 from
`authenticatorMakeCredential` and invalid for `authenticatorGetAssertion` on a
`clientPin`-based roaming key — so every real `FIDO_2_1` authenticator rejected
both ceremonies with `CTAP2_ERR_INVALID_OPTION` (`0x2C`) before any user
gesture. The automated suite stayed green only because the deterministic
NON_REAL fixture honoured the invalid shape (the RHAMP-INV-018 gap).

The production provider now:

1. reads `authenticatorGetInfo` and negotiates the supported PIN/UV protocol
   via the pinned `fido2` library's `ClientPin` (`PinProtocolV2` preferred,
   `PinProtocolV1` fallback where valid, no-compatible-protocol rejected);
2. acquires a **permission-scoped** (`makeCredential` / `getAssertion` only),
   **rp-bound** (`hpac.pcae.local`) `pinUvAuthToken` — built-in UV where the
   authenticator advertises it, otherwise a **trusted, non-logging,
   non-persisted local `getpass` PIN entry** (never a CLI argument, environment
   variable, repository / config value, or chat prompt; non-interactive fails
   closed);
3. derives a **command-scoped** `pinUvAuthParam` over the canonical
   `client_data_hash` and threads `pin_uv_param` + `pin_uv_protocol` through
   both ceremonies;
4. sends **no bare `"uv"` option**, performs **no bare-`uv` fallback**, and
   rejects any authenticator that cannot perform UV and any `makeCredential`
   returned with `FLAG.UV` clear — **no UP-only downgrade** (RHAMP-REQ-034/035).

The PIN is dropped (`del pin`) the instant the token is obtained, never stored
on the provider, never placed on an exception message, and never written to any
RHAMP artifact — `RHAMP-INV-006` / §18 / §54 intact. PIN/UV errors map to
**existing** frozen `terminal_reason_code` values (the enum stays at 41).

**No normative contract byte changed.** The client-side `ClientPin` handshake
is a pinned-library wire detail (like `CoseKey.verify` in the same module), not
a normative delta; RHAMP-REQ-035 already names "PIN" as the UV factor.

## Preservation

`DeterministicCtap2Provider` is byte-unchanged. A new structurally NON_REAL
(`SIMULATION_ONLY = True`, `PROVIDER_KIND_IS_REAL = False`) protocol-faithful
`_VirtualCtap2Authenticator` + `_VirtualClientPin` + `build_virtual_ctap2_test_seam()`
model the CTAP 2.1 wire contract (reject bare `uv` → `0x2C`, missing
`pinUvAuthParam` → `0x36`, wrong protocol → `0x02`, wrong param / permission /
rp_id → `0x33`) so the real provider code path runs in automated tests without
hardware; they are reachable only through underscore-prefixed test seams and
never by `resolve_production_ctap2_provider()` (seam-free / env-free /
flag-free).

`RHAMP-FIDO2-CREDENTIAL/1.0` sidecar, `RHAMP-COUNTER-STATE/1.0`,
`FIDO2HumanAuthenticator`, the RHAMP-REQ-102 verify core, `hpac_verifier` REAL
branch, protected presentation, Gate 5 / Gate 9, PAWA, PPA, policy / PB, the
runtime capability model — all byte-unchanged. Runtime `not_implemented` /
`Observed` / `observe` / `unavailable`; 0 plugins / 0 capabilities; first
external effect ABSENT / UNREACHABLE. N-16-3 / N-16-4 CLOSED; N-16-6 / N-16-7
OPEN / UNTOUCHED (N-16-7 strictly last); N-23-1 INFO / N-23-2 INFO-DEFERRED
carried unchanged. Historical BLOCKED phases (`.1R.30`, `.30R.3.3`,
`.30R.3.5`, `.30R.4`, `.30R.5`) remain immutable — the `.30R.5` document is
byte-unchanged; only its forward-looking point-in-time *test* guards are
reconciled.

## Tests

**Fresh `.1R.30R.5R` repair suite:**
`tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_ctap2_pin_uv_repair.py`
— **48 tests, 0 failed.** Software baselines re-run green: merged RHAMP
mechanism suite (148, `test_33` reconciled), merged RHAMP IV (0 failed),
`.30R.5` hardware-cert/closure suite (15, four forward-looking guards
reconciled).

**Test reconciliations (widened, not weakened — exact filenames, `.1R.30R.5R`
comments, no `def test_` renamed / removed / skipped / xfailed):** the guards
this one-file production change directly trips —
`.30R.3.4::test_33_non_discoverable_and_uv_options_requested` (was asserting the
H-1 bug shape; now asserts the repaired shape),
`.30R.4R.2::test_70`, `.30R.4R.1::test_03` / `::test_72` (RHAMP-FIDO2
byte-unchanged bounds pinned to their owning phase's finalized head), and the
`.30R.5` `test_h1_locus…` / `test_no_production_or_script_or_pyproject_change_since_A`
/ `test_no_effect_adapter_or_dispatch_introduced_since_A` /
`test_this_phase_touched_only_doc_test_and_status_files` guards.

**Fixed-SHA A/B (A = `9f004ea9`, clean git worktree): 0 repair-attributable
functional regressions.** The `Ctap2Provider` protocol boundary is unchanged
and every consumer is byte-unchanged and green. The only new failures anywhere
are 3 HMIC "working tree dirty" `git status` guards that clear on commit
(verified). The `.1R.19R` / `.1R.19R.1` / `.1R.30R.1` since-baseline guards
were independently reproduced as **already failing at `R0`** (the pre-existing
F-1 + three-sibling carried debt); their full phase-aware reconciliation is
folded into the dedicated successor IV, which re-baselines all point-in-time
guards.

## N-16-5

Certification placement (§36) — **Option A, repair only.** No real hardware was
accessed (RHAMP-REQ-153); a passing protocol-faithful fixture is not a hardware
certification. **N-16-5 complete-requirement table row 14 (≥ 1 real-CTAP2
hardware verification) still false → N-16-5 NOT CLOSED.**

## Recommended next phase

`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.1` — Independent Verification of the CTAP2
PIN/UV Repair + Mandatory Real-CTAP2-Hardware Verification + N-16-5 Closure
(== RHAMP `.1R.33`). Own explicit human authorization + own protected human
approval required; ID recommended, NOT reserved. Do not begin N-16-6, N-16-7,
Slice C, a first external effect, or execution enablement.
`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` preserved.
