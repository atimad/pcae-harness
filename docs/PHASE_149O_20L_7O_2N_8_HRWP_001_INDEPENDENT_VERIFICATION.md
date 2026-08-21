# Phase 149O.20L.7O.2N.8 — HRWP-001 Remote WebAuthn Provider Contract Independent Verification

**Verdict:** HRWP-001 v1.0 — INDEPENDENTLY VERIFIED WITH ONE
NON-BLOCKING FINDING — IMPLEMENTATION PREREQUISITES MAY PROCEED. No
Blocking defect found. Hybrid local-CTAP + remote-WebAuthn model
verified. Multi-authenticator model verified against current
registry/deployment semantics. Remote registration and remote
assertion/signing contractually supported through the provider-specific
WebAuthn proof profile. RP-ID/origin semantics frozen; literal
hostname/TLS infrastructure still to be selected/provisioned. No real
credential created; no production source or contract text amended.

## Directive

Independently re-derive and verify Phase 149O.20L.7O.2N.7's frozen
`HRWP-001 v1.0` contract
(`docs/contracts/HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md`) against
current primary contracts and production source — not against 2N.7's
own report, tests, comments, or conclusions. Verification only: no
contract amendment, no implementation, no hardware, no infrastructure
provisioning, no credential creation.

## Phase-entry commit

`c847f3a8` (HEAD at phase entry; unchanged throughout this phase — no
`src/pcae/**` or `docs/contracts/**` file was modified).

## Contracts and source read directly this phase

HRWP-001 v1.0 (full text), HHCE-001 v1.1, HPSE-001 v1.1, HSCE-001 v1.3
(including its §46/§48 Model-B repair), HBDC-001 v1.2, HATP-001 v1.0 —
all read fresh, not assumed from 2N.7's summary.

Production source read directly: `src/pcae/core/hatp_fido2_provider.py`
(full), `src/pcae/core/hatp_providers.py`,
`src/pcae/core/hatp_hardware_credentials.py`,
`src/pcae/core/hatp_bootstrap.py`,
`src/pcae/core/hatp_signing_ceremony.py::_resolve_deployment_binding_signer`,
and `hatp_mandatory_certification.py`'s frozen file-scope list.

## Requirement completeness

Independently re-extracted by regex, not trusted from the contract's
own self-count: `HRWP-REQ-001`..`HRWP-REQ-068` — sequential, gapless, no
duplicates. Confirms the contract's own claim.

## Central cryptographic re-derivation

`Fido2HardwareProvider.request_signature()`/`.verify()` independently
re-confirmed to construct and verify a signature over
`authenticatorData || SHA-256(clientDataJSON)` — the standard WebAuthn
`getAssertion` construction — with the challenge bound to
`sha256(canonical_payload)`, not an arbitrary caller-supplied value.
This is byte-identical in *shape*, not wire encoding, to what a browser
assertion produces (independently re-derived from WebAuthn/CTAP2
semantics). The one load-bearing divergence is origin/RP-ID: the local
provider uses fixed, non-HTTPS internal constants
(`hatp.pcae.local` / `pcae-hatp://hatp.pcae.local`, confirmed at
`hatp_fido2_provider.py:102-104`) that cannot satisfy a real browser's
origin enforcement — exactly the gap HRWP-001 names as an open
infrastructure requirement (see RP-ID/origin section below), not a
cryptographic incompatibility. Result: **(A) cryptographic construction
is materially identical**; the arbitrary-message-signing claim is
correctly *not* made byte-for-byte — HRWP-001 correctly frames remote
signing as a provider-specific assertion profile reusing the existing
verification algorithm, not an incompatible scheme.

## Challenge-binding sufficiency

The existing local challenge (`sha256(canonical_payload)`) already
binds every authority-sensitive field HSCE-001's own table requires
(`principal_id`, `signer_key_id`, `provider_profile`, `repository_id`,
decision-record identity, binding identity, rollback site, operation
reference, `issued_at`, `proof_version`). HRWP-REQ-039's remote
challenge-context field list is a superset covering the same ground at
the transport layer. No gap found.

## HSCE-001 relationship

Correctly disposed, not a bypass. HSCE-001's own definition of a
"signing ceremony" (interactive, foreground, human-initiated, single
continuous invocation) does not literally fit an asynchronous,
network-round-trip remote ceremony. HRWP-001 does not claim authority
to redefine that model unilaterally — it names a required future
HSCE-001 companion/amendment for ceremony/evidence-capture
orchestration, while correctly claiming the cryptographic/evidence
compatibility question (above) is already resolved and does not itself
require HSCE-001 amendment.

## Multi-credential / multi-signer / DeploymentBinding semantics

Independently re-verified: the registry supports multiple
`HardwareCredentialRecord`s and multiple `SignerRecord`s per Principal
with no hidden singleton assumption; `DeploymentBinding` selects exactly
one `(principal_id, signer_key_id, provider_profile)` tuple at a time
(confirmed live in `_resolve_deployment_binding_signer`, which reads
`binding.signer_key_id` singular); switching credentials requires an
admin-only `rotate_deployment_binding`, not simultaneous dual-credential
use — matching HRWP-001's own (non-overclaiming) framing. EXPLICIT_SIGNER
policy confirmed unambiguous: server-derived `allowCredentials`, never
client-asserted.

## RP-ID / origin semantics

Confirmed load-bearing and correctly resolved: the local constants are
non-HTTPS and structurally unusable as a browser RP ID. HRWP-001
correctly freezes the *semantic* behavior now (server-side origin/RP-ID
validation mandatory in addition to browser enforcement) while
explicitly and correctly leaving the *literal* hostname/TLS selection
open as infrastructure work for a later phase — satisfying the
semantic-vs-literal distinction this verification was required to test.

## Schema-change claim — Finding (Non-Blocking)

Independently tested HRWP-REQ-019's "no schema widening" claim.
`SignerRecord.provider_profile`, `DeploymentBinding.provider_profile`,
and `HardwareCredentialRecord.provider_profile` are confirmed true —
open string fields, no closed enum in code. **`HardwareCredentialRecord.protocol_name`
is false**: `hatp_hardware_credentials.py::_parse_credential` enforces a
closed `_PROTOCOL_VALUES = frozenset({"FIDO2", "PIV"})` allowlist in
code, contradicting HHCE-REQ-002's "plain string field" description that
HRWP-REQ-019 relies on. A real WebAuthn-sourced registration with
`protocol_name="WEBAUTHN"` would be rejected as malformed today until
that frozenset is widened. This is a narrow, one-line, mechanically
obvious future code change — it does not affect cryptographic
soundness, governance ordering, or any security invariant, and mirrors
the kind of narrative-vs-code discrepancy HHCE-001 v1.1's own §30 repair
already precedented and closed in-place without blocking.
**Recommendation:** a future narrow text repair to HRWP-001
§10/HRWP-REQ-019 stating that `protocol_name="WEBAUTHN"` requires
widening `_PROTOCOL_VALUES` in `hatp_hardware_credentials.py`. Not
performed in this verification-only phase.

No other finding, Blocking or Non-Blocking, survived independent
re-derivation across attestation parity, transport independence,
replay/concurrency/CSRF binding, governance ordering, UP/UV policy,
failure taxonomy, audit evidence, recovery-boundary exclusions,
trusted-kernel/transport split, and the implementation prerequisite DAG
— all confirmed accurate and non-overclaiming against current source
and the four existing frozen HATP contracts.

## Independent test suite

`tests/test_phase_149o_20l_7o_2n_8_hrwp_001_independent_verification.py`
— 10 freshly authored tests (not copied from 2N.7): requirement-numbering
completeness; the local provider's exact signature-construction line;
non-HTTPS RP-ID/origin constants; `HardwareCredentialRecord.provider_profile`
openness; the `protocol_name` closed-enum contradiction (the Finding
above); `DeploymentBinding`'s schema (no protocol/transport field);
Model-B signing-time resolution never calling `credential_identity()`;
no-attestation capability; the closed one-member production
`provider_profile` allowlist; absence of any remote-WebAuthn
implementation source. **10/10 passed.**

## Fast Green

`pytest -m fast_green -q`: 341 failed, 8690 passed, 4 skipped, 9 errors,
27068 deselected (554s). All failures pre-existing and unrelated — this
phase changed zero `src/pcae/**`/`docs/contracts/**` files and added
exactly one new, independently-passing test file. No A/B stash
comparison was required: the phase's only change has zero production
footprint, so pre-existing-failure attribution is definitional here, not
inferred.

## No-Go confirmation

No implementation. No WebAuthn server, HTTP route, browser client,
provider class, or new `provider_profile`/`protocol_name` constant added
to production source. No credential created. No device touched. No
contract amended. No HMIC-001 change. No redeployment. Runtime state
unchanged (Observed).

## Recommended next phase

Per HRWP-001's own sequencing and this phase's confirmation of no
Blocking finding, recommend an **HSCE-001 remote-WebAuthn assertion
companion contract** next — a pure contract-text phase with no
infrastructure dependency, unblocking the ceremony-orchestration
question named above independent of any DNS/TLS decision, before RP-ID/
origin/HTTPS deployment-infrastructure architecture selection.
