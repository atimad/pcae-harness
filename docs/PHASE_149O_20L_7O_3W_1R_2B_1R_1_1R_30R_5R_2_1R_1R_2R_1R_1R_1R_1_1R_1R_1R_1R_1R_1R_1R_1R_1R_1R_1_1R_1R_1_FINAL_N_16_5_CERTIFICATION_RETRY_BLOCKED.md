# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1 — Final Real-Human / Genuine-YubiKey Protected-Presentation N-16-5 Certification and Closure Adjudication — Retry After Canonical Production Credential Bootstrap

## Status: BLOCKED. N-16-5: NOT CLOSED.

## Summary

The predecessor bootstrap phase (`…5R.2.…1.1R`) resolved C-1: it established the
canonical mechanism-neutral `PrincipalRecord hp-8cee9b36b6784608ae48261af86289b8`
and, via one real genuine-YubiKey CTAP2 `makeCredential`, the canonical
`CredentialRecord hpc-2e7bbfa0c1b2480ba84ab5792159179d` + FIDO2 sidecar +
generation-0 counter-state under the trusted protected root. This phase is the
retry of the final N-16-5 real-assurance certification ceremony against that
now-populated registry.

**All certification preconditions independently revalidated and PASS.** The
phase then **stopped before any ceremony step** — no protected-presentation
request, no helper launch, no human election, no `getAssertion`, no PIN/touch
request, no proof, no challenge, no Gate 5 — because of a newly-identified
blocking architectural finding:

**Finding H-3 (BLOCKING):** the real end-to-end N-16-5 certification chain has
**no production authority path**. `verify_human_authentication(require_real_assurance=True)`
→ PRODUCTION `AuthenticatedHumanPrincipal` → Gate 5 requires a usable
`PRODUCTION` `HPACStoreAuthority` on the real protected root plus `PRODUCTION`
writer capabilities for the roles `hpac_challenge_coordinator`,
`hpac_assertion_recorder`, `human_authentication_proof_verifier`,
`hpac_gate5_binder`, and `hpac_rhamp_counter_state_verifier`. None of these is
reachable outside the disclosed **test-only** seams. Closing the gap requires a
`src/pcae` change, which is outside this phase's authorized scope.

**N-16-5: NOT CLOSED. F-5: DEPLOYMENT VERIFIED — CERTIFICATION BLOCKED.**
No `src/pcae` / `scripts` / `tests` / contract / dependency change. Zero writes
to the protected root. Counter state untouched (generation 0). Runtime
unchanged (`not_implemented` / `Observed` / `observe` / `unavailable`, 0
plugins / 0 capabilities). No first governed runtime external effect.
N-16-6 / N-16-7 remain OPEN / UNTOUCHED.

## Anchors

- **R0 (phase-entry SHA):** `afacc333263f9c079f3e5f0faf1b4ef81e114955`
- **Predecessor:** `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R` — Deployment-Owner First Production Credential Bootstrap (COMPLETE; latest canonical completed phase — confirmed via `pcae session bootstrap` + `pcae phase-report show --latest`).
- **CPIPC successor validation:** no formal CPIPC grammar CLI exists; the append-`.1` token is the direct successor by the established convention, is absent from `tasks/done/`, and matches the predecessor report's own "Successor" recommendation verbatim. No mechanical discrepancy — the operator-supplied phase ID is used exactly as given.
- **`origin/main..HEAD` at entry:** 0.

## Certification preconditions — independently revalidated (steps 7–11, 16–20)

Method: operator-run **privileged read-only** inspection of the protected root
(`sudo cat` / `ls` / `find`; 0 mutations; 0 Python; all content non-secret —
public keys, digests, counters, metadata), plus agent-side digest
recomputation. No `production_writer()` transaction, no authority-layer call,
no ceremony.

| # | Check | Result |
|---|---|---|
| 1 | Predecessor bootstrap is latest canonical completed phase | ✅ |
| 2 | Canonical principal exists | ✅ `hp-8cee9b36b6784608ae48261af86289b8` |
| 3 | Principal ID matches production registry | ✅ |
| 4 | Principal status active | ✅ (`status:active`, `revoked_at:null`) |
| 5 | Principal mechanism-neutral | ✅ (`PrincipalRecord` carries no `mechanism_id`) |
| 6 | Exactly the intended credential exists | ✅ 1 credential |
| 7 | Credential binds exact principal | ✅ registry + sidecar `principal_id` identical |
| 8 | Credential status active | ✅ |
| 9 | Mechanism exactly `hpac.fido2.uv_presence.v2` | ✅ |
| 10 | RP ID exactly `hpac.pcae.local` | ✅ |
| 11 | Credential not revoked | ✅ `revoked_at:null` (registry + sidecar) |
| 12 | Counter state exists | ✅ `RHAMP-COUNTER-STATE/1.0` |
| 13 | Counter canonical/valid, no unexplained change | ✅ generation 0 / last_accepted_meaningful 0 / last_observed_raw 0 / review_flag false; `updated_at` = bootstrap time (unchanged) |
| 14 | Genuine YubiKey available | operator-confirmed physically connected; **not exercised this phase** (ceremony not reached) |
| 15 | Credential ↔ intended authenticator | ✅ sidecar `aaguid b7d3f68e88a6471e9ecf2df26d041ede`; `raw_credential_id` sha256 recomputes to `e9ab1a21…` (== bootstrap evidence); `cose_public_key` sha256(hex-ascii) recomputes to `bea8316c…` (== bootstrap evidence); registry `public_key` byte-identical to sidecar `cose_public_key`; sidecar `record_digest` == bootstrap evidence |
| 16 | Generation-1 presentation deployment current | ✅ `current_generation:1`, `status:active`, `installation_id hppi-648bee5e…`; `descriptor_digest c4e9a04d…` and `installation_digest ab23db59…` cross-consistent across `current-generation.json`, `installations/1/installation.json`, `descriptor.json` |
| 17 | Helper exact bytes / currentness | ✅ `helper_sha256 933c6646…`; `src/pcae/protected_presentation_helper.py` byte-unchanged since commit `a85abff6` (2026-09-03), which predates the gen-1 install (2026-09-05T16:53:22Z) |
| 18 | PPA descriptor / current-generation current | ✅ `verifier_kind pcae-protected-local-presentation/1.0`, `verifier_configuration_digest 951182f5…` (descriptor == installation) |
| 19 | Topology trusted | ✅ protected root `drwx------ root:admin 0700` — not accessible to the configured agent principal (uid 501) |
| 20 | Runtime unavailable | ✅ `not_implemented` / `Observed` / `observe` / `unavailable`, 0 / 0 |

Additionally: all RHAMP-FIDO2 / verifier / Gate-5 / authenticator / lifecycle /
proof / counter-state / sidecar modules are **byte-unchanged** since
`0250e5f7`; the only `src/pcae` changes in that range are
`protected_presentation.py` / `protected_presentation_helper.py` (via the
single commit `a85abff6`, which predates the gen-1 install) plus unrelated
`hatp_class_b_topology_verifier.py` / `notifications.py` / `phase_reports.py`.

**H-1** (CTAP2 PIN/UV repair) and **H-2** (missing interactive human-election
surface) are both **resolved**: `protected_presentation_helper.py` now contains
`_observe_trusted_terminal_election`, which opens `/dev/tty` directly and
requires the human to type exactly `APPROVE` or `REJECT` (fail-closed to
`CANCEL` on anything else). The blocker below is neither H-1 nor H-2.

## Blocking finding H-3 — no production authority path for the N-16-5 certification chain

The positive certification path is:
`run_protected_presentation_ceremony(authority=…)` (real helper render → real
`/dev/tty` APPROVE) → `HumanAuthenticationProofStore.create_canonical(writer, proof)`
→ `HPACLifecycleStore.open_challenge_canonical / record_assertion_canonical /
record_verified_canonical` → `verify_human_authentication(require_real_assurance=True,
gate5_writer=…, counter_state_writer=…)` → PRODUCTION `AuthenticatedHumanPrincipal`
→ Gate 5.

Every step needs either a usable `PRODUCTION` `HPACStoreAuthority` bound to the
real protected root, or a `PRODUCTION` `HPACWriterCapability` for one of the
roles `hpac_challenge_coordinator` / `hpac_assertion_recorder` /
`human_authentication_proof_verifier` / `hpac_gate5_binder` /
`hpac_rhamp_counter_state_verifier`. Re-derived from primary source:

1. **`HPACStoreAuthority.production()` fails closed for this use.** It
   constructs with `_configured_agent_identity = None`. The first store
   operation runs `_ensure_root` → `_validate_production_boundary`, which keys
   the negative boundary off `_current_agent_identity()` (the live euid) when
   no configured identity is bound. Run as the deployment owner (root — the
   only OS principal with write access to the 0700 root), the live euid *owns*
   the root, so the check raises
   `HPACAuthorityError: production HPAC root is not protected from the configured
   agent principal (root=agent_is_owner_with_write_bit)`. This is exactly the
   predecessor's finding **F-11**.

2. **`_configured_agent_identity` (uid 501) is bound only inside
   `production_writer()`'s HPAC-PAWA-001 v1.1 §33 recognition sequence.**

3. **`production_writer()` is the sole production admin-writer factory and
   accepts a closed `PawaOperation` set:** `ENROLL_PRINCIPAL`,
   `REVOKE_PRINCIPAL`, `REVOKE_CREDENTIAL`, `ENROLL_CREDENTIAL`,
   `INITIALIZE_CREDENTIAL_SIDECAR_STATE`, `CONFIGURE_PRESENTATION_MECHANISM`.
   None covers challenge coordination, assertion recording, proof
   verification, Gate 5 binding, counter-state verification, or a
   certification operation. It mints only the frozen `_REGISTRY_WRITER_ROLE` /
   `_PRESENTATION_INSTALLER_ROLE`, and `_detect_caller_module` restricts
   callers to the two Slice-1 consumers plus declared tests — a phase harness
   cannot call it.

4. **`HPACStoreAuthority._mint_production_writer_capability(role, subject,
   _factory_seal=_PRODUCTION_WRITER_FACTORY_SEAL)`** is called from exactly
   three `src` sites, all inside `hpac_protected_admin_writer.py`:
   `production_writer()` (closed op set, frozen roles) and
   `mint_protected_presentation_evidence_writer()` (the launcher's
   post-APPROVE evidence writer only). **No `src` path mints the
   certification-chain roles.**

5. **The only place the full chain composes is test code** — e.g.
   `tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_1_ctap2_pin_uv_repair_iv.py::test_25`,
   which uses `HPACStoreAuthority._production_test_fixture` (guarded by the
   disclosed test-only `_PRODUCTION_TEST_FIXTURE_SEAL`), a directly-imported
   `_PRODUCTION_WRITER_FACTORY_SEAL`, an in-process shim for
   `_launch_and_exchange`, the structurally-NON_REAL `DeterministicCtap2Provider`,
   and the `_test_decision_source` seam. Its own docstring: *"an IV
   observation, not a certification."*

**Why not repaired here.** A genuine production certification path requires a
`src/pcae` change — a new `PawaOperation` (or a dedicated production
challenge / proof / lifecycle / Gate-5 certification orchestrator) reachable
outside the test fixture, with its own §33-style recognition sequence. That is
explicitly outside this phase's authorized scope (§60 NO PRODUCT SOURCE
MODIFICATION; §64 boundary 53; the STOP conditions). Manufacturing the chain
from a phase harness — by importing the test-only `_PRODUCTION_WRITER_FACTORY_SEAL`
against `HPACStoreAuthority.production()`, or by piggybacking on an unrelated
`production_writer()` transaction's recognized authority — would make the
resulting `AuthenticatedHumanPrincipal` a fixture / forged object, not a
genuine production authentication. That is the same "not vacuously / not
through a test seam" principle the phase enforces for the human APPROVE
election (§18) and for verifier-issued principal trust (§29), and it is
consistent with the predecessor's own F-11 reasoning (it refused to "invent a
new authority path to route around" the boundary). Adjudicated and **NOT
repaired**, per the `.1R.30R.5` (H-1) and `.1R.30R.5R.1` (H-2) precedent.
§28 of the phase directive anticipates exactly this: *"If this call fails: do
not manually mint a principal. N-16-5 remains open."*

**Smallest current blocker:** no production-authorized entry point for the
N-16-5 certification chain (challenge / proof / lifecycle / Gate-5 /
counter-state-verify).

## N-16-5 minimum closure criteria (§47) — reconciled

| Criterion | Verdict |
|---|---|
| 1 generation-1 deployment current/trusted | **PASS** |
| 2 canonical human principal verified | **PASS** |
| 3 canonical active FIDO2 credential verified | **PASS** |
| 4 counter state verified | **PASS** |
| 19 credential not revoked | **PASS** |
| 39 no runtime capability enabled | **PASS** |
| 40 first governed runtime effect absent/unreachable | **PASS** |
| 5–18 (real helper / operation render / APPROVE / presentation evidence / genuine YubiKey / getAssertion / UP / UV / RP / challenge / signature / counter transition) | **NOT ATTEMPTED** — stopped before ceremony |
| 20–25 (real auth proof / real presentation / `require_real_assurance=True` / PRODUCTION `AuthenticatedHumanPrincipal` / verifier-issued / Gate 5) | **NOT PERFORMABLE (H-3)** |
| 26–37 (wrong-challenge / replay / revoked-credential / missing-presentation / non-real-presentation / non-real-authentication / PB-DENY / policy-DENY / forged-principal / stale-presentation / revoked-presentation / single-use denials) | **NOT ATTEMPTED** — require the positive artifacts |
| 38 no unresolved current N-16-5 blocker | **FAIL** — blocking finding H-3 |
| RHAMP-REQ-152 bullet 4 (presentation-bound approval → PRODUCTION principal) | **NOT PERFORMABLE (H-3)** |

7 PASS / 1 FAIL (H-3) / 6 NOT PERFORMABLE / the remainder NOT ATTEMPTED.
**No partial closure. N-16-5: NOT CLOSED.**

## Required final verdicts

```
CANONICAL HUMAN PRINCIPAL:                       VERIFIED (hp-8cee9b36b6784608ae48261af86289b8, active, mechanism-neutral)
CANONICAL FIDO2 CREDENTIAL:                      VERIFIED (hpc-2e7bbfa0c1b2480ba84ab5792159179d)
CREDENTIAL STATUS:                               ACTIVE
CREDENTIAL -> PRINCIPAL BINDING:                 VERIFIED
COUNTER STATE BEFORE:                            generation 0 / last_accepted_meaningful 0 / last_observed_raw 0 / review_flag false
REAL INSTALLED PROTECTED HELPER:                 NOT USED (stopped before ceremony; deployment VERIFIED current, helper_sha256 933c6646…)
REAL HUMAN ELECTION:                             NOT COMPLETED (no election requested)
REAL PROTECTED-PRESENTATION EVIDENCE:            NOT CREATED
GENUINE YUBIKEY:                                 PRESENT (operator-confirmed); NOT EXERCISED this phase
REAL CERTIFICATION getAssertion:                 NOT ATTEMPTED
USER PRESENCE:                                   NOT ATTEMPTED
USER VERIFICATION:                               NOT ATTEMPTED
COUNTER STATE AFTER:                             generation 0 / last_accepted_meaningful 0 / last_observed_raw 0 / review_flag false (unchanged — no getAssertion)
REAL FIDO2 AUTHENTICATION:                       NOT VERIFIED (not performable — H-3)
REAL PROTECTED PRESENTATION:                     NOT VERIFIED (not performable — H-3)
require_real_assurance=True:                     NOT VERIFIED (not performable — H-3)
PRODUCTION AuthenticatedHumanPrincipal:          NOT VERIFIED (not performable — H-3)
GATE 5 PRODUCTION ASSURANCE CONSUMPTION:         NOT VERIFIED (not performable — H-3)
WRONG-CHALLENGE NEGATIVE:                        NOT VERIFIED (blocked upstream)
REPLAY NEGATIVE:                                 NOT VERIFIED (blocked upstream)
REVOKED-CREDENTIAL NEGATIVE:                     NOT VERIFIED (blocked upstream)
MISSING-PRESENTATION NEGATIVE:                   NOT VERIFIED (blocked upstream)
NON-REAL-PRESENTATION NEGATIVE:                  NOT VERIFIED (blocked upstream)
NON-REAL-AUTHENTICATION NEGATIVE:                NOT VERIFIED (blocked upstream)
PB-DENY DOMINANCE:                               NOT VERIFIED (blocked upstream)
POLICY-DENY DOMINANCE:                           NOT VERIFIED (blocked upstream)
FORGED-PRINCIPAL NEGATIVE:                       NOT VERIFIED (blocked upstream)
STALE-PRESENTATION NEGATIVE:                     NOT VERIFIED (blocked upstream)
REVOKED-PRESENTATION NEGATIVE:                   NOT VERIFIED (blocked upstream)
N-16-5 CLOSURE CRITERIA:                         7 PASS / 1 FAIL / rest NOT PERFORMABLE or NOT ATTEMPTED
N-16-5:                                          NOT CLOSED
F-5:                                             DEPLOYMENT VERIFIED — CERTIFICATION BLOCKED
RUNTIME:                                         not_implemented / Observed / observe / unavailable (0 plugins / 0 capabilities)
FIRST GOVERNED RUNTIME EXTERNAL EFFECT:          ABSENT / UNREACHABLE
```

## Ceremony distinction preserved

`makeCredential` ≠ `getAssertion`. Credential enrollment ≠ authentication ≠
protected approval. The predecessor's real `makeCredential` enrollment ceremony
is **not** partial N-16-5 certification. This phase performed **no** ceremony
of any kind: 0 `makeCredential`, 0 `getAssertion`, 0 protected APPROVE / REJECT,
0 presentation evidence, 0 challenges opened, 0 proofs, 0 Gate 5, 0 principals
minted, 0 secrets requested / echoed / logged, 0 writes to the protected root.

## Boundaries preserved

- No principal / credential / counter / protected-root / helper / generation /
  PPA-registration state created, recreated, reset, rotated, or repaired.
- No `src/pcae`, `scripts`, `pyproject.toml`, `docs/contracts`, or existing
  `tests/` change (`git diff --name-only R0 HEAD` touches only `.pcae/**`,
  `docs/PHASE_…`, `PROJECT_STATUS.md`, `CHANGELOG.md`, `tasks/**`).
- Runtime `not_implemented` / `Observed` / `observe` / `unavailable`, 0 / 0 —
  unchanged. No `adapter.dispatch`, no `DispatchEnvelope`, no plugin, no
  first governed runtime external effect.
- Human principal remains **mechanism-neutral**. The
  `hpac.fido2.uv_presence.v2` and `pcae-protected-local-presentation/1.0`
  profiles remain **supported / non-exclusive**; the mobile-only future path
  stays open. YubiKey and local TTY are **not** globally mandatory for PCAE
  development.
- `DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` preserved. No
  delegated worker was used; the primary human-authorized session performed
  all read-only investigation, evidence authoring, task lifecycle, commits,
  and push. The operator ran the one privileged read-only inspection in their
  own trusted local terminal (no admin password seen / requested in chat /
  echoed / logged).
- Durable Telegram Acceptance Receipt / Phase-Notification Auditability Repair:
  INDEPENDENTLY VERIFIED — preserved. No historical notification re-dispatch.
  This phase's normal completion notification is authorized.

## Ordinary-development non-regression

`pcae health` (healthy), `pcae check` (passed), `pcae status coherence`
(coherent), `pcae runtime inspect` (`not_implemented` / `Observed` / `observe`
/ `unavailable`, 0 / 0) — all pass with no YubiKey, no FIDO2 PIN, no protected
APPROVE, no real assurance. The certified/enrolled profile remains opt-in for
authority-bearing operations only.

## Evidence

`.pcae/certification/n16_5_final_certification_30r5r2_1r1r2r1r1r1r1_1r1.json`
(schema `PCAE-N16-5-FINAL-CERTIFICATION/1.0`) records R0, the CPIPC successor
validation, the full precondition revalidation with recomputed digests, the
H-3 root-cause chain, the reconciled closure table, the human/hardware
interaction audit (all zeros), and the boundary state.

## Successor (derived — NOT begun)

A narrowly-scoped `src/pcae` repair phase that adds a **genuine production
authority path for the N-16-5 certification chain**: a dedicated
`PawaOperation` and/or a production challenge / proof / lifecycle / Gate-5
certification orchestrator reachable outside the test fixture, with its own
§33-style recognition sequence — plus its independent verification. After that
repair + IV, this exact final certification phase should be re-attempted
unchanged against the (unchanged) canonical principal / credential / counter /
generation-1 deployment.

N-16-6 and N-16-7 remain OPEN / UNTOUCHED and strictly out of scope; N-16-7
remains strictly last.
