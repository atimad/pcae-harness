# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R Complete — Deployment-Owner First Production Human-Principal / Genuine-YubiKey FIDO2 Credential Bootstrap and Canonical Registry Establishment

- Phase: `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R`
- Status: **COMPLETE — C-1 RESOLVED**
- F-5: **DEPLOYMENT VERIFIED — FINAL CERTIFICATION PENDING**
- N-16-5: **NOT CLOSED** (unchanged; no certification ceremony performed)

Predecessor phase `...1.1R` stopped BLOCKED (C-1: empty production
principal/credential registries). This phase performed exactly the
missing deployment-owner bootstrap: `scripts/hpac_protected_root_admin.py
enroll-principal` created `PrincipalRecord hp-8cee9b36b6784608ae48261af86289b8`,
then `scripts/hpac_principal_admin.py enroll-first-credential` performed
one real CTAP2 `makeCredential` against the genuine YubiKey (aaguid
`b7d3f68e88a6471e9ecf2df26d041ede`), atomically writing `CredentialRecord
hpc-2e7bbfa0c1b2480ba84ab5792159179d` + FIDO2 sidecar + counter-state
(generation 0), bound to `hpac.fido2.uv_presence.v2` / `rp_id
hpac.pcae.local`. Both run once each, by the primary human operator, in
their own trusted terminal, with real sudo authentication and real
YubiKey touch + PIN. No delegated worker executed either ceremony.

**PRINCIPAL: ESTABLISHED (hp-8cee9b36b6784608ae48261af86289b8).**
**CREDENTIAL: ESTABLISHED (hpc-2e7bbfa0c1b2480ba84ab5792159179d).**
**C-1: RESOLVED.**
**REAL N-16-5 CERTIFICATION CEREMONY: NOT PERFORMED.**
**N-16-5: NOT CLOSED.**
**RUNTIME: not_implemented / Observed / observe / unavailable, 0 plugins/capabilities.**
**FIRST GOVERNED RUNTIME EXTERNAL EFFECT: ABSENT / UNREACHABLE.**

Independent post-write confirmation via raw filesystem read-back as root
(bypassing the Python authority layer): 1 principal, 1 credential, no
duplicates/orphans, all fields cross-check exactly. Two environmental
(non-code) invocation issues were hit and resolved (`sudo` PATH
inheritance tripping the fail-closed ACL-trust-tool resolver; `env -i`
clearing `HOME` and breaking `fido2` resolution) — see phase report
finding F-10. One genuine architectural gap found and left unrepaired as
out of scope (F-11): no canonical read-only, boundary-safe inspection
path exists for the HPAC registries outside an active `production_writer()`
transaction.

Recommended next phase: a fresh N-16-5 certification retry against the
now-populated production registry (derived, not begun).
N-16-6/N-16-7 remain OPEN/UNTOUCHED.
