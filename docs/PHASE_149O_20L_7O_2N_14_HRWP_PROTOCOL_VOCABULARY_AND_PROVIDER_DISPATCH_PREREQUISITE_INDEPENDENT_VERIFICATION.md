# Phase 149O.20L.7O.2N.14 — Remote WebAuthn Production Vocabulary and Provider-Dispatch Prerequisite Independent Verification

**Verdict: A — 2N.13 PRODUCTION PREREQUISITE INDEPENDENTLY VERIFIED, WITH ONE NON-BLOCKING FINDING (stale recommended-next-phase prose).**

NBF-149O.20L.7O.2N.12-2: INDEPENDENTLY CONFIRMED CLOSED.
NBF-149O.20L.7O.2N.12-1: OUTCOME A INDEPENDENTLY CONFIRMED.
RP-ID / ORIGIN / HTTPS ARCHITECTURE MAY PROCEED.

Independently verifies Phase 149O.20L.7O.2N.13's two claimed production-prerequisite
resolutions. Re-derived from primary source, the fixed pre-2N.13 checkpoint
(`778aa39a~1`), and the governing contracts directly — not from 2N.13's own
report, tests, or comments.

## True phase-entry commit

`fa18675b` (HEAD == origin/main at phase entry; verified clean push state).

## 1. Fixed pre-2N.13 checkpoint (`778aa39a~1`)

Independently re-read via `git show`:

- `hatp_hardware_credentials.py::_PROTOCOL_VALUES` was
  `frozenset({"FIDO2", "PIV"})` — no `WEBAUTHN`.
- `hatp_hardware_credential_admin.py` independently hardcoded
  `protocol_name not in ("FIDO2", "PIV")` — a second, mirrored literal,
  not an import of the canonical constant.
- `hatp_providers.py` contained no `REMOTE_WEBAUTHN` reference anywhere.

This confirms the predecessor's two named problems were real, not
overstated.

## 2. Current protocol vocabulary

`src/pcae/core/hatp_hardware_credentials.py:62`:

```python
_PROTOCOL_VALUES = frozenset({"FIDO2", "PIV", "WEBAUTHN"})
```

Exact spelling/case confirmed; no aliases; still a `frozenset` (closed,
not extensible at call sites).

## 3. Fail-closed protocol validation

Mechanically verified via `_parse_credential`: `FIDO2`, `PIV`, and
`WEBAUTHN` are each accepted; an arbitrary unknown value
(`SOME_FUTURE_PROTOCOL`) is rejected with
`HATPHardwareCredentialStoreMalformedError`. No behavior change for the
two legacy protocols.

## 4. Admin validator centralization — proven by identity, not text

`hatp_hardware_credential_admin.py` imports `_PROTOCOL_VALUES` directly
from `hatp_hardware_credentials.py`. Independently confirmed
`admin_module._PROTOCOL_VALUES is credentials_module._PROTOCOL_VALUES`
(object identity, not merely equal frozensets) — a real import, not a
second definition with the same value. No hardcoded
`("FIDO2", "PIV")`/`["FIDO2", "PIV"]` literal remains in the admin
module.

## 5. Dependency direction

`hatp_hardware_credentials.py` does not import
`hatp_hardware_credential_admin.py` (no cycle). The admin module's
import of an underscore-private symbol from its sibling module mirrors
an already-established repository convention (the admin module's own
docstring documents this; other underscore-private imports of the same
kind already exist in this module). No authority inversion: the
constant's owning module (`hatp_hardware_credentials.py`, the parser
layer) is the more foundational one; the admin/enrollment layer
consuming it is the correct direction.

## 6. No third duplicate validator

Full-tree `grep` across `src/pcae/**` and `scripts/**` for
`("FIDO2", "PIV")`/`["FIDO2", "PIV"]` literals and for any other module
mentioning `protocol_name` with a still-closed `{"FIDO2", "PIV"}`-only
literal: zero hits outside the two intentionally-changed files.
Independently re-run (not the predecessor's own grep invocation).

## 7. Structural schema

`HardwareCredentialRecord` fields: `signer_key_id`, `provider_profile`,
`protocol_name`, `algorithm`, `public_key`, `status`, `revoked_at` —
unchanged. `CredentialEnrollmentEvidence` retains its `protocol_name`
field with no structural addition/removal. Vocabulary widening only.

## 8. Historical / mixed-protocol / multi-credential regression

Disposable, non-authoritative in-memory records: `FIDO2` and `PIV`
records parse identically to their pre-2N.13 behavior; a `WEBAUTHN`
record is now representable; `FIDO2` + `PIV` + `WEBAUTHN` credentials
coexist in one registry without collision; a multi-credential registry
document (3 signers, 3 distinct protocols) still parses correctly via
`_parse_credential_registry_document`. No new singleton assumption
introduced.

## 9. Provider factory — primary source

`hatp_providers.py` re-read directly:

```python
_PRODUCTION_HARDWARE_PROVIDER_PROFILES = (HATP_HARDWARE_PROVIDER_V1,)
```

`create_production_hardware_provider()`: a single closed-allowlist gate
(`if provider_profile not in _PRODUCTION_HARDWARE_PROVIDER_PROFILES:
raise HATPProviderUnavailableError`) followed by an **unconditional**
attempt to construct `Fido2HardwareProvider` — no branch keyed to a
specific profile value between the gate and that construction.
`discover_hardware_providers()` only ever reports `FIDO2`/`PIV`
availability facts; no `REMOTE_WEBAUTHN` code path exists anywhere in
this module or any production module.

## 10. Current remote-profile behavior

`create_production_hardware_provider("HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN")`
mechanically raises `HATPProviderUnavailableError` — confirmed by direct
call, not by inspection alone. No silent fallback for the *current*
(unmodified) allowlist.

## 11. Artificial allowlist admission test — load-bearing, mechanically reproduced

This phase does **not** trust 2N.13's source-grep-only proof
(`test_factory_source_confirms_no_per_profile_dispatch_branch_exists`,
which only asserted the string `"HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN"`
was absent from the factory body). Instead, this phase mechanically
reproduces the scenario: `monkeypatch` the **real, unmodified**
`create_production_hardware_provider` function's own module-level
`_PRODUCTION_HARDWARE_PROVIDER_PROFILES` tuple to additively include
`"HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN"` (no
`RemoteWebAuthnProvider` implementation exists anywhere), then call the
factory with that profile string.

**Result: Outcome B, confirmed.** The call returns a real
`Fido2HardwareProvider` instance — not an explicit-unavailable error
(Outcome A) and not some other ambiguous path (Outcome C). The returned
object's `capabilities().provider_profile` is
`HATP_HARDWARE_PROVIDER_V1` (the *local* profile), carrying no trace
that the caller ever asked for the remote profile — a true silent
fallback, mechanically demonstrated, not merely argued from source text.

This independently confirms 2N.13's central safety claim and directly
validates the correctness of its non-implementation decision: adding the
remote profile to the allowlist *today*, without a real
`RemoteWebAuthnProvider`, would be unsafe (silent remote→local
substitution), exactly as HRWP-001's client trust model (§19) and this
phase's own governing prompt (§20) prohibit.

## 12. HRWP-REQ-006 interpretation

`docs/contracts/HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md`, §3:

> **HRWP-REQ-006.** `create_production_hardware_provider()` ... is NOT
> amended by this contract. A future implementation phase MUST decide,
> as its own scoped question, whether remote-WebAuthn provider selection
> is added to that factory's existing `provider_profile`-string dispatch
> or reached by a distinct call path — this contract does not resolve
> that dispatch question...

This explicitly defers the dispatch-mechanism decision to a future
implementation phase. The current fail-closed state (§10 above) is
fully compatible with this deferral: HRWP-001 does not require present
factory recognition of the remote profile, so leaving
`_PRODUCTION_HARDWARE_PROVIDER_PROFILES` unchanged is not a contract
violation.

## 13. Outcome A validity

Confirmed from source (§9, §11 above), tests (§11), and contract text
(§12): the factory allowlist denotes profiles with a **concrete,
implemented** provider construction path, not merely all
contract-known profile identities. `HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN`
has no such implementation. Naive admission is demonstrably unsafe
(§11). The current remote-profile request fails closed (§10). HRWP-001
permits deferred dispatch implementation (§12). All five Outcome-A
criteria hold.

**Confirmed: NOT A PRESENT PRODUCTION DEFECT — FUTURE
REMOTE-PROVIDER-IMPLEMENTATION OBLIGATION**, not "closed" as though a
remote provider now exists.

## 14. Discovery / capability truthfulness

`discover_hardware_providers()` results all have `protocol_name` in
`("FIDO2", "PIV")`; none mention `WEBAUTHN`. No API/CLI path collapses
"protocol recognized" with "provider available." Current truthful
summary:

- `WEBAUTHN` protocol_name: **KNOWN**
- `HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN` provider profile:
  **CONTRACT-DEFINED**
- Remote-WebAuthn provider implementation: **UNAVAILABLE**
- Remote-WebAuthn execution: **UNAVAILABLE**

## 15. No remote→local fallback / local FIDO2 / PIV regression

No generic `if provider_profile in allowed: return Fido2HardwareProvider(...)`
pattern exists beyond the single, already-reviewed allowlist gate.
`create_production_hardware_provider(HATP_HARDWARE_PROVIDER_V1)` still
constructs a real `Fido2HardwareProvider`; the explicit-opt-in PIV
fallback path (`allow_piv_fallback=True`) still reaches the gate
without raising for an unrelated reason. No regression in either
profile's production behavior.

## 16. NBF disposition (final)

- **NBF-149O.20L.7O.2N.12-2: INDEPENDENTLY CONFIRMED CLOSED.** Every
  production protocol validator accepts `WEBAUTHN`; unknown values
  remain fail-closed; the admin vocabulary is truly centralized
  (identity-confirmed); no hidden third validator exists; legacy
  protocols and structural schemas are unchanged.
- **NBF-149O.20L.7O.2N.12-1: OUTCOME A INDEPENDENTLY CONFIRMED** — not a
  present defect, a future provider-implementation obligation (§13).

## 17. Future provider factory gate (frozen requirement, restated)

When `RemoteWebAuthnProvider` is eventually implemented, the provider
factory/discovery surface must evolve atomically enough that the remote
profile becomes discoverable/constructible **only** when a legitimate
remote provider exists — no intermediate silent fallback. The eventual
implementation's own test suite must at minimum cover: remote profile →
`RemoteWebAuthnProvider`; local profile → `Fido2HardwareProvider`;
remote profile never → `Fido2HardwareProvider`; unknown profile → fail
closed.

## 18. HMIC membership / count

`hatp_mandatory_certification.py::_FROZEN_AUTHORITY_BEARING_FILES`
independently inspected: both `core/hatp_hardware_credentials.py` and
`core/hatp_hardware_credential_admin.py` are members;
`len(_FROZEN_AUTHORITY_BEARING_FILES) == 38` (module-level `assert`,
independently re-confirmed via import). No HMIC amendment required —
both files were already bound members before 2N.13. HMIC contract
remains v1.7/38.

## 19. Implementation digest / Dell freshness

This is a local (Mac development) session with no SSH/administrative
access to hac-dell from this environment. Consistent with 2N.13's own
disposition (and every prior verification phase in this DAG), this
phase does **not** attempt to recompute or assert hac-dell's deployed
digest or CertificationRecord state directly. Per `PROJECT_STATUS.md`
and 2N.13's own completion report (both read as status evidence, not
as proof of code behavior): Dell was not redeployed or recertified by
2N.13, and this phase performs no action that would change that.
**Development digest changed (2N.13's two source-file edits) ≠ Dell
deployed digest changed** — these remain distinct facts; this phase
does not conflate them and does not call the Mac development digest
"certified."

## 20. No operational remote-WebAuthn claim

`PROJECT_STATUS.md`'s current top-of-file entry (Phase 2N.13) and this
phase's own text were checked for language implying remote WebAuthn now
works, a provider is available, or enrollment is operational: none
found. Correct, confirmed conclusion: only the protocol-record
vocabulary prerequisite has been implemented.

## 21. HRAC status freshness

`docs/contracts/HATP_REMOTE_ASSERTION_CEREMONY_CONTRACT.md` confirms
HRAC-001 v1.0, frozen by Phase 149O.20L.7O.2N.9.
`PROJECT_STATUS.md`'s Phase 149O.20L.7O.2N.10 entry independently
confirms: "HRAC-001 v1.0 INDEPENDENTLY VERIFIED — VERIFIED WITH
NON-BLOCKING FINDINGS, NEXT PREREQUISITES MAY PROCEED. NO BLOCKING
DEFECT." Current canonical state: **HRAC-001 is frozen and
independently verified — not unresolved, not reopened by this phase.**

**Non-blocking finding (this phase, NBF-149O.20L.7O.2N.14-1):** the
*committed* `.pcae/phase-completion-metadata.json`
`recommended_next_phase` field for 2N.13 (surfaced verbatim by
`pcae session bootstrap`) describes future implementation as "gated on
... HSCE-001's own named-but-unresolved remote-ceremony
evidence-capture companion work (HRWP-REQ-060)." Read literally, this
implies the HRAC-001 companion contract itself remains an open gap.
That is stale: the companion work HRWP-REQ-060 names is HRAC-001, which
was frozen in 2N.9 and independently verified in 2N.10 with no blocking
defect — the *contract* is resolved; only its *implementation* remains
outstanding, a materially different status than "unresolved." This
phase's own top-of-file `PROJECT_STATUS.md` "Current Phase" block does
**not** itself repeat this stale claim (mechanically verified: no
`"HRAC-001"` + `"unresolved"` co-occurrence in that block). Non-blocking
— no code or governance state depends on the stale phrasing — but
recorded so a future phase does not copy it forward as though HRAC-001
implementation work were still contractually undefined.

## 22. RP-ID / origin / HTTPS remaining prerequisite

`HRWP-REQ-027` (RP ID): confirmed still an "explicit open requirement
for the implementation phase" — no literal hostname selected.
`HRWP-REQ-031` (HTTPS/TLS): confirmed WebAuthn requires a secure context
with no PCAE-side exception, and no CA/reverse-proxy/DNS topology has
been selected. Both remain genuinely open, unresolved infrastructure
prerequisites — unaffected by this phase.

## 23. Dependency DAG (re-derived, not inherited)

```
2N.14 verification complete (this phase)
        ↓
RP-ID / origin / HTTPS infrastructure architecture selection
   (149O.20L.7O.2N.15 — architecture-only, no provisioning)
        ↓
remote WebAuthn server/provider implementation architecture or implementation
   (must satisfy: remote profile discoverable/constructible only when a
   real RemoteWebAuthnProvider exists — §17 above)
        ↓
synthetic interoperability
        ↓
independent verification
        ↓
HMIC source-scope evolution if new files are introduced
        ↓
redeploy / recertify (hac-dell)
        ↓
real enrollment / signing
```

No stale "HRAC unresolved" node is carried forward (§21).

## Findings

**NBF-149O.20L.7O.2N.14-1 (Non-Blocking).** 2N.13's committed
`recommended_next_phase` metadata text describes the HSCE-001/HRAC-001
companion work with wording that, read literally, implies the companion
*contract* remains unresolved, when in fact HRAC-001 was frozen (2N.9)
and independently verified (2N.10) — only its implementation is
outstanding. No blocking defect; no code or gate depends on this text.
Recommend a future documentation-only phase (or the next phase's own
report) restate this precisely, rather than a dedicated repair phase.

No other findings. No blocking defects identified.

## Independent test suite

`tests/test_phase_149o_20l_7o_2n_14_hrwp_protocol_vocabulary_and_provider_dispatch_prerequisite_independent_verification.py`
— 37 freshly authored tests, none copied from 2N.13's suite, covering:
fixed pre-2N.13 checkpoint reproduction; current exact protocol set;
`WEBAUTHN` accepted / arbitrary-unknown rejected; admin centralization
by object identity; no third validator (independent grep); legacy
FIDO2/PIV regression; mixed-protocol representation; multi-credential
registry regression; current remote-factory fail-closed behavior; the
load-bearing artificial-allowlist-admission mechanical reproduction
(Outcome B); local/PIV provider regression; discovery truthfulness;
HMIC membership/count; HRAC-001 current status; RP-ID/HTTPS still-open
requirements. All 37 passing.

## Fast Green

A/B, git-stash-isolated, identical `-n auto` parallelism:

- **Baseline** (my new test file stashed out, i.e. exact HEAD =
  `fa18675b` state): 339 failed / 8688 passed / 4 skipped / 9 errors,
  135.29s.
- **With this phase's change** (new test file restored): 339 failed /
  8688 passed / 4 skipped / 9 errors, 134.95s.

Byte-identical FAILED/ERROR sets (both listed above; unchanged from
each other). **Zero phase-attributable regressions** — expected, since
this phase adds one new, unmarked (not in `FAST_GREEN_MODULES`) test
file and touches no production source; the `-m fast_green` selection is
therefore unaffected by this phase's diff. Zero raw new failures either,
unlike 2N.13's own run (which correctly attributed 2 to
uncommitted-diff self-checks resolving on push) — this phase's diff
does not touch any file those self-checks watch.

## Proof of no implementation

No `RemoteWebAuthnProvider` class, HTTP route, request store, or
browser/client code added. No `makeCredential`/`getAssertion` invoked.
No `HardwareCredentialRecord`/`Principal`/`Signer`/`DeploymentBinding`
created in the real store — all test-suite objects are disposable,
in-memory, never persisted. No DNS/TLS/RP-ID provisioned. No HMIC-001
amendment (membership count independently reconfirmed at 38). No
hac-dell redeployment or recertification performed or claimed. No HATP
activation. No Permission Broker/runtime change. `git diff --stat
fa18675b..HEAD -- src/pcae/ scripts/` is empty (verified before commit)
— this phase touches only `tests/`, `docs/`, `PROJECT_STATUS.md`,
`CHANGELOG.md`, and `.pcae/phase-completion-*`.

## Runtime unchanged

No Permission Broker, PCAE runtime, or HATP activation state was
touched or read for its own sake beyond the read-only contract/source
inspection above.

## Next phase

**149O.20L.7O.2N.15 — Remote WebAuthn RP-ID / Origin / HTTPS
Infrastructure Architecture Selection.** Architecture-only: select a
literal RP-ID / origin naming strategy consistent with HRWP-REQ-027/
HRWP-REQ-029/HRWP-REQ-031; do **not** provision DNS/TLS/certificates,
and do not begin remote-provider/server implementation before this
selection is itself independently verified.
