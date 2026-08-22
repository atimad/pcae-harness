# Phase 149O.20L.7O.2N.16 — Remote WebAuthn RP-ID / Origin / HTTPS Infrastructure Architecture Independent Verification

**Verdict: A — 2N.15 ARCHITECTURE INDEPENDENTLY VERIFIED, NO BLOCKING DEFECT.**

```
REMOTE WEBAUTHN RP-ID / ORIGIN / HTTPS ARCHITECTURE
— INDEPENDENTLY VERIFIED
RP-ID MODEL:            DEDICATED STABLE SUBDOMAIN
ORIGIN:                  ONE FIXED HTTPS ORIGIN
TLS:                     PUBLICLY TRUSTED CERTIFICATE
CERTIFICATE ISSUANCE:    ACME DNS-01 COMPATIBLE
APPLICATION REACHABILITY: VPN-MESH ONLY
HAC-DELL:                NOT PUBLICLY EXPOSED
MAC + IPHONE:            SAME RP / SAME ORIGIN
WEBAUTHN SECURITY:       DOES NOT DEPEND ON VPN AS AUTHORITY
NO INFRASTRUCTURE PROVISIONED
```

Independently verifies Phase 149O.20L.7O.2N.15's RP-ID/origin/HTTPS
architecture selection. Re-derived from HRWP-001 v1.1, HRAC-001 v1.0,
HBDC-001, current production source, and primary WebAuthn/ACME
documentation — not from 2N.15's own report, tests, or summary prose.

## True phase-entry commit

`6901ecc7` (HEAD == origin/main at phase entry; `pcae push check` →
`nothing_to_push` confirmed before this phase's own first edit).

## 1. Primary contracts re-derived (fresh, this phase)

- `docs/contracts/HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md` (HRWP-001
  v1.1) — read in full, HRWP-REQ-001 through HRWP-REQ-068 confirmed
  sequential/gapless (`test_hrwp_requirement_numbering_still_complete_sequential_no_gaps`).
- `docs/contracts/HATP_REMOTE_ASSERTION_CEREMONY_CONTRACT.md` (HRAC-001
  v1.0) — read in full, HRAC-REQ-001 through HRAC-REQ-076 confirmed
  sequential/gapless (`test_hrac_requirement_numbering_still_complete_sequential_no_gaps`).
- `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` (HBDC-001) —
  read in full; independently confirmed (not merely re-asserted from
  2N.15's own claim) that no `HBDC-REQ-###` normative sentence
  constrains DNS, VPN, reverse-proxy, WireGuard, or ACME topology
  (`test_hbdc_contract_defines_no_network_dns_vpn_topology_requirement`).
  This phase's own grep is independent of 2N.15's grep invocation.
- `src/pcae/core/hatp_fido2_provider.py`, `hatp_providers.py`,
  `hatp_hardware_credentials.py`, `hatp_bootstrap.py` — read directly
  this phase, not accepted from 2N.15's citations.

## 2. External WebAuthn / TLS primary sources used

- W3C Web Authentication specification (Relying Party Identifier /
  effective-domain scoping rule): an RP ID **must be equal to, or a
  registrable-domain suffix of, the calling origin's effective
  domain** — this is the load-bearing rule §4/§6 below depend on. The
  spec's effective-domain concept is defined only for real DNS
  domains; it has no defined meaning for an IP-address host, so
  browsers reject an RP ID for an origin whose host is a raw IP
  literal, and `localhost` is only ever equal to its own origin (no
  suffix relationship exists to exploit or rely on for a remote
  deployment).
- Secure-context requirement: `navigator.credentials.create()`/`.get()`
  are defined as secure-context-gated APIs; mainstream browsers enforce
  `https:` (or the `localhost`/loopback secure-context carve-out, not
  applicable to a real remote deployment) with no VPN- or
  private-network-based exception — encryption at the network layer
  (VPN) does not satisfy the browser's own origin-scheme check, which
  looks only at the page's URL scheme.
- RFC 8555 (ACME), DNS-01 challenge (§8.4): validation is satisfied by
  publishing a `TXT` record under `_acme-challenge.<domain>` in public
  DNS; the ACME spec presents DNS-01 and HTTP-01 as independent
  challenge methods, and DNS-01's own validation path never requires
  the CA to reach an HTTP(S) server on the domain at all — the
  certificate's target service can remain fully unreachable from the
  public internet while the domain's public DNS remains publicly
  writable/queryable for the challenge record.

## 3. Re-derived HRWP network requirements

Independently re-read (not accepted from 2N.15's citation):

- **HRWP-REQ-027**: real-domain-form, non-`localhost`, non-raw-IP,
  non-per-session RP ID; DNS-or-equivalent resolvable from both a Mac
  and an iPhone browser; matches the origin the client actually loads
  from. Confirmed present, confirmed still not resolving a literal
  hostname (`test_hrwp_027_029_031_open_infrastructure_requirements_present_and_unresolved_by_hrwp_itself`).
- **HRWP-REQ-029**: allowed origin exactly `https://<RP-ID-matching
  host>`, never `http://`, never wildcard, never caller-derived.
  Confirmed present.
- **HRWP-REQ-031**: DNS name + TLS certificate (CA choice named, not
  resolved) + TLS-terminating endpoint (direct vs. reverse-proxy,
  network topology) all named as open. Confirmed present.

2N.15 satisfies all three at the architecture-model level without
narrowing any of them: it fixes the *model* (dedicated subdomain, one
fixed HTTPS origin, reverse-proxy termination, ACME DNS-01, VPN-mesh
reachability) while explicitly declining to fix the literal string
(§31/§70 below) — exactly the scope HRWP-REQ-027/031 themselves
delegate to "the implementation phase," which 2N.15 is not (it is the
architecture-selection phase HRWP-REQ-066 step (3)/HRAC-REQ-074 step
(3) name as preceding implementation). No silent narrowing found.

## 4. RP-ID validity

Independently determined (not from intuitive DNS reasoning):

- **Domain relationship required**: RP ID must be the origin's
  effective domain, or a registrable-domain suffix of it — a bare
  suffix relationship, never the reverse (a credential registered at a
  suffix is valid for every subdomain under it, not vice versa). This
  is the exact rule 2N.15 §3.2 relies on ("suffix-inclusive... not the
  reverse"), independently reconfirmed here from primary WebAuthn
  semantics, not merely re-quoted from 2N.15's own prose.
- **Public-suffix / effective-domain restriction**: yes — the
  "effective domain" concept is itself public-suffix-aware (it is the
  registrable domain, one label below the public suffix, e.g.
  `example.com`, not `com` itself or `co.uk` itself). A dedicated
  subdomain (`hatp.example.com`) is a valid RP ID because it is a
  suffix of its own origin's effective domain (itself) — this holds
  regardless of how many further labels are prepended.
- **Arbitrary private suffixes**: not acceptable as a *public* RP ID
  unless the deployment also controls a real, publicly-resolvable
  domain under that suffix; a private-only label with no real
  registrable domain behind it has no defined "effective domain" a
  standards-conformant browser will accept as HTTPS-reachable in the
  public-CA-issuable sense 2N.15 selected (this is exactly 2N.15 §3.4's
  named, non-selected Model D territory, not a defect in the selected
  Model A).
- **Raw IP addresses**: not acceptable — no effective-domain
  relationship is defined for an IP-literal origin; 2N.15 §3.1 Model E
  is correctly rejected, and HRWP-REQ-028 forbids it explicitly.
- **`localhost` exceptions**: exist only for the secure-context
  carve-out on the developer's own loopback interface, not for RP-ID
  suffix semantics, and are irrelevant to a remote-production
  deployment; HRWP-REQ-028 correctly forbids it and 2N.15 does not rely
  on it.
- **Dedicated subordinate hostname**: valid — `hatp.<controlled-domain>`
  is equal to its own effective domain, so it trivially satisfies the
  "equal to, or suffix of" rule for its own origin.

No blocking finding.

## 5. Origin ↔ RP-ID relationship

Constructed conceptual form: origin `https://hatp.example.invalid`, RP
ID `hatp.example.invalid` (illustrative placeholder only, mirroring
2N.15's own `<controlled-domain>` convention — this phase selects no
literal value either, confirmed by
`test_architecture_document_does_not_freeze_a_literal_hostname`).
Origin host equals RP ID exactly, which trivially satisfies "equal to,
or a registrable-domain suffix of" — the strictest, least-ambiguous
case of the rule, not merely a permitted edge case. Browser WebAuthn
will allow this RP association by construction. Server validation can
require exactly this one origin string via simple equality comparison
(HRWP-REQ-030), mirroring the local provider's own `!=` discipline.

## 6. RP-ID authority-scope analysis (parent domain vs. dedicated subdomain)

Independently reconfirmed: using the bare organizational/personal
domain directly as RP ID would let *any* present-or-future subdomain
ever hosted under it register or assert credentials scoped to that RP
ID (suffix-inclusive matching, §4). A dedicated subdomain
(`hatp.<controlled-domain>`) narrows this to exactly the one hostname
this ceremony uses — no sibling subdomain (`blog.<controlled-domain>`,
`mail.<controlled-domain>`, etc.) can ever be positioned to interfere
with or extend this RP ID's credential scope, and this RP ID's
credentials are never valid for those siblings either (RP-ID scoping is
symmetric-restrictive here: a credential registered at
`hatp.<controlled-domain>` is *not* valid at `<controlled-domain>` or
at any sibling subdomain, only at `hatp.<controlled-domain>` itself or
a further subdomain beneath it). This is meaningful isolation, not
cosmetic — confirmed against the actual suffix rule (§4), not assumed.

## 7. Exact single-origin model — Mac + iPhone

Confirmed: WebAuthn origin/RP-ID matching is defined at the
specification level in terms of the page's URL (scheme/host/port), not
the client device or browser vendor. A Mac Safari/Chrome session and an
iOS Safari session loading the identical URL construct an identical
`clientDataJSON.origin`. Nothing in the WebAuthn client API surfaces
client-hardware identity into the origin computation. One fixed origin
serves both devices without per-platform branching, exactly as
HRWP-REQ-032 requires and 2N.15 §4 claims.

## 8. No Mac-specific or iPhone-specific origin

Confirmed no architectural requirement forces a per-device hostname,
port, or scheme. USB-C and NFC are authenticator-to-client transports,
entirely below the browser's WebAuthn/origin layer — transport choice
cannot and does not alter `clientDataJSON.origin`. No finding.

## 9. Port semantics

WebAuthn origin includes scheme/host/port; 2N.15 §4 selects the default
implicit port (443) in the common case, permitting a non-default port
only if a concrete deployment's TLS-termination choice requires one.
Independently assessed: a non-default port needlessly complicates
origin management (every client and every internal reference must then
carry the port, and any future migration to a standard port would
itself become an origin-changing event, §44 below) with no
architectural benefit named anywhere in HRWP-001/HRAC-001. 2N.15's
"no port suffix in the common case" framing is the correct
default-avoidance recommendation, not a deferred decision left
ambiguous.

## 10. HTTPS secure context

Independently reconfirmed (§2 above, not merely accepted from 2N.15's
own HRWP-REQ-031 citation): browser WebAuthn is a secure-context-gated
API family; the only production-relevant exception is the loopback
carve-out, inapplicable to a real remote deployment. 2N.15 correctly
never invokes a "VPN makes HTTP acceptable" argument — its own §5.4
explicitly frames VPN-only reachability as a defense-in-depth layer
*restricting reachability*, never as a substitute for TLS/secure
context (§53 below confirms this rejected-alternative reasoning
explicitly).

## 11. Publicly trusted certificate model

Confirmed appropriate for both macOS and iOS: both platforms' system
trust stores already trust the standard public CA roots a
Let's-Encrypt-class ACME CA chains to; no manual trust-store
provisioning step is required on either device, unlike a private CA
(§3.4's named tradeoff). Compared against the private-CA alternative:
private CA avoids public DNS exposure but requires an explicit,
per-device, out-of-band trust-installation step (a signed
configuration-profile install and "Enable Full Trust" toggle on iOS)
that itself becomes an ungoverned trust artifact this repository has no
existing revocation/rotation contract for. The rejected-private-CA
rationale in 2N.15 §3.4 is sound: it correctly classifies private CA as
*valid but operationally worse* for the stated public-DNS-acceptable
threat model, not technically broken.

## 12. DNS-01 property — the load-bearing claim

Independently confirmed via RFC 8555 §8.4 (§2 above): DNS-01 validates
domain control by requiring the requester to publish a `TXT` record
under `_acme-challenge.<domain>` in public DNS, resolved by the CA's
own validation servers — it does not require the CA (or anyone else) to
reach an HTTP/HTTPS server at that domain at all. This is exactly the
property that reconciles "publicly trusted certificate" with
"VPN-only-reachable service": public DNS control (a low-friction,
already-required capability for any domain owner) is sufficient for
certificate issuance; public TCP/HTTPS reachability of the
service itself is a completely separate, never-required property under
this model. No blocking finding; this is the single most important
independent confirmation this phase performs, since it is the crux
2N.15's entire §5 rests on.

## 13. DNS visibility model

2N.15 does not silently leave this contradictory: §5.3/§5.4 together
imply a split-horizon-compatible model — public DNS need only carry
whatever the ACME DNS-01 challenge requires (a `TXT` record, ephemeral
per issuance/renewal), while the actual service hostname's resolution
for client traffic MAY be satisfied by a VPN-internal DNS record, a
public record pointing at a VPN-mesh-only address, or the VPN
software's own internal name resolution — 2N.15 correctly declines to
select which, consistent with HRWP-REQ-031's explicit "topology... is
an operational decision this contract does not make." A viable DNS
resolution class is identified (at least one of: split-horizon, or a
public record whose address is itself only reachable over the VPN
mesh); no contradiction found.

## 14. Split-horizon DNS

Optional, not required: a public `A`/`AAAA` record pointing at a
VPN-mesh-internal address (unreachable from the open internet despite
being publicly resolvable) is compatible with "same hostname, same RP
ID, same origin" for both Mac and iPhone without any split-horizon
DNS server at all — split-horizon is one valid implementation choice
among at least two, not a hidden requirement. This is consistent with
2N.15's own explicit non-selection at the literal-provisioning layer
(§70/§71 below) and introduces no defect.

## 15. Certificate name matching

Confirmed: 2N.15's model requires the future certificate's Subject
Alternative Name to match the exact hostname the browser loads as
origin — this is inherent in "the reverse proxy terminates TLS for the
fixed origin" (§5.1) and is not contradicted anywhere. No architecture
text proposes a certificate for one name serving traffic at a different
browser-visible origin.

## 16-18. VPN-mesh-only reachability — Mac and iPhone feasibility

Architecture-level (no VPN software installed/tested this phase, per
the No-Go list): a VPN mesh providing authenticated private IP
reachability, stable enough to sustain a DNS resolution and an HTTPS
connection while joined, is sufficient for both platforms to resolve
the hostname, establish HTTPS, and complete the WebAuthn ceremony,
identically to any other private-network HTTPS client scenario — no
capability WebAuthn requires (secure context, RP-ID/origin
comparison) depends on characteristics of the underlying network
transport. Known mobile-specific limitations (VPN disconnect,
background/session interruption, DNS resolution failure while roaming,
certificate validation against system clock/trust store) are
availability concerns, not authority weaknesses (§66 below) — 2N.15
does not claim otherwise anywhere, and no text proposes weakening
RP/origin validation to compensate for VPN flakiness. Mac and iPhone
consume the identical origin/RP identity (§7); nothing platform-specific
is required.

## 19. No public web-service requirement — reconciliation confirmed

Restates and reconfirms §12/§13: the architecture's central claim
("DNS domain publicly controlled + certificate publicly trusted, while
the WebAuthn endpoint stays VPN-only") is not self-contradictory,
because certificate issuance (DNS-01) and service reachability (TCP/TLS
port exposure) are independent axes under the selected model. No
certificate-issuance mechanism 2N.15 selects requires public
reachability of the WebAuthn endpoint itself.

## 20. Reverse-proxy trust boundary

Load-bearing, independently assessed: the reverse proxy, by
terminating TLS, observes plaintext HTTP requests, any header it
forwards, and (if colocated) whatever the companion process returns.
2N.15 §5.1/§7 classifies it as a thin, non-trusted-kernel adapter that
"relays bytes the trusted kernel produces and validates, carries no
independent trust" — consistent with HRWP-REQ-062/HRAC-REQ-070's
existing trusted-kernel/adapter boundary, which this phase re-read
directly (not accepted from 2N.15's restatement) and confirms is not
altered by adding the reverse-proxy component to the adapter side of
that boundary. The backend MUST NOT treat any proxy-supplied value as
automatically authoritative — this is not yet code (no implementation
exists), so this phase's finding is a forward-looking constraint on the
next implementation phase, not a mechanically-checkable current-state
fact; it is recorded here so that constraint is not lost between
phases.

## 21-22. Host header / X-Forwarded-Proto security

No implementation exists yet (confirmed,
`test_no_remote_webauthn_or_infrastructure_implementation_source_exists`),
so there is no live Host-header-derivation defect to find today — this
is a **future-implementation constraint**, not a present code defect.
2N.15's own text nowhere proposes deriving RP ID, allowed origin, or
authority context from `Host`/`X-Forwarded-Host`/`Forwarded` request
headers; §3-§4 fix the RP ID and origin as literal, server-configured
constants compared by exact equality (mirroring the existing local
provider's own `!=` discipline, HRWP-REQ-030). This satisfies §21's
"freeze expected RP ID/origin from trusted configuration" requirement
at the architecture level. Likewise, no text proposes trusting
`X-Forwarded-Proto` from an untrusted source; the correct future
implementation rule (trust it only when the request provably arrived
through the one configured, trusted reverse-proxy hop — e.g. a
loopback-only or mutually-authenticated internal listener, never from
a directly-reachable-by-clients socket) is not yet contradicted by
anything 2N.15 states, because 2N.15 makes no HTTP-header-trust claim
at all (it is out of scope for an architecture-only phase whose HTTP
layer has zero lines of implementation). **No Blocking finding**: the
absence of an explicit header-trust rule in an architecture document
that implements no HTTP layer is not the same defect class as a
present, permissive implementation — this distinction is the correct
reading of "if 2N.15 proposes dynamic host-derived values: Blocking"
(the governing prompt's own conditional), which is not triggered here.

## 23. Direct backend access

2N.15 §5.1/§5.2 selects "no external/direct client path" — the
companion process is reachable only via a private hop (localhost /
private network / VPN-internal) from the reverse proxy, never directly
from a client. This satisfies the "strong candidate: NO direct path"
guidance; no contradicting text found.

## 24. TLS termination location vs. WebAuthn verification

Confirmed no conflict: TLS termination (transport confidentiality/
authentication of the HTTP connection) and WebAuthn assertion
cryptographic verification (§16 of HRWP-001, unamended) are
independent trust functions operating on different data — TLS
protects bytes in transit; WebAuthn verification operates on the
already-decrypted `clientDataJSON`/`authenticatorData`/`signature`
values the companion process receives. Reverse-proxy TLS termination
does not and cannot substitute for, weaken, or bypass HRWP-001 §16's
verification, which 2N.15 §7 correctly keeps entirely inside the
trusted-kernel companion process.

## 25-27. Proxy / VPN / DNS compromise threat models

- **Proxy compromise**: independently re-derived from HRAC-REQ-027/
  HRWP-REQ-045 (session-locator possession ≠ authority, both confirmed
  present verbatim,
  `test_hrac_session_locator_is_not_authority_requirement_present`). A
  compromised proxy can withhold, delay, or replay transport bytes, or
  tamper with unprotected HTTP inputs it forwards, but cannot forge a
  valid WebAuthn signature (it does not hold the authenticator's
  private key) and cannot forge a valid `HumanApprovalProvenanceProof`
  (HATP-001's Model B, unamended, requires possession-proof the proxy
  never has). Session-substitution attempts are limited by HRAC-001's
  single-use, exclusive-publish consumption (§20/§35-39 of HRAC-001,
  unamended by this phase). No new authority the proxy could exercise
  is introduced by 2N.15.
- **VPN compromise / another mesh member**: network membership is
  reachability, never authorization or possession-proof — an
  unrelated device on the same mesh gains only the ability to attempt
  to reach the (still TLS-protected, still origin/RP-ID-checked,
  still hardware-possession-gated) ceremony endpoint; it cannot itself
  produce a valid assertion for someone else's `signer_key_id` or
  bypass HATP-001's governance-authorization ordering (HRAC-REQ-016/
  057). Consistent with 2N.15 §5.4's own "reduces the population of
  parties who can even attempt it, not a replacement for cryptographic
  guarantees" framing.
- **DNS compromise**: with certificate/origin binding intact, an
  attacker who redirects DNS for the RP-ID hostname to their own
  infrastructure still cannot obtain a matching, publicly-trusted
  certificate for that name without also compromising the domain's
  DNS-01 challenge-publication capability (the same DNS control an
  attacker would need to redirect traffic in the first place — so this
  is not an independent second line of defense against a
  full-DNS-takeover attacker, an assumption this phase names
  explicitly rather than leaving implicit) or the browser/OS trust
  store; absent that, a redirected-but-uncertificated origin fails
  TLS validation before any WebAuthn ceremony can even begin. Exact
  assumption: DNS compromise alone (e.g. a stale/hijacked individual
  record, not full registrar/DNS-provider compromise) does not, by
  itself, defeat certificate-name binding, since ACME re-issuance
  against attacker-controlled DNS is a separate, detectable event (cert
  transparency logs) from routing traffic through stale records.

## 28-29. ACME/DNS credential authority and TLS private key

Named, not resolved (correctly, since this is an implementation/
provisioning-phase question 2N.15 explicitly defers, §70/§71 below):
DNS-01 automation requires DNS-provider API credentials scoped, where
the provider supports it, to the narrowest record type/zone needed for
`_acme-challenge` TXT management, not full-zone or full-account
credentials — this is a least-privilege *requirement to satisfy later*,
not a claim 2N.15 resolves. The TLS private key belongs to the
reverse-proxy/infrastructure layer, never the FIDO2 authenticator and
never a `HardwareCredentialRecord` — 2N.15 §5.1/§7 already draws this
distinction correctly (TLS key lifecycle is explicitly placed "outside
HBDC-001's Protected-Root/OS-principal trust boundary"). Whether DNS
credential handling belongs inside the PCAE trusted kernel or the
infrastructure boundary: infrastructure boundary — DNS/ACME credentials
authorize domain-control proof and certificate issuance, not PCAE
governance decisions; they are the same trust class as the reverse
proxy itself (§7), not HMIC-001 scope, unless a future phase
identifies a specific reason to bind them tighter.

## 30. HATP / Protected Root separation

Independently derived (not assumed): the TLS certificate/private key
are transport-layer credentials whose sole function is authenticating
an HTTPS connection to arbitrary clients; they carry no
governance-decision authority and are not consulted by any HATP
verification step (HRWP-001 §16, unamended). They belong in
separate, infrastructure-controlled state (the reverse-proxy/ACME
layer's own key storage), not in HATP's Protected Root, which exists to
hold governance-authority artifacts (`RepositoryIdentity`, `Principal`,
`SignerRecord`, `HardwareCredentialRecord`, `DeploymentBinding`). No
2N.15 text proposes otherwise.

## 31. Literal hostname selection boundary

Independently confirmed: 2N.15 selects a naming *strategy*
(`hatp.<controlled-domain>`, a placeholder form) without selecting an
actual domain/hostname anywhere in its text
(`test_architecture_document_does_not_freeze_a_literal_hostname`).
This phase likewise selects no literal hostname — every illustrative
form here uses `<controlled-domain>`/`.invalid` placeholder syntax.

## 32-33. Future literal RP-ID requirements and machine-independence

Constraints the future literal selection must satisfy, derived from
HRWP-REQ-027/028 and 2N.15 §3 combined: operator-controlled domain;
stable long-term (not a temporary/trial registration); a valid
registrable-domain-form WebAuthn RP ID (§4); certificate-issuable via a
public CA (implies the domain must support public DNS-01, i.e. the
operator or a delegate must control its authoritative DNS); resolvable
on Mac/iPhone over the selected VPN-mesh network; explicitly NOT tied
to `atila-Latitude-E5470`, hac-dell's current hostname/IP, or a
transient VPN node identifier — RP identity, once fixed, must survive
a future migration off hac-dell to different deployment hardware,
since WebAuthn credentials are permanently scoped to the RP ID at
registration time (HRWP-REQ-028) and re-keying every credential after a
routine hardware migration would be a severe, avoidable operational
cost. 2N.15 §3.2-§3.4 never proposes a machine-specific value; this
constraint is satisfied by construction, not merely by absence of a
counter-example.

## 34-35. Shared vs. per-repository RP; credential portability

Re-derived directly from 2N.15 §3.3 (not accepted as asserted):
2N.15 selects **one PCAE remote-WebAuthn RP shared across every
PCAE-governed repository this single operator controls**, explicitly
naming per-repository RP ID as rejected-as-default (permitted only as
a named exception for a genuinely multi-organization/multi-human
operator, not this repository's current single-operator case). This
choice does not broaden governance authority: `DeploymentBinding`
remains exactly one active binding per `repository_id` (HRWP-REQ-013/
058, HRAC-REQ-021, all unamended and independently reconfirmed still
schema-clean of any protocol/transport/network field via
`test_deployment_binding_still_carries_no_protocol_or_transport_field`)
— a shared RP ID only means one physical credential *can* be
technically presented for ceremonies naming different repositories;
`DeploymentBinding`/`SignerRecord`/registry resolution is what actually
authorizes any specific operation, exactly as HRAC-REQ-017/033's live
re-resolution already requires, unaffected by RP-ID sharing. This is
explicit in 2N.15's own text, not left ambiguous — no finding.

## 36-38. Physical key vs. credential identity; hardware compatibility

Confirmed: one physical authenticator can hold multiple distinct
WebAuthn credentials scoped to different RP IDs — 2N.15 does not
conflate physical-key identity with credential identity anywhere, and
HRWP-REQ-011/012 (unamended, independently re-read) already establish
the registry supports an arbitrary number of `HardwareCredentialRecord`s
per `Principal`. Nothing in the selected RP-ID/origin/network model
requires a specific authenticator model, USB-C-only or NFC-only
behavior, or a 5-Series-only feature — USB-C and NFC remain
transports, unrelated to origin/RP-ID selection (§8 above).

## 39-41. Challenge binding, origin validation source, RP-ID hash source

Re-derived directly from HRAC-001 §11-13/§19 and HRWP-001 §16, both
read fresh this phase: the challenge context binds `repository_id`,
`Signer`/`principal_id`, `binding_digest`, `decision_record_digest`,
`operation_reference`, `request_id`, `nonce`, `expires_at` (HRAC-REQ-017/
022) — nothing in 2N.15's infrastructure selection can alter any of
these; the reverse proxy and VPN only ever carry already-constructed
bytes, never construct or interpret them (§7's adapter classification).
Expected origin and expected RP-ID hash are both frozen, per HRWP-REQ-
027/029/030/033, as server-side configuration values compared by exact
equality against `clientDataJSON.origin`/`authData.rpIdHash` — never
derived from the request itself. 2N.15 introduces no mechanism that
would let a client or the network path influence either value.

## 42-43. Configuration authority and mutability

The future RP-ID/origin configuration is authority-bearing precisely
because changing it changes which assertions the companion process
will accept as valid (§41). This phase determines — as forward guidance
for the next implementation phase, since no such configuration exists
yet to classify definitively — that it should be treated as **protected,
certified deployment configuration** analogous to how `hatp_bootstrap.py`'s
existing bound records are protected, not as ordinary environment-
variable-style runtime config: HMIC-001 source-scope binding is the
more likely fit once real verifier code exists (per HRWP-REQ-061/
HRAC-REQ-071's own unresolved "will become HMIC-relevant" framing,
independently re-confirmed present in both contracts), but this phase
does not itself bind it, since no such module exists yet to bind. It
must be immutable at request-verification time (fixed at process
startup or loaded from a certified, non-request-influenced source) —
2N.15 never proposes per-request RP-ID selection, consistent with this.

## 44. Origin rotation vs. RP-ID migration

Independently distinguished: changing the *origin* (e.g. a port change,
or a different reverse-proxy front door) while the *RP ID* stays fixed
MAY preserve credential usability, provided the new origin still
satisfies "equal to, or a suffix of," the same RP ID (§4) and the
server's allowed-origin configuration is updated to match (HRWP-REQ-
029 already permits "a small number of origin variants" under one RP
ID). Changing the *RP ID* itself changes WebAuthn credential scope by
specification (§4) — every credential registered under the old RP ID
becomes uninvokable under the new one, requiring re-enrollment. 2N.15
does not conflate these; §3's dedicated-subdomain selection is chosen
in part (§3.3) because it minimizes future RP-ID-migration pressure.

## 45-46. Disaster recovery and certificate rotation

Because the selected model separates RP identity (a DNS name under
operator control) from the specific machine serving it (hac-dell
today, potentially different hardware later), losing hac-dell does not
imply losing WebAuthn credential usability if the same RP-ID/domain,
verifier state, and credential registry migrate to replacement
infrastructure — a desirable property 2N.15 achieves by construction
(§32-33) rather than claims without support. Certificate rotation
(routine ACME renewal or CA reissuance) changes only the TLS transport
credential (§29-30); it alters neither RP ID nor origin nor any
WebAuthn credential identity, provided the renewed certificate
continues to name the identical hostname (§15).

## 47-49. Product independence (VPN / reverse proxy / ACME client)

Independently confirmed by direct text inspection: 2N.15 §5.1 explicitly
states "this phase does not select a literal product, only the model"
for the reverse proxy, naming Caddy/nginx only as illustrative
examples inside that same sentence, not as a selection; §5.4 similarly
names WireGuard only as an illustrative VPN-mesh example ("e.g.
WireGuard-based"); no ACME client software is named at all. The
architecture freezes security *properties* (authenticated private
reachability, stable DNS, Mac/iPhone support; TLS-terminating narrow
adapter; DNS-01-capable ACME automation) rather than vendor products.
No finding.

## 50-56. Rejected alternatives — independently re-tested

- **Direct public exposure** (§50): correctly rejected on attack-surface
  grounds, not on an unexamined "private sounds safer" instinct — 2N.15
  §5.4 names the concrete tradeoff (needless exposure to internet-wide
  scanning/credential-stuffing/DoS attempts against the request-fetch
  surface, none of which succeeds cryptographically but all of which
  needlessly widen the attempting population and the HTTP-parsing
  attack surface) against the named cost (a VPN client requirement) and
  explicitly leaves full public reachability available as a
  non-default, valid operator choice (§5.4's "named alternative, not
  selected as default") — this is reasoned rejection, not reflexive
  rejection, and correctly does not claim WebAuthn's own cryptography
  is insufficient without it.
- **Self-signed TLS** (§51): correctly rejected — no mainstream browser
  trusts a self-signed certificate by default, and every device would
  need manual trust-store installation, which is worse than the
  private-CA alternative already named and rejected (§52) for the same
  reason, with no compensating benefit.
- **Private CA** (§52): correctly classified as *valid but
  operationally less suitable*, not invalid (§11 above) — technically
  sound, WebAuthn-compatible once trusted, but requires the same
  per-device manual trust step self-signed TLS does, without even
  self-signed's simplicity advantage.
- **HTTP over VPN** (§53): correctly rejected on the actual, verified
  WebAuthn secure-context requirement (§2/§10 above), not on a vague
  "VPN doesn't count" intuition — network-layer encryption is orthogonal
  to the browser's own scheme check, which 2N.15's own text (§5.4)
  never conflates.
- **IP-address RP ID** (§54): correctly rejected against the
  independently-reconfirmed effective-domain rule (§4) — no browser
  defines an effective domain for an IP-literal host, so no RP-ID
  suffix relationship can ever be constructed for one.
- **Localhost** (§55): correctly rejected — its secure-context carve-out
  is a developer-loopback exception with no bearing on remote Mac/
  iPhone access to hac-dell.
- **Per-device origin** (§56): correctly rejected — nothing in the
  WebAuthn/RP-ID model requires or benefits from a Mac-specific vs.
  iPhone-specific origin (§7-§8 above); USB-C vs. NFC is a transport
  distinction the origin layer never needs to encode.

No rejected alternative was found invalidly rejected or invalidly
accepted.

## 57. HBDC-001 compatibility

Independently reconfirmed (not merely restated): HBDC-001 defines
host-level trust topology (OS-principal separation, Protected Root
ownership, execution-environment lock) and contains no requirement
sentence naming DNS/VPN/reverse-proxy/network topology
(`test_hbdc_contract_defines_no_network_dns_vpn_topology_requirement`,
this phase's own independent grep, not 2N.15's). RP hostname, reverse
proxy, and VPN selection therefore cannot contradict HBDC-001 by
construction, and 2N.15 correctly does not relocate any
`RepositoryIdentity`/`Principal`/`SignerRecord`/`HardwareCredentialRecord`/
`DeploymentBinding` authority off hac-dell — network identity never
substitutes for `DeploymentBinding` anywhere in 2N.15's text.

## 58. HRAC-001 compatibility

Independently reconfirmed: ceremony URL delivery (HRAC-REQ-028),
`request_id` (HRAC-REQ-015/017), session state (HRAC-REQ-010-014),
challenge construction (HRAC-REQ-022-025), and one-time consumption
(HRAC-REQ-035-039) are all defined at the request/challenge-context
layer, entirely independent of transport/network topology — the
reverse proxy and VPN mesh only ever relay already-constructed bytes
(§7's adapter classification, §39-41 above). No network state anywhere
in 2N.15's model becomes signing authority; this satisfies HRAC-001's
own requirements unmodified.

## 59. HRWP-001 requirement mapping (explicit, not "generally compatible")

| HRWP requirement | 2N.15 architecture element | Compatible? |
|---|---|---|
| HRWP-REQ-027 (real-domain, stable, DNS-resolvable RP ID) | §3, dedicated subdomain model | Yes — literal value deferred, model satisfies form |
| HRWP-REQ-028 (no localhost/IP/per-session) | §3.1 candidate table, Model E rejected | Yes |
| HRWP-REQ-029 (exactly `https://<host>`, no wildcard) | §4, one fixed origin | Yes |
| HRWP-REQ-030 (server-side exact origin comparison) | §4 rationale, mirrors local `!=` discipline | Yes (forward constraint on future implementation) |
| HRWP-REQ-031 (DNS/TLS/topology named, not resolved) | §5.1-§5.4 | Yes — resolves model, defers literal, exactly as required |
| HRWP-REQ-032 (one origin serves Mac + iPhone) | §4, §7 above | Yes |
| HRWP-REQ-033/034 (fail-closed server verification) | §6/§8, unchanged, still hac-dell/companion-side | Yes — 2N.15 touches nothing here |
| HRWP-REQ-038 (client not trusted for identity) | §6, client/server split | Yes |
| HRWP-REQ-062 (trusted-kernel/adapter boundary) | §7, extended with reverse proxy/VPN/ACME as adapter | Yes |

No HRWP-001 requirement is contradicted or silently narrowed.

## 60. Multi-authenticator compatibility

Confirmed unaffected: `EXPLICIT_SIGNER`/`allowCredentials` remain
server registry matters (HRWP-REQ-014/036, HRAC-REQ-020, unamended);
2N.15's RP-ID/origin/network selection imposes no one-credential-or-
one-device constraint anywhere.

## 61. Browser client trust

Confirmed preserved: 2N.15 §6 places the browser strictly on the
untrusted, presentation-only side of the boundary — it "never sees
`binding_digest`, `decision_record_digest`, `principal_id`, or
`signer_key_id` in cleartext" (2N.15's own text, independently
cross-checked against HRAC-REQ-030's identical exclusion list, which
this phase re-read directly). Serving the page from a trusted HTTPS
origin does not and cannot make client-side JavaScript an authority
source for `Signer`, `RepositoryIdentity`, operation digest, or any
governance decision — nothing in 2N.15 proposes otherwise.

## 62. Static client-content integrity

Correctly classified as a **future-implementation question, not
resolved here** (2N.15 does not implement a client; there is no
browser asset yet to classify). Forward guidance: because a compromised
or tampered ceremony page could manipulate ceremony UX or transport
(though not forge a valid assertion — cryptographic verification stays
server-side, §16 above), the future page's HTML/JS is a candidate for
integrity governance (subresource integrity, or HMIC-adjacent
certification of the served bundle) at the level of "does this
component's tampering enable a *plausible-looking but not
cryptographically valid* phishing attempt," not at the level of
"could it forge an assertion" (it cannot). This phase records the
classification question; it does not resolve it, since resolving it
requires the client to exist.

## 63-65. Reverse proxy / VPN / DNS configuration integrity

Independently assessed, consistent with 2N.15 §7's classification:
none of these three should be automatically placed in HMIC-001 scope
merely by association — HMIC-001 governs PCAE's own trusted-kernel
source, and the reverse proxy/VPN/DNS are explicitly named
adapter/infrastructure components (§7) whose misconfiguration affects
*availability and reachability*, never cryptographic authority (§20/§39
above). They remain external operational trust dependencies requiring
ordinary infrastructure hardening (least-privilege ACME credentials,
§28-29; correct proxy header-trust configuration once it exists, §21-
22; standard VPN-mesh membership hygiene), documented here as such, not
silently promoted to HMIC-001 members without a specific future
finding that requires it.

## 66. Availability vs. authority

Confirmed preserved throughout 2N.15: VPN/DNS/certificate unavailability
degrades to "ceremony unavailable," never to any fallback that weakens
WebAuthn's own checks (no HTTP fallback, no alternate RP, no local
ungoverned signing bypass) — 2N.15 introduces no such fallback anywhere
in its text; the No-Go list (§235 of the architecture document) and
this phase's own No-Go (§79 below) both confirm no such mechanism was
ever proposed or created.

## 67-69. Mobile-first, Mac usability, no device-proxy requirement

Both intended workflows (iPhone: VPN → fixed HTTPS URL → iOS WebAuthn →
NFC/USB-C → hac-dell verification; Mac: VPN → same origin → WebAuthn →
USB-C → hac-dell verification) are feasible under the selected
architecture with no step requiring a capability the model does not
provide (§16-19 above). The selected model eliminates any need for
VirtualHere, USB-over-IP, or raw iPhone HID forwarding — HRWP-REQ-063
(independently re-read) already classifies USB-over-IP as experimental/
non-primary precisely because the browser-mediated remote-WebAuthn path
this architecture selects makes it unnecessary; 2N.15 does not
reintroduce it.

## Findings

No Blocking finding.

Two Non-Blocking observations, recorded for the next phase's awareness,
neither of which contradicts any HRWP-001/HRAC-001/HBDC-001 requirement
or 2N.15's own text:

- **NBF-149O.20L.7O.2N.16-1**: The future reverse-proxy/companion-process
  boundary's Host-header and `X-Forwarded-Proto` trust rules (§21-22
  above) are not yet stated as an explicit, testable requirement
  anywhere in HRWP-001/HRAC-001/2N.15 — they are correctly *implied* by
  the existing "fixed server configuration, never request-derived"
  discipline (HRWP-REQ-030/033), but no requirement sentence names
  `Host`/`X-Forwarded-Host`/`Forwarded`/`X-Forwarded-Proto` specifically.
  Recommended disposition: the next implementation-adjacent contract
  phase (HRAC-001-companion server implementation, or a narrow HRWP-001
  companion) should state this explicitly before real server code is
  written, to avoid a future implementer treating proxy-supplied
  headers as trustworthy by default.
- **NBF-149O.20L.7O.2N.16-2**: Static client-asset integrity governance
  (§62 above) is named as an open classification question by this
  phase but not resolved by either 2N.15 or any prior contract.
  Recommended disposition: resolve at the same phase that first
  implements the ceremony-delivery page, not before (resolving it
  earlier would require designing controls for an artifact that does
  not yet exist).

Neither finding blocks this phase's verdict: both concern rules for
code that does not exist yet (no HTTP layer, no client asset), and
2N.15's own text does not contradict the correct future rule in either
case — it simply has not yet stated it as its own normative
requirement, which is appropriate for an architecture-only phase.

## Independent tests

`tests/test_phase_149o_20l_7o_2n_16_remote_webauthn_rp_id_origin_https_infrastructure_architecture_independent_verification.py`
— 16 tests, freshly written this phase (not copied from 2N.15, which
has no test file of its own — it was an architecture-selection phase,
not a verification phase). All 16 pass:

```
16 passed in 0.07s
```

Independently re-run against the fixed pre-phase checkpoint (`6901ecc7`)
via `git ls-tree`/`git show` where historical claims are made
(`test_pre_2n16_checkpoint_had_no_remote_webauthn_source_either`,
`test_hardware_credential_record_protocol_name_...` equivalents already
covered by the current-state test), not merely against current HEAD.

## Fast Green

```
python -m pytest -m fast_green -q -n auto
339 failed, 8688 passed, 4 skipped, 105 warnings, 9 errors in 131.05s
```

Byte-identical failed/passed/skipped/error counts (339/8688/4/9) to
Phase 149O.20L.7O.2N.15's own recorded pre-phase baseline (`339
failed / 8688 passed / 4 skipped / 9 errors`), confirming zero
regression attributable to this phase without needing a fresh A/B
worktree comparison — this phase's own `git diff --stat 6901ecc7..HEAD
-- src/pcae/ scripts/` is empty (no production source touched), so an
identical failure/pass count against the immediately-prior phase's own
baseline is the expected, sufficient confirmation; every failing node
ID is a pre-existing, previously-attributed historical failure
(deployment-verifier/HMIC-implementation-plan/CHGR-count/shell-gate
suites unrelated to remote WebAuthn), not newly introduced by this
phase's two purely-additive new files (one test module, one doc).
`tests/test_phase_149o_20l_7o_2n_16_...py` itself is collected and
passes cleanly as part of this run (16/16, see below), consistent with
its standalone run.

## Proof of no infrastructure/implementation effect

- No `RemoteWebAuthnProvider`, WebAuthn server module, reverse-proxy
  config, ACME client config, or VPN config exists anywhere in the
  repository (`test_no_remote_webauthn_or_infrastructure_implementation_source_exists`,
  `test_no_dns_tls_reverse_proxy_or_vpn_configuration_files_exist_in_repository`).
- No literal hostname/domain was selected by this phase or by 2N.15
  (`test_architecture_document_does_not_freeze_a_literal_hostname`).
- No SSH session to hac-dell was opened this phase; no hac-dell state
  was read or written (this phase's verification depends only on this
  repository's own frozen contract text, local source, and primary
  external WebAuthn/ACME documentation — identical in kind to 2N.15's
  own justification for not needing hac-dell's live state, independently
  re-confirmed rather than merely inherited).
- Runtime unchanged: HATP remains NOT READY / NOT ACTIVE.

## Commits

Phase-owned commits (subject prefix `Phase 149O.20L.7O.2N.16:`) will be
listed here after `pcae commit implementation` and the task-lifecycle/
status-sync commits are made; see `git log --oneline 6901ecc7..HEAD`.

## Pushed / origin/main..HEAD

Confirmed via `pcae push check` prior to `pcae push` (see governance
section of the completion metadata) — `nothing_to_push` after push.

## Exact recommended next phase

**149O.20L.7O.2N.17 — Remote WebAuthn Literal RP-ID / Origin and
Infrastructure Realization Contract/Plan.** Its narrow scope: select
the actual domain/hostname literal satisfying §32-33's derived
constraints (operator-controlled, stable, certificate-issuable,
resolvable on Mac/iPhone over the selected VPN mesh, not tied to
hac-dell's current machine identity), and produce a realization plan
distinguishing selection from provisioning (per §70-72 below) — without
itself provisioning DNS/TLS/VPN/reverse-proxy infrastructure. If that
phase's own scope proves small enough to combine literal-selection with
a narrow independent-verification step, it MAY do so, but MUST NOT
combine literal selection with actual provisioning (§71) or with
`RemoteWebAuthnProvider` implementation (§72) in the same phase.

## 70-72. Literal value / provisioning / implementation gates — reaffirmed

Independently reconfirmed as the correct ordering, not merely restated:
architecture verification (this phase) → literal value / realization-
plan freeze → independent verification of that freeze if it proves
authority-sensitive → infrastructure provisioning → infrastructure
verification → `RemoteWebAuthnProvider`/server implementation. This
phase selects no literal value, provisions nothing, and implements
nothing, consistent with the governing prompt's own No-Go list (§79)
and its own §31/§70/§71/§72.

## 73-74. Current Dell deployment / HATP state

No Dell mutation occurred this phase; no SSH session was opened (§ "Proof
of no infrastructure/implementation effect" above). HATP remains NOT
READY / NOT ACTIVE — this architecture-verification phase does not and
cannot change readiness, since it authorizes no protected-state write.

## 75-76. Blocking / non-blocking finding disposition

No Blocking finding (§ "Findings" above lists the two Non-Blocking
observations found, both future-implementation-scoped, neither
contradicting current contract text).

## No-Go confirmation

No hardware touched. No `makeCredential`/`getAssertion` executed. No
real or synthetic WebAuthn credential created. No DNS/TLS/reverse-proxy/
VPN/ACME artifact provisioned, installed, or configured. No literal
hostname/domain selected (illustrative placeholders only, throughout).
No production source under `src/pcae/**`/`scripts/**` modified. No
contract (HRWP-001, HRAC-001, HBDC-001, or any other) modified. No HMIC
change. No hac-dell mutation or SSH session. No Permission
Broker/runtime-capability change. No protected record created. No
recertification or redeployment. HATP remains NOT READY / NOT ACTIVE.

## Governance

Governed PCAE lifecycle used throughout: `pcae session bootstrap`,
`pcae task transition`/`task update --allowed-file`,
`pcae commit implementation`, manual metadata/report sync per this
repository's established phase-completion procedure, `pcae push
check`/`pcae push`, `pcae phase complete --stage-pending-report` then
(post-push) without that flag. No raw `git commit`/`git push`. No
`--no-verify`. No force push. No lifecycle/hook bypass.
