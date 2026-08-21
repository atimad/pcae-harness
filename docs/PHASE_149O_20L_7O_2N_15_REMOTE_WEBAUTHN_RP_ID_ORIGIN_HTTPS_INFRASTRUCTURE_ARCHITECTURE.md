# Phase 149O.20L.7O.2N.15 — Remote WebAuthn RP-ID / Origin / HTTPS Infrastructure Architecture Selection

**Status:** COMPLETE — ARCHITECTURE ANALYSIS AND SELECTION ONLY. NO DNS PROVISIONED. NO TLS CERTIFICATE ISSUED. NO REVERSE PROXY CONFIGURED. NO FIREWALL CHANGE. NO HTTP SERVER IMPLEMENTED. NO CLIENT IMPLEMENTED. NO `RemoteWebAuthnProvider` CODE. NO PROVIDER-DISPATCH CHANGE. NO HMIC CHANGE. NO REDEPLOYMENT. NO CERTIFICATION CHANGE. NO CREDENTIAL CREATED. NO HARDWARE TOUCHED.

## 0. Purpose and relationship to HRWP-001 / HRAC-001

HRWP-001 v1.1 (`docs/contracts/HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md`) freezes the cryptographic/evidence-format contract for remote WebAuthn but explicitly leaves the **literal** RP-ID/origin/HTTPS infrastructure unresolved (HRWP-REQ-027, HRWP-REQ-031: "this contract does NOT select a literal hostname value… each named here as an explicit infrastructure requirement the implementation phase must resolve"). HRAC-001 v1.0 (`docs/contracts/HATP_REMOTE_ASSERTION_CEREMONY_CONTRACT.md`) freezes the asynchronous request/response/evidence orchestration layer and carries the same open dependency forward unmodified (HRAC-REQ-062).

This phase is that infrastructure-selection step, named by both contracts' own implementation-sequence sections (HRWP-REQ-066 step (3)/HRAC-REQ-074 step (3)) as a prerequisite to server implementation. It resolves the **architecture** — which model, why, what it plugs into — not the literal values (no domain is registered, no certificate is issued). This document performs no contract freeze of its own; it is a design decision record a future HRWP-001/HRAC-001-companion or amending phase can cite when it does select literal values and, if warranted, formalizes them into contract text.

## 1. Independent source re-derivation this phase performed

Read fresh, this phase, not from prior phase summaries:

- `docs/contracts/HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md` (HRWP-001 v1.1, full text, §12–§14/§26–§27/§40 in particular).
- `docs/contracts/HATP_REMOTE_ASSERTION_CEREMONY_CONTRACT.md` (HRAC-001 v1.0, full text, §11–§13/§40–§41 in particular).
- `src/pcae/core/hatp_fido2_provider.py` — confirms the exact local/raw constants this architecture must NOT reuse unmodified: `_HATP_RP_ID = "hatp.pcae.local"`, `_HATP_ORIGIN = "pcae-hatp://hatp.pcae.local"` (lines 102–104), and the exact verification checks (`clientDataJSON.origin`, `rp_id_hash`, challenge-as-payload-digest) a remote provider's server-side verifier must reproduce with new constants (§16 there).
- `src/pcae/core/hatp_providers.py` — confirms `HATP_HARDWARE_PROVIDER_V1` is a security-property name, not a protocol tag (line 179 comment); confirms `create_production_hardware_provider()`'s allowlist (`_PRODUCTION_HARDWARE_PROVIDER_PROFILES = (HATP_HARDWARE_PROVIDER_V1,)`, line 187) does not yet include `HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN` and that adding a profile string alone would not by itself route correctly, since the factory's post-allowlist branch always attempts `Fido2HardwareProvider` first, unconditionally — matches PROJECT_STATUS.md's own account of Phase 149O.20L.7O.2N.13/.14's finding (NBF-149O.20L.7O.2N.12-1, Outcome A, "not a present defect, a future implementation obligation"). **This architecture phase changes nothing here and depends on nothing here being resolved** — dispatch is a code-routing question or­thogonal to RP-ID/origin/HTTPS selection.
- `src/pcae/core/hatp_hardware_credentials.py` — confirms `_PROTOCOL_VALUES = frozenset({"FIDO2", "PIV", "WEBAUTHN"})` (line 62) **already includes `"WEBAUTHN"`**. This is a fresh, independent re-confirmation (via `git log -S'"WEBAUTHN"'`) that Phase 149O.20L.7O.2N.13 (commit `778aa39a`) already performed the additive closed-vocabulary widening HRWP-REQ-019/HRAC-REQ-066 named as an open prerequisite, and Phase 149O.20L.7O.2N.14 already independently verified it. **This architecture phase's own RP-ID/origin/HTTPS selection has no dependency on that prerequisite** (HRAC-REQ-066 already states the same: signer resolution never reads `protocol_name`), but it is worth recording here that the prerequisite this phase's own governing prompt flagged as "already resolved" (`HRAC-001 is already FROZEN and INDEPENDENTLY VERIFIED — do not carry forward stale prose treating it as unresolved`) is corroborated directly against current source, not merely against the prior phase's own claim.
- `src/pcae/core/hatp_bootstrap.py` — confirms `SignerRecord` (keyed by `signer_key_id`, carries `principal_id`/`provider_profile`/`status`) and `DeploymentBinding` (keyed by `repository_id`, carries `principal_id`+`signer_key_id`+`provider_profile`, exactly one active binding per repository) schemas (lines 103–140), matching HRWP-001 §6/§32-33 and HRAC-001 §9-10's own descriptions exactly — no drift found.
- `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` (HBDC-001) — confirms deployment topology (OS-principal separation, Protected Root ownership, execution-environment lock) is **host-level** trust topology and explicitly does not define network reachability/DNS/TLS (grep for "network"/"VPN"/"topology" across the contract returns no requirement text constraining it) — this architecture phase is free to select network topology without HBDC-001 amendment or conflict.
- `docs/PHASE_149O_20L_7O_2N_6_...ARCHITECTURE.md` §26 (prior architecture analysis) — read fresh for orientation, not relied on for conclusions; its own one-line RP-ID framing ("a private/LAN/VPN domain behind a reverse proxy, or a dedicated small HTTPS companion service in front of hac-dell") is independently re-derived and expanded below, not merely restated.

No DNS, TLS, reverse-proxy, or Tailscale/VPN configuration exists anywhere in this repository today (`grep -rli` across `docs/**` for prior infrastructure decisions returns no prior commitment) — this phase starts from a clean slate, consistent with HRWP-REQ-027's "no PCAE-controlled domain, LAN name, or reverse-proxy hostname has been provisioned or decided as of this freeze."

## 2. Constraints this selection must satisfy (carried forward, not reopened)

From HRWP-001 (unamended):
- HRWP-REQ-027/028: stable, non-`localhost`, non-raw-IP, non-per-session, real-domain-form RP ID, DNS-or-equivalent resolvable from both a Mac and an iPhone browser.
- HRWP-REQ-029: allowed origin(s) exactly `https://<the RP-ID-matching host>` (no `http://`, no wildcard, no caller-derived origin).
- HRWP-REQ-031: DNS name, TLS certificate (public-CA vs private-CA tradeoff named, not resolved), TLS-terminating endpoint (direct-on-hac-dell vs reverse-proxy, topology LAN/VPN/public), all explicit open decisions.
- HRWP-REQ-032: one stable origin serves both Mac and iPhone identically — no per-platform branching in the server-side contract.

From HRAC-001 (unamended):
- HRAC-REQ-061: the ceremony-delivery page SHALL be served from the identical fixed origin HRWP-REQ-029 requires — no separate "delivery domain."
- HRAC-REQ-062: this contract consumes a single fixed `expected_rp_id`/allowed-origin set; no new infrastructure dependency beyond HRWP-001's.

From HBDC-001 (unamended): hac-dell remains the sole authoritative backend for `RepositoryIdentity`/`Principal`/`SignerRecord`/`HardwareCredentialRecord`/`DeploymentBinding` — whatever network/TLS topology this phase selects, it MUST NOT relocate governance authority off hac-dell (HRWP-REQ-003 restated).

## 3. RP-ID architecture — selected model

**Selected: a dedicated, real, publicly-registrable subdomain of a domain the human already controls (e.g. `hatp.<controlled-domain>`), used as the RP ID, with network reachability restricted below the TLS layer (§5) rather than by using a non-public domain.**

### 3.1 Candidates considered

| Model | RP-ID form | Verdict |
|---|---|---|
| A. Dedicated hostname on a real, human-controlled public domain | `hatp.example-domain.tld` | **Selected** |
| B. Organization domain used directly | `example-domain.tld` (no subdomain) | Rejected |
| C. Repository-specific domain (per-repo RP ID) | `pcae-harness.example-domain.tld` or similar, one per repository | Rejected as the *default*, permitted as a documented variant |
| D. Internal-only domain (private DNS + private CA) | `hatp.internal.lan` or similar, resolved only inside a private network/VPN, trusted via a private root CA | Rejected as primary, named as fallback |
| E. Raw IP / `localhost` / per-session value | — | Rejected — explicitly forbidden by HRWP-REQ-028 |

### 3.2 Why A over B (organization domain directly)

WebAuthn's RP-ID scoping rule is "an RP ID must be a registrable domain suffix of, or equal to, the origin's effective domain" — using the bare organization/personal domain directly as RP ID would let *any* subdomain or service ever hosted under that domain register or assert credentials scoped to it (WebAuthn RP-ID matching is suffix-inclusive: a credential registered for `example-domain.tld` is valid for every subdomain of it, not the reverse). HATP governance signing is a single, narrow, high-value ceremony type; scoping its RP ID to a dedicated subdomain (`hatp.example-domain.tld`) means a completely unrelated future service hosted at, say, `blog.example-domain.tld` can never be positioned to interfere with or extend the credential's RP-ID scope, and vice versa — this is the same "narrowest value that names exactly the one authority" discipline HBDC-REQ-072 already applies to `DeploymentBinding.authority_scope` in this repository, applied here to DNS/RP-ID scope instead. This also mirrors HRWP-REQ-008's own naming discipline (name by security property/narrow purpose, not convenience).

### 3.3 Why A over C (repository-specific/per-repo domain)

This governing phase's own scope explicitly requires "no singleton assumptions" (§6 of the governing prompt) for **credential** selection, but RP-ID is a different axis: it scopes *WebAuthn credential portability*, not authority. A per-repository RP ID would mean a credential enrolled while working on one PCAE-governed repository is **not** invocable for a different PCAE-governed repository without a second, separate enrollment ceremony under a second RP ID — even though `DeploymentBinding`/`SignerRecord` already support one `Principal` legitimately owning multiple credentials, and even though the human's *physical* authenticator is the same device regardless of which repository they're currently governing. Splitting RP ID by repository multiplies enrollment ceremonies for no security benefit (repository identity is already enforced independently, at the `repository_id`/`DeploymentBinding` layer — HRAC-REQ-017/033 re-resolve `repository_id` live at both request-creation and verification time; RP-ID is not the layer WebAuthn or this architecture needs to carry repository identity). One stable RP ID for "HATP remote WebAuthn" as a whole (across every PCAE-governed repository this human operates) is simpler, requires fewer enrollment ceremonies, and does not weaken any existing repository-identity check. **Named exception, not forbidden:** an operator governing repositories under genuinely different trust domains (e.g. separate organizations, separate humans) MAY legitimately choose per-domain or per-organization RP IDs — this is a deployment-operator choice this architecture does not foreclose, but it is not the default this phase recommends for the single-operator (hac-dell) case this repository currently has.

### 3.4 Why A over D (internal-only domain, private CA)

Model D (private DNS name + private CA) avoids ever exposing a real, publicly-resolvable DNS label — a genuine privacy/attack-surface reduction HRWP-REQ-031 itself names as private-CA's main advantage ("avoids exposing a public DNS name for a personal deployment"). It is rejected as the *primary* recommendation for one concrete, source-grounded reason: **it requires provisioning a private root CA certificate as explicitly trusted on the iPhone client** (via a signed configuration profile, `Settings → General → About → Certificate Trust Settings → Enable Full Trust`), a manual, per-device, non-standard trust operation that itself becomes a second, informally-governed trust artifact outside HATP's own credential/revocation model (HHCE-001/HPSE-001 govern hardware-credential revocation; nothing in this repository governs private-CA-root revocation or rotation). A publicly-trusted CA certificate (Model A) requires no such out-of-band trust operation on either client device — the browser's existing public trust store already trusts it, satisfying HRWP-REQ-031's "simplest client compatibility" branch directly. Model D remains a documented, legitimate fallback (§3.5) for an operator who prefers zero public DNS footprint over zero private-CA-trust ceremony — the tradeoff is named, not concealed, per this contract family's own established discipline (HRWP-REQ-026's own "does not conceal the largest architectural difference" precedent).

### 3.5 Fallback model, named not selected

If a future operator determines public DNS exposure of even a dedicated subdomain is unacceptable (e.g. a stricter personal threat model), Model D (private DNS + private CA, or a VPN-mesh-integrated equivalent that itself issues publicly-trusted certificates for a private-only-reachable name — see §5.3) remains architecturally valid under this same RP-ID discipline (§3.2/§3.3 reasoning is model-independent). This is recorded so a future implementation phase is not forced to re-derive the tradeoff from nothing.

## 4. Origin architecture

**Selected: exactly one allowed origin, `https://hatp.<controlled-domain>` (no port suffix in the common case; a non-default-port variant permitted only if the concrete deployment's reverse-proxy/TLS-termination choice, §5, requires one — HRWP-REQ-029's own explicit allowance), serving both the WebAuthn ceremony page (client) and the request/challenge/verification API (server) from the identical origin.**

Rationale, independently derived:
- HRAC-REQ-061 already forbids a separate "delivery domain" distinct from the WebAuthn RP origin — a single origin for both the ceremony-delivery page and the API surface is not a convenience choice, it is the only HRAC-001-conformant shape.
- `http://` is categorically excluded — WebAuthn's secure-context requirement (HRWP-REQ-031) makes this a hard technical constraint, not a preference.
- No wildcard origin, and no origin computed from caller-supplied input (HRWP-REQ-029) — the origin is a fixed literal the server-side verifier compares against exactly, mirroring `hatp_fido2_provider.py`'s own `parsed.client_data.origin != _HATP_ORIGIN` discipline (confirmed at `hatp_fido2_provider.py:503`) with the new fixed value substituted in, per HRWP-REQ-030.
- One origin for both Mac and iPhone: WebAuthn origin/RP-ID matching is platform-neutral by specification (HRWP-REQ-029's own closing clause) — no PCAE-side per-platform branching is introduced by this architecture, consistent with HRWP-REQ-032/HRAC-REQ-059.

## 5. HTTPS / TLS deployment model

**Selected: hac-dell does not itself terminate public TLS. A thin reverse proxy in front of hac-dell terminates TLS for the fixed origin (§4) and forwards plaintext (or mTLS-internal) traffic to a companion HTTP process running on hac-dell (or colocated with it) that implements the HRAC-001 request/challenge/verification surface. Network reachability to that reverse proxy is restricted to a private mesh/VPN, not the open public internet, even though the DNS name and TLS certificate are publicly issued (§5.3).**

### 5.1 Where TLS terminates

Two candidates were weighed:

- **(a) Direct-on-hac-dell termination** — hac-dell's own companion process holds the certificate/private key and terminates TLS itself. Simpler topology (one fewer hop, one fewer component to trust), but couples hac-dell (the Protected-Root-owning, HBDC-001-governed trusted host) directly to internet-facing TLS/HTTP-parsing code, expanding the attack surface of the one host HBDC-001 already goes to considerable lengths to isolate (OS-principal separation, Protected Root ownership/permissions, HMIC-scoped execution-environment lock).
- **(b) Reverse-proxy termination (selected)** — a narrow, well-audited, widely-deployed reverse proxy (e.g. Caddy or nginx; this phase does not select a literal product, only the model) terminates TLS and forwards to hac-dell's companion process over a private, non-internet-facing hop (localhost, a private network segment, or a VPN-mesh internal address). This keeps hac-dell's own attack surface limited to what it already has today (SSH, the governance CLI) plus one narrow internal listener never itself directly internet-reachable. TLS certificate lifecycle (renewal, rotation) is handled entirely by the reverse-proxy layer, outside HBDC-001's Protected-Root/OS-principal trust boundary — consistent with HRWP-REQ-062/HRAC-REQ-070's own "thin, replaceable adapter outside the trusted kernel" classification for the HTTP transport layer.

Rationale for (b): mirrors this contract family's own repeated "trusted kernel vs. thin adapter" boundary (HRWP-REQ-062, HRAC-REQ-070, restated at §7 below) — TLS termination and HTTP parsing are exactly the kind of "relay bytes the trusted kernel produces and validates, carries no independent trust" component both contracts already classify as outside the trusted kernel. Putting it in a separate process (even if colocated on the same physical machine) keeps that classification true in practice, not only in principle: a bug in the reverse proxy's HTTP/TLS parsing cannot, by construction, read Protected Root state or `HardwareCredentialRecord`/`DeploymentBinding` files directly — it can only reach the narrow internal API the companion process exposes.

### 5.2 Does PCAE own the endpoint or consume an existing gateway

**Selected: PCAE (a new, narrowly-scoped companion process, not the existing `pcae` CLI itself) owns the internal HRAC-001 request/verification API; a separate, off-the-shelf reverse proxy owns the public TLS endpoint.** PCAE does not consume a third-party API gateway/BaaS — HATP-001's Model B ("registry resolves governance identity; hardware proves possession") requires hac-dell to remain the sole authority for challenge issuance/verification (HRWP-REQ-003), which forecloses delegating that logic to an external SaaS gateway. The reverse proxy is infrastructure plumbing (TLS termination, request forwarding), not a governance-authority delegate — it never sees `HardwareCredentialRecord`/`DeploymentBinding` state and is never in the trusted-kernel boundary (§7).

### 5.3 Certificate ownership model

**Selected: a publicly-trusted CA certificate (e.g. via ACME/Let's Encrypt), issued using the DNS-01 challenge method rather than HTTP-01.** This is the load-bearing detail that reconciles §3.4's "public DNS, no private-CA-trust ceremony" preference with §5.1's "not open to the public internet" preference: DNS-01 issuance proves domain control via a DNS TXT record, not by exposing an HTTP server to the public internet — so the certificate can be publicly trusted (satisfying client compatibility on both Mac and iPhone with zero manual trust-store configuration) while the actual HTTPS listener stays reachable only over a private network path (§5.4), never from the open internet. This is a well-established pattern for exactly this shape of requirement (a real, publicly-trusted TLS identity for a service that is deliberately not publicly reachable) and requires no bespoke PCAE-side certificate-authority code — it is standard reverse-proxy/ACME-client configuration, entirely within the "thin adapter" boundary (§7).

Rejected alternative: a private/internal CA (§3.4's Model D) remains valid but is not the default recommendation, for the client-trust-ceremony reason already given.

### 5.4 Network topology — reachability, not just TLS

**Selected: the reverse proxy is reachable only over a private network path — a VPN mesh (e.g. WireGuard-based) joining hac-dell's network segment, the Mac, and the iPhone — never a port exposed to the raw public internet.** This is an explicit, additional defense-in-depth layer, named here as **not a substitute for WebAuthn's own origin/RP-ID/challenge verification** (HRAC-REQ-061's phishing-boundary discipline is not weakened or replaced by this choice — restated explicitly per HRAC-REQ-061's own "no alternate origin… would weaken WebAuthn's own phishing resistance" caution, which this network restriction does not violate: it restricts *reachability*, not *origin*, and introduces no second/alternate origin).

Rationale: HATP governance signing authorizes source-code rollback/promotion operations — a narrow, high-value ceremony. Even though WebAuthn's cryptographic protocol is itself phishing- and replay-resistant by design (HRAC-REQ-040/HRWP-REQ-033), an internet-reachable ceremony-delivery page is additionally reachable by every internet scanner and every attacker attempting credential-stuffing/DoS/probing against the request-fetch surface (HRAC-REQ-030) — none of which succeeds cryptographically, but all of which needlessly widens the population of parties who can even attempt it, and needlessly exposes the companion process's HTTP-parsing surface to the entire internet rather than to a small, pre-authenticated (at the network layer) set of devices. Restricting network reachability to a private mesh is a standard "reduce the blast radius of an unknown future HTTP-parsing bug" measure, layered on top of (never instead of) WebAuthn's own cryptographic guarantees — consistent with this repository's general fail-closed, defense-in-depth discipline (e.g. HRWP-REQ-034's "fail closed on any single check" precedent, applied here at the network layer as one more independent check, not a replacement for any existing one).

**Named alternative, not selected as default:** fully public reachability (no VPN gate) remains architecturally *possible* under this same RP-ID/origin/certificate model — WebAuthn's own security does not depend on network-layer restriction — and an operator who prioritizes "reachable from any network without a VPN client installed" over "minimize internet-facing attack surface" MAY choose it without violating any HRWP-001/HRAC-001 requirement. This phase names it as an explicit, available choice, not a rejected one, consistent with HRWP-REQ-031's own instruction to name rather than resolve the LAN-only/VPN-gated/public tradeoff.

## 6. Remote ceremony boundary — client/server split (confirmed compatible, not redesigned)

This is already fully specified by HRWP-001 §19 (HRWP-REQ-038) and HRAC-001 §48 (HRAC-REQ-070); this architecture selection changes none of it and is confirmed compatible with the RP-ID/origin/HTTPS model above:

**Client side** (thin, untrusted, outside the trusted kernel — §7): browser/mobile WebAuthn ceremony invocation (`navigator.credentials.get()`), authenticator interaction (NFC tap / USB-C touch), user-presence/user-verification as performed by the platform and authenticator. The client fetches exactly HRAC-REQ-030's field list from the origin selected in §4, over the TLS connection terminated per §5.1, and posts exactly HRAC-REQ-032's response schema back to the same origin. It never sees `binding_digest`, `decision_record_digest`, `principal_id`, or `signer_key_id` in cleartext (HRAC-REQ-030's own exclusion list) and never runs on hac-dell itself.

**Server side** (hac-dell, or the narrowly-scoped companion process colocated with it, inside the trusted kernel — §7): challenge creation and canonical-context construction (HRAC-REQ-022), request-state management (HRAC-001 §7), the credential allow-list (HRWP-REQ-014/HRAC-REQ-020), assertion validation (HRWP-001 §16, reusing this architecture's fixed `expected_rp_id`/allowed-origin values from §3–§4), authority mapping via the unmodified `DeploymentBinding`/`SignerRecord` resolution (HSCE-REQ-080, confirmed unchanged at `hatp_bootstrap.py`), and audit-evidence capture (HRAC-001 §29, reusing `HATPEvidenceStore.publish` unmodified per HRAC-REQ-052).

The RP-ID/origin/HTTPS selection above does not move any of this boundary: the reverse proxy (§5.1) sits strictly on the client-facing side of the "server side" list above, never inside it — it relays TLS-terminated bytes to the companion process, which is where every item in the paragraph above actually executes.

## 7. Trusted-kernel / adapter boundary (this architecture's own component list, extending HRWP-REQ-062/HRAC-REQ-070)

```
                                   PUBLIC / VPN-MESH BOUNDARY
                                   (network reachability, §5.4)
  ┌──────────────┐   HTTPS (public CA cert,   ┌──────────────────┐
  │  Mac browser │──────────DNS-01 issued─────▶│  Reverse proxy    │
  │  iPhone      │◀─────────§5.3───────────────│  (TLS terminator, │  ADAPTER — thin,
  │  browser     │                              │  HTTP forwarder)  │  replaceable, no
  └──────────────┘                              └─────────┬─────────┘  independent trust
         ▲  untrusted for                                 │ private hop
         │  governance identity                            │ (localhost /
         │  (HRWP-REQ-038)                                  │ private net /
                                                             │ VPN-internal)
                                                             ▼
                                              ┌──────────────────────────┐
                                              │  Companion HTTP process   │
                                              │  (request/challenge/      │  TRUSTED KERNEL —
                                              │   verification API,       │  HMIC-scope-bearing
                                              │   HRAC-001 §7-§29)        │  once implemented
                                              └────────────┬──────────────┘  (HRWP-REQ-062 /
                                                            │                 HRAC-REQ-070)
                                                            ▼
                                              ┌──────────────────────────┐
                                              │  hac-dell governance      │
                                              │  kernel (unchanged):      │
                                              │  RepositoryIdentity,      │
                                              │  Principal, SignerRecord, │
                                              │  HardwareCredentialRecord,│
                                              │  DeploymentBinding,       │
                                              │  HATPEvidenceStore        │
                                              └──────────────────────────┘
```

Inside the trusted kernel (unchanged classification, restated with this phase's components named): challenge construction/binding, request-state management, credential allow-list construction, HRWP-001 §16 verification call and TOCTOU re-resolution, exclusive-publish consumption, evidence-record/envelope building — all already named by HRWP-REQ-062/HRAC-REQ-070. **This architecture adds no new trusted-kernel component**; the "companion HTTP process" box above is exactly where HRAC-001 §7-§29's existing trusted-kernel logic runs — an execution-location decision, not a new authority-bearing component.

Outside the trusted kernel, thin/replaceable, named explicitly by this architecture: the reverse proxy (TLS termination, HTTP forwarding — §5.1), the DNS/ACME/certificate-lifecycle tooling (§5.3), and the VPN-mesh client software on Mac/iPhone/hac-dell (§5.4, reachability only — it grants network path, never governance authority, mirroring HRAC-REQ-027's "possessing a session locator is not authority" restated for network reachability).

## 8. Challenge/assertion flow (end-to-end, this architecture's values substituted into HRAC-001's frozen sequence)

```
1. Human triggers a governed operation requiring a remote signature
   (already authorized per HRAC-REQ-016/057 -- e.g. an ag3/ag5 rollback
   already approved through its own governing contract).
2. hac-dell (companion process, trusted kernel) creates a PENDING
   remote assertion request (HRAC-001 §7-§8), resolving repository_id /
   DeploymentBinding / SignerRecord live, and binds:
     expected_rp_id     = "hatp.<controlled-domain>"        (§3)
     allowed origin     = "https://hatp.<controlled-domain>" (§4)
     domain             = "PCAE/HATP/HRAC/SIGN/V1"           (HRAC-REQ-026, unamended)
3. hac-dell delivers a single-use HTTPS URL under that same origin
   (HRAC-REQ-028, §4) -- e.g. via the existing Telegram notification
   channel (HRWP-REQ-044, outbound-only, never inbound authority).
4. Human opens the URL on Mac or iPhone. TLS is terminated by the
   reverse proxy (§5.1) using the publicly-trusted, DNS-01-issued
   certificate (§5.3), reached only over the private VPN mesh (§5.4).
5. Browser fetches HRAC-REQ-030's field set from the companion process
   (relayed through the reverse proxy) and invokes
   navigator.credentials.get() with challenge/expected_rp_id/
   allowCredentials exactly as delivered -- the browser itself enforces
   that the page's actual origin matches "https://hatp.<controlled-
   domain>" before it will even construct clientDataJSON (this is
   WebAuthn's own built-in phishing defense, not something this
   architecture implements).
6. Authenticator performs the getAssertion ceremony locally (NFC tap /
   USB-C touch); private key never leaves the device.
7. Browser returns HRAC-REQ-032's response schema to the same origin.
8. hac-dell (companion process) re-resolves live state (TOCTOU,
   HRAC-REQ-033 step 2), calls HRWP-001 §16's verifier with the fixed
   expected_rp_id/origin from step 2, transitions VERIFIED, captures
   evidence via the unmodified HATPEvidenceStore (§29), transitions
   COMPLETED.
```

No step in this flow is implemented by this phase; every step reuses HRAC-001/HRWP-001 text verbatim, with only the RP-ID/origin/certificate/network literals from §3-§5 substituted into the already-frozen shape.

## 9. Threat analysis

| Threat | Mitigation, and where it lives |
|---|---|
| **Phishing** (attacker-controlled page tricks the human into completing a ceremony against a fake origin) | WebAuthn's own origin/RP-ID enforcement, browser-side (step 5 above) — a page not served from `https://hatp.<controlled-domain>` cannot construct a valid `clientDataJSON` the authenticator will sign against this RP ID. This architecture contributes nothing new here beyond correctly fixing one real, stable origin (§4) instead of the local provider's non-browser-enforceable internal string (§3.4's rejected-D and HRWP-REQ-026's own finding) — the fix *is* making phishing resistance possible at all for the remote path. Network-layer VPN gating (§5.4) is additional depth: an attacker not on the mesh cannot even reach a real ceremony page to attempt to mimic, though this is not the primary defense. |
| **Origin confusion** (a legitimate-looking but distinct origin, e.g. a typo-squatted domain or a different subdomain of the same parent domain, is accepted) | Server-side origin check against the single fixed literal (HRWP-REQ-030, reproducing `hatp_fido2_provider.py`'s own `!=` comparison discipline with the new value) — no wildcard, no prefix/suffix matching, exact string comparison. Choosing a *dedicated* subdomain (§3.2) rather than the bare organization domain narrows what "the right origin" even means, reducing the population of same-organization subdomains an attacker could plausibly get confused with a legitimate ceremony page for. |
| **Replay** (a previously captured valid assertion reused later) | HRAC-001's one-time consumption (§20, HRAC-REQ-035/036, exclusive-publish via `os.link`) and challenge-context digest binding (§11-12) — a captured assertion's `clientDataJSON.challenge` is bound to one specific `request_id`/canonical context; replaying it against a new request fails the challenge-match check (HRAC-REQ-033 step 3). This architecture selection introduces no new replay surface; it supplies the fixed RP-ID/origin values that check consumes. |
| **Stale challenge** (a response arrives long after issuance, e.g. after the human's authorization context has changed) | HRAC-REQ-013/037's `expired_challenge` rejection, short fixed expiry (HRAC-001 §20-§21, unamended) — happens entirely at the request-state layer, independent of this phase's RP-ID/origin/network selections. |
| **Wrong repository binding** (assertion produced for/verified against the wrong `repository_id`) | `repository_id` is re-resolved live at both request-creation and verification time (HRAC-REQ-017/033 step 2, TOCTOU recheck) — RP-ID is deliberately *not* the layer carrying repository identity (§3.3's rationale) precisely so this check remains repository-identity-specific and cannot be confused with, or substituted for, the (deliberately shared, one-for-all-repositories) RP-ID/origin selected here. |
| **Wrong signer selection** (assertion accepted for a `signer_key_id` other than the one `DeploymentBinding` resolved) | `allowCredentials` is server-constructed, scoped exclusively to the request-creation-time-resolved `signer_key_id` (HRAC-REQ-020/HRWP-REQ-014/036) — never broadened by client input or browser "discoverable credential" behavior. This architecture's single shared origin does not weaken this: `allowCredentials` scoping happens per-request at the application layer, not by RP-ID/origin partitioning. |
| **Credential substitution** (a different physical authenticator's credential accepted in place of the resolved one) | The credential-ID check inside `allowCredentials` (previous row) plus HRWP-001 §16's signature verification against the specific stored public key for the resolved `signer_key_id` (HRWP-REQ-033 item (f)) — cryptographically enforced, independent of RP-ID/origin/network topology. |

## 10. Compatibility confirmation — no singleton assumptions introduced

- **Multiple credentials per Principal**: unaffected. One shared RP ID (§3.3) does not constrain how many `HardwareCredentialRecord`s a `Principal` owns (HRWP-REQ-011/012, HRAC-REQ-021) — every credential enrolled under this RP ID remains independently selectable via the existing `allowCredentials` mechanism (§6/§9).
- **Multiple Signers**: unaffected — `SignerRecord` keying and multi-signer-per-Principal support (HPSE-001, unamended) is orthogonal to which RP ID/origin/network topology this phase selects.
- **`DeploymentBinding` EXPLICIT_SIGNER selection**: unaffected and directly reused — §6/§8's flow explicitly re-derives `DeploymentBinding`-resolved `(principal_id, signer_key_id)` live at both request-creation and verification time (HSCE-REQ-080, HRAC-REQ-019), exactly as already frozen; this architecture selection supplies only the transport-layer values (RP-ID, origin, certificate, network path) that flow *around*, never *into*, that resolution.
- **Local/raw FIDO2 path**: unaffected and unmodified (HRWP-REQ-064, restated) — `hatp_fido2_provider.py`'s own internal `_HATP_RP_ID`/`_HATP_ORIGIN` constants are untouched by this phase; the two providers use disjoint RP-ID/origin values by design (HRWP-REQ-026's own finding: the local constants are "NOT reusable, unmodified" — this phase does not attempt to reuse them, it selects a distinct real value instead).

## 11. Decision summary

| Question | Decision | Rejected alternatives |
|---|---|---|
| RP-ID | Dedicated subdomain of a human-controlled real domain (`hatp.<controlled-domain>`), one value shared across all PCAE-governed repositories this operator controls | Bare organization domain (§3.2); per-repository domain, as default (§3.3); internal-only/private-CA domain, as default (§3.4, named fallback); raw IP/localhost (forbidden by contract) |
| Origin | Exactly `https://hatp.<controlled-domain>`, serving both ceremony page and API | Separate delivery domain (forbidden by HRAC-REQ-061); `http://` (forbidden by contract); wildcard/multi-origin |
| TLS termination | Reverse proxy in front of hac-dell, private internal hop to a companion process | Direct-on-hac-dell termination (rejected: expands trusted-host attack surface) |
| Certificate | Publicly-trusted CA via ACME DNS-01 challenge | Private/internal CA (named fallback, §3.5); no cert / self-signed (forbidden — browsers reject) |
| Network reachability | Private VPN mesh only (defense-in-depth, not a substitute for WebAuthn security) | Fully public reachability (named as available, not default); LAN-only without VPN (weaker: excludes remote iPhone use case this architecture exists to serve) |

## 12. Success criteria — self-check

- HRWP-001 RP-ID/origin requirements concretely resolved at architecture level: §3-§4 (literal value still deferred to implementation phase, per HRWP-REQ-027's own framing — this phase resolves the *model*, not the *string*).
- HRAC-001 ceremony flow has a compatible infrastructure model: §6, §8 confirm every HRAC-001 step maps onto this architecture without modification.
- No existing HATP contract assumption violated: §2/§10 confirm against HRWP-001, HRAC-001, HBDC-001, HPSE-001/HHCE-001 (via `DeploymentBinding`/`SignerRecord`/`HardwareCredentialRecord`, unamended).
- No implementation performed, no real authority state changed: confirmed — no source file under `src/pcae/**` is touched by this phase; no DNS/TLS/reverse-proxy/VPN artifact was provisioned.

## 13. No-Go confirmation

No hardware touched. No `makeCredential`/`getAssertion` executed. No credential created. No DNS/TLS provisioned. No production source modified (`git status --short` confirms only this document plus `PROJECT_STATUS.md`/`CHANGELOG.md`/`.pcae/**`/task-lifecycle files change). No HMIC change. No hac-dell mutation (no SSH session to hac-dell was opened this phase; this phase performed no remote read or write against it — unlike Phase 149O.20L.7O.2N.6's own read-only hac-dell inspection, this phase needed no fresh hac-dell state, since RP-ID/origin/HTTPS selection depends only on this repository's own frozen contract text and local source, not on hac-dell's live state).

## 14. Recommended follow-up (restated from HRWP-REQ-066/HRAC-REQ-074, not reopened or reordered)

A future implementation phase may now consider, only after this architecture is itself independently verified: remote WebAuthn server/companion-process implementation (§5-§8's model as its blueprint); literal RP-ID/domain selection and real DNS-01 certificate issuance; reverse-proxy and VPN-mesh provisioning; provider-dispatch resolution in `create_production_hardware_provider()` (named open, unresolved by this phase, per §1's finding); HMIC-001 source-scope impact assessment for the new companion-process/verifier/state-manager components (§7). Only after those steps, in the order HRWP-REQ-066/HRAC-REQ-074 already fix, should real remote WebAuthn enrollment be considered.
