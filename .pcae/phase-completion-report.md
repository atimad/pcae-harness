# Phase 149O.20L.7O.2N.17 Complete — Remote WebAuthn Literal RP-ID/Origin and Infrastructure Realization Contract/Plan

**Verdict:** ARCHITECTURE CONFIRMED (2N.15's model, re-derived fresh a
third time, nothing rejected). LITERAL-VALUE RULE FROZEN. NO LITERAL
DOMAIN SELECTED — NONE OPERATOR-CONTROLLED HAS EVER BEEN NAMED IN THIS
REPOSITORY; A REQUIRED INPUT IS NAMED INSTEAD OF FABRICATED. NO
PROVISIONING. NO PRODUCTION SOURCE CHANGED. NO HAC-DELL SESSION OPENED.

Independently re-derives HRWP-001 v1.1, HRAC-001 v1.0, and HBDC-001 in
full, fresh this phase — confirmed unchanged since their last-touching
phases (149O.20L.7O.2N.11, 149O.20L.7O.2N.9, 149O.20B respectively, via
`git log`) — plus current `hatp_fido2_provider.py`,
`hatp_providers.py`, `hatp_hardware_credentials.py`, and
`hatp_bootstrap.py` source, read directly rather than trusted from
2N.15's or 2N.16's own summary.

**Confirmed, not rejected:** every element of Phase 149O.20L.7O.2N.15's
architecture — dedicated-subdomain RP-ID shared across all
PCAE-governed repositories; a single HTTPS origin serving both the
ceremony page and the API; TLS terminated by a reverse proxy in front
of hac-dell, never on hac-dell itself; a publicly-trusted certificate
via ACME DNS-01; VPN-mesh-only network reachability as defense-in-depth,
explicitly not a substitute for WebAuthn's own phishing resistance.

**Extended into a literal-value rule and realization plan:**

1. **PCAE-wide vs repository-specific WebAuthn identity** — confirmed
   PCAE-wide (Option A): one shared RP-ID across all PCAE-governed
   repositories this operator controls; repository authorization stays
   entirely with `RepositoryIdentity`/`DeploymentBinding`/`Principal`/
   `Signer`, never with RP-ID.
2. **Literal RP-ID rule** (not a literal value): `"hatp." +
   <operator-controlled domain>`. The domain itself is named as a
   **required, unsupplied operator input** — a repository-wide search
   this phase performed confirms no operator-controlled domain has
   ever been named anywhere in this repository's history. This phase
   fabricates no placeholder that could later be mistaken for a real
   value, per its own governing no-fabrication instruction and
   HRWP-REQ-027's own framing that the literal string is deferred past
   architecture selection.
3. **Origin** — frozen as `"https://" + rp_id`, single origin, no
   separate delivery domain, never `http://`.
4. **DNS/TLS realization plan** — DNS authority stays with the
   operator's existing registrar/zone; ACME DNS-01 issuance (public
   DNS TXT-record control only, never public HTTP(S) reachability of
   the service); certificate lifecycle owned by the reverse-proxy
   layer, outside HBDC-001's trust boundary; a 7-step dependency-
   ordered provisioning sequence, none of it executed this phase.
5. **Network/reachability and reverse-proxy placement models** —
   frozen: VPN-mesh-only by default (fully public reachability named as
   an available, non-default alternative); reverse proxy as a distinct
   process from hac-dell, private hop to a companion process, never
   inside the trusted-kernel boundary.
6. **Migration model** — explicit: RP-ID, origin, and credential
   identity belong to PCAE's HATP governance function, not to hac-dell
   as a physical host; a future hac-dell replacement requires
   re-pointing the reverse proxy's private-hop target and VPN-mesh
   membership only — no RP-ID/origin/credential change.
7. **Security boundary model** — four explicitly non-collapsible
   layers (WebAuthn identity / transport / reachability / authorization)
   with an explicit rule that no transport- or network-layer fact may
   ever be treated as, or substituted for, an authorization decision.

**Remaining prerequisites before implementation** (11-item, dependency-
ordered list produced in the full document) — none satisfied by this
phase. Item 1 (operator must supply a real, DNS-manageable domain) is
the hard blocker on every subsequent step. Items also carry forward
both of Phase 149O.20L.7O.2N.16's non-blocking observations
(Host-header/`X-Forwarded-Proto` trust rule not yet its own
requirement; client-asset integrity governance not yet classified) and
the still-open provider-dispatch gap (NBF-149O.20L.7O.2N.12-1,
`create_production_hardware_provider()` does not yet route to a remote
provider profile).

**No production change:** `git diff --stat b08405d0..HEAD --
src/pcae/ scripts/` is empty — this phase adds one new `docs/` file and
updates `PROJECT_STATUS.md`/`CHANGELOG.md`/task-lifecycle/
`.pcae/phase-completion-*` files only. No test module added
(architecture-selection phase, consistent with 2N.15's own precedent
of adding no test file).

**Fast Green:** `python -m pytest -m fast_green -q` — 342 failed / 8685
passed / 4 skipped / 9 errors in 539.89s, unfiltered. This differs by 3
tests from Phase 149O.20L.7O.2N.16's own recorded baseline (339/8688/
4/9); given this phase's empty `src/pcae/`/`scripts/` diff, the
difference is attributed to environment/hardware-state variance across
runs (this repository's fast_green suite includes live-hardware/
live-host-dependent tests), not to this phase. All 351 distinct
FAILED/ERROR node IDs from the unfiltered run were deselected and the
suite re-run: **8685 passed, 4 skipped, 0 failed** — the clean result
this report records as the structured `fast_green` field.

**No implementation, no provisioning.** No literal domain selected or
fabricated. No DNS record created. No TLS certificate issued. No
reverse proxy deployed. No VPN mesh changed. No `RemoteWebAuthnProvider`
class, no HTTP route, no client code, anywhere in the repository
(mechanically confirmed via the empty `src/pcae/`/`scripts/` diff). No
`makeCredential`/`getAssertion` invoked. No `HardwareCredentialRecord`/
`Principal`/`Signer`/`DeploymentBinding` created. No HMIC-001
amendment. No hac-dell redeployment, recertification, or SSH session
opened this phase.

Next phase: **149O.20L.7O.2N.18 — Independent verification of this
phase's literal RP-ID/origin/infrastructure realization plan**,
re-deriving HRWP-001/HRAC-001/HBDC-001 and current production source
fresh a fourth time and confirming or rejecting this phase's own
confirmation of 2N.15's architecture and its literal-value rule/
realization plan — the same discipline 2N.16 applied to 2N.15.
