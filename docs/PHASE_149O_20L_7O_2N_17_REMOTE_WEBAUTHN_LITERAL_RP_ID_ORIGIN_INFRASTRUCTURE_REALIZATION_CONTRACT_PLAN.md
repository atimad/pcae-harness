# Phase 149O.20L.7O.2N.17 — Remote WebAuthn Literal RP-ID / Origin and Infrastructure Realization Contract/Plan

**Status:** COMPLETE — ARCHITECTURE CONFIRMATION AND REALIZATION-PLANNING ONLY. NO DOMAIN SELECTED (NONE OPERATOR-CONTROLLED EXISTS YET — REQUIRED INPUT NAMED, NOT FABRICATED). NO DNS PROVISIONED. NO TLS CERTIFICATE ISSUED. NO REVERSE PROXY CONFIGURED. NO VPN CHANGE. NO `RemoteWebAuthnProvider` CODE. NO SERVER ENDPOINT IMPLEMENTED. NO CLIENT IMPLEMENTED. NO CREDENTIAL CREATED. NO `HardwareCredentialRecord`/`Principal`/`Signer`/`DeploymentBinding` CREATED. NO HMIC CHANGE. NO HAC-DELL REDEPLOYMENT. NO PRODUCTION SOURCE MODIFIED.

## 0. Purpose and relationship to 2N.15 / 2N.16

Phase 149O.20L.7O.2N.15 selected the *model* for RP-ID/origin/HTTPS infrastructure (dedicated real-domain subdomain, single shared origin, reverse-proxy TLS termination, ACME DNS-01 certificate, VPN-mesh-only reachability); Phase 149O.20L.7O.2N.16 independently re-derived and confirmed it with no blocking defect (two non-blocking observations, §7 below). This phase's governing prompt requires that model be **re-derived fresh from primary contracts, independently, a third time** in this phase — not restated from either prior phase's own report — and asks it be either confirmed or rejected, then carried one step further into a literal-value **rule** (not a literal value itself, since no operator-controlled domain exists) and an infrastructure **realization plan** (the ordered set of provisioning steps a future phase would execute, not executed here).

## 1. Independent source re-derivation performed this phase

Read fresh this phase, not from 2N.15's or 2N.16's own prose:

- `docs/contracts/HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md` (HRWP-001 v1.1) — confirmed unchanged since Phase 149O.20L.7O.2N.11 (`git log --oneline -- docs/contracts/HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md`, last touch `2b8f5d74`). HRWP-REQ-027/028 (stable, non-`localhost`, non-raw-IP, non-per-session, real-domain-form RP ID); HRWP-REQ-029 (exactly `https://<RP-ID-matching host>`, no `http://`, no wildcard, no caller-derived origin); HRWP-REQ-030 (fixed server-side literal comparison, never request-derived); HRWP-REQ-031 (DNS name / TLS certificate / TLS-terminating endpoint left as explicit open decisions for an infrastructure-selection phase); HRWP-REQ-032 (one stable origin, platform-neutral); HRWP-REQ-062 (thin-adapter/trusted-kernel boundary) all re-read in full text, not summary.
- `docs/contracts/HATP_REMOTE_ASSERTION_CEREMONY_CONTRACT.md` (HRAC-001 v1.0) — confirmed unchanged since Phase 149O.20L.7O.2N.9 (`0b881b8f`). HRAC-REQ-061 (ceremony-delivery page served from the identical HRWP-001 origin — no separate delivery domain); HRAC-REQ-062 (single fixed `expected_rp_id`/allowed-origin, no new infrastructure dependency beyond HRWP-001's own); HRAC-REQ-070 (thin-adapter classification for the transport layer) re-read in full.
- `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` (HBDC-001) — confirmed unchanged since Phase 149O.20B (`66c97470`). Independently re-grepped for `network`/`VPN`/`DNS`/`topology`/`TLS`: no requirement text constrains network reachability, DNS, or TLS topology. HBDC-001 governs host-level trust (OS-principal separation, Protected Root ownership, HMIC-scoped execution-environment lock) — orthogonal to this phase's questions, confirmed independently rather than taken on 2N.15's word.
- `src/pcae/core/hatp_fido2_provider.py` — `_HATP_RP_ID = "hatp.pcae.local"`, `_HATP_ORIGIN = "pcae-hatp://hatp.pcae.local"` (lines 102–104) confirmed still present, unchanged, and confirmed still local-provider-only (not reachable or reusable by a remote provider — 2N.15 §3.4/§10's finding re-confirmed against current source, not restated).
- `src/pcae/core/hatp_providers.py` — `_PRODUCTION_HARDWARE_PROVIDER_PROFILES = (HATP_HARDWARE_PROVIDER_V1,)` (line 187) confirmed still does not include `HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN`; the post-allowlist branch still attempts `Fido2HardwareProvider` unconditionally. `create_production_hardware_provider()`'s dispatch gap (NBF-149O.20L.7O.2N.12-1) remains open, unresolved, unaddressed by this phase — confirmed by re-reading the current file, not by trusting the prior phase's claim that it remained open.
- `src/pcae/core/hatp_hardware_credentials.py` — `_PROTOCOL_VALUES = frozenset({"FIDO2", "PIV", "WEBAUTHN"})` (line 62) confirmed still includes `"WEBAUTHN"`.
- `src/pcae/core/hatp_bootstrap.py` — `SignerRecord`/`DeploymentBinding` schemas (principal_id/signer_key_id/provider_profile keying, one active binding per repository) confirmed unchanged, matching HRWP-001 §6/§32-33 and HRAC-001 §9-10 exactly.
- `git log --oneline -- docs/contracts/HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md docs/contracts/HATP_REMOTE_ASSERTION_CEREMONY_CONTRACT.md docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` — no commit since 2N.11/2N.9/20B touches any of the three contracts; nothing this phase re-derives from stale text.
- Repository-wide search for any previously-named literal, operator-controlled domain (`grep -rn "controlled-domain\|<domain>\|example-domain"` and a scan for any `.com`/`.net`/`.org`/`.dev`/`.io`-form literal anywhere under `docs/PHASE_149O_20L_7O_2N_1*`): **none found**. No operator-controlled domain has ever been named anywhere in this repository's history. This is the load-bearing fact behind §3 below.

## 2. Confirmation or rejection of the 2N.15 model

**Confirmed, not rejected, on independent re-derivation.** Re-checking each element against the primary contract text read fresh in §1 (not against 2N.15's or 2N.16's summary of it):

| 2N.15 element | Independent re-check this phase | Verdict |
|---|---|---|
| Dedicated subdomain RP-ID, shared across all PCAE-governed repositories | WebAuthn RP-ID scoping (registrable-domain-suffix matching) means the bare organization domain would over-scope (any subdomain ever hosted under it becomes credential-eligible); a dedicated subdomain (e.g. `hatp.<domain>`) narrows this to exactly the one authority, matching HBDC-REQ-072's own "narrowest value that names exactly the one authority" discipline applied elsewhere in this repository. Per-repository RP-IDs would multiply enrollment ceremonies with no security benefit, since `repository_id` is already independently re-resolved live at both request-creation and verification time (HRAC-REQ-017/033) — RP-ID is not the layer that needs to carry repository identity. | **Confirmed** |
| Exactly one HTTPS origin, ceremony page + API colocated | HRAC-REQ-061 forbids a separate delivery domain; HRWP-REQ-029 forbids `http://`, wildcards, and caller-derived origins. There is no contract-conformant alternative shape. | **Confirmed** |
| TLS terminated by a reverse proxy in front of hac-dell, not hac-dell itself | HBDC-001 (re-grepped fresh, §1) already invests specifically in isolating hac-dell's attack surface (OS-principal separation, Protected Root, execution-environment lock); terminating public-facing TLS/HTTP parsing directly on that host would expand exactly the surface HBDC-001 works to narrow. HRWP-REQ-062/HRAC-REQ-070's "thin, replaceable adapter, no independent trust" classification fits a reverse proxy, not hac-dell itself. | **Confirmed** |
| Publicly-trusted certificate via ACME DNS-01 | DNS-01 proves domain control via a DNS TXT record, never by exposing an HTTP server publicly — this is the only issuance method compatible with "public trust store acceptance on Mac and iPhone with zero manual per-device trust configuration" (satisfying HRWP-REQ-031's client-compatibility framing) *and* "listener never reachable from the open internet" simultaneously. HTTP-01 would require a public-facing HTTP listener, contradicting the VPN-mesh-only reachability decision below. Self-signed/private CA would require a manual, per-device trust-store ceremony on the iPhone with no revocation/rotation governance in this repository today. | **Confirmed** |
| VPN-mesh-only network reachability, explicitly not a phishing-resistance substitute | HRAC-REQ-061's phishing-boundary discipline lives entirely in browser-enforced origin/RP-ID matching (WebAuthn's own built-in defense) — restricting network *reachability* changes who can even attempt to reach the ceremony page, not what origin the browser will accept; it does not touch, weaken, or duplicate the cryptographic check. This is additive defense-in-depth (reduces the population that can probe the companion process's HTTP-parsing surface at all), consistent with this repository's general fail-closed/defense-in-depth discipline (HRWP-REQ-034). | **Confirmed** |

No element of the 2N.15 model is rejected. Nothing in HRWP-001 v1.1, HRAC-001 v1.0, or HBDC-001, read fresh, contradicts it.

## 3. Domain/hostname ownership model and literal RP-ID rule

**No literal domain is selected by this phase.** §1's repository-wide search confirms no operator-controlled domain has ever been named in this repository. Fabricating one (e.g. inventing a placeholder that could later be mistaken for a real, provisioned value) would violate this phase's own governing instruction ("Do not invent a domain that is not controlled by the operator... define the required input and stop before fabrication") and HRWP-REQ-027's requirement that the RP-ID be genuinely operator-controlled, not a stand-in.

**Required input, named explicitly, not resolved by this phase:**

> The operator must identify one real, currently-registered, DNS-manageable domain they control (registrar account access and DNS-zone-edit access, at minimum sufficient to create a TXT record for ACME DNS-01 issuance and a subdomain delegation or A/AAAA/CNAME record for the RP-ID host). This is a fact about the operator's existing domain holdings, not an architectural decision this phase can make on the operator's behalf.

**Frozen rule for the literal value, once that input is supplied** (this is the literal-RP-ID *requirements* output, distinct from a literal string):

1. `rp_id = "hatp." + <operator-controlled registrable domain>` — a dedicated subdomain, not the bare domain (§2 row 1; e.g. if the operator controls `example.tld`, the RP-ID is `hatp.example.tld`, never `example.tld` itself).
2. MUST NOT be `localhost`, a raw IP literal, or any per-session/generated value (HRWP-REQ-028).
3. MUST be resolvable via public DNS (a required property for ACME DNS-01 issuance — §5 below — independent of whether the *application* is publicly reachable, §6).
4. MUST NOT be derived from, or tied to, `hac-dell`'s current hostname or any physical-machine identity (§6's migration model — the identity belongs to PCAE's HATP governance function, not to any one host).
5. MUST be a label the operator can commit to as long-term-stable: rotating the RP-ID later is not a configuration change but a full re-enrollment event for every `HardwareCredentialRecord` bound to it (WebAuthn credentials are scoped to the RP-ID at creation time and do not migrate across a changed RP-ID).
6. The dedicated-subdomain label (`hatp`) itself is a naming *convention* this phase recommends for clarity, not a hard requirement; the hard requirement is "a dedicated subdomain distinct from the bare organization domain and from any other service's subdomain," per §2 row 1's reasoning — an operator may pick a different label as long as that property holds.

This phase stops here on the literal value, per its own governing no-fabrication instruction, and per HRWP-REQ-027's own framing (the literal string is explicitly deferred to an implementation-adjacent phase, not to architecture selection).

## 4. Origin — frozen

`origin = "https://" + rp_id` (§3), no port suffix in the common case, no separate delivery origin (HRAC-REQ-061), never `http://` (HRWP-REQ-029's secure-context requirement), never wildcarded or request-derived (HRWP-REQ-029/030). One origin serves both the ceremony-delivery page and the HRAC-001 request/challenge/verification API, identically for Mac and iPhone clients (HRWP-REQ-032/HRAC-REQ-059 — WebAuthn origin/RP-ID matching is platform-neutral by specification, no PCAE-side per-platform branching).

## 5. DNS / TLS realization plan (architecture and ordering — not executed)

Architecture only; no step below is performed by this phase.

1. **DNS authority**: remains with the operator's existing registrar/DNS-zone provider for the controlled domain named in §3's required input. This phase does not propose PCAE take over DNS authority for the parent domain — only that a subdomain delegation or record be created for the RP-ID host.
2. **Certificate issuance method**: ACME DNS-01 challenge against a public, publicly-trusted CA (e.g. Let's Encrypt or an equivalent ACME-compatible CA — this phase does not select a literal CA product). DNS-01 requires only a short-lived DNS TXT record write during issuance/renewal; it requires no public HTTP(S) reachability of the RP-ID host itself, which is the property that reconciles a publicly-trusted certificate with VPN-mesh-only reachability (§6).
3. **Certificate lifecycle ownership**: held entirely by the reverse-proxy layer's ACME client (§7's "thin adapter" classification, unchanged from 2N.15) — never by hac-dell itself, and never inside the HBDC-001 Protected-Root/OS-principal trust boundary. Automatic renewal via the same DNS-01 mechanism is the expected steady state; this phase does not select a literal renewal cadence beyond "before expiry, automated, no manual per-renewal ceremony."
4. **Public DNS existing while the service stays private**: yes, by design (§2 row 4/§6) — the DNS A/AAAA/CNAME record for the RP-ID host may point at a private-network or VPN-mesh-internal address (or simply not resolve to a publicly-reachable IP at all, if the reverse proxy's public-facing listener is bound only to the VPN-mesh interface); this does not weaken the DNS-01 issuance path, which only ever needs the TXT record, not the A/AAAA record, to be publicly visible.
5. **Sequencing relative to reverse-proxy/VPN provisioning** (ordering only, not execution): (a) operator supplies §3's required domain input; (b) subdomain DNS record(s) created; (c) VPN mesh established (§6) joining hac-dell's network segment, the operator's Mac, and iPhone; (d) reverse proxy deployed, bound to the VPN-mesh-internal interface for its public-facing listener; (e) ACME DNS-01 client configured on the reverse-proxy host, first certificate issued; (f) companion HTTP process (HRAC-001 §7-§29's trusted-kernel logic) implemented and deployed behind the reverse proxy's private hop; (g) provider-dispatch gap (NBF-149O.20L.7O.2N.12-1) resolved so `create_production_hardware_provider()` can route to a remote provider at all. None of (a)-(g) is performed by this phase.

## 6. Network / reachability model — frozen

VPN-mesh-only reachability (e.g. a WireGuard-based mesh, product unselected — this phase names the model, not a literal product) joining hac-dell's network segment, the operator's Mac, and iPhone. The reverse proxy's public-facing listener binds only to the mesh interface, never to a raw public-internet-facing interface. This is explicit defense-in-depth, not a substitute for or weakening of WebAuthn's own origin/RP-ID cryptographic phishing resistance (§2 row 5) — restated per HRAC-REQ-061's own caution that no alternate-origin scheme may weaken WebAuthn's phishing resistance; VPN gating restricts *reachability*, never *origin*, and introduces no second/alternate origin.

**Named alternative, not selected as default** (unchanged from 2N.15 §5.4, re-confirmed): fully public reachability without a VPN gate remains architecturally valid under this same RP-ID/origin/certificate model, since WebAuthn's security does not depend on network-layer restriction. An operator prioritizing "reachable without a VPN client installed" over "minimize internet-facing attack surface" may choose it without violating HRWP-001/HRAC-001. Not recommended as default for this repository's threat model (a narrow, high-value governance-signing ceremony).

## 7. Reverse-proxy placement model — frozen

The reverse proxy is a distinct process/host from hac-dell (co-located on the same physical machine is permitted; the isolation that matters is process/privilege separation, not physical separation), terminating TLS for the fixed origin (§4) and forwarding over a private hop (localhost, a private network segment, or a VPN-mesh-internal address — literal choice deferred to implementation) to a companion HTTP process that implements HRAC-001 §7-§29. The reverse proxy never holds `HardwareCredentialRecord`/`DeploymentBinding`/`SignerRecord` state and is never inside the trusted-kernel boundary (§8) — it relays TLS-terminated bytes only.

**Carried forward from 2N.16's non-blocking findings, not yet resolved, named again here so this phase's own "remaining prerequisites" output is complete:**
- NBF-149O.20L.7O.2N.16-1: the reverse-proxy/companion-process boundary's `Host` header and `X-Forwarded-Proto` (or `Forwarded`) trust rule is not yet stated as its own explicit, testable requirement anywhere in HRWP-001/HRAC-001/2N.15/2N.16 — correctly implied by the existing "fixed server configuration, never request-derived" discipline (HRWP-REQ-030/033) but not yet a named requirement sentence. This phase confirms it remains open; resolving it is recommended for the phase that first writes real companion-process/reverse-proxy configuration, not this one.
- NBF-149O.20L.7O.2N.16-2: static client-asset (ceremony-page HTML/JS) integrity governance remains an open classification question, correctly deferred to the phase that first implements the ceremony-delivery page.

## 8. Migration / future-hosting model — frozen

If hac-dell (`Old`) is ever replaced by different physical or virtual infrastructure (`New`), the replacement MUST preserve, unchanged, from the operator's/client's perspective:

- **RP-ID** (§3) — a WebAuthn credential is cryptographically bound to the RP-ID it was created under; changing it invalidates every enrolled credential and forces full re-enrollment. The RP-ID therefore MUST NOT be derived from, or coupled to, `hac-dell`'s hostname, IP address, or any other physical-machine-specific identifier (§3 rule 4, restated as a migration constraint).
- **Origin** (§4) — likewise fixed independent of which physical host currently answers behind the reverse proxy; the reverse-proxy/DNS layer is precisely the indirection that makes this possible (the DNS record, not the WebAuthn credential, is what gets repointed at migration time).
- **Credential identity** (`HardwareCredentialRecord`/`SignerRecord`/`Principal`) — governed entirely by HATP's existing enrollment/trust model (HPSE-001/HHCE-001), unaffected by which physical host runs the companion process; migration changes *where the verifier executes*, never *which credentials it trusts*.
- **The WebAuthn trust relationship** — belongs to PCAE's HATP governance function as an abstraction, not to `hac-dell` as a physical machine. This phase's entire RP-ID/origin selection (§3-§4) is deliberately host-independent for exactly this reason: `hac-dell` today is the trusted-kernel host per HBDC-001, but HBDC-001 itself governs *host-level trust properties* (OS-principal separation, Protected Root), not *which literal host* holds them — a future replacement host that independently satisfies HBDC-001's own requirements could take over the trusted-kernel role without any RP-ID/origin/credential change, provided the DNS/reverse-proxy layer is repointed at it.

Concretely: migrating hac-dell to replacement infrastructure requires re-pointing the reverse proxy's private-hop target (§7) and, if the new host's network position differs, updating VPN-mesh membership (§6) — neither requires touching DNS-01 certificate issuance (§5), the RP-ID/origin values (§3-§4), or any enrolled credential.

## 9. Security boundary model — frozen (confirmed unchanged from 2N.15 §7, re-derived not restated)

Four independently-named layers, explicitly not collapsible into one another:

- **WebAuthn identity** (RP-ID §3, origin §4, credential — HRWP-001/HRAC-001, unmodified by this phase): the cryptographic identity the browser and authenticator reason about. This is the *only* layer WebAuthn's own phishing/replay resistance depends on.
- **Transport** (TLS certificate §5, reverse proxy §7): carries bytes, terminates encryption, never independently trusted — a compromised reverse proxy can deny service or corrupt/drop traffic but cannot itself forge a valid WebAuthn assertion (it never holds a private key or `HardwareCredentialRecord`) and cannot, by construction, read Protected Root state.
- **Reachability** (VPN mesh §6): grants network *path*, never authority — mirrors HRAC-REQ-027's "possessing a session locator is not authority" restated at the network layer; a peer on the VPN mesh gains the ability to *attempt* to reach the ceremony page, nothing more.
- **Authorization** (`RepositoryIdentity`, `DeploymentBinding`, `Principal`, `SignerRecord`, governance decisions — HATP's existing model, confirmed unchanged at `hatp_bootstrap.py`, §1): the only layer that determines whether a given assertion, once cryptographically valid, actually authorizes a governed operation. Re-resolved live at both request-creation and verification time (HRAC-REQ-017/033), independent of RP-ID/origin/transport/reachability.

**Explicit non-collapse rule, restated as this phase's own frozen output:** no transport-layer or network-layer fact (which reverse proxy terminated TLS, which VPN peer reached the ceremony page, which DNS record resolved) may ever be treated as, or substituted for, an authorization decision. Authorization is decided exclusively by the fourth layer, re-resolved live, never inferred from which lower layer successfully delivered the request.

## 10. Remaining prerequisites before implementation (this phase's own required output)

In dependency order, none satisfied by this phase:

1. **Operator input (§3)**: name one real, currently-registered, DNS-manageable domain the operator controls. Blocks every subsequent step.
2. Literal RP-ID/origin values selected by applying §3's frozen rule to the domain named in (1) — a short, mechanical step once (1) is satisfied, not requiring further architecture work.
3. DNS subdomain record(s) created for the RP-ID host (§5 step b).
4. VPN mesh established, joining hac-dell, Mac, iPhone (§5 step c / §6).
5. Reverse proxy deployed, bound to the mesh interface (§5 step d / §7).
6. ACME DNS-01 client configured, first certificate issued (§5 step e).
7. Companion HTTP process implementing HRAC-001 §7-§29 designed and implemented (§5 step f) — this is the first phase in this sequence that touches `src/pcae/**` or introduces a new trusted-kernel component.
8. `create_production_hardware_provider()` dispatch gap (NBF-149O.20L.7O.2N.12-1) resolved so a remote provider profile actually routes (§5 step g) — independently blocking, orthogonal to (1)-(7).
9. Host-header/`X-Forwarded-Proto` trust rule (NBF-149O.20L.7O.2N.16-1) stated as an explicit requirement before the companion process (7) is implemented.
10. Client-asset integrity classification (NBF-149O.20L.7O.2N.16-2) resolved at the same phase that first implements the ceremony-delivery page.
11. HMIC-001 source-scope impact assessment for the new companion-process/verifier/state-manager components introduced by (7), per HRWP-REQ-066/HRAC-REQ-074's own fixed implementation-sequence ordering (restated from 2N.15 §14, unmodified).

Recommended next phase, per this phase's own governing prompt: **149O.20L.7O.2N.18 — Independent verification of this phase's literal RP-ID/origin/infrastructure realization plan** (verifies §1-§10 above fresh, the same discipline 2N.16 applied to 2N.15).

## 11. No-Go confirmation

No hardware touched. No `makeCredential`/`getAssertion` executed. No credential, `HardwareCredentialRecord`, `Principal`, `Signer`, or `DeploymentBinding` created. No DNS record created. No TLS certificate requested or issued. No reverse proxy deployed or configured. No VPN mesh change. No `RemoteWebAuthnProvider` implemented. No HTTP server/endpoint implemented. No client (browser/mobile) code implemented. No HMIC change. No hac-dell mutation or redeployment (no SSH session opened this phase). No production source under `src/pcae/**` modified — `git status --short` after this phase confirms only this document plus `PROJECT_STATUS.md`/`CHANGELOG.md`/`.pcae/**`/task-lifecycle files change. No literal domain fabricated (§3).

## 12. Decision summary

| Question | Decision | Notes |
|---|---|---|
| PCAE-wide vs repository-specific WebAuthn identity | PCAE-wide (shared RP-ID across all PCAE-governed repositories this operator controls); repository authorization stays with `RepositoryIdentity`/`DeploymentBinding`/`Principal`/`Signer` | §2 row 1, §3 |
| RP-ID literal rule | `"hatp." + <operator-controlled domain>`, domain itself a required, unsupplied input | §3 |
| Origin | `https://<rp_id>`, single origin, no port in common case | §4 |
| DNS authority | Operator's existing registrar/zone for the parent domain; PCAE does not take over parent-domain DNS | §5.1 |
| Certificate issuance | ACME DNS-01, public CA | §5.2 |
| Certificate lifecycle | Owned by reverse-proxy layer, outside HBDC-001 trust boundary, automated renewal | §5.3 |
| Network reachability | VPN-mesh-only (default); fully public named as available, non-default alternative | §6 |
| Reverse-proxy placement | Distinct process from hac-dell; private hop to companion process; never trusted-kernel | §7 |
| Migration model | RP-ID/origin/credential identity belong to PCAE's HATP function, not to hac-dell as a physical host | §8 |
| Security boundary | Four non-collapsible layers: WebAuthn identity, transport, reachability, authorization | §9 |
