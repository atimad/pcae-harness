# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R — Deployment-Owner First Production Human-Principal / Genuine-YubiKey FIDO2 Credential Bootstrap and Canonical Registry Establishment

## Status: COMPLETE

## Summary

Predecessor phase `...1.1R` correctly stopped BLOCKED before real N-16-5
certification because the production human-principal and FIDO2 credential
registries were empty (C-1: no canonical credential existed to bind a real
assertion to a canonical human principal). This phase performed exactly the
missing deployment-owner bootstrap ceremony and nothing more: it does not
perform certification, does not mint a PRODUCTION `AuthenticatedHumanPrincipal`,
and does not touch N-16-5/N-16-6/N-16-7.

Primary source (not narrative assumption) established that bootstrap is
**two** deployment-owner-only ceremonies, not one:

1. `scripts/hpac_protected_root_admin.py enroll-principal` — creates the
   `PrincipalRecord` (mechanism-neutral; `hpac_principal_admin.py` alone
   cannot bootstrap from an empty registry, since `enroll_first_credential`
   requires an already-`active` principal — `human_principal_registry.py`
   `_require_active_principal`).
2. `scripts/hpac_principal_admin.py enroll-first-credential` — performs the
   real CTAP2 `makeCredential` ceremony against the genuine YubiKey and
   atomically writes `CredentialRecord` + FIDO2 sidecar + counter-state.

Both were executed once each, by the primary human operator, in their own
trusted local terminal, with real sudo authentication and a real YubiKey
touch + PIN. No delegated worker executed, orchestrated, or had access to
either ceremony.

## Required Final Verdicts

```
FIRST-PRODUCTION-PRINCIPAL BOOTSTRAP:            COMPLETE
CANONICAL HUMAN PRINCIPAL:                       ESTABLISHED
HUMAN-PRINCIPAL IDENTITY SOURCE:                 CANONICALLY GENERATED (new_hpac_id("hp"))
HUMAN PRINCIPAL MECHANISM NEUTRALITY:            VERIFIED
GENUINE YUBIKEY:                                 VERIFIED (aaguid b7d3f68e88a6471e9ecf2df26d041ede)
REAL makeCredential:                             VERIFIED
ENROLLMENT USER PRESENCE:                        VERIFIED
ENROLLMENT USER VERIFICATION:                    VERIFIED
PRODUCTION FIDO2 CREDENTIAL:                     ESTABLISHED (hpc-2e7bbfa0c1b2480ba84ab5792159179d)
CREDENTIAL -> HUMAN PRINCIPAL BINDING:           VERIFIED
CREDENTIAL PROFILE:                              VERIFIED (hpac.fido2.uv_presence.v2, rp_id=hpac.pcae.local)
CREDENTIAL REVOCATION STATE:                     ACTIVE
COUNTER STATE:                                   ESTABLISHED (generation=0)
BOOTSTRAP TRANSACTION:                           COMPLETE
AUTHORIZED BOOTSTRAP WRITE SET:                  VERIFIED (see evidence artifact)
UNAUTHORIZED MUTATING HOST COMMANDS:             0
C-1:                                             RESOLVED
REAL N-16-5 CERTIFICATION CEREMONY:              NOT PERFORMED
F-5:                                             DEPLOYMENT VERIFIED -- FINAL CERTIFICATION PENDING
N-16-5:                                          NOT CLOSED
RUNTIME:                                         Observed / observe / unavailable
FIRST GOVERNED RUNTIME EXTERNAL EFFECT:          ABSENT / UNREACHABLE
```

## Evidence

Durable non-secret evidence: `.pcae/certification/rhamp_first_credential_bootstrap_2e7bbfa0.json`.
It records the pre/post registry state (raw filesystem read-back, not the
Python authority API — see below), the write set, the two identity-boundary
incidents hit and resolved during the ceremony, and the human/hardware
interaction audit (1 real `makeCredential`, 1 touch, 1 PIN prompt, 0
protected APPROVE/REJECT, 0 certification `getAssertion`, 0 presentation
evidence, 0 secrets persisted).

Independent post-write confirmation was obtained by having the operator
`cat`/`ls` the protected-root JSON files directly as root (bypassing the
Python `HPACStoreAuthority` layer entirely), rather than through a fresh
ad hoc script calling `HumanPrincipalRegistryStore.production()`. The
latter was attempted first and correctly failed closed
(`HPACAuthorityError: production HPAC root is not protected from the
configured agent principal (root=agent_is_owner_with_write_bit)`) — see
finding below.

## Findings

**F-10 (environmental, resolved, no code change).** `sudo` on this host
inherits the invoking interactive shell's `PATH` (no `secure_path` in
sudoers). Several `PATH` entries the operator's shell prepends ahead of
`/bin` are owned/writable by the configured agent principal (uid 501).
`hatp_class_b_topology_verifier.py::_resolve_trusted_executable_for_subject`
correctly refuses to trust `ls`/`getfacl` when an agent-writable directory
precedes the real binary in `PATH` (an attacker with that write access
could otherwise plant a spoofed `ls` to fake "no ACL"), producing
`acl_inspection_unavailable` for every protected-root ancestor. Fixed by
invoking with `sudo env -i PATH=/usr/bin:/bin:/usr/sbin:/sbin ...`.
`env -i` also clears `HOME`, which broke Python's user-site resolution of
the `fido2` package (installed at
`~/Library/Python/3.14/lib/python/site-packages`); fixed by additionally
passing `PYTHONPATH=<that directory>`. Neither fix touches the OS `PATH`
the ACL-trust check inspects. No `src/pcae` change.

**F-11 (architectural gap, not repaired — out of this phase's scope).**
There is no canonical read-only, production-boundary-safe inspection path
for the HPAC registries outside an active `production_writer()` mutating
transaction. `HPACStoreAuthority._validate_production_boundary()` checks
writability against `self._configured_agent_identity` if bound (only ever
bound inside `production_writer()`'s recognition sequence for one specific
`PawaOperation`), else falls back to the live process's own ambient
identity. A standalone script calling `HumanPrincipalRegistryStore.production()`
directly — even run as root, the legitimate deployment owner — is checked
against root's own identity, which trivially owns the protected root, so
the boundary check fails closed (correctly refusing to let the guarantee
be asserted vacuously). This phase did not construct a new authority path
to route around it (that would itself be exactly the "generic
reader/writer authority" this architecture is designed to prevent); it
relied instead on (a) the write ceremonies' own internal, correctly-bound
read-back verification (RHAMP-REQ-025 / HPAC-REQ-015 — already exercised
and already passed, which is why both CLI invocations returned success
rather than raising), and (b) plain filesystem `cat`/`ls` as root for
independent confirmation, which never touches the Python authority layer
at all. Recorded here for a future phase to consider (e.g. a dedicated
read-only `PawaOperation` / inspection capability) — not attempted here.

## Boundaries preserved

- No protected APPROVE/REJECT election; no presentation evidence created;
  no certification `getAssertion`; `require_real_assurance=True` not
  invoked; no PRODUCTION `AuthenticatedHumanPrincipal` minted; no Gate 5
  final certification.
- Generation-1 protected-presentation deployment untouched (neither
  enrollment ceremony imports or calls any `protected_presentation*`
  module).
- Runtime confirmed unchanged post-ceremony: `pcae runtime inspect` →
  `Observed` / `observe` / `unavailable` / 0 plugins / 0 capabilities.
- Ordinary-PCAE-cannot-enroll boundary re-confirmed: targeted guard tests
  in `test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_1_writer_anchor_adjudication_iv.py`
  (agent/reachability-scoped selection) pass.
- `git diff --stat` shows zero `src/pcae`, `scripts/`, `tests/`,
  `docs/contracts`, or `pyproject.toml` change from this phase; only
  `.pcae/**`, `docs/PHASE_...md`, `PROJECT_STATUS.md`, `CHANGELOG.md`, and
  `tasks/**` were touched.

## Targeted regression

Ran the RHAMP/registry/topology/PAWA-writer test modules
(`test_hpac_foundation_independent_verification_3w1r2b1r111r31.py`,
`test_hpac_foundation_trust_root_repair_3w1r2b1r111r32.py`,
`test_phase_149o_20i_hatp_class_b_topology_verifier.py`,
`test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_1_pawa_writer_anchor_slice1.py`,
`test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_2_1_pawa_writer_capability_integrity_repair.py`,
`test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_4_merged_rhamp_mechanism.py`,
`test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_5_merged_rhamp_iv.py`):
**365 passed, 9 failed** — all 9 failures are pre-existing and unrelated
(intentional `test_blocking_reproduction_*` documentation-of-defect tests
plus one point-in-time HMIC-frozen-scope-set assertion); confirmed
zero-attributable since `git diff --stat HEAD` for `src/pcae`/`tests/` is
empty for this entire phase (no source or test file was touched, so these
failures are identical to the phase-entry baseline by construction, not
by A/B stash).

## Successor

Bootstrap succeeded (C-1 RESOLVED). Per phase scope, the fresh N-16-5
certification retry successor is **derived but not begun**. This CLI has
no formal CPIPC grammar-validation command; the naming series to date is
convention, not machine-enforced, so the token below is a recommendation
for whoever opens that phase to confirm against `pcae task list` /
`tasks/done/` at that time, not a validated identifier:

> `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1`
> — Final Real-Human / Genuine-YubiKey Protected-Presentation N-16-5
> Certification and Closure Adjudication — Retry After Canonical
> Production Credential Bootstrap

It must independently revalidate before ceremony: the principal and
credential still exist and are active, the credential binds to the
principal, counter state is canonical, generation-1 protected-presentation
deployment is still current, and the genuine YubiKey is still available —
then it may perform the real protected APPROVE → presentation evidence →
real `getAssertion` → UP+UV → `require_real_assurance=True` →
`AuthenticatedHumanPrincipal` → Gate 5 → N-16-5 negative matrix → closure
adjudication chain. Not started here.
