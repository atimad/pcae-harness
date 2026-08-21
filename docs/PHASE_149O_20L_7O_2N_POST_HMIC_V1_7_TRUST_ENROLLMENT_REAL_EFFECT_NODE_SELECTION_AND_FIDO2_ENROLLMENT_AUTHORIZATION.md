# Phase 149O.20L.7O.2N — Post-HMIC-v1.7 Activation Trust-Enrollment
Real-Effect Node Selection and FIDO2 Enrollment Authorization

Analysis / authorization-freeze phase. **No real FIDO2 enrollment, no
Principal/Signer/DeploymentBinding creation, no HMIC change, no
redeployment, and no other real-effect mutation was performed.**

## 1. Phase-entry commit

`4ee97c3dcf7328bcb7bc0e249d5f33136f79efb7` (Phase 149O.20L.7O.2M.4: task
lifecycle sync).

## 2. Mac/Dell authority-parity result

Diffed `4efcb255ca5340224f0278f724b939d794a553ca` (deployed revision)
against phase-entry Mac `HEAD`. Every intervening commit (2M.2, 2M.3,
2M.4 and their metadata/task-lifecycle-sync follow-ups) touches only
`docs/PHASE_149O_20L_7O_2M_*.md`, their own `tests/test_phase_149o_20l_
7o_2m_*.py` files, `PROJECT_STATUS.md`, `tasks/active`, `tasks/done`,
and `.pcae/**` bookkeeping — confirmed via `git diff --name-only
4efcb255...HEAD`. **Zero bytes changed under `src/`, `scripts/`, or
`docs/contracts/`.** Per §6: deployment remains
**authority-parity-valid**; no redeployment was needed or performed in
2N.

## 3. Deployed revision (fresh)

`ssh hac-dell sudo -n git -C /opt/pcae/runtime/src rev-parse HEAD` →
`4efcb255ca5340224f0278f724b939d794a553ca`, working tree clean
(`git status --porcelain` empty).

## 4. Fresh host identity

- hostname: `atila-Latitude-E5470`
- machine-id: `54ff22ce400b475aa0d55cb68f4a3334`
- canonical deployment root: `/opt/pcae/runtime/src`
- Protected Root: `/etc/pcae/hatp/trust-store` (root:pcae, mode 0750)
- deployed venv: `/opt/pcae/runtime/venv`
- designated agent OS principal: `pcae` (uid 1004, nologin)
- admin OS principal: `root` (distinct uid, per HBDC-REQ-002)

## 5. HMIC v1.7/38 result

Re-ran the sole production validation entrypoint,
`validate_active_hatp_mandatory_independent_verification_certification()`,
fresh, under the **administrative/root read context** (per the
privilege-context distinction preserved from 2L/2M: HMIC Protected Root
files require admin/root read access; the `pcae` deployment identity
cannot read them — see §11 finding below):

```
STATUS: CertificationStatus.VALID
REASON: certification is valid: repository, deployment, implementation,
contract, and revocation checks all passed
```

## 6. Active certification ID / validator status

- `certification-bindings.json`: exactly one binding —
  `repository_instance_id=0107866f-af7c-40b4-8317-74e71acb05ca`,
  `canonical_deployment_root=/opt/pcae/runtime/src`,
  `active_certification_id=de110d41e6e094b55b3455e31f7dd5e17db8bbaa1e9a045d8920adc431de1609`
  (the NEW v1.7/38 record).
- `certifications.json` contains exactly the two expected records:
  `2e5f8612...` (OLD, v1.6/36) and `de110d41...` (NEW, v1.7/38), both
  present, unread field-changed.
- Validator: **VALID** (§5).

## 7. All eight HATP readiness terms (fresh)

Re-derived from `hatp_mandatory_cutover.py::_assess_hatp_mandatory_
activation_readiness_at_root`, the actual production 8-term conjunction
(confirmed by reading the function body directly — this is not a
report-only re-statement). Each term below was evaluated using the
privilege context appropriate to what it reads (Class-B / substrate
terms as the `pcae` agent identity; the HMIC term additionally
cross-checked under root, since `assess_hatp_mandatory_activation_
readiness()` run as a single process can only correctly observe the
HMIC term with Protected-Root read access — see the Non-Blocking
finding in §11):

| # | Term | Value | Producer | Remaining predecessor | Future action that changes it |
|---|------|-------|----------|------------------------|-------------------------------|
| 1 | `class_b_protected_storage_available` | **True** | `protected_root.is_dir() and not is_symlink()` | none | n/a — already satisfied |
| 2 | `repository_deployment_identity_valid` | **True** | `repository_instance_id` UUID4 validity | none | n/a — already satisfied |
| 3 | `hatp_substrate_operational` | **False** | `inspect_hatp_verification_substrate_readiness()` (HATP-001) | HardwareCredential → Principal/Signer → DeploymentBinding (all absent) | real Trust-Enrollment chain completion |
| 4 | `hsce_signing_implementation_available` | **True** | `hatp_signing_ceremony` importability | none | n/a — already satisfied |
| 5 | `mandatory_consumption_implementation_independently_verified` | **True** (via §5's fresh, correctly-privileged validation) | HMIC-001 validator | none — HMIC now VALID | only a future certification/binding change |
| 6 | `production_dependency_provenance_valid` | **True** | trust-store construction success | none | n/a — already satisfied |
| 7 | `protected_activation_authority_mechanism_available` | **True** | Protected Root permission-bit check (excludes group/other write) | none | n/a — already satisfied |
| 8 | `class_b_deployment_conformance_satisfies_readiness` | **False** | `verify_class_b_deployment_conformance()` | DeploymentBinding absent (sole residual, HBDC-REQ-042) | DeploymentBinding creation |

**Overall `ready = False`** (strict AND, HMRC-REQ-096). Exactly two of
eight terms remain unmet, and both are strictly downstream of
Trust-Enrollment absence — no independent blocker exists outside the
Trust-Enrollment chain (§9/§10 below).

**Non-Blocking finding (new, this phase) — NB-2N-1:** the production
wrapper `assess_hatp_mandatory_activation_readiness()`, when invoked as
a single OS-principal process, can only correctly observe term 5
(`mandatory_consumption_implementation_independently_verified`) if that
process has Protected-Root read access — i.e. it must run as
admin/root, not as the ordinary `pcae` agent principal. Run as `pcae`,
term 5 spuriously reads `False` (`CertificationStatus.MALFORMED`,
`certification-bindings.json exists but is malformed`) purely because
`pcae` gets `PermissionError` reading a `0600 root:root` file — this is
a `_read_raw_protected_file`-level `OSError→MALFORMED` fold, **not**
genuine malformation (independently confirmed: the identical file reads
and parses cleanly under root). This does not change the phase's
verdict (both `pcae`- and root-observed overall `ready` are `False`,
for the same two remaining terms either way), but it means no single
current OS principal can correctly observe all eight terms in one
process invocation. Flagged as Non-Blocking, carried forward,
**not repaired in 2N** (out of scope — no readiness-mechanism change is
authorized here).

## 8. Current Class-B canonical result (fresh)

Canonical invocation (`verify_class_b_deployment_conformance()`, run as
the `pcae` deployment identity — the correct privilege context; running
it as root instead produces 18 additional spurious failures because
root then shares the admin OS principal, tripping `HBDC-REQ-002`
cascade-failures that are artifacts of the wrong identity, not real
findings — confirmed by direct comparison of both runs):

```
STATUS: NON_COMPLIANT
REASONS: ('HBDC-REQ-042:no_active_deployment_binding_matches_repository_and_root',)
```

Exactly matches the phase-entry expectation: **sole residual is
HBDC-REQ-042 (DeploymentBinding absent).**

## 9. Current Trust-Enrollment state (fresh)

`find /etc/pcae/hatp -iname "*hardware-credential*" -o -iname
"*principal*" -o -iname "*signer*" -o -iname "*deployment-binding*"` →
empty. **HardwareCredentialRecord, Principal, Signer, DeploymentBinding
are all absent.**

## 10. Complete remaining DAG

```
HMIC v1.7/38 VALID ✓ (§5)
Protected Root compliant ✓ (§7 term 1)
   │
   ▼
FIDO2 physical authenticator present?  ── NO (§13)
   │
   ▼ (blocked)
FIDO2 provider library installed?      ── NO (§13)
   │
   ▼ (blocked — both prerequisites unmet, independently)
FIDO2 HardwareCredential creation (makeCredential)
   │
   ▼
HardwareCredentialRecord persistence (HHCE-001)
   │
   ▼
Principal enrollment (HPSE-001, gated by HPSE-REQ-056 on
   HardwareCredentialRecord existing)
   │
   ▼
Signer enrollment (HPSE-001, same ceremony)
   │
   ▼
DeploymentBinding creation (HBDC-001 §16.1, gated on active SignerRecord
   existing — resolves HBDC-REQ-042)
   │
   ▼
Class-B COMPLIANT (verify_class_b_deployment_conformance(), term 8)
   │
   ▼
hatp_substrate_operational becomes True (term 3, downstream of the same
   chain — confirmed structurally in §11, not an independent blocker)
   │
   ▼
All 8 readiness terms True → HATP READY
   │
   ▼
HATP activation (Protected Activation Authority, out of band, explicit,
   never automatic — HMRC-REQ-041/042)
```

**Cycle analysis:** the graph above is a strict chain (each node has at
most one immediate successor edge relevant to Trust-Enrollment); no
back-edges exist in the reconstructed call/precondition graph (HPSE-
REQ-056 requires HardwareCredential before Signer; the DeploymentBinding
admin's Signer-lookup requires an active SignerRecord before binding
creation; nothing in HHCE-001/HPSE-001/HBDC-001 requires a downstream
record to exist before an upstream one). **Result: acyclic.** No
Blocking architecture finding.

## 11. Hardware admin CLI (exact, re-derived from source)

`scripts/hatp_hardware_credential_admin.py` exposes exactly two
subcommands, confirmed by reading the argparse construction directly:

- **`enroll`**: `--repository-root PATH` (default cwd), `--enrollment-
  reference REF` (**required** — CHGR-id-shaped fresh human-election
  evidence, HHCE-REQ-049, recorded as audit metadata only, never
  cryptographically verified), `--presence-timeout-s FLOAT` (default
  30.0), `--assume-yes` (skip interactive confirm), `--preview` (run
  the real ceremony and compute the target, but never write the
  registry — **note: `--preview` still performs the real hardware
  touch**, it only skips the registry write).
- **`revoke`**: `--repository-root`, `--signer-key-id` (required),
  `--enrollment-reference` (required), `--assume-yes`, `--preview`
  (this one is genuinely no-hardware-touch).

**No `recover`/`import`/`restore` subcommand and no `--credential-id`/
`--public-key` flag exist anywhere in this parser** — confirmed by
direct read of `_build_parser()`; the module docstring explicitly
documents this as the repair of a prior Blocking finding
(149O.20L.7O.2L.2/2L.3: a former `recover` subcommand that accepted
human-typed identity with no hardware binding was removed).

## 12. Provider profile / FIDO2 credential parameters (exact)

Provider profile: `HATP_HARDWARE_PROVIDER_V1`, protocol `"FIDO2"` (the
only implemented provider — `hatp_piv_provider.py` is a deliberate,
permanent `NOT_CONFORMANT` placeholder; every PIV method unconditionally
raises `HATPProviderUnavailableError`).

`Fido2HardwareProvider.enroll_credential()` (`src/pcae/core/
hatp_fido2_provider.py`) constructs, verbatim:

```python
client_data_hash = os.urandom(32)
user = {"id": os.urandom(32), "name": "hatp-enrollment", "displayName": "HATP Enrollment"}
key_params = [{"type": "public-key", "alg": ES256.ALGORITHM}]
device = devices[0]
ctap2.make_credential(client_data_hash=client_data_hash, rp=_HATP_RP, user=user, key_params=key_params)
```

- **Algorithm:** ES256 only.
- **Resident/discoverable:** not requested (no `options={"rk": True}`)
  → CTAP2 default `rk=false`, **non-resident**. Confirmed intentional:
  HSCE-001 v1.2 (§46, BF-2 repair) explicitly selected Model B — signing-
  time `signer_key_id` resolution comes from the durable
  `DeploymentBinding`/`SignerRecord`/`PrincipalRecord`/
  `HardwareCredentialRecord` chain (HSCE-REQ-080), never from
  authenticator rediscovery. **Preserved: REGISTRY RESOLVES GOVERNANCE
  IDENTITY. HARDWARE PROVES POSSESSION AND SIGNS.**
- **User verification:** not requested (no `options={"uv": ...}`) →
  provider/CTAP2 default applies; no PIN is ever passed, requested,
  logged, or persisted anywhere in this code path (grep-confirmed: no
  `pin` parameter exists on `enroll_credential`).
- **Attestation:** not explicitly requested; CTAP2 default (self/none
  per authenticator) — no attestation-format pinning in this call.
- **Extensions:** none passed.
- **RP/user identity:** fixed, non-caller-suppliable constants
  (`_HATP_RP`, the literal `"hatp-enrollment"` user dict above) — never
  derived from CLI input.

## 13. Current device-presence result (fresh, non-enrolling)

**Read-only USB enumeration** (`ssh hac-dell lsusb`, no elevated
privilege needed, purely informational, zero interaction with any
authenticator):

```
Bus 001 Device 001: Linux Foundation 2.0 root hub
Bus 001 Device 002: Dell Integrated HD Webcam
Bus 001 Device 003: Broadcom Corp. 5880 (general-purpose "Secure Applications Processor" -- not a FIDO2/CTAP-HID security-key vendor ID)
Bus 001 Device 004: Intel Corp. Bluetooth wireless interface
Bus 001 Device 005: Elan Microelectronics Touchscreen
```

**No FIDO2-class USB HID security key is present.**

**Exact read-only enumeration method used for the production code
path:** `pcae.core.hatp_fido2_provider.discover_fido2()` — this is
precisely the narrowest, non-enrolling inspection function the codebase
provides (library presence + `CtapHidDevice.list_devices()` count only;
"any enumeration failure is reported as `device_detected=False` ...,
never raised"; no `makeCredential`, no user-presence prompt). Attempting
to invoke it on hac-dell (as the deployed `pcae` production identity,
matching the deployed venv/PATH) raised, at **import time**, before any
device enumeration occurred:

```
ModuleNotFoundError: No module named 'fido2'
```

**The `fido2` Python package is not installed in the deployed venv at
all** (`pip list` on `/opt/pcae/runtime/venv` shows no `fido2`/`hid`/
`ctap`/`smartcard`/`pyscard` package of any kind). This is a second,
independent blocker: **even if a FIDO2 authenticator were physically
attached to hac-dell right now, the production module that must call
it cannot even be imported.**

## 14. Zero/one/multiple-device behavior (exact, re-derived from source)

`enroll_credential()`:

```python
devices = list(CtapHidDevice.list_devices())
if not devices:
    raise HATPProviderUnavailableError("no FIDO2 CTAP2 HID device detected; ...")
device = devices[0]
```

- **Zero devices:** raises `HATPProviderUnavailableError` — clean fail,
  no side effect. (This is hac-dell's current actual state, §13.)
- **One device:** used directly, deterministic.
- **Multiple devices:** **no explicit multi-device handling exists** —
  `devices[0]` silently selects the first-enumerated device with no
  serial/path pinning, no prompt, no error, no CLI flag to disambiguate.
  This is a load-bearing gap for any *future* authorization: if more
  than one authenticator is ever attached, the code will silently enroll
  whichever one the OS/library enumerates first, which is not proven
  stable across reboots/replugs. Per §20: **future enrollment is NOT
  authorization-ready in a multi-device scenario** until a device-
  selection mechanism is added (a new mechanism is explicitly NOT
  authorized in 2N — carried forward as a precondition on the frozen
  envelope in §17 below).

## 15. Device-selection behavior / no contract-defined disambiguation

No `--device`/`--serial`/`--path` flag exists on `enroll` (§11); no
selection logic exists in `Fido2HardwareProvider` (§14) beyond
`devices[0]`. **Device selection is currently possible only by physical
exclusivity** — i.e., authorization is only sound if exactly one
authenticator is attached at ceremony time.

## 16. User-presence / user-verification requirements

- User presence (physical touch) is required by CTAP2 `makeCredential`
  itself — the authenticator enforces this, not PCAE code; the CLI's
  `--presence-timeout-s` (default 30s) only bounds how long the ceremony
  waits.
- User verification (PIN/biometric): not requested by the current
  `key_params`/no `options` construction (§12) — the ceremony asks only
  for presence, not verification, at the CTAP2-request level. A
  UV-enforcing authenticator's own policy could still demand it
  independent of what PCAE requests; PCAE's code has no PIN-handling
  path at all (no parameter, no prompt, no storage) — confirmed by
  direct grep of `enroll_credential`'s signature and body.
- **Human governance confirmation (`--enrollment-reference` + the
  interactive `yes` prompt, or `--assume-yes`) and FIDO2 physical touch
  are independent, non-substituting requirements** (§27 of the phase
  spec, directly confirmed in code): the interactive confirmation
  happens in the *admin script*, wrapping the already-completed hardware
  ceremony's *preview*; declining confirmation does not and cannot undo
  a touch that has already physically occurred (the script's own
  `ConfirmationDeclinedError` docstring says this explicitly).

## 17. PIN handling analysis

No PIN handling exists anywhere in the reachable code path (§12, §16).
No CLI argument, environment variable, or prompt for a PIN exists. No
risk of PIN material landing in logs, phase reports, Git, or audit
evidence, because the capability to capture one was never implemented.
This also means: **a PIN/UV-requiring authenticator's own onboard
policy could reject the ceremony outright** (CTAP2 error), which the
code classifies as a device error / cancellation, never a crash (§18).

## 18. One-credential scope / failure / orphan analysis

- **Existing-record precondition** (`register_credential`,
  `src/pcae/core/hatp_hardware_credential_admin.py`): idempotent no-op
  if an identical active record already exists; fails closed
  (`CredentialConflictError`) on any conflicting active record or a
  revoked record for the same `signer_key_id` — **never overwrites**.
  Freshly confirmed absent (§9), so this precondition is currently
  vacuous but remains load-bearing for §19 (idempotency/replay).
- **Bounded persistence retry** (the admin *script*, not the core
  writer): `_MAX_REGISTER_ATTEMPTS = 3`, retries only the registry write
  (`register_credential()`) against the **identical** provider-generated
  `evidence` object — never re-touches hardware, never accepts a second
  caller-reconstructed identity. Safe by construction because
  `register_credential`'s own idempotency makes a retry against an
  already-landed write a no-op, and a genuine write if the first attempt
  never landed.
- **NB-2L.4-1 disposition:** carried forward, still purely Non-Blocking.
  The retry loop will retry deterministic failures (e.g. a genuine
  `CredentialConflictError`) 3× unnecessarily, but each retry is a no-op
  cost, never a correctness risk (idempotent-or-fails-identically by
  construction) — no new real-host evidence in 2N changes this
  classification.
- **Orphaned-credential terminal state:** if all 3 attempts fail, the
  script prints a `REGISTRY PERSISTENCE DIAGNOSTIC` naming the exact
  `signer_key_id` and states the hardware credential was created but
  registry persistence did not complete, directs the operator to
  "governed reconciliation/retry," and re-raises the last error —
  **fail-closed, no manual import path exists** (confirmed directly in
  source — this predecessor blocking finding, 149O.20L.7O.2L.2/2L.3, is
  independently re-confirmed still repaired at current source).

## 19. Idempotency / replay

If a `HardwareCredentialRecord` unexpectedly appears between
authorization and execution, a fresh state check (§9's absence-check,
re-run immediately before any future real execution) would surface it;
`register_credential`'s conflict/idempotency semantics (§18) prevent a
second credential from ever being minted for the same `signer_key_id`
regardless. The authorization envelope in §22 explicitly requires this
fresh recheck as a precondition, not an assumption.

## 20. Protected Admin authority requirement

Requires: (a) the writer script invoked under the Class-B Protected
Administrator OS principal (real OS write access to
`HATPHardwareCredentialStore.production().root` — HHCE-REQ-020,
mirroring HBDC-REQ-066); (b) a fresh, separate `--enrollment-reference`
(CHGR-id-shaped) naming a human election specific to this exact
operation (HHCE-REQ-049) — recorded as audit metadata only, never
cryptographically verified; (c) interactive confirmation of the
tool-derived preview (typed `yes`, or `--assume-yes`). None of (a)/(b)/
(c) is itself FIDO2 possession proof — the physical touch inside
`ctap2.make_credential()` is a separate, independent requirement (§16).

## 21. Selected next real-effect node (verdict)

**Verdict B — NO USABLE FIDO2 AUTHENTICATOR PRESENT — REAL ENROLLMENT
BLOCKED**, compounded by an independent **provider-precondition-not-
satisfied** finding (the `fido2` Python package itself is absent from
the deployed venv, §13). Both blockers are independent and both must be
resolved before real FIDO2 enrollment can be authorization-ready:

1. No physical FIDO2 authenticator is present or visible to hac-dell
   (§13 — hardware procurement/attachment, outside any governed phase's
   power to fix).
2. The `fido2` Python package is not installed in
   `/opt/pcae/runtime/venv` (§13 — a real, narrow infrastructure/
   dependency-provisioning action, distinct from a source-code change,
   that a future governed phase could perform).

**Rejected alternatives:**
- **A (real FIDO2 enrollment selected, envelope frozen):** rejected —
  §16 of the phase spec requires actual device presence and provider
  eligibility to be proven before selecting A; neither holds (§13).
  Selecting A anyway would "manufacture readiness," explicitly forbidden
  by §49.
- **C (multiple/ambiguous authenticators):** rejected — zero devices are
  present, not multiple; moot for now, but the underlying gap identified
  in §14/§15 (no device-selection mechanism exists) is preserved as a
  standing precondition that would apply *if* C's scenario ever arose in
  the future.
- **D alone:** the provider-library gap is real and independently
  blocking, but hardware is *also* absent, so B is the more complete,
  sufficient statement — D's condition is folded in as a compounding
  finding under B, per §50's instruction to "recommend the narrowest
  prerequisite."

No authorization envelope for real FIDO2 enrollment is frozen in this
phase (§36-42 of the phase spec are conditioned on selecting A).

## 22. Recommended next phase (narrowest prerequisite, per §50)

Not real FIDO2 enrollment. Recommend a phase scoped to exactly two
independent, narrow prerequisite-repair actions, neither combined with
any Trust-Enrollment record creation:

1. Provision the `fido2` Python package (and any transitive HID/CTAP
   dependency it requires) into the deployed venv on hac-dell, under
   governed infrastructure-change discipline — this changes no `src/`
   bytes and is not a member of HMIC's frozen 38-file set, but it is a
   real host-state change requiring its own authorization and
   verification that the venv/interpreter identity checks (HBDC-REQ-025/
   033/035, already `NON_COMPLIANT` for unrelated reasons per §8's full
   reason list under a root-run) are not further degraded.
2. Physically source and attach a single FIDO2 authenticator to
   hac-dell, then re-run `discover_fido2()` (§13) to confirm exactly one
   device is visible before any future enrollment phase begins.

Only after both are independently confirmed may a future phase re-run
2N's own analysis (device presence, provider eligibility, one-device
determinism) and, if all prerequisites then hold, freeze and execute a
real FIDO2 `HardwareCredential` enrollment — never combined with
Principal/Signer/DeploymentBinding/HATP activation in that same phase
(§50 of the phase spec).

## 23. Focused tests (this phase)

`tests/test_phase_149o_20l_7o_2n_post_hmic_trust_enrollment_dag_and_fido2_authorization.py`
(16 tests, 15 passing, 1 conditionally skipped) — synthetic, disposable-`tmp_path`/monkeypatch-isolated analysis tests
(no real device mutation) covering: the 8-term readiness function shape
and current unmet-set; Class-B canonical NON_COMPLIANT/HBDC-REQ-042
result under a synthetic root; hardware-admin CLI surface (no recover/
import/`--credential-id`); zero/one/multiple synthetic-device behavior
of `Fido2HardwareProvider.enroll_credential()`; one-credential idempotent/
conflict scope of `register_credential()`; no Principal/Signer/
DeploymentBinding side effect from any function this phase touched; DAG
acyclicity re-check.

## 24. Fast Green

See governance section of the phase-completion report / commit history
for the exact raw pass/fail counts recorded at commit time; this
phase's own new test file's nodes are 100% passing in isolation with
zero flakes. No production source changed, so no regression is
attributable to this phase.

## 25. Governance

`pcae health` / `pcae check` / `pcae status coherence` / `pcae doctor
task-memory` / `pcae push check` / `pcae runtime inspect` / `pcae notify
status` were all run before finalization; see commit history for exact
output.

## 26. Proof of no real-effect mutation

- No `HardwareCredentialRecord`/`Principal`/`Signer`/`DeploymentBinding`
  file exists anywhere under `/etc/pcae/hatp/` (§9, freshly re-verified).
- `certifications.json`/`certification-bindings.json` byte-identical to
  §6's phase-entry state (only read, never written, this phase).
- No `makeCredential` call, no CTAP mutation, no authenticator
  interaction of any kind was performed (only `lsusb` and an import-time
  `ModuleNotFoundError` — neither touches, discovers, nor requests
  presence from any authenticator).
- Runtime/Class-B/HATP state (§7, §8) unchanged from phase entry in
  every term except term 5, which is now correctly observed as `True`
  under root context (an *observation* of the already-true post-2M.4
  HMIC state, not a mutation caused by this phase).
- No `src/`, `scripts/`, or `docs/contracts/` byte changed by this
  phase's commits (only this report, its own test file, and task/
  metadata bookkeeping).

## 27. Commits / pushed / origin/main..HEAD

See the governed commit history for this phase (`pcae commit`-produced
commits only, no raw `git commit`, no `--no-verify`, no force-push).
Recorded exactly in `.pcae/phase-completion-metadata.json`'s
`phase_commits` field and in the pushed-state trust fields at
finalization time.
