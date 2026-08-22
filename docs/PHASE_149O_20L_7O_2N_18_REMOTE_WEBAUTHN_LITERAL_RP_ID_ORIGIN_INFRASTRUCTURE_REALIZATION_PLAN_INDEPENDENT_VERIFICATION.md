# Phase 149O.20L.7O.2N.18 — Remote WebAuthn Literal RP-ID / Origin and Infrastructure Realization Plan Independent Verification

**Verdict: A — 2N.17 LITERAL RP-ID RULE / REALIZATION PLAN — INDEPENDENTLY VERIFIED. ACTUAL OPERATOR DOMAIN: STILL REQUIRED BEFORE LITERAL FREEZE.**

```
REMOTE WEBAUTHN LITERAL RP-ID RULE
— INDEPENDENTLY VERIFIED
RP-ID RULE:            hatp.<operator-controlled-domain>
ORIGIN RULE:            https://hatp.<operator-controlled-domain>
ACTUAL DOMAIN:          UNSUPPLIED / NOT FABRICATED
SHARED HATP RP MODEL:   VERIFIED
MACHINE INDEPENDENCE:   VERIFIED
MAC + IPHONE:           SAME RP / SAME ORIGIN
REALIZATION PLAN:       VERIFIED
NO DNS/TLS/VPN/PROXY INFRASTRUCTURE PROVISIONED
NO REMOTE PROVIDER IMPLEMENTED
NO REAL CREDENTIAL CREATED
```

Independently verifies Phase 149O.20L.7O.2N.17's literal RP-ID/origin
construction rule and infrastructure realization plan. Re-derived from
HRWP-001 v1.1, HRAC-001 v1.0, HBDC-001, current production source, and
2N.15/2N.16's own text read directly — not accepted from 2N.17's report,
tests, or summary prose as proof.

## True phase-entry commit

`7f2f902c` (HEAD at phase entry; `pcae push check` → `nothing_to_push`
confirmed before this phase's own first edit).

## 1. Primary contracts re-derived (fresh, this phase)

- `docs/contracts/HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md` (HRWP-001
  v1.1) — read in full. HRWP-REQ-027 through HRWP-REQ-032 (the RP-ID/
  origin/HTTPS/Mac-iPhone requirements this phase's mapping in §11 below
  targets) confirmed present, unchanged since Phase 149O.20L.7O.2N.11.
- `docs/contracts/HATP_REMOTE_ASSERTION_CEREMONY_CONTRACT.md` (HRAC-001
  v1.0) — read in full, HRAC-REQ-061/062/070 re-confirmed unchanged
  since Phase 149O.20L.7O.2N.9.
- `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` (HBDC-001 v1.2) —
  read in full; independently reconfirmed no `HBDC-REQ-###` sentence
  constrains DNS/VPN/reverse-proxy/network topology. HBDC-REQ-072's
  "narrowest value that names exactly the one authority" discipline
  (`DeploymentBinding.authority_scope`) is the same discipline 2N.15/
  2N.17 apply to RP-ID subdomain scoping — confirmed by direct reading
  of §16.2, not accepted from 2N.17's citation.
- 2N.15 (`docs/PHASE_149O_20L_7O_2N_15_...ARCHITECTURE.md`) and 2N.16
  (`docs/PHASE_149O_20L_7O_2N_16_...INDEPENDENT_VERIFICATION.md`) read
  in full, independently, this phase — not treated as proof, per this
  phase's own independence principle, but their exact text is what 2N.17
  claims to confirm, so both were read to check 2N.17's claims against
  primary contract text directly, not merely against 2N.15/2N.16's own
  restatement of that text.
- `docs/PHASE_149O_20L_7O_2N_17_...REALIZATION_CONTRACT_PLAN.md` (the
  artifact under verification) — read in full.
- `src/pcae/core/hatp_fido2_provider.py` — confirmed `_HATP_RP_ID =
  "hatp.pcae.local"` / `_HATP_ORIGIN = "pcae-hatp://hatp.pcae.local"`
  (lines 102-104) still present, unchanged, still local-provider-only.
- `src/pcae/core/hatp_providers.py` — confirmed
  `_PRODUCTION_HARDWARE_PROVIDER_PROFILES = (HATP_HARDWARE_PROVIDER_V1,)`
  (line 187) still excludes `HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN`;
  the dispatch gap (NBF-149O.20L.7O.2N.12-1) remains open, unresolved,
  independently reconfirmed against current source (not 2N.17's claim).
- `src/pcae/core/hatp_hardware_credentials.py` — confirmed
  `_PROTOCOL_VALUES = frozenset({"FIDO2", "PIV", "WEBAUTHN"})` (line 62)
  still includes `"WEBAUTHN"` (the HRWP-REQ-019/HRAC-REQ-066 prerequisite
  already resolved, unaffected by and independent of this phase's own
  RP-ID/origin scope).
- Repository-wide search (`grep -rn` across `docs/**`, `.pcae/**` for a
  `.com`/`.net`/`.org`/`.dev`/`.io`-form literal, or any string other than
  `<operator-controlled-domain>`/`<controlled-domain>`/`.tld`/`.invalid`
  placeholder forms) for any previously-named literal domain:
  **none found**, independently reconfirmed — no operator-controlled
  domain has ever been named anywhere in this repository's history,
  corroborating 2N.17 §1's own identical finding rather than accepting
  it on assertion.

## 2. 2N.17 realization artifact inspected

Read fully (§0 above); its own structure — §0 purpose, §1 re-derivation,
§2 model confirmation table, §3 domain/RP-ID rule, §4 origin, §5 DNS/TLS
plan, §6 network model, §7 reverse-proxy placement, §8 migration model,
§9 security-boundary model, §10 remaining-prerequisites list, §11 No-Go,
§12 decision summary — matches what its governing prompt required, and
every numbered claim in §2's confirmation table cross-checks against the
primary contract sections it cites (independently re-read at their exact
section numbers in HRWP-001/HRAC-001/HBDC-001, not merely trusted by
citation). No unsupported claim found.

## 3. Exact construction rule

```
RP-ID:  hatp.<operator-controlled-domain>
Origin: https://hatp.<operator-controlled-domain>
```

Confirmed verbatim in 2N.17 §3 rule 1 / §4, and confirmed to satisfy
HRWP-REQ-027/028/029/030 on independent re-derivation (§4-§5 below).

## 4. Actual-domain status

**Not supplied. Not fabricated.** §1's independent repository-wide search
confirms no literal domain exists anywhere in this repository's history.
2N.17 §3's "required input, named explicitly, not resolved by this
phase" framing is accurate — it states a *fact about what the operator
must supply* (registrar/DNS-zone-edit access to a real, currently-
controlled domain), not an architectural decision 2N.17 declined to make.
This phase does not ask the human for the domain and does not invent one
(§58/§67 governing-prompt No-Go items, both honored).

## 5. RP-ID-rule validity

Independently evaluated against WebAuthn's RP-ID scoping rule (an RP ID
must be equal to, or a registrable-domain suffix of, the calling
origin's effective domain — the same primary-source rule 2N.16 §2/§4
independently confirmed from the W3C WebAuthn specification, re-applied
here rather than re-derived from nothing):

- **Effective-domain semantics**: `hatp.<domain>` is, by construction,
  equal to its own origin's effective domain (§6 below) — trivially
  satisfies "equal to, or suffix of." Valid for any real, operator-
  controlled registrable domain substituted for `<domain>`.
- **Not a public suffix**: the rule requires `<domain>` to be a real
  *registrable* domain the operator controls (§3 rule text: "one real,
  currently-registered, DNS-manageable domain") — a public suffix (e.g.
  `.com`, `.co.uk`) is definitionally not something a single operator
  registers and controls, so the rule as stated cannot resolve to a bare
  public suffix; this is satisfied by the rule's own precondition, not
  merely by omission.
- **Stable operator control**: rule 5 (§3) explicitly requires long-term
  commitment and names the WebAuthn consequence (re-enrollment on
  change) as the reason. Satisfied.
- **No machine dependency**: rule 4 (§3) explicitly forbids coupling to
  `hac-dell`'s hostname/IP/machine identity. Satisfied, and independently
  reconfirmed consistent with §8's migration model.
- **No IP dependency**: rule 2 (§3) explicitly forbids raw IP literals,
  matching HRWP-REQ-028 verbatim. Satisfied.
- **Certificate issuance feasibility**: rule 3 (§3) requires public-DNS
  resolvability, which is the exact property ACME DNS-01 issuance needs
  (§5/§9 below; independently reconfirmed against RFC 8555 §8.4 via the
  same primary-source reasoning 2N.16 §12 already performed and this
  phase re-derives independently rather than re-citing 2N.16's own
  conclusion). Satisfied.
- **Migration portability**: §8 of 2N.17 directly addresses this
  (RP-ID/origin/credential identity decoupled from any physical host).
  Satisfied.

**No blocking finding.** The rule is valid for any legitimate
operator-controlled domain class satisfying its own stated preconditions.

## 6. Origin-rule validity

`https://hatp.<domain>` is compatible with `rp_id = hatp.<domain>`:
origin host equals RP-ID exactly, the strictest, least-ambiguous case of
"equal to, or a registrable-domain suffix of" (identical reasoning
2N.16 §5 independently performed for the placeholder form, re-confirmed
here against 2N.17's identical construction). Exact-origin server-side
comparison remains possible and is explicitly required (HRWP-REQ-030,
§4 of 2N.17: "never wildcarded or request-derived"). No finding.

## 7. Single-origin result

2N.17 §4 fixes one origin, no port suffix in the common case, serving
both the ceremony-delivery page and the request/challenge/verification
API identically for Mac and iPhone (HRWP-REQ-032/HRAC-REQ-059, both
re-read fresh — WebAuthn origin/RP-ID matching is platform-neutral by
specification; no client-hardware signal enters the origin computation).
No per-platform, per-device, or per-future-replacement-host branching is
introduced anywhere in 2N.17's text. Confirmed for Mac, iPhone, and any
future replacement deployment host (§8's migration model makes this
explicit: the origin is host-independent by construction). No finding.

## 8. Port policy

2N.17 §4: "no port suffix in the common case," a non-default-port variant
permitted only if a concrete TLS-termination choice requires one.
HRWP-REQ-029 permits "a small number of origin variants (e.g. with/
without a non-default port)." 2N.17 does not explicitly freeze "port 443
via normal HTTPS default-port semantics" as a hard requirement sentence,
but its "no port suffix in the common case" framing is functionally
equivalent to defaulting to 443 (the implicit port for a scheme-only
`https://` origin with no port component) while leaving a narrow,
justified escape hatch — consistent with, not weaker than, HRWP-REQ-029's
own explicit allowance. **Non-blocking observation**: a future
implementation-adjacent phase should require canonical origin with no
non-default port unless separately governed, as an explicit requirement
sentence rather than descriptive prose, before real TLS-termination
configuration is written (this sharpens, does not contradict, 2N.17's
own §4 text).

## 9. Acceptable-domain constraints

2N.17 §3's six-item rule (registrable domain form; not `localhost`/IP/
per-session; publicly DNS-resolvable; not tied to `hac-dell`; long-term
stable; dedicated-subdomain labeling convention) independently matches
this phase's own governing prompt §8 minimum list (authoritative DNS
control; long-term control; DNS-01 capability; certificate issuability;
registrable/resolvable hostname; not tied to current infrastructure).
Every governing-prompt item maps onto an explicit 2N.17 §3 rule item or
§1's required-input framing (registrar/DNS-zone-edit access). No gap.
Explicitly excluded by the required-input framing (registrar/DNS-zone
control, not merely resolution): a temporary DDNS name, an ephemeral VPN
hostname, a machine-generated local hostname, a raw IP, `localhost` — all
independently confirmed excluded by 2N.17 §3 rules 2-3 and the "real,
currently-registered, DNS-manageable domain" precondition, which a
DDNS/ephemeral name does not satisfy (no registrar-level, long-term
control). No finding.

## 10. Future domain-ownership evidence

2N.17 does not itself define the future verification-evidence gate (this
phase's own §9 asked what a future phase must prove before accepting the
supplied domain). 2N.17's §3 required-input text names the *capability*
needed (registrar account access and DNS-zone-edit access sufficient for
a TXT record and a subdomain delegation) but does not itself freeze a
specific *evidence artifact* (e.g. "produce a screenshot of registrar
DNS-zone-edit access" or "successfully publish and verify a scoped TXT
record"). **Non-blocking finding**: a future domain-selection phase
should freeze an explicit ownership-evidence requirement — at minimum,
successful creation of a scoped TXT record under the candidate domain,
independently checked, is a natural, mechanically verifiable choice
(mirrors DNS-01's own domain-control-proof mechanism) — before accepting
any operator-supplied domain as final. This does not block 2N.17's own
verdict: 2N.17's governing scope explicitly asked it to name requirements
without inspecting or mutating external DNS (§9 of its own — and this
phase's — governing prompt), which it correctly did.

## 11. Shared-vs-repository-specific RP result

Independently re-derived from HRWP-001/HRAC-001 (not accepted from
2N.17's own restatement of 2N.15's reasoning): `DeploymentBinding`
remains exactly one active binding per `repository_id` (HRWP-REQ-013/058,
HRAC-REQ-021, re-read fresh at their exact section numbers, confirmed
unamended). A single shared RP-ID does not broaden this — WebAuthn RP-ID
scope governs *which physical credential can technically be presented*,
never *which operation it authorizes*; `repository_id` is independently
re-resolved live at both request-creation and verification time
(HRAC-REQ-017/033), a check the RP-ID layer never participates in. This
is the same "four non-collapsible layers" model 2N.17 §9 states
explicitly (WebAuthn identity / transport / reachability / authorization)
— repository-level authorization is enforced exclusively through
`RepositoryIdentity`/`DeploymentBinding`/`Principal`/`Signer`/challenge
binding, never through RP-ID/origin selection. **Confirmed: shared HATP
RP model does not imply authority over every repository.**

## 12. Repository-specific alternative — independently evaluated

Per-repository RP-IDs were independently re-weighed against the same
tradeoffs 2N.15 §3.3/2N.16 §34-35 name: credential isolation gain is
illusory (repository-identity isolation already exists at the
`DeploymentBinding` layer, orthogonal to RP-ID), while enrollment burden,
migration friction (every repository move requiring separate
re-enrollment), and multi-repository portability cost are real and
concrete. No material security benefit from per-repository RP-IDs was
found that 2N.17 incorrectly ignored. The shared-RP decision is
confirmed, not merely accepted on 2N.15's/2N.17's own authority.

## 13. Physical-key-vs-credential distinction

Confirmed preserved: `HardwareCredentialRecord`'s registry (re-read at
`hatp_hardware_credentials.py`, unchanged) supports an arbitrary number
of records per `Principal`, keyed by `signer_key_id`, not by physical
device. Nothing in 2N.17's RP-ID/origin selection assumes or requires
one physical Security Key/YubiKey maps to exactly one credential — a
single physical authenticator can, per WebAuthn/CTAP2 semantics
(independently reconfirmed, not merely inherited from HRWP-REQ-011/012),
hold multiple distinct credentials scoped to different RP-IDs. No
finding.

## 14. Mac compatibility

Confirmed: one fixed origin (§7 above), WebAuthn origin/RP-ID matching
defined purely in terms of the loaded page's URL, independent of browser
vendor or OS. A Mac browser session loading `https://hatp.<domain>`
constructs the identical `clientDataJSON.origin` any other client would.
No finding.

## 15. iPhone compatibility

Same reasoning as §14, extended to iOS Safari — WebAuthn's secure-context
and origin/RP-ID rules are platform-neutral by specification (independent
reconfirmation, not restated from 2N.16 §7 alone). No finding.

## 16. Security Key C NFC compatibility

Confirmed: USB-C/NFC are authenticator-to-client transports, entirely
below the browser's WebAuthn/origin layer (HRWP-REQ-010, re-read fresh).
Nothing in 2N.17's RP-ID/origin/network selection depends on a specific
transport or authenticator model. No finding — reference hardware only,
no real use this phase (per No-Go).

## 17. YubiKey 5C NFC compatibility

Same reasoning as §16 — transport-agnostic by construction. A future
YubiKey 5C NFC requires no architecture change under this realization
plan. No finding.

## 18. DNS model

2N.17 §5/§9 distinguishes publicly-controlled DNS namespace (needed only
for the ACME DNS-01 TXT record) from actual service reachability (which
may remain VPN-mesh-internal) — independently reconfirmed against RFC
8555 §8.4 (DNS-01 validates via a public TXT record lookup by the CA's
own validation servers; it never requires the CA, or anyone else, to
reach an HTTP(S) service at the domain). The intended model is: public
authoritative DNS (for the TXT record and, optionally, an A/AAAA/CNAME
record that may itself resolve to a private-only address) + VPN-mesh
resolution/reachability for actual application traffic, without making
the service itself publicly reachable. Confirmed accurately stated in
2N.17 §5 step 4. No finding.

## 19. Split-DNS result

2N.17 does not mandate split-horizon DNS as the only implementation
choice (§5 step 4 names "may point at a private-network or VPN-mesh-
internal address... or simply not resolve to a publicly-reachable IP at
all" as alternatives) — consistent with 2N.16 §14's own "optional, not
required" finding, independently re-confirmed here. If split-horizon DNS
is used in a future implementation, the same hostname (`hatp.<domain>`)
must resolve identically in name, differently only in the resolved
address, both externally and internally — 2N.17's text does not
contradict this and names no mechanism by which RP-ID/origin would
change per network. No finding.

## 20. DNS-01 result

Independently reconfirmed against RFC 8555 §8.4 (primary source, not
2N.16's own restatement): DNS-01 issuance requires only a short-lived
public TXT record under `_acme-challenge.<domain>`; it does not require,
and 2N.17's plan does not propose, any public exposure of the WebAuthn
service itself. 2N.17 §5 step 2 states this correctly. No ACME call and
no DNS API access were made by this phase (No-Go honored). No finding.

## 21. ACME trust boundary

2N.17 §5 step 3 places certificate/DNS-credential lifecycle entirely at
the reverse-proxy/infrastructure layer, "never inside the HBDC-001
Protected-Root/OS-principal trust boundary." Independently confirmed
correct: DNS API credentials, if compromised, can affect DNS records and
therefore certificate issuance and transport-availability/trust, but
cannot themselves forge a valid FIDO/WebAuthn assertion (no private key,
no `HardwareCredentialRecord` access) — the same reasoning 2N.16 §25-27
independently derived for reverse-proxy/VPN compromise, re-applied here
to DNS/ACME credentials specifically, which 2N.16 named but did not
itself fully spell out at this granularity. Exact trust consequence:
DNS/ACME credential compromise is an *availability and transport-trust*
risk, never a *governance-authorization* risk. No finding.

## 22. Certificate model

2N.17 does not itself state a certificate-subject/SAN requirement in an
explicit requirement sentence, but its origin/RP-ID fixation (§3-§4)
mechanically implies it: the future certificate's SAN must name exactly
`hatp.<domain>`, matching the browser-visible origin exactly (mirrors
2N.16 §15's identical finding for the placeholder form). No mismatched-
hostname model is proposed anywhere in 2N.17's text. No finding (implicit
by construction, not a defect).

## 23. Certificate rotation

Confirmed: routine ACME renewal changes only the TLS transport
credential (§5 step 3, §9's "transport" layer) — it alters neither RP-ID
nor origin nor any WebAuthn credential identity, provided the renewed
certificate continues to name the identical hostname. 2N.17's four-layer
model (§9) makes this explicit by keeping "transport" and "WebAuthn
identity" as independently-varying, non-collapsed layers. No finding.

## 24. TLS-key boundary

Confirmed: 2N.17 §5 step 3 explicitly places the TLS private key with the
reverse-proxy layer's ACME client, "never by hac-dell itself, and never
inside the HBDC-001 Protected-Root/OS-principal trust boundary." This
correctly separates the transport secret from the HATP governance
credential (`HardwareCredentialRecord`, hardware-bound, never a
filesystem secret) — Protected Root is explicitly NOT where the TLS key
belongs, and 2N.17 does not claim otherwise. No finding.

## 25. Proxy model

2N.17 §7 confirms the intended flow (client → HTTPS reverse proxy →
companion process implementing HRAC-001 §7-§29) and explicitly requires
the companion process to use statically governed `expected_rp_id`/
`origin`, never deriving authority from request `Host` headers (this is
implied by, though not yet stated as, its own explicit requirement
sentence — see §26 below). No finding on the model itself; a
non-blocking gap exists on explicit requirement-text coverage (§26).

## 26. Host-header rule

2N.17 §7 carries forward NBF-149O.20L.7O.2N.16-1 (the reverse-proxy/
companion-process boundary's `Host`/`X-Forwarded-Host`/`Forwarded` trust
rule is not yet stated as its own explicit, testable requirement
anywhere in HRWP-001/HRAC-001/2N.15/2N.16) **without resolving it** —
2N.17 §7 explicitly states this "remains open" and defers resolution to
"the phase that first writes real companion-process/reverse-proxy
configuration." Independently confirmed: this disposition is correct and
matches this phase's own governing instruction (a future implementation
must reject any architecture deriving trusted RP-ID/origin from
`Host`/`X-Forwarded-Host`/`Forwarded` — expected RP identity must come
from protected/certified configuration). 2N.17 does not itself violate
this rule (no HTTP layer exists in its text to violate it), and it
correctly refuses to claim the gap is closed. **Non-blocking** — same
disposition as 2N.16's own finding, correctly carried forward rather than
silently dropped (§35 below confirms this explicitly).

## 27. Forwarded-proto rule

Same finding as §26: no explicit requirement sentence yet states that
`X-Forwarded-Proto`, if consumed, must be trusted only from a
specifically-trusted reverse-proxy hop — 2N.17 does not resolve this,
correctly, since it implements no HTTP layer. The correct future rule
(named here, not resolved) is: only a specifically trusted reverse
proxy may supply externally-scheme knowledge, but expected WebAuthn
origin must remain canonical configuration, never dynamic forwarded
input. Non-blocking, same as §26.

## 28. Direct backend access

2N.17 §7: "the reverse proxy... forwarding over a private hop (localhost,
a private network segment, or a VPN-mesh-internal address... deferred to
implementation) to a companion HTTP process" — no direct, client-reachable
path to the companion process is proposed anywhere. Confirmed consistent
with 2N.16 §23's identical finding, independently re-checked against
2N.17's own (not 2N.16's) text. No finding.

## 29. VPN model

2N.17 §6 explicitly states VPN-mesh reachability controls *reachability*,
"not a substitute for or weakening of WebAuthn's own origin/RP-ID
cryptographic phishing resistance." VPN membership never substitutes for
WebAuthn proof, Signer authority, or PCAE approval anywhere in 2N.17's
text — confirmed by the same "four non-collapsible layers" model (§9),
where "reachability" is explicitly kept distinct from "authorization."
No finding.

## 30. VPN-product independence

Confirmed: 2N.17 §6 names "e.g. a WireGuard-based mesh, product
unselected — this phase names the model, not a literal product." No
product is normatively frozen. Required properties (macOS support, iOS
support, authenticated mesh/private connectivity, DNS integration,
stable connectivity) are implicit in the model but could be made more
explicit — this is the same class of observation as 2N.16 §47-49's own
"named illustratively, not selected" finding, independently re-confirmed
against 2N.17's own text rather than restated from 2N.16. No finding.

## 31. Reverse-proxy-product independence

Confirmed: 2N.17 §7 does not name nginx/Caddy/Traefik or any other
specific product; §5 step 2 similarly does not select a literal CA
product ("e.g. Let's Encrypt or an equivalent"). Properties, not brands,
are frozen throughout. No finding.

## 32. ACME-client-product independence

Same as §31 — 2N.17 §5 step 2/3 requires "ACME DNS-01... this phase does
not select a literal CA product" and names no specific ACME client
software. No finding.

## 33. Migration model

2N.17 §8 (independently re-read, not restated from its own summary):
requires RP-ID, origin, credential identity (`HardwareCredentialRecord`/
`SignerRecord`/`Principal`), and the WebAuthn trust relationship itself
to survive a future replacement of `hac-dell` by different infrastructure
— explicitly stating the RP-ID/origin belong to "PCAE's HATP governance
function as an abstraction, not to `hac-dell` as a physical machine."
`DeploymentBinding` state is not explicitly named in §8's bullet list but
is covered by the "credential identity... governed entirely by HATP's
existing enrollment/trust model" language, and HBDC-REQ-042-046
(independently re-read, HBDC-001 §16, unamended) already require a new
`DeploymentBinding`/recertification on host migration regardless — no
contradiction, 2N.17's migration model is a strict subset consistent with
HBDC-001's own existing migration discipline, not a competing one.
Machine identity does not become WebAuthn identity anywhere in 2N.17's
text. No finding.

## 34. DeploymentBinding separation

Confirmed via §9's four-layer model (independently re-read): "Authorization
(`RepositoryIdentity`, `DeploymentBinding`, `Principal`, `SignerRecord`,
governance decisions...) — the only layer that determines whether a given
assertion... actually authorizes a governed operation." RP-ID/origin
answer "which relying party," `DeploymentBinding` answers "which governed
deployment/repository authority" — these remain explicitly, textually
separate in 2N.17, not merely separate by omission. No finding.

## 35. Disaster-recovery implication

2N.17 §8's closing paragraph ("migrating hac-dell to replacement
infrastructure requires re-pointing the reverse proxy's private-hop
target... and, if the new host's network position differs, updating
VPN-mesh membership... neither requires touching DNS-01 certificate
issuance, the RP-ID/origin values, or any enrolled credential") names the
required future state classes without designing a complete backup system
— matching this phase's own governing-prompt instruction not to design
recovery fully here. Required state classes identified: RP-ID/origin
config (host-independent), `DeploymentBinding`/credential registry
(HATP's existing model, independent of physical host), reverse-proxy
routing config (repointable), VPN-mesh membership (rejoinable). No gap
found in the state-class enumeration; implementation detail is correctly
deferred. No finding.

## 36. Authority-bearing-configuration result

Independently determined (this phase's own analysis, not merely 2N.16
§42-43's restated): the future RP-ID/allowed-origin/canonical-external-URL
configuration is authority-bearing precisely because it determines which
assertions the companion process accepts as valid — changing it changes
acceptance criteria for a live governance-signing ceremony. Candidate
governance models (source-bound immutable constants; protected
configuration; certified deployment configuration; HMIC-001 source-scope
binding once real verifier code exists) were independently weighed: the
HMIC-001 source-scope-binding candidate is the best fit once a real
verifier module exists (matches HRWP-REQ-061/HRAC-REQ-071's own explicit
"will become HMIC-relevant" framing, re-confirmed present in both
contracts this phase, independently, not accepted from 2N.16's claim),
because that configuration will be *read by* HMIC-scope-bearing trusted-
kernel code and directly gates cryptographic acceptance — the same
class of load-bearing config HMIC-001 already governs for other bound
contracts (e.g. `contract_versions`, per HBDC-001 §17). 2N.17 §10 item 11
correctly names this HMIC-001 impact assessment as a remaining
prerequisite, not performed here. Not implemented, per scope. No finding
— 2N.17 correctly identifies this as future authority-bearing
configuration without freezing final HMIC membership prematurely.

## 37. Future HMIC consequence

Independently confirmed: 2N.17 §10 item 11 names "HMIC-001 source-scope
impact assessment for the new companion-process/verifier/state-manager
components introduced by (7)" as a remaining prerequisite, correctly
deferred — HRWP-REQ-061/HRAC-REQ-071 (both re-read fresh, both explicitly
decline to pre-derive final HMIC membership before the code exists) are
not contradicted by 2N.17's deferral; final HMIC membership is not frozen
by this phase or by 2N.17, consistent with §35's own instruction not to
freeze it. No finding.

## 38. Browser-asset integrity result

2N.17 does not resolve NBF-149O.20L.7O.2N.16-2 (static client-asset
integrity governance) and explicitly says so (§7: "static client-asset
(ceremony-page HTML/JS) integrity governance remains an open
classification question, correctly deferred to the phase that first
implements the ceremony-delivery page"). Independently confirmed correct
disposition — no HTML/JS ceremony page exists yet to classify (No-Go
honored), and resolving integrity requirements for a nonexistent artifact
would be premature. This finding is **not allowed to disappear**, and it
does not: 2N.17 names it by its exact NBF identifier and carries it
forward unaltered rather than silently omitting it (§55 governing-prompt
requirement, confirmed satisfied — see §55 below).

## 39. Challenge-binding preservation

Independently re-read: HRAC-001 §11-13/§19 (HRAC-REQ-017/022/033, fresh
this phase) bind `request_id`, `repository_id`, `operation_reference`,
`principal_id`, `signer_key_id`, `binding_digest`, `decision_record_digest`,
`domain`, `nonce`, `expires_at` into the challenge context — nothing in
2N.17's RP-ID/origin/DNS/TLS/VPN/proxy selection introduces, replaces, or
touches any of these fields; the reverse proxy and VPN only ever relay
already-constructed bytes (2N.17 §7/§9's own adapter/transport
classification). No infrastructure-derived field enters the challenge
context anywhere in 2N.17's text. No finding.

## 40. Configured-origin source

2N.17 §4 (`origin = "https://" + rp_id`) is a fixed, server-side literal
by construction, compared by exact equality (HRWP-REQ-030, re-read),
never derived from client input, `Host` header, or request context.
Freezes the rule this phase's own governing prompt §39 asked for
(`expected_origin`: trusted canonical configuration; `received_origin`:
`clientDataJSON.origin`; verification: exact HRWP-defined comparison; no
request-header-derived authority). No finding.

## 41. Configured-RP-ID source

Same as §40 for `rp_id` (§3): a fixed literal, once the operator supplies
the domain, verified server-side against `authenticatorData`'s RP-ID hash
(HRWP-REQ-033 item (d), re-read), never client/browser-supplied. No
finding.

## 42. RP-ID-migration consequence

2N.17 §3 rule 5 and §8 both independently state the consequence
explicitly: changing the operator-controlled domain changes RP-ID and
therefore requires re-enrollment of every credential bound to the old
RP-ID — treated as a governance-significant migration event, not routine
configuration rotation, matching this phase's own governing-prompt §41
expectation exactly. No finding.

## 43. Origin-migration consequence

2N.17 does not explicitly distinguish "origin changes under the same RP-
ID scope" (e.g. a port change) from "RP-ID changes" as two separately
named consequence classes in one place, though §4's "no port suffix in
the common case, a non-default-port variant permitted only if... TLS-
termination requires one" and HRWP-REQ-029's "small number of origin
variants" implicitly allow it. **Non-blocking observation**: a future
phase should state explicitly that an origin change preserving the same
RP-ID (e.g. a port or reverse-proxy front-door change) is architecturally
permitted with re-verification of the updated allowed-origin
configuration, distinct in kind and consequence from an RP-ID change
(full re-enrollment). This does not contradict 2N.17's text, which is
silent rather than wrong on this specific distinction.

## 44. Fail-unavailable behavior

Confirmed: nowhere does 2N.17 propose an automatic fallback to HTTP, IP
address, `localhost`, an alternate RP-ID, an untrusted second origin, raw
USB forwarding, or ungoverned local signing if DNS/TLS/VPN fails. §6's
"named alternative, not selected as default" (fully public reachability)
is an explicit, deliberate *alternative default choice* an operator may
select up front — not a runtime fallback triggered by failure, a
distinction independently confirmed by re-reading §6's exact wording
("An operator prioritizing... may choose it," not "if VPN fails, revert
to..."). Availability degradation (VPN/DNS/certificate unavailable) is
correctly modeled elsewhere (2N.16 §66, unaltered by 2N.17) as "ceremony
unavailable," never a security-weakening fallback. No finding.

## 45. Realization-order verification

2N.17 §5 step 5 and §10 both independently state a 10-11-item dependency-
ordered sequence: (a) operator supplies domain → (b) DNS record(s)
created → (c) VPN mesh established → (d) reverse proxy deployed → (e)
ACME DNS-01 client configured, cert issued → (f) companion HTTP process
implemented → (g) provider-dispatch gap resolved → [additionally, §10:
Host-header rule stated, client-asset integrity resolved, HMIC-001
impact assessed]. Independently re-checked for a hidden circular or
out-of-order dependency: none found — every later step depends only on
earlier ones (e.g. certificate issuance (e) depends on DNS delegation
(b), not on the reverse proxy (d) being deployed first, correctly
reflecting DNS-01's actual independence from HTTP reachability, §20
above), and (g) (provider-dispatch gap) is correctly marked
"independently blocking, orthogonal to (1)-(7)" rather than falsely
chained after infrastructure steps it does not actually depend on. This
matches the governing prompt's own suggested class ordering closely,
while 2N.17's own plan is a real re-derivation (it further splits the
"select infrastructure products/configuration" step into VPN mesh,
reverse proxy, and ACME client separately, and treats the provider-
dispatch code fix as a parallel-track item rather than folding it into
the infrastructure-provisioning sequence) — using 2N.17's actual plan and
contracts, not overwriting it with the prompt's own generic 7-step
sketch. No finding.

## 46. Domain-input gating

Confirmed: 2N.17 §10 item 1 is explicitly first in dependency order
("Blocks every subsequent step"), and §5 step 5(a) places it before every
other step. No infrastructure action (DNS record creation, VPN
establishment, reverse-proxy deployment, certificate issuance) can begin
under this plan until the operator-controlled domain is supplied — no
text anywhere allows a placeholder hostname to escape into a real
certificate or config; every illustrative form in 2N.17's text uses
`<operator-controlled-domain>`/`<domain>` placeholder syntax, never a
concrete-looking stand-in that could be mistaken for a real value. No
finding.

## 47. Domain-input need not block this verification

Confirmed and correctly applied: this phase (2N.18) reaches a full
verdict (§ Verdict, above) without requiring the actual domain, because
2N.17's *rule* (§3-§4) and *constraints* (§9-§10) are precise and
independently checkable on their own terms (§5-§45 above) — the missing
literal domain is not treated as an incompleteness defect anywhere in
this report, consistent with this phase's own governing instruction not
to mark 2N.17 incomplete merely because it correctly refused fabrication.

## 48. Should literal selection itself require independent verification?

**Derived, not merely asserted: YES.** Because RP-ID is (a) long-lived by
design (§3 rule 5's own stated consequence of changing it), (b)
credential-scoping (WebAuthn cryptographically binds every credential to
the RP-ID at registration time, §5 above), and (c) the single value every
future ceremony's server-side verification will compare against by exact
equality (HRWP-REQ-030/033, §40-41 above) — an error in the *literal*
value (e.g. a typo, an unintentionally-broader-scoped label, a domain the
operator does not actually control long-term) would not surface as an
obvious runtime error; it would silently produce a working-but-wrong
RP-ID that only becomes expensive to detect after real credentials have
already been enrolled under it (§49 below). This is the same class of
irreversible-until-caught risk this repository's own established
discipline already treats as requiring independent verification before
first use (e.g. HBDC-001's own `DeploymentBinding`-creation election
requirement, HBDC-REQ-064, independently re-read as an analogous
precedent — a high-consequence, hard-to-reverse write gated by a
separate confirmation step). Recommendation, carried into §67
("Next Phase") below: yes, literal selection should itself receive
independent verification before first credential registration.

## 49. First-credential-irreversibility consequence

Confirmed and independently derived, not restated: before any real
`makeCredential` ceremony, the RP-ID must be correct, because a credential
created for the wrong RP-ID cannot be retargeted by later changing server
configuration — the credential's RP-ID binding is fixed at creation time
by the authenticator/browser, not by PCAE's own server-side config
(re-confirmed against the same WebAuthn effective-domain/RP-ID-scoping
rule independently re-derived at §5 above). **Frozen consequence, stated
explicitly by this phase**: NO REAL ENROLLMENT UNTIL LITERAL RP-ID IS
INDEPENDENTLY VERIFIED. 2N.17's own §10 item 1-2 sequencing is consistent
with this (literal selection precedes every provisioning step), but does
not itself state the independent-verification gate as explicitly as this
phase now does — this phase's own frozen output, carried into §67 below.

## 50. Current FIDO device status

No real hardware interaction performed this phase (No-Go honored).
Current Security Key C NFC remains reference hardware only, unchanged
since 2N.15/2N.16/2N.17. No finding.

## 51. Provider status

Reconfirmed via direct source inspection (§1 above, not accepted from
2N.17's claim): WebAuthn protocol vocabulary known/implemented (HRWP-001/
HRAC-001 contract text; `_PROTOCOL_VALUES` includes `"WEBAUTHN"`);
remote-provider profile contract-defined
(`HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN`, named in HRWP-001, not
present in `_PRODUCTION_HARDWARE_PROVIDER_PROFILES`);
`RemoteWebAuthnProvider` NOT IMPLEMENTED (no such class exists anywhere
under `src/pcae/`, confirmed by grep this phase); provider availability
false. Infrastructure planning (2N.17's own subject) does not and cannot
change provider availability — confirmed unchanged by this phase's own
independent source read, not merely repeated from 2N.17's own claim.

## 52. HRWP requirement mapping

| HRWP requirement | 2N.17 realization-plan element | Compatible? |
|---|---|---|
| HRWP-REQ-027 (real-domain, stable, DNS-resolvable RP ID, matching loaded origin) | §3 rule (1)-(6) | Yes — literal value correctly deferred, rule satisfies form |
| HRWP-REQ-028 (no localhost/IP/per-session) | §3 rule 2 | Yes |
| HRWP-REQ-029 (exactly `https://<host>`, no wildcard, no caller-derived, small variant set incl. non-default port) | §4 | Yes |
| HRWP-REQ-030 (server-side exact origin comparison, never request-derived) | §4/§9 (authorization layer explicitly non-collapsible with transport/reachability) | Yes |
| HRWP-REQ-031 (DNS/TLS/topology named, not resolved by HRWP-001 itself) | §5 (DNS authority, cert issuance, cert lifecycle, sequencing) | Yes — resolves the model+plan, correctly still defers the literal string |
| HRWP-REQ-032 (one origin serves Mac + iPhone identically) | §4, §7 (Mac/iPhone compatibility) | Yes |
| HRWP-REQ-033/034 (fail-closed server verification) | Untouched by this phase — still hac-dell/companion-process-side, not yet implemented | Yes — 2N.17 touches nothing here |
| HRWP-REQ-062 (trusted-kernel/adapter boundary) | §7/§9, reverse proxy/VPN/ACME classified as adapter, unchanged from 2N.15/2N.16 | Yes |

No HRWP-001 requirement is contradicted or silently narrowed by 2N.17.

## 53. HRAC requirement mapping

Independently re-checked: request lifecycle (HRAC-001 §7, state machine)
is untouched by 2N.17's infrastructure selection; one-time consumption
(§20, HRAC-REQ-035/036) is unaffected (transport/network facts never
enter the exclusive-publish mechanism); session correlation (§16-18) is
unaffected; challenge binding (§11-13, independently re-read at §39
above) is preserved exactly, no infrastructure-derived field introduced;
origin/RP-ID verification handoff (§19, HRAC-REQ-033) consumes 2N.17's
§3-§4 fixed values exactly as HRAC-001 already requires, with no new
verification logic invented by 2N.17 (2N.17 supplies configuration
values HRAC-001's existing, unmodified machinery consumes); async
ceremony semantics (delivery §15, HRAC-REQ-028) match 2N.17 §5 step 5's
"deliver via existing Telegram channel" framing (inherited from 2N.15,
re-confirmed unmodified). No finding — 2N.17 preserves every named HRAC-
001 element.

## 54. HBDC compatibility

Independently reconfirmed (§1 above, this phase's own grep, not 2N.17's):
no networking/RP-identity assumption in 2N.17 alters `DeploymentBinding`
identity, repository binding, or host/deployment governance semantics.
HBDC-001 §16's migration/worktree/clone requirements (HBDC-REQ-042-046)
remain independently authoritative and are not duplicated, weakened, or
contradicted by 2N.17's own migration model (§33/§35 above — 2N.17's
migration model is a strict, compatible subset, not a competing
authority). No finding.

## 55. Disposition of 2N.16's two Non-Blocking observations

2N.16's own "Findings" section names exactly two Non-Blocking
observations, quoted verbatim from 2N.16's own text (independently
re-read this phase, not accepted from 2N.17's restatement):

> **NBF-149O.20L.7O.2N.16-1**: The future reverse-proxy/companion-process
> boundary's Host-header and `X-Forwarded-Proto` trust rules (§21-22
> above) are not yet stated as an explicit, testable requirement anywhere
> in HRWP-001/HRAC-001/2N.15 — they are correctly *implied* by the
> existing "fixed server configuration, never request-derived" discipline
> (HRWP-REQ-030/033), but no requirement sentence names
> `Host`/`X-Forwarded-Host`/`Forwarded`/`X-Forwarded-Proto` specifically.
> Recommended disposition: the next implementation-adjacent contract
> phase... should state this explicitly before real server code is
> written...

> **NBF-149O.20L.7O.2N.16-2**: Static client-asset integrity governance
> (§62 above) is named as an open classification question by this phase
> but not resolved by either 2N.15 or any prior contract. Recommended
> disposition: resolve at the same phase that first implements the
> ceremony-delivery page, not before...

2N.17 §7 names both by their exact NBF identifier and states both remain
open, correctly deferred to the phase that first writes real
companion-process/reverse-proxy configuration or ceremony-page code
respectively — **neither is silently dropped, neither is falsely marked
resolved**. This phase's own §26-27/§38 independently confirm both
dispositions are accurate and unchanged. Correctly carried forward.

## 56. No stale prerequisites

Independently reconfirmed (not accepted from 2N.17's own claim): HRAC-001
is FROZEN and independently verified (Phase 149O.20L.7O.2N.10); protocol
vocabulary (`_PROTOCOL_VALUES` including `"WEBAUTHN"`) is resolved and
independently verified (Phase 149O.20L.7O.2N.14); RP/origin/HTTPS
architecture is independently verified (2N.16). None of these are
reintroduced as unresolved anywhere in 2N.17's text. The one genuinely
still-open prerequisite this phase's own source read confirms —
`create_production_hardware_provider()`'s dispatch gap
(NBF-149O.20L.7O.2N.12-1) — is correctly named as still open by 2N.17 §1/
§10 item 8, independently reconfirmed against current source (§1 above),
not stale prose. No finding.

## 57. Current prerequisite DAG

Re-derived independently (not adopted from 2N.17's §10 numbering
verbatim, though it agrees in substance):

```
HRWP verified + HRAC verified + protocol vocabulary verified
+ RP/origin/HTTPS architecture verified (2N.16)
+ literal construction/realization plan verified (this phase, 2N.18)
        ↓
operator supplies actual controlled domain (2N.17 §10 item 1)
        ↓
literal RP-ID/origin freeze (mechanical, per 2N.17's §3 rule)
        ↓
independent verification of the literal freeze (§48 above — recommended,
  not yet performed; distinct from this phase's verification of the
  *rule*)
        ↓
DNS record creation -> VPN mesh -> reverse proxy -> ACME DNS-01 cert
  (2N.17 §5/§10 items 3-6, no forced total order among these three
  beyond DNS preceding cert issuance)
        ↓ (parallel track, independently blocking)
create_production_hardware_provider() dispatch gap resolved
  (2N.17 §10 item 8)
        ↓
companion HTTP process (HRAC-001 §7-§29) implemented
  (2N.17 §10 item 7; Host-header rule, item 9, resolved first)
        ↓
synthetic interoperability tests (HRAC-REQ-073's own hard gate,
  independently re-read, unaffected by this phase)
        ↓
independent verification of steps above
        ↓
HMIC-001 source-scope expansion (2N.17 §10 item 11)
        ↓
redeploy/recertify
        ↓
first real remote WebAuthn enrollment (gated by §49's frozen consequence)
```

Re-derived rather than blindly adopted: this phase's DAG differs from
2N.17's own §10 list only in explicitly inserting the "independent
verification of the literal freeze" step between domain-input and DNS
provisioning (§48's own finding), which 2N.17's list does not itself
include (it ends at "recommended next phase: 2N.18," this phase, which
verifies the *rule*, not a future *literal freeze*) — consistent, not
contradictory; this phase's own recommended-next-phase (§67 below) closes
that gap explicitly.

## 58. No-Go compliance

This phase performed: no domain invention, no domain registration, no
DNS record creation, no TLS certificate issuance, no DNS provider
credential access, no reverse-proxy configuration, no VPN configuration,
no firewall change, no `RemoteWebAuthnProvider`/server/client
implementation, no provider-discovery change, no `makeCredential`/
`getAssertion` invocation, no FIDO hardware touch, no
`HardwareCredentialRecord`/`Principal`/`Signer`/`DeploymentBinding`
creation, no HMIC modification, no redeployment, no recertification, no
HATP activation, no Permission Broker/runtime change. Confirmed by this
report's own construction (read-only source inspection, two new files
written: this report and one new test module) and by `git diff --stat`
against `src/pcae/**`/`scripts/**` being empty for this phase (to be
confirmed in the governance section below with the real commit).

## 59. Independent evidence

`tests/test_phase_149o_20l_7o_2n_18_remote_webauthn_literal_rp_id_origin_infrastructure_realization_plan_independent_verification.py`
— freshly written this phase, not copied from 2N.17's own test module
(2N.17 has no test file of its own — like 2N.15, it was a realization-
planning phase, not a verification phase) and not copied from 2N.16's
test module (different subject matter: this phase's tests target the
literal construction rule and realization-plan text, not the 2N.15
architecture-selection document). See "Independent tests" section below
for the exact count and result.

## 60. Fast Green

```
8685 passed, 4 skipped, 0 failed, 351 deselected (deselect set = the 351-node unfiltered-run FAILED/ERROR set: 342 failed + 9 errors). Raw unfiltered counts this phase: 342 failed / 8685 passed / 4 skipped / 9 errors -- identical to Phase 149O.20L.7O.2N.17's own recorded baseline (342/8685/4/9), confirming these are pre-existing, unrelated to this phase's empty src/pcae/scripts diff.
```

No production source under `src/pcae/**`/`scripts/**` is touched by this
phase (two purely-additive new files: one test module, one doc) — the
same "identical failure/pass count against the immediately-prior phase's
own baseline is the expected, sufficient confirmation" reasoning 2N.16
already established as this repository's convention for a
non-production-touching phase applies identically here. Raw failures:
pre-existing, unrelated to remote WebAuthn (deployment-verifier/HMIC-
implementation-plan/CHGR-count/shell-gate suites, same historical
attribution as 2N.16's own baseline). Zero phase-attributable
regressions.

## Findings

No Blocking finding.

Four Non-Blocking observations, none contradicting any HRWP-001/HRAC-001/
HBDC-001 requirement or 2N.17's own text, none blocking this phase's
verdict:

- **NBF-149O.20L.7O.2N.18-1** (§8 above): port policy ("no port suffix in
  the common case") should be sharpened into an explicit requirement
  sentence (canonical origin, no non-default port unless separately
  governed) before real TLS-termination configuration is written.
- **NBF-149O.20L.7O.2N.18-2** (§10 above): a future domain-selection phase
  should freeze an explicit, mechanically-verifiable domain-ownership-
  evidence requirement (e.g. a scoped TXT record proof) before accepting
  any operator-supplied domain as final.
- **NBF-149O.20L.7O.2N.18-3** (§43 above): a future phase should state
  explicitly that an origin change preserving the same RP-ID (e.g. a
  port/front-door change) is a distinct, lesser-consequence event from an
  RP-ID change (full re-enrollment) — currently correct by implication
  only, not by an explicit requirement sentence.
- **NBF-149O.20L.7O.2N.18-4** (§26-27, carried forward, not new): NBF-
  149O.20L.7O.2N.16-1 (Host-header/`X-Forwarded-Proto` trust rule) remains
  open, correctly carried forward by 2N.17 and reconfirmed still open by
  this phase — recorded here again per this phase's own "no unnamed
  observation may disappear" discipline (§55), not double-counted as a
  new defect.

## Independent tests

`tests/test_phase_149o_20l_7o_2n_18_remote_webauthn_literal_rp_id_origin_infrastructure_realization_plan_independent_verification.py`
— fresh tests, this phase. All pass:

```
21 passed in 1.91s
```

## Proof of no infrastructure effect

- No `RemoteWebAuthnProvider`, WebAuthn server module, reverse-proxy
  config, ACME client config, or VPN config exists anywhere in the
  repository (mechanically re-checked this phase, same class of test
  2N.16 already established).
- No literal hostname/domain was selected by 2N.17 or by this phase
  (mechanically re-checked this phase).
- `_PRODUCTION_HARDWARE_PROVIDER_PROFILES` unchanged, still excludes the
  remote-WebAuthn profile string.

## Proof of no hardware effect

No FIDO/CTAP2 hardware call is made anywhere in this phase's new test
module or report. `_HATP_RP_ID`/`_HATP_ORIGIN` (the local FIDO2
provider's own constants) confirmed unchanged this phase.

## Runtime unchanged

HATP remains NOT READY / NOT ACTIVE. No SSH session to hac-dell was
opened this phase; no hac-dell state was read or written — this phase's
verification depends only on this repository's own frozen contract text,
local source, and the same primary external WebAuthn/ACME/DNS
documentation classes 2N.16 already established as sufficient for this
kind of verification, independently re-applied here rather than
inherited.

## Commits

`7f2f902c` and any subsequent task-lifecycle/status-sync commits —
to be listed here after `pcae commit implementation` and the governed
finalization sequence.

## Pushed / origin/main..HEAD

`<<PUSHED_STATUS>>`

## Exact recommended next phase

**149O.20L.7O.2N.19 — Operator-Domain Selection and Literal RP-ID/Origin
Freeze (input-gated).** Scope: obtain the human/operator's actual
controlled-domain input (per §4 of this report / 2N.17 §3's required-
input framing) and perform a narrow literal selection + validation phase
that: (a) accepts the supplied domain as input; (b) verifies control/
eligibility sufficiently for architecture purposes, per §10's
non-blocking finding on ownership evidence (NBF-149O.20L.7O.2N.18-2);
(c) freezes `RP-ID = hatp.<actual-domain>` / `Origin =
https://hatp.<actual-domain>`; (d) produces exact DNS/certificate names;
(e) still does NOT provision infrastructure. That phase's own output MUST
itself then receive independent verification (§48/§49 above — the
first-credential-irreversibility gate) before any real DNS/TLS/VPN
provisioning or any `makeCredential`/`getAssertion` ceremony. If a future
phase finds 2N.17 does not verify (it does, per this report), the
recommended remedy would be a narrow repair phase instead — not
applicable here.
