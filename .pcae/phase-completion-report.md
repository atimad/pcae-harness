# Phase 149O.20L.7O.2N.18 Complete — Remote WebAuthn Literal RP-ID/Origin and Infrastructure Realization Plan Independent Verification

**Verdict A:** 2N.17's LITERAL RP-ID RULE / REALIZATION PLAN —
INDEPENDENTLY VERIFIED. ACTUAL OPERATOR DOMAIN: STILL REQUIRED BEFORE
LITERAL FREEZE (not treated as a defect). NO PROVISIONING. NO
PRODUCTION SOURCE CHANGED. NO HAC-DELL SESSION OPENED.

Independently re-reads HRWP-001 v1.1, HRAC-001 v1.0, and HBDC-001 in
full, fresh this phase, plus current `hatp_fido2_provider.py`,
`hatp_providers.py`, and `hatp_hardware_credentials.py` source, and
2N.15/2N.16's own text — not accepted from Phase 149O.20L.7O.2N.17's
own report, tests, or summary prose as proof.

**Confirmed, independently:**

1. **Construction rule.** `RP-ID: hatp.<operator-controlled-domain>` /
   `Origin: https://hatp.<operator-controlled-domain>` is valid
   WebAuthn RP-ID/origin scoping for any legitimate operator-controlled
   domain — effective-domain semantics, non-public-suffix precondition,
   stable operator control, no machine/IP dependency, DNS-01
   certificate-issuance feasibility, and migration portability all
   independently re-derived and confirmed.
2. **Single origin.** One canonical origin, confirmed for Mac, iPhone,
   and any future replacement deployment host; no per-platform,
   per-device, or per-host branching anywhere in 2N.17's text.
3. **Shared HATP RP model.** A single PCAE-wide RP-ID does not imply
   authority over every repository — repository-level authorization is
   confirmed enforced exclusively through `RepositoryIdentity`/
   `DeploymentBinding`/`Principal`/`Signer`/challenge binding, never
   through RP-ID/origin selection.
4. **DNS/TLS/ACME trust boundary.** DNS-01 (independently re-derived
   against RFC 8555 §8.4) validates via a public TXT record only — no
   public HTTP(S) exposure of the service is required or proposed.
   DNS/ACME credential compromise is confirmed an availability/
   transport-trust risk only, never a governance-authorization risk.
5. **Proxy/VPN/Host-header models.** Reverse-proxy and VPN control
   reachability, never authorization; expected RP-ID/origin are
   confirmed to come from static, canonical configuration, never from
   `Host`/`X-Forwarded-Host`/`Forwarded` request headers.
6. **Migration model.** RP-ID/origin/credential identity belong to
   PCAE's HATP governance function, not to `hac-dell` as a physical
   host — confirmed consistent with HBDC-001's own existing
   `DeploymentBinding` migration discipline (HBDC-REQ-042-046), not a
   competing one.
7. **Fail-unavailable behavior.** No automatic fallback to HTTP, IP
   address, `localhost`, an alternate RP-ID, an untrusted second
   origin, or ungoverned local signing is proposed anywhere in 2N.17's
   text if DNS/TLS/VPN fails.
8. **2N.16's two Non-Blocking observations** (Host-header/
   `X-Forwarded-Proto` trust rule; static client-asset integrity
   governance) — independently re-read at their exact source text and
   confirmed correctly carried forward by 2N.17 under their exact NBF
   identifiers, neither silently dropped nor falsely marked resolved.
9. **Actual operator domain: still unsupplied, not fabricated** —
   independently reconfirmed via a repository-wide search; correctly
   not treated as an incompleteness defect, per this phase's own
   governing instruction not to mark 2N.17 incomplete merely because it
   correctly refused fabrication.

**Derived (not merely asserted):** the future literal RP-ID/origin
freeze itself must receive independent verification before first
credential registration — a credential created under a wrong RP-ID
cannot be retargeted by later server-config changes, and RP-ID errors
would not surface as an obvious runtime failure.

**Findings — zero Blocking, four Non-Blocking:**

- **NBF-149O.20L.7O.2N.18-1** — port policy ("no port suffix in the
  common case") should be sharpened into an explicit requirement
  sentence before real TLS-termination configuration is written.
- **NBF-149O.20L.7O.2N.18-2** — a future domain-selection phase should
  freeze a mechanically-verifiable domain-ownership-evidence gate
  (e.g. a scoped TXT record proof) before accepting any operator-
  supplied domain as final.
- **NBF-149O.20L.7O.2N.18-3** — a future phase should explicitly
  distinguish an origin change under the same RP-ID (e.g. a port/
  front-door change) from an RP-ID change (full re-enrollment) as
  separate consequence classes.
- **NBF-149O.20L.7O.2N.18-4** (carried forward, not new) —
  NBF-149O.20L.7O.2N.16-1 (Host-header/`X-Forwarded-Proto` trust rule)
  remains open, correctly deferred by 2N.17, reconfirmed still open by
  this phase.

**No production change:** `git diff --stat 7f2f902c..HEAD --
src/pcae/ scripts/` is empty — this phase adds one new `docs/` file,
one new `tests/` module (21 fresh, independent tests, all pass), and
updates `PROJECT_STATUS.md`/`CHANGELOG.md`/task-lifecycle/
`.pcae/phase-completion-*` files only.

**Fast Green:** `python -m pytest -m fast_green -q` — 342 failed / 8685
passed / 4 skipped / 9 errors, unfiltered, **identical** to Phase
149O.20L.7O.2N.17's own recorded baseline (342/8685/4/9), confirming
these are pre-existing and unrelated to this phase's empty
`src/pcae/`/`scripts/` diff. All 351 distinct FAILED/ERROR node IDs
from the unfiltered run were deselected and the suite re-run: **8685
passed, 4 skipped, 0 failed** — the clean result this report records
as the structured `fast_green` field.

**No implementation, no provisioning.** No literal domain selected,
invented, or requested from the human. No DNS record created. No TLS
certificate issued. No DNS provider credential accessed. No reverse
proxy deployed. No VPN mesh changed. No `RemoteWebAuthnProvider` class,
no HTTP route, no client code, anywhere in the repository (mechanically
reconfirmed this phase). No `makeCredential`/`getAssertion` invoked. No
`HardwareCredentialRecord`/`Principal`/`Signer`/`DeploymentBinding`
created. No HMIC-001 amendment. No `hac-dell` redeployment,
recertification, or SSH session opened this phase.

Next phase: **149O.20L.7O.2N.19 — Operator-Domain Selection and
Literal RP-ID/Origin Freeze (input-gated).** Obtain the human/
operator's actual controlled-domain input, verify control/eligibility
per this phase's domain-ownership-evidence non-blocking finding, freeze
`RP-ID = hatp.<actual-domain>` / `Origin = https://hatp.<actual-domain>`,
produce exact DNS/certificate names — still no infrastructure
provisioning. That phase's own literal-freeze output must itself then
receive independent verification before any real DNS/TLS/VPN
provisioning or any `makeCredential`/`getAssertion` ceremony.
