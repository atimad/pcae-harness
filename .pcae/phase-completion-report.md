# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.29 Complete — N-16-5 Real Human Authentication Mechanism & Protected Presentation Profile Contract Freeze (RHAMP-001 v1.0)

**Phase ID:** 149O.20L.7O.3W.1R.2B.1R.1.1R.29
**Type:** governed contract freeze / primary-source analysis / contract-versioning re-derivation / decision-freezing / documentation
**Status:** RHAMP-001 v1.0 FROZEN AS THE SOLE NORMATIVE DELTA — N-16-5 CONTRACT PROFILE FROZEN — IMPLEMENTATION NOT BEGUN
**Phase-entry SHA:** `4ae0a025` (`origin/main` synced; `origin/main..HEAD = 0` at entry)
**Production source changed:** none (`git diff 4ae0a025 HEAD -- src/pcae` empty; the deterministic NON_REAL `human_authenticator` / protected-presentation doubles are byte-identical)
**Normative contracts changed:** exactly one new companion contract added — `git diff --name-only 4ae0a025 HEAD -- docs/contracts` names only `docs/contracts/REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md` (RHAMP-001 v1.0, initial freeze); **no existing contract edited**; HPAC-001 stays v2.1
**Runtime:** `not_implemented / Observed / observe / unavailable`; 0 plugins / 0 capabilities; FIRST EXTERNAL EFFECT ABSENT; execution NOT enabled

## Summary

This phase turned the `.1R.28` planning decisions into a precise normative
companion contract, **RHAMP-001 v1.0 — Real Human Authentication Mechanism &
Protected Presentation Profile** (RHAMP-REQ-001..169, RHAMP-INV-001..018),
authored under HPAC-001 v2.1's existing extension points and changing none of its
text. Primary sources read to complete relevant scope: HPAC-001 v2.1 (§0 walls;
§6 HPAC-REQ-019; §7 HPAC-REQ-021..024; §8–§11 HPAC-REQ-025..035; §14
HPAC-REQ-039..046; §15 HPAC-REQ-047/048; §16 HPAC-REQ-049..051; §18
HPAC-REQ-054/055; §19–§20 HPAC-REQ-056..060; §21–§22 HPAC-REQ-061..068; §23
HPAC-REQ-069/070; §30–§32 HPAC-REQ-082..084; §34 HPAC-REQ-086; §37 versioning;
§38–§41 HPAC-REQ-089..099), RIHAC-001 v2.0 §12 condition 7 / §16, RIASC-001 v3.0
§2/§3, REPRC-001 v1.0 (the companion-contract shape), RDGO-001 v3.1, HPSE-001
v1.1, RPAC-001 v1.0, the HATP contract family; and, as evidence only,
`src/pcae/core/hpac_verifier.py`, `human_principal_registry.py`,
`approval_presentation.py`, `hatp_fido2_provider.py`, `pyproject.toml` — none
modified. Every load-bearing RHAMP-001 clause is anchored to an HPAC-REQ-### id
or a named production symbol.

## Native CTAP2 terminology verdict + WebAuthn/browser-origin exclusion

RHAMP-001 v1.0 is a **native CTAP2** mechanism (RHAMP-REQ-008). FIDO2 (umbrella),
CTAP2 (the protocol used, over USB-HID / NFC via `fido2.ctap2`), WebAuthn (the
browser client API — **not used**) are frozen distinct. RHAMP-001 adopts the
WebAuthn/CTAP2 **wire shapes** only (RHAMP-REQ-009) — not a WebAuthn ceremony.
§56 (RHAMP-REQ-141/142): no browser, no web origin, no TLS, no secure context,
no localhost HTTP, no port, no CSRF/cookie/session model, no web UI. A future
browser/loopback profile requires a new governed HPAC-001 version.

## Frozen profile (RHAMP-001 v1.0)

- **Real `mechanism_id` allowlist** = exactly `{hpac.fido2.uv_presence.v2}` —
  one entry, no wildcard, verifier-owned; `_ELIGIBLE_MECHANISM_IDS` widens by
  exactly that in `.1R.30`, `frozenset` literal, with a citation (§4).
- **Real `verifier_kind` allowlist** = exactly
  `{pcae-protected-local-presentation/1.0}`; `deterministic-test-fixture` stays
  `FIXTURE_NON_REAL`-only (§5).
- **RP ID** `rp_id = "hpac.pcae.local"` — compiled-in PCAE constant, distinct
  from HATP's `hatp.pcae.local`; `authenticatorData.rpIdHash` verified against
  `SHA-256(UTF-8("hpac.pcae.local"))`; not caller-selectable; **not a web
  origin** (§6).
- **PCAE canonical native-CTAP2 client-data context** `RHAMP-CLIENT-CONTEXT/1.0`
  (§7) — closed object; `context_identifier`
  `pcae-hpac://hpac.pcae.local/runtime-invocation-approval.v2` classified as a
  **PCAE-internal domain-separation constant, not a browser security origin**
  (RHAMP-REQ-028); `client_data_hash = SHA-256(canonical bytes)`; the CTAP2 call
  signs `authenticatorData ‖ client_data_hash`; verification reconstructs from
  trusted state and rejects any mismatch.
- **No false phishing-resistance / origin-enforcement claim** (§8) — RHAMP-001
  states exactly the true posture; the anti-substitution property provided is a
  local helper-integrity property, not a network-origin one.
- **Authenticator profile** (§9) — roaming/cross-platform, CTAP2,
  non-discoverable, `allowList`-bound, USB-HID or NFC, UP + UV. Unsupported in
  v1.0: BLE, hybrid/cross-device, synced passkeys, platform authenticators,
  discoverable/resident credentials, usernameless flows.
- **UP + UV mandatory** (§10) — both `FLAG.UP` and `FLAG.UV` checked; UP-only
  never yields an `AuthenticatedHumanPrincipal`; **RHAMP-001 adds the `FLAG.UV`
  check `hatp_fido2_provider.py` omits** (finding N-16-5-3); no downgrade, no
  fallback mechanism.
- **Authentication ≠ approval** (§11, §12) — assertion / `AuthenticatedHumanPrincipal`
  / touch are each not approval; presentation resolution (HPAC-REQ-054 step 5)
  and signature (step 6) are independent verifier steps; blind touch →
  `election_missing`.
- **Ceremony order** (§12) — reserve `approval_id` → render + hash the 13 closed
  `human_visible_facts` → **explicit `approve` election** → **then** build
  challenge + canonical client-data + drive CTAP2 `getAssertion` → verify
  (HPAC-REQ-054 steps 1–10, real signature branch) → mint proof; reject → no
  assertion, no proof.
- **First-credential bootstrap authority** (§14) — HPAC-REQ-023's **external
  deployment-owner protected administration principal**; never an arbitrary CLI
  caller, OS username, first registrant, agent, repo/Git identity, session id,
  env var, or stdin; unprovable anchor → `bootstrap_authority_unproven` / BLOCK.
- **Credential schema** (§17) — `CredentialRecord` **byte-unchanged**;
  `public_key = hex(cbor(COSE_Key))`. Raw CTAP2 credential id + `rp_id` +
  transports + advisory AAGUID → **new protected per-credential sidecar**
  `RHAMP-FIDO2-CREDENTIAL/1.0` at
  `<HPAC_PROTECTED_ROOT>/credentials/<credential_id>/fido2-credential.json`.
- **Private-key / biometric / PIN boundary** (§18) — PCAE stores none
  (structural — no field on any RHAMP-001 artifact); only `FLAG.UV` observed.
- **Attestation** (§19, §52) — not authoritative; none/self accepted
  unvalidated; enterprise attestation prohibited; no MDS; no AAGUID
  classification; no device-uniqueness claim.
- **Signature-counter policy** (§20) — not "always monotonic"; 0/absent →
  accept; `> last` → accept + update; non-zero `<= last` → **fail closed**
  `signature_counter_regression` + audit + admin-review flag; **never
  auto-revoke**.
- **Counter-state artifact** (§21, §22) — **new protected**
  `RHAMP-COUNTER-STATE/1.0` at
  `<HPAC_PROTECTED_ROOT>/credentials/<credential_id>/counter-state.json`; atomic
  replace + read-back; corruption / missing for an active credential → fail
  closed (never silently "counter 0"); **not** a `CredentialRecord` change,
  **not** an authority-generation input; frozen create/update linearization
  (verify → step-10 proof mint → **then** atomic counter update).
- **TTL bounds** (§23–§25) — challenge TTL ≤ 120 s; `max_proof_age_seconds`
  ≤ 300 s; presentation `expires_at` == the RIASC approval `expires_at`; each
  may be tightened, never loosened.
- **Replay** (§27) — registration challenge one-use; auth/approval challenge +
  nonce one-use; approval proof one authority lifecycle; Gate-9
  `consumption.json` final single-use; replay at any layer fails closed.
- **Protected presentation helper** (§28–§35) — PCAE-owned fixed implementation;
  administrator-installed `active` descriptor; **helper integrity evidence**
  (pinned executable digest in a protected installation record + descriptor
  digest + `verifier_configuration_digest` + supply-chain-admitted package /
  signed descriptor where the architecture provides it) — **not path/name
  alone**; unprovable → BLOCK; process-isolated, short-lived, local-only,
  non-networked; renders exactly the 13 closed `human_visible_facts` with no
  truncation of a mandatory field; deterministic `renderer_profile`; digest over
  the neutralized displayed bytes; `approval_preview_digest ==
  human_visible_representation_digest`; untrusted repository text cannot alter a
  trusted label/control; explicit Approve + explicit Reject controls (no
  implicit / timeout / touch-alone approval); no-accidental-approval UX
  safeguards frozen; helper admission **separate** from N-16-6 adapter
  admission.
- **Assertion verification** (§37) — credential lookup + principal ownership;
  `rpIdHash` equality; COSE signature via
  `CoseKey.parse(cbor.decode(public_key)).verify(authenticatorData ‖
  client_data_hash, sig)`; `client_data_hash` equality + context constants; UP
  **and** UV; the §20 counter policy; credential + principal `active`; challenge
  active/unconsumed + `challenge_digest` recompute; mechanism eligible + ≥
  `PRINCIPAL_VERIFIED_INTENT`; HPAC-REQ-054 step 5 presentation + step 9
  lifecycle/consumption; proof age + authority-generation currentness. **No
  custom cryptography.** The real branch is reachable only when
  `_authority_class_of(...)` is `PRODUCTION` for every resolved record and the
  resolved mechanism is in the real allowlist — a `FIXTURE_NON_REAL` credential
  never reaches it (finding N-16-5-2).
- **HATP FIDO2 reuse boundary** (§38) — shared library only (HPAC-REQ-019),
  never a live HATP trust dependency, never against HATP state; the UP-only
  presence check is **not** reusable as-is (RHAMP adds `FLAG.UV`);
  `_HATP_RP_ID` / `_HATP_ORIGIN` / HATP registry semantics **not** reusable.
- **Dependency** (§39) — reuse the already-declared `fido2>=1.1,<2` +
  `cryptography>=42,<45`; **no new dependency**; pins not loosened; no custom
  cryptography; no dependency install in `.1R.29`.
- **NON_REAL non-upgradeability** (§41) — `NON_REAL + real-looking mechanism_id
  + copied fields != REAL authority`; enforced structurally by
  `SIMULATION_ONLY`, the `_ELIGIBLE_MECHANISM_IDS` frozenset,
  `HPACAuthorityClass` propagation, `_authority_class_of`, the identity
  registry, `__reduce__` raising — none weakened.
- **Revocation / currentness** (§43, §44) — revoked credential / disabled
  principal cannot authenticate; revocation invalidates outstanding authority
  (HPAC-REQ-063/064); credential lifecycle **reuses** the existing
  `credential_generation` marker (HPAC-REQ-098a) — **no parallel freshness
  system**.
- **Proofs / writer** (§45–§47) — no new authentication-proof artifact
  (`HPAC-PROOF/2.0` already suffices); the real approval proof is a `PRODUCTION`
  / `PRINCIPAL_VERIFIED_INTENT` proof for exactly one approval; still `approval
  proof != PB permission != RE approval != runtime capability != execution`;
  only the trusted verifier / proof writer under the protected root mints
  canonical artifacts.
- **Local interactive control-plane host required** (§53–§55) — headless-only
  host **ineligible**; the human carries the USB key to whichever local
  interactive control-plane host owns the authority; **no remote Mac→Dell
  transport added**; remote / headless / networked approval **OUT OF SCOPE,
  deferred, authorized by no part of this contract**.
- **Mandatory real-hardware verification** (§62) — ≥ 1 real CTAP2 hardware
  verification with a frozen minimum-evidence list, **before N-16-5 closes (in
  `.1R.33`)**; no hardware accessed in `.1R.29` or any phase before `.1R.33`.
- **Automated-fixture policy** (§63) — deterministic virtual/synthetic
  authenticator fixture, explicitly TEST / NON_PRODUCTION; no synthetic object
  ever becomes REAL authority in a production registry; N-16-5 closure requires
  **both** the ≥ 55-case automated suite green **and** the real-hardware
  evidence.

## `terminal_reason_code` vocabulary — RE-DERIVED to 41 codes, discrepancy disclosed

`.1R.28` §12 item 10 and its summary state a "25-code" vocabulary; its §18
enumerated block actually lists **27** tokens and omits enrollment/bootstrap,
helper-integrity, explicit-human-rejection, cancellation, and timeout codes.
RHAMP-001 §49 (RHAMP-REQ-129/130) **re-derives** the closed set from every
rejection point across the real ceremony and freezes **41** codes, with a full
table (code / stage / trigger / human-visible category / retryable / audit
significance / authority result) in RHAMP-001 §49.1 and five distinct
human-visible categories in §50. The "25" and "27" figures are superseded.

## Existing-contract versioning re-derivation

Each artifact's own versioning rule was re-read. **No existing contract moves.**
HPAC-001 stays v2.1 (every residual decision fits an existing extension point;
RIHAC-001 §12 condition 7 names "HPAC-001 v2.1" literally → a bump would
cascade). RIHAC-001 v2.0 / RIASC-001 v3.0 / HPSE-001 v1.1 /
`HPAC-AUTHORITY-CONSUMPTION` /2.1 / PBRD-001 v3.0 / RDGO-001 v3.1 / RPAC-001
v1.0 / REPRC-001 v1.0 / the RE No-Go Registry / every HATP contract are
byte-unchanged. **The only normative delta of the entire N-16-5 track through
`.1R.29` is RHAMP-001 v1.0** (initial freeze, REPRC-001 v1.0 companion
precedent). RHAMP-001 versioning rules (MAJOR/MINOR criteria) are frozen in
§70.

## Production positive path after N-16-5 alone: NONE

Gate 6 still blocks (no admissible adapter — N-16-6); production Gate 7 still
DENYs (N-16-4 seam only); runtime stays `unavailable` (N-16-7 untouched and
last); no `adapter.dispatch(` call site exists. **First external effect:
UNREACHABLE.** N-16-6 / N-16-7 separation preserved — RHAMP-001 does not govern
adapter admission; real approval does not enable runtime capability. N-23-1
INFO / N-23-2 INFO / DEFERRED carried. Prerequisite ordering reconfirmed: N-16-3
(CLOSED) → N-16-4 (CLOSED) → N-16-5 → N-16-6 → N-16-7 (STRICTLY LAST); Slice C /
Slice D keep no phase ID until N-16-3..7 all close.

## Implementation decomposition (frozen; IDs recommended, NOT reserved)

1. **`.1R.30`** — real FIDO2 credential registry + authentication mechanism
   implementation (production `HumanPrincipalRegistryStore` writer path; the
   sidecar + counter-state stores; protected-admin enrollment + first-credential
   bootstrap ceremony tool; `FIDO2HumanAuthenticator`; real CTAP2 assertion
   verification in `hpac_verifier` incl. the `FLAG.UV` check;
   `_ELIGIBLE_MECHANISM_IDS += {hpac.fido2.uv_presence.v2}`;
   `terminal_reason_code` wiring; reuse `hatp_fido2_provider` CTAP2 primitives as
   a shared library). No protected UI, no real approval-authority production
   path yet.
2. **`.1R.31`** — Independent Verification of `.1R.30`.
3. **`.1R.32`** — real protected approval presentation mechanism
   (`pcae-protected-local-presentation/1.0`; process-isolated helper;
   deterministic `renderer_profile`; helper integrity/provenance; explicit
   Approve/Reject; real `mechanism_attestation`; administrator-installed
   `PRODUCTION` descriptor) + wire `require_real_assurance=True` through Gate 5 /
   Gate 9; a `PRODUCTION` `AuthenticatedHumanPrincipal` becomes obtainable for
   exactly one bound approval.
4. **`.1R.33`** — Independent Verification of `.1R.32` + **mandatory
   real-CTAP2-hardware verification** + N-16-5 closure.

Then N-16-6 → N-16-7 (strictly last). Slice C / Slice D keep **no phase ID**
until N-16-3..7 all close.

## Governance

- `pcae health` healthy · `pcae check` passed · `pcae status coherence` coherent
  · `pcae push check` `nothing_to_push` (pre-push) · `pcae doctor task-memory`
  warning-only historical `DONE.md` omissions (pre-existing hygiene debt; no
  current-phase error) · `pcae runtime inspect` `not_implemented / Observed /
  observe / unavailable`, 0/0.
- **DELEGATED `.3` FINALIZATION / COMMIT / PUSH: UNAUTHORIZED** — preserved.
  Only the primary human-authorized operator holds `.1R.29` lifecycle
  authority. Governed `pcae` lifecycle only — no raw `git commit`/`git push`, no
  `--no-verify`, no force push, no history rewrite, no hook bypass.
- No STOP / BLOCKED condition reached — every valid early-STOP condition in the
  phase prompt was checked (canonical doc §27) and none applies.

## Verdict

**RHAMP-001 v1.0: FROZEN** as the sole normative delta of the N-16-5 track
through `.1R.29`.

- **N-16-5: CONTRACT PROFILE FROZEN — IMPLEMENTATION NOT BEGUN.**
- **REAL HUMAN AUTHENTICATION: CONTRACT FROZEN — NOT IMPLEMENTED.**
- **PROTECTED HUMAN APPROVAL: CONTRACT FROZEN — NOT IMPLEMENTED.**
- **REAL APPROVAL PROOF: CONTRACT FROZEN — NOT IMPLEMENTED.**
- **HPAC-001: v2.1 (NO bump). Every other existing contract: byte-unchanged.
  `src/pcae/**`: unchanged.**

**Runtime: not_implemented / Observed / observe / unavailable. First external
effect: ABSENT. Execution enabled: NO.**

## Recommended next phase

`149O.20L.7O.3W.1R.2B.1R.1.1R.30` — **N-16-5 Real FIDO2 Credential Registry and
Authentication Mechanism Implementation** — scope frozen in RHAMP-001 §64. Then
`.1R.31` (IV) → `.1R.32` (protected presentation + real-assurance wiring) →
`.1R.33` (IV + mandatory real-CTAP2-hardware verification + N-16-5 closure).
Then N-16-6 → N-16-7 (strictly last). Each requires its own separate explicit
human authorization; IDs recommended, NOT reserved. **Do not begin `.1R.30`.**
Do not modify `src/pcae`. Do not modify normative contracts. Do not implement
real FIDO2/WebAuthn/CTAP. Do not implement the protected UI. Do not access
hardware authenticators. Do not begin N-16-6..7. Do not begin Slice C. Do not
implement or call the first external effect. Do not enable execution.

See `docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_29_N_16_5_REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT_FREEZE.md`
and `docs/contracts/REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md`.
