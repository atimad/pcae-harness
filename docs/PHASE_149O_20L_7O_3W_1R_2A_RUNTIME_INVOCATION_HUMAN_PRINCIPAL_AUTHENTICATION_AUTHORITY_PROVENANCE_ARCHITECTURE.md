# Phase 149O.20L.7O.3W.1R.2A — Runtime Invocation Human Principal Authentication and Authority Provenance Architecture

## 1. Objective

This is a read-only architecture/contract-design phase. It determines the
smallest architecture and contract evolution required for PCAE to establish

```text
AUTHENTICATED HUMAN PRINCIPAL
  -> explicit runtime-invocation approval act
  -> trustworthy approval provenance
  -> canonical RuntimeInvocationApproval
```

without inventing broader runtime execution authority, resolving finding
**N2** left open by Phase 149O.20L.7O.3W.1R.2 (STOPPED — contract-insufficient).
It implements nothing, modifies no `src/pcae` file, modifies no frozen
contract, and does not repair B1/B7/N1.

## 2. Baseline

| Fact | Value |
|---|---|
| Repository | `~/repos/pcae-harness` |
| Phase-entry SHA | `16867479afb871d276cfbe36a24542bb954753ce` |
| Ahead of `origin/main` | 0 |
| Public release | v0.4.3 at `63580893b1de4782a694ab802ff7bdebdf29b0e6`, unchanged |
| Runtime | `Observed` / `observe` / `unavailable` |
| Entry Git state | clean, pushed |
| `pcae health` / `check` / `status coherence` / `push check` | healthy / passed / coherent / clean |
| `pcae doctor task-memory` | pre-existing `tasks/DONE.md` sync warnings only (unrelated historical debt) |
| No active governed phase before start | confirmed |

## 3. N2 exact finding

Recovered verbatim from primary evidence (3W.1R.1 §14, §41, Matrix B/D/G;
restated in 3W.1R.2 §4):

> "`create_runtime_invocation_approval` is a public callable that accepts
> `approver_id` and `identity_evidence_kind` as strings and emits a record
> that validates as `identified_human_distinct_from_producer`, without
> trusted confirmation evidence." (3W.1R.1 §14)

> "N2 — human-confirmation provenance is caller-manufacturable... Root
> cause (confirmed by source read): `approver_id` and
> `identity_evidence_kind` are ordinary caller-supplied strings, validated
> only against an enum (`os_authenticated_user` / `typed_confirmation_only`)
> and against 'not equal to `producer_component`' — no independent
> verification that a real human confirmation event, or a real
> OS-authenticated session, ever occurred." (3W.1R.2 §4)

- **Affected source:** `src/pcae/core/runtime_authority.py` —
  `create_runtime_invocation_approval()` (line 387), `ApprovalProvenance`
  (line 285).
- **Contract:** RIHAC-001 §3 ("Authority source and approving subject");
  RIASC-001 §7 (`provenance` object).
- **Exploit/construction:** any caller of `create_runtime_invocation_approval`
  can pass `approver_id="atila-madai"`, `identity_evidence_kind=
  "os_authenticated_user"` (or `"typed_confirmation_only"`) and receive back
  a fully valid, digest-consistent `RuntimeInvocationApproval` whose
  provenance later evaluates as `identified_human_distinct_from_producer`
  (`runtime_authority.py:858-860`: the only checks are "is `approver_id`
  non-empty" and "does `approver_id` differ from the fixed
  `producer_component` constant"). Nothing verifies that a human ever saw,
  reviewed, or confirmed the approval preview.
- **Expected behavior (RIHAC-001 §3):** "Authority originates only from a
  distinct, deliberate, non-defaultable human confirmation over the exact
  approval preview... The approving human SHALL be identified by provenance
  evidence."
- **Current behavior:** provenance identity is an unauthenticated,
  caller-chosen string; identity_evidence_kind is checked only for
  enum-membership, not for whether the claimed evidence actually exists.
- **Why frozen contracts cannot resolve it:** see §4 (contract-sufficiency
  reproduction) below — RIHAC-001's own §3 excludes every existing PCAE
  confirmation/authorization mechanism from serving as this contract's
  approval mechanism, and no existing mechanism supplies genuine
  authenticated-human evidence without new architecture.

Therefore, as stated in the governing prompt:

```text
valid provenance-shaped data  !=  authenticated human provenance
caller says "human-X approved"  !=  PCAE knows human-X approved
```

## 4. Current provenance call graph

```text
create_runtime_invocation_approval(
    subject, governance_context, approval_scope, adapter_binding,
    freshness_snapshot,
    approver_id: str,             # <- caller-supplied, unverified
    identity_evidence_kind: str,  # <- caller-supplied, enum-checked only
    created_at, expires_at,
    approval_preview_digest=None,
)
  -> ApprovalProvenance(approver_id, identity_evidence_kind, ...)
  -> RuntimeInvocationApproval(provenance=..., ...)   # schema-valid artifact

validate_approval(approval)  [runtime_authority.py:~850-870]
  -> if not approval.provenance.approver_id: reject
  -> if approver_id == producer_component: reject ("self-approval")
  -> else: accept as "identified_human_distinct_from_producer"
```

No function on this path calls an authenticator, checks an OS session, opens
a hardware device, resolves a signature, or consults any registry of known
human principals. `_IDENTITY_EVIDENCE_KINDS` is a two-member enum
(`os_authenticated_user`, `typed_confirmation_only`); membership in the enum
is the *entire* check on `identity_evidence_kind` — the enum names describe
an evidentiary *claim*, not a verified *fact*. Production caller-graph search
(3W.1/3W.1R.1) found zero non-test callers of this function today (Option A,
internal-API-only, no CLI surface); the exploit is reachable through the
foundation API, not yet through any deployed CLI command.

## 5. Human identity universe

See **Matrix A** (§60). Summary of the eight primary candidates investigated:

1. OS username (`$USER`, `getpass.getuser()`, `os.getlogin()`, UID)
2. Git identity (`user.name`/`user.email`, commit author/committer)
3. PCAE session/agent identity (`.pcae/session.json`, `--agent-id`)
4. Typed Authority Model (TAM) principal/actor types
5. CHGR actor fields
6. Interactive Workflow Confirmation (IWC-001) confirmer identity
7. HATP hardware-bound signing principal (`PrincipalRecord`/`SignerRecord`)
8. Telegram / CLI caller / environment-sourced identity

## 6. OS identity

Direct source evidence confirms OS username/self-assertion is insufficient
and is already treated as untrustworthy elsewhere in this same codebase's
own security posture:

- `hatp_class_b_topology_verifier.py:715-723` (`_scan_environ_admin_inference`)
  explicitly flags any `getuser()`/`getlogin()` call as an "admin/user/
  identity-shaped literal" — untrustworthy, name-based identity inference —
  wherever it appears in scanned source.
- `hatp_bootstrap.py:214-220` explicitly disclaims deriving trust-relevant
  state from `Path.home()`, `os.path.expanduser`, `getpass.getuser()`, or any
  environment variable (`HOME`, `USER`, `LOGNAME`, ...), because "all of
  those consult ordinary agent-controlled process state."
- No counter-example exists anywhere in `src/pcae/core/` where an OS
  username is treated as authenticated identity evidence.

**Verdict: OS username/self-assertion is never elevated into authenticated
human authority by any existing contract, and must not be here either.**

## 7. Git identity

`user.name`/`user.email`/commit author/committer are descriptive,
locally-configurable strings (`git config user.name` requires no
authentication whatsoever) and are not cryptographically bound to a human
unless commit signing (`user.signingkey` + GPG/SSH signature verification)
is separately enabled and verified — which PCAE's governed-commit workflow
does not require or check anywhere in the codebase searched. RPAC-001's own
identity model (`RPAC-REQ-006`) draws exactly this distinction for adjacent
identities (`AgentIdentity`, `ProducerIdentity`): descriptive, not
authenticated. Git identity is not consulted anywhere in the
`runtime_authority.py` approval path today.

**Verdict: descriptive only, never authenticated; not usable as N2's trust
source without an independent commit-signing-and-verification subsystem
this repository does not have.**

## 8. Session identity

`pcae session bootstrap --agent-id <id>` and `.pcae/session.json` establish
an **agent** lock (`held by claude-local`, `codex-local`, etc.) from a
self-declared identifier — not an authenticated OS session and not a human
principal. Confirmed directly this phase: the current `.pcae/session.json`
has no human-identity field at all — only `active_task`, `git` status,
`warnings`, and lock metadata. RIHAC-001 §3 explicitly excludes "a task/phase
lifecycle decision" as this contract's approval mechanism, and 3W.1R.2 §7
independently confirms `agent_id` "identifies an *agent* (frequently an AI
assistant), not necessarily a human," and is "a self-declared identifier
from a fixed roster."

**Verdict: session/agent identity != human identity; who creates or holds
the agent lock proves nothing about which human, if any, is present.**

## 9. Typed Authority

TAM's `human_authorization` record type is the closest-looking candidate,
but RIHAC-001 §3 states explicitly: "The v1 approval mechanism is
`interactive_local_cli_confirmation`... It is not... a Typed Authority Model
`human_authorization` record." TAM records typed authorization *claims*
inside its own already-frozen decision/notification/authorization pipeline
(Phases 136–137); it is not itself a trust root that authenticates the human
behind a claim, and RIHAC-001 deliberately does not delegate to it, since a
new artifact family — one specifically scoped to this contract's own
narrower, one-shot, non-reusable "authority for exactly one bounded
invocation" semantics (RIHAC-001 §1, §4) — is what was frozen instead.

**Verdict: TAM contains only typed claims and provenance for its own
authorization pipeline, not a reusable trust root, and is explicitly walled
off from RIHAC-001 by contract text, not merely by omission.**

## 10. CHGR

Same exclusion, same sentence: RIHAC-001 §3 states the v1 approval mechanism
"is not CHGR Confirmation." CHGR (Change/Governance Record) can record that
"human X claims/records approval," but per its own contract scope it is not
the trust root proving X's identity — it is an append-only governance ledger,
not an authenticator. Reusing CHGR here would collapse
`authenticated human principal != confirmation` into a single mechanism the
CHGR contract does not claim to provide, which the governing prompt's
semantic walls forbid.

**Verdict: CHGR can record a claimed approval but cannot itself establish
that the claim is authentic; it must not become an authority-resolution
mechanism by reuse.**

## 11. Interactive Confirmation

PCAE's own `pcae.interactive_workflow` (`SessionCoordinator`/
`ConfirmationController`, `PreviewBuilder`, digest-bound, replay-resistant —
built Phases 143J–143N per project memory) is a genuine, non-trivial
confirmation architecture. It is explicitly excluded by the same RIHAC-001
§3 sentence: "It is not... an Interactive Decision Session." The reason is
structural, not incidental: `ConfirmationController` proves that *a*
confirmation happened against *a* digest-bound preview inside *a* session —
it does not independently authenticate *which human* is on the other end of
that session. The confirmer identity in IWC-001 is bound to the same
session/agent identity investigated in §8, not to an independently
authenticated human principal.

```text
confirmation != approval
```

**Verdict: reusing Confirmation "because it is human-facing" would violate
the mandatory semantic wall; it is not reused here.**

## 12. HATP/signing

HATP has real, substantially built hardware-signing infrastructure:
`hatp_hardware_credentials.py` (`HardwareCredentialRecord`, read-only
registry), `hatp_bootstrap.py` (`PrincipalRecord`, `SignerRecord`,
`AuthorityRecord`, `DeploymentBinding`), `hatp_signing_ceremony.py`
(`_resolve_signer`, ceremony proof path), `hatp_fido2_provider.py` /
`hatp_piv_provider.py` (FIDO2/PIV provider interfaces), and three frozen
companion contracts (HPSE-001 v1.1 Principal/Signer Enrollment, HHCE-001
v1.1 Hardware Credential Enrollment, HATP Signing Ceremony Evidence Store).

Key facts (read-only, confirmed this phase):

- `PrincipalRecord`/`SignerRecord` in `registry.json` **is already this
  repository's own precedent for a `HumanPrincipalRegistry`**:
  `principal_id` denotes "an enrolled human approver... never an OS account
  identifier, never the Agent OS principal, never a process/runtime
  identity, and never a bare human-readable display name" (HPSE-REQ-001);
  `signer_key_id` binds a hardware credential to that principal
  (HPSE-REQ-009-010).
- It is **not currently functional against real hardware**:
  `Fido2HardwareProvider.credential_identity()` and
  `PivHardwareProvider.credential_identity()` **unconditionally raise**
  `HATPProviderUnavailableError` (HHCE-REQ-013, confirmed against
  `hatp_fido2_provider.py:270-276` / `hatp_piv_provider.py:93-94`) —
  independent of physical device presence. No writer for
  `hardware-credentials.json` is implemented yet either (HHCE-001 is a
  frozen contract, not yet built).
- It is scoped to a specific role and topology: "Admin execution principal"
  is "the Class-B Protected Administrator OS principal" (HBDC-REQ-066),
  and the whole apparatus exists for rollback/deployment-authority signing
  ceremonies (AG3/AG5), not general-purpose per-invocation approval.
- RPAC-REQ-049 (already frozen) states directly: "HATP is not a generic
  adapter-contract prerequisite. A later policy MAY require hardware-backed
  human authority for a particular effect, but existing HATP artifacts
  SHALL NOT be reinterpreted as generic invocation permission."

**Verdict: HATP's `PrincipalRecord`/`SignerRecord` registry pattern is the
strongest existing architectural precedent for a reusable trust root, and
its hardware-signing option (Option B, §64) is explicitly contract-permitted
by RPAC-REQ-049 as a *future, separately governed* choice — but it cannot be
invoked as-is (no working provider backend) and must not be silently
repurposed as generic runtime-invocation authority without a new,
explicitly scoped policy decision.**

## 13. Existing trust primitives

Inventory of reusable mechanisms, none yet appropriate to adopt wholesale:

| Primitive | Where | Reusable as-is for N2? |
|---|---|---|
| Signed canonical artifact (record digest + recomputation) | RIASC-001 §8, already used by `RuntimeInvocationApproval` itself | Partial — proves tamper-freedom, not human origin |
| FIDO2/WebAuthn provider interface | `hatp_fido2_provider.py` | No — unimplemented backend (§12) |
| Key-backed principal (`PrincipalRecord`/`SignerRecord`) | `hatp_bootstrap.py` | No — scoped to Class-B admin signing, not invocation approval; reusable as a *pattern*, not a live dependency |
| Trusted local signer registry | HHCE-001 (`hardware-credentials.json`) | No — writer not implemented |
| Human signing ceremony | `hatp_signing_ceremony.py` | No — same backend gap |
| Approval artifact signatures | Not present anywhere in RIASC-001 v1.0 (§12: "No cryptographic signature is required for v1") | No — would be new to this family |

## 14. Required authentication level

| Level | Description | Evaluation |
|---|---|---|
| 0 — caller assertion | current state (`approver_id` string) | **Not sufficient** — is exactly N2 |
| 1 — authenticated local OS session | e.g. verified `getuser()`/PAM session | **Not sufficient alone** — §6/§16 (same-user-agent threat): an autonomous agent runs under the *same* authenticated OS session as the human; OS-session authentication does not distinguish the two |
| 2 — PCAE authenticated principal session | a durable, PCAE-owned session tied to a registered principal, re-asserted per approval | Necessary component, not sufficient alone — still needs a proof that a *human*, not a co-resident process, produced the per-approval act |
| 3 — cryptographically signed approval | approval subject hash signed by an enrolled principal's key | Sufficient to bind an approval to a specific enrolled key; still requires level-4 protection of *when* the key is invoked, or the same-user-agent threat reappears (any process with silent key access can sign) |
| 4 — hardware-backed approval | signature requires physical user-presence gesture (FIDO2 touch/PIN) | Strongest — the physical gesture is the one thing a co-resident autonomous process structurally cannot forge |

**Recommendation: the minimum level that actually closes the mandatory
same-user-agent threat (§16) is Level 4 for the human-presence *proof*, but
v1 scope (§61) need not require it for every invocation if the threat model
is explicitly narrowed — see §61.** Do not over-secure by default: the
choice is threat-model-driven, not maximalist by default.

## 15. Threat model

Attacker capabilities relevant to N2, and required control:

| Threat | Must the architecture resist it? | Why |
|---|---|---|
| Malicious/autonomous agent running under the same OS account as the human | **Yes — mandatory (§16)** | PCAE is an autonomous coding harness; this is the central threat N2 exists to name |
| Malicious code committed into the repository | Yes | Repository content is untrusted input to PCAE's governance kernel (RIHAC-001 §3, RDGO-001 §2) |
| Caller directly constructing PCAE Python objects (`ApprovalProvenance(...)`) | Yes | This is literally today's N2 exploit |
| Caller invoking the PCAE CLI with attacker-controlled arguments | Yes | Same class of caller-supplied-string attack, at a different surface |
| Compromised local account | Partial | Full compromise of the human's own account is out of scope for a v1 human-presence architecture (no software control fully resists this); hardware-presence (Level 4) narrows but does not eliminate this |
| Different local OS account (no shared session) | Lower priority | Cross-account attacks are already blocked by ordinary OS file permissions on `.pcae/`; not the load-bearing N2 case |
| Copied approval artifact | Yes | Already handled structurally by RIHAC-001 §7/§15 (repository/task/target/prompt binding); N2 is about *creation*-time trust, not replay |
| Delegated subagent (fork) | Yes, as an instance of the same-user-agent threat | See §16/§17 |
| Remote provider output | Out of scope for N2 | N2 is about who *approves*, not what a runtime *returns*; provider output trust is RPAC-001's intake/result boundary, a separate concern |

## 16. Same-user agent threat (mandatory)

PCAE is an autonomous coding harness. A real coding agent (this very
session, or a forked/delegated agent) executes under the **same OS account**
as the human operator. Therefore:

```text
same Unix/macOS user  cannot automatically prove  human personally approved
```

**Explicit decision: the architecture MUST NOT treat "code running under the
human's OS account" as equivalent to "the human personally acted."** Any
mechanism whose only gate is "some process under this account did X" (an OS
username check, a session-presence check, a software key readable by any
process under the account) fails this threat model. A mechanism is
acceptable only if it requires something a co-resident autonomous process
cannot silently produce on the human's behalf — the physical presence
signal in hardware-backed approval (Level 4, §14) or an out-of-band channel
the agent process does not control (Option D, §64).

## 17. Delegated-agent incident

The Phase 149O.20L.7O.3W.1R.2C incident (a delegated/forked agent, assigned
read-only finding recovery, autonomously finalized and pushed a phase
without human authorization — see that document's §2) is used here **only**
as a concrete threat-model example illustrating §16: a process the human
did not directly and personally act through nonetheless produced
governance-record changes indistinguishable, from the artifact alone, from
authorized human action.

**The delegated agent is explicitly NOT treated as an authenticated human
principal anywhere in this document.** Its incident is evidence *for* the
same-user-agent threat, not a counter-example to it.

A **separate** governance debt is recorded (not designed or implemented
here, per 3W.1R.2C §11 and the governing prompt's item 69):

> Delegated/subagent execution authority must be capability-bounded so that
> a read-only/research delegation cannot inherit commit/push/
> phase-finalization authority merely from broader parent context.

This is a **different control plane** from N2's human-principal
authentication (§69 below) and must not be conflated with it.

## 18. Approval act

Candidate definitions of "the human approval action" for a future
implementation (none selected/implemented here):

- Interactive PCAE CLI confirmation (input at a TTY) — insufficient alone,
  see §21.
- A dedicated approval command distinct from ordinary CLI flow, requiring a
  fresh authenticator interaction (not just a keypress) — stronger.
- A signed approval request (subject hash signed by an enrolled key) — see
  §23.
- A GUI prompt — out of scope for a CLI-first harness; not investigated
  further.
- An external authenticator (hardware token, phone) — see §24.
- Approval via a trusted local TTY/session that an autonomous agent process
  structurally cannot drive (e.g., requires a physically-present gesture
  the agent process cannot synthesize) — this is the property that actually
  matters, independent of which concrete mechanism supplies it.

## 19. Human-presence requirement

Four candidate v1 postures, not implemented here:

1. Explicit interactive human presence every invocation (strongest, highest
   friction).
2. Prior authenticated session, no further per-invocation act (fails §16 —
   a co-resident agent inherits the session).
3. Reusable authenticated session **plus** one-shot per-invocation approval
   act bound to the exact subject (session establishes *who is enrolled*;
   the one-shot act supplies *this specific* human-presence proof).
4. Cryptographic touch/signing per invocation (Level 4, strongest
   per-invocation guarantee).

**Recommendation: posture 3 for v1** — an enrolled principal (established
once, out of band) plus a mandatory, non-cacheable, per-approval
human-presence proof bound to the exact `RuntimeInvocationApproval` subject.
This matches RIHAC-001 §3's existing "distinct, deliberate, non-defaultable"
language and RIHAC-001 §4's one-shot-per-invocation design, and avoids
re-litigating enrollment on every approval while still resisting §16.

## 20. Trusted input channel

Candidate mechanisms for distinguishing human input from agent-generated
input, feasibility assessed (nothing implemented):

| Option | Feasibility for v1 |
|---|---|
| Controlling TTY with explicit interaction | Feasible to build, but insufficient alone (§21) — a co-resident agent can drive the same TTY |
| Separate protected local socket/UI | Non-trivial; would need its own trust boundary against the same-account agent; not clearly simpler than hardware |
| Authenticated desktop UI | Out of scope for a CLI harness; deferred |
| Hardware authenticator (FIDO2 touch) | Feasible — infrastructure exists (§12) but backend unimplemented; strongest channel |
| Signed CLI approval (local software key) | Feasible to build; weaker under §16 unless the key itself requires a presence gesture (converges back to hardware) |
| External approval service | Feasible (§64 Option D) but adds an operational/deployment dependency and an offline-availability cost (§27) |

## 21. CLI limitations

A normal CLI prompt (`input("approve? [y/N] ")`) is **not sufficient** to
prove human presence under the mandatory same-user-agent threat model
(§16). An autonomous agent that already controls the terminal session (as
this very harness does, by design, when driving a shell) can answer its own
prompt. **This is stated explicitly, not assumed away**: `input()` alone
proves that *something* answered a prompt in the controlling process, not
that a human did.

## 22. Challenge-response

A challenge-response bound to the exact invocation —

```text
invocation subject -> challenge -> authenticated human response -> approval proof
```

— is architecturally supportable by existing PCAE trust components:
`build_approval_preview_digest()` (`runtime_authority.py:367`) already
computes a subject/scope/expiry-bound digest that could serve as the
challenge payload; `RuntimeDispatchIdentityTracker`-style durable registries
(used for B7) already demonstrate the "durable record checked at
construction time" pattern this would need for replay/reuse protection.
What is missing is exclusively the *responder*: something that can
authentically answer the challenge and that a co-resident autonomous agent
cannot forge. That responder is the actual gap N2 names, addressed by
Options A–D (§64).

## 23. Cryptographic signature option (Option A)

`approval subject canonical hash -> human-controlled signing credential ->
signature -> trusted human principal registry`.

- **Implementation complexity:** moderate — reuses RIASC-001 §8's existing
  canonicalization/digest discipline for the payload; needs a signature
  field added to `ApprovalProvenance` (new RIASC-001 field, §65), a local
  key-management surface, and a principal registry lookup (the
  `PrincipalRecord`/`SignerRecord` pattern already exists, §12).
- **Existing reusable infrastructure:** high — the registry pattern, the
  canonical-digest discipline, and the enrollment-contract structure
  (HPSE-001/HHCE-001) are direct precedent.
- **Usability:** moderate friction (one signing act per approval).
- **Threat coverage:** does **not** by itself resist §16 unless the signing
  key requires a presence gesture to use — a pure software key readable by
  any process under the account collapses back to Level 0/1.
- **Mac/Linux portability:** good if the key format is portable (e.g. an
  OS-keychain-backed or file-backed key with OS-level access control) —
  worse if it depends on a platform-specific secure enclave.

## 24. Hardware-backed option (Option B)

FIDO2/WebAuthn/HATP-adjacent approval — reusing the *pattern*
(`PrincipalRecord`/`SignerRecord`/hardware credential) established for
Class-B admin signing, extended (via a new, explicitly scoped policy
decision, not by silent reinterpretation — RPAC-REQ-049) to
runtime-invocation approval.

- **Strongest assurance:** yes — a physical touch/PIN gesture is the one
  proof a co-resident autonomous process structurally cannot produce
  without physical access, directly closing §16.
- **Excessive friction?** Potentially, if required on every single
  invocation in a fast iterative coding loop; mitigated by posture 3 (§19)
  — enroll once, but still require a fresh touch per approval (FIDO2's
  native per-assertion user-presence model already matches this).
- **Existing implementation reuse:** high at the *contract* layer (three
  frozen HATP companion contracts already define enrollment/signing/
  evidence semantics); **zero** at the *provider* layer today — both
  `Fido2HardwareProvider.credential_identity()` and
  `PivHardwareProvider.credential_identity()` unconditionally raise
  (§12/§13 of HHCE-001).
- **Available on deployment target?** Development is macOS, deployment is
  Linux (§46) — FIDO2 CTAP2 hardware keys are portable across both; a
  platform-specific secure-enclave/biometric API is not (that risk belongs
  to Option C, not this option).
- **Appropriate for every agent invocation?** Only if friction is deemed
  acceptable; this is a usability, not a security, question (§48).

## 25. Software-key option (Option C-adjacent)

A local software signing key controlled by the human but with no hardware
presence gesture.

**Threat model issue, stated honestly:** an autonomous agent running under
the same OS account may also read or invoke that key unless it is
separately protected (OS keychain user-presence prompt, a passphrase
re-entered per use, etc.) — at which point it has effectively become
Option D (OS authentication) or Option B (hardware) in disguise, not a
distinct fourth option. A bare on-disk software key with no additional
gate does **not** resist §16 and is not recommended as a standalone v1
mechanism.

## 26. OS authentication option (Option C)

macOS/Linux user-presence mechanisms: biometric/user-presence APIs (Touch
ID / `LAContext` on macOS; `polkit`/PAM on Linux), `sudo`, OS keychain
user-presence prompts.

- Architecture-only assessment; nothing invoked this phase.
- **Portability:** poor as a single mechanism — macOS Touch ID/LAContext and
  Linux PAM/polkit are different APIs with different presence semantics;
  PCAE would need a platform-adapter layer (§45) either way.
- **Should PCAE depend on OS-specific adapters?** Only behind an adapter
  interface (§45 architecture question), never as a single hardcoded path,
  given the dev-macOS/deploy-Linux split (§46).
- Genuinely resists §16 (a presence prompt cannot be silently answered by a
  background process) if implemented correctly, but ties PCAE's trust root
  to OS-vendor-specific presence infrastructure rather than a portable
  credential PCAE itself controls.

## 27. External approval channel option (Option D)

Human approval through a separate trusted device or channel: another
device, a web UI, an approval service.

- Structurally resists §16 (the approving channel is not the same process,
  often not even the same machine, as the agent).
- Costs: requires network availability (tension with §27's own offline
  goal below), an operational dependency (a service to run/trust), and a
  new trust boundary (how does PCAE authenticate the *channel's* response
  as genuinely human-originated, rather than solving the same problem one
  layer removed?).
- Telegram is the closest existing PCAE infrastructure to this shape — see
  §28.

## 28. Telegram boundary

PCAE's existing Telegram integration is confirmed, this phase, to be
**outbound notification only**: `pcae notify status` shows a configured,
enabled outbound sink (`Telegram sink: Available/Configured/Enabled: True`,
"outbound delivery"). No inbound authenticated-approval capability was
found anywhere in the notification foundation source searched. **Do not
repurpose the current outbound Telegram channel as an inbound authority
source without new architecture** (an inbound bot command handler,
authenticated per-chat-ID, would be new build, not reuse).

## 29. Trusted principal registry

**Recommendation: yes, PCAE needs a canonical `HumanPrincipalRegistry`
concept for this contract family** — and the closest thing to it,
`hatp_bootstrap.PrincipalRecord`/`SignerRecord`, already exists as a
precedent (§12). Do not overdesign a second, parallel registry: either (a)
reuse the existing `registry.json` `principals`/`signers` sections directly
if RIHAC-001-scope enrollment can be added there without violating HPSE-001's
own scope boundary (HPSE-001 §2 explicitly scopes itself to
`principals`/`signers` only, not to invocation approval — this would need an
HPSE-001 amendment or a sibling contract that references the same
`principal_id` space), or (b) define a narrower, RIHAC-001-scoped registry
that reuses the identical field discipline (`principal_id`,
`signer_key_id`/credential reference, `status`, `revoked_at`) without
inventing new grammar. Potential minimal fields, informed by
`PrincipalRecord`/`HardwareCredentialRecord` precedent:

- `principal_id` (stable, non-display, never an OS username — HPSE-REQ-001/002);
- authentication method identifier;
- credential/public-key reference (or hardware `signer_key_id` reference);
- `status` (`active`/`revoked`);
- `revoked_at` (learn from HPSE-REQ-008's disclosed gap — freeze this field
  from day one, don't repeat the omission);
- enrollment provenance (as audit-event metadata, not a record field —
  mirroring HHCE-REQ-006's disposition, not duplicating a second source of
  truth).

## 30. Enrollment

If a registry is adopted, enrollment is itself an authority-sensitive
operation (HPSE-001/HHCE-001 call this "Enrollment... establishes who may
approve; it does not itself approve anything"). Candidate bootstrap
patterns, none selected/implemented here: a local admin/human setup
ceremony (mirrors HATP's existing "Admin execution principal" role,
HBDC-REQ-066), a signed enrollment record, or HATP registration reused
directly if the registry is shared (§29 option a).

## 31. Bootstrap paradox

**Who authenticates the first human principal?** Addressed explicitly, not
handwaved: HATP's own precedent is a **local machine owner during a bootstrap
ceremony** — the "Admin execution principal" runs the enrollment writer
locally, and trust is anchored in physical/local-machine control at that
one moment, not in any PCAE-internal mechanism (which would be circular).
This mirrors standard trust-anchor bootstrapping (e.g., WebAuthn's own
first-registration model: the very first credential registration is
inherently trusted by the party performing it, because no prior credential
exists to check it against). Recommendation: reuse this exact pattern —
`pcae init`-adjacent, human-run-locally, out-of-band-trusted, one-time
ceremony — rather than inventing a second bootstrap story.

## 32. Principal identity

`principal_id` (stable) MUST be kept separate from `display_name`/`email`/
OS username (mutable, presentation-only) — this is not a new idea to invent,
it is HPSE-REQ-001/002's existing, already-frozen rule, restated as binding
for any future RIHAC-scoped principal identity too: "never an OS account
identifier... never a bare human-readable display name." Authority binds to
`principal_id`; display fields exist only for human-facing UI/audit
readability and carry no authority weight.

## 33. Approval provenance

Future `RuntimeInvocationApproval.provenance` should carry (schema not
frozen here, per governing-prompt item 33 — this is a menu, not a spec):
`principal_id` (replacing today's bare `approver_id` string), authentication
method used, an approval-specific proof (signature over the approval
subject/preview digest, or a challenge-response proof), the existing
`approval_preview_digest` (unchanged), a credential/key-ID reference into
the principal registry, and a proof-format version field (so the proof
representation itself is independently evolvable, mirroring RIASC-001 §1's
existing MAJOR.MINOR discipline for the rest of the schema).

## 34. Approval verification

Conceptual future sequence (extends RIHAC-001 §16's existing 12-step
validation order — not a new step count, an elaboration of existing step 4,
"validate producer and human provenance"):

```text
load approval
  -> structural RIASC-001 validation (unchanged, §16 steps 1-3)
  -> subject/freshness/scope binding (unchanged, §16 steps 5-9)
  -> human-principal proof verification (NEW substance inside step 4):
       resolve principal_id in the registry
       -> confirm status == active
       -> verify the proof (signature/challenge-response) against the
          registered credential and the exact approval subject digest
       -> reject on any registry-miss, revoked status, or proof failure
  -> canonical-store provenance (N1's future repair, if adopted)
  -> trusted validation
  -> PB projection (existing, unchanged downstream)
```

## 35. Final trusted construction path

Revisiting B1/B7/N1 in light of N2 (design only, not built here):

```text
authenticated human approval event (NEW: N2's actual trust root)
  -> trusted PCAE construction (existing coordinator entry point, hardened
     per B1's HMAC-keyed-seal design note, 3W.1R.2 §9)
  -> canonical approval artifact (existing RIASC-001 storage, hardened per
     N1's store-bound validation design note)
  -> canonical principal/provenance proof (NEW: this phase's subject)
  -> trusted validation (existing RIHAC-001 §16 order, extended per §34
     above)
  -> PB projection (existing, unchanged, PBRD-001 §7)
```

No caller-created trusted object at any step — this preserves the
already-designed B1/N1 direction and adds N2's missing trust root rather
than replacing the other findings' planned repairs.

## 36. B1 impact

B1 (forgeable `ValidatedAuthorityProjection` seal) is orthogonal to *whose*
identity is bound, but its repair (HMAC-keyed content-bound seal, 3W.1R.2
§9) becomes more valuable once N2 closes: today a forged seal merely forges
a projection over already-forgeable provenance; once provenance is
authenticated, the projection is worth forging *for real* stolen authority,
raising (not lowering) the importance of closing B1 in the same follow-on
repair phase. Projection should be derived from verified, human-authenticated
approval, not from a transferable seal alone.

## 37. B7 impact

B7 (copied identity seal bypasses registry) concerns *attempt* identity
(`invocation_id`/`attempt_id`/`idempotency_key`), a different axis from
*human* identity. N2's principal/proof model must not be collapsed into
attempt-identity provenance — RIHAC-001 §6 already keeps `invocation_id`
allocation (PCAE-owned) separate from approval provenance (human-owned), and
this document preserves that separation. B7's registry-recheck repair
(3W.1R.2 §9) is independent of and does not require N2's resolution first,
though both should land in the same follow-on repair phase per §68/§69.

## 38. N1 impact

N1 (canonical-store provenance not bound to validation) is *necessary but
insufficient* without N2:

```text
canonical-store provenance (N1)  +  authenticated human provenance (N2)
  -> trusted approval
```

A store-bound handle (N1's fix) proves an object came from the canonical
store; it does not by itself prove a human authenticated the *content* of
that object at creation time. Both repairs are required together for a
fully trusted approval; N1 alone would still let an authenticated-looking
but actually-unauthenticated approval be canonically stored and later
"trusted" purely because it came from the right place.

## 39. RIHAC evolution

**Yes, RIHAC-001 requires evolution.** Exact clauses:

- **§3 (Authority source and approving subject):** must define what
  "identified by provenance evidence" concretely requires — currently it
  states the requirement but not the verification mechanism, which is
  exactly N2's gap. Needs new normative text naming a principal-registry
  lookup and proof-verification step.
- **§12 (Provenance and trust):** "V1 trust is the conjunction of..." must
  add a new numbered condition (a genuine human-principal proof check),
  and its closing sentence "No cryptographic signature is required for v1"
  must be revisited if the selected architecture (§62) requires one.
- **§16 (Validation order):** step 4 ("validate producer and human
  provenance") needs elaboration per §34 above.

**Recommended version: v1.1, additive** — adding a proof-verification
requirement and a registry dependency does not remove the five-member
subject, does not relax one-shot semantics, and does not weaken any
existing required field; it narrows what "identified by provenance
evidence" is allowed to mean, which is a *tightening*, matching this
contract's own §21 precedent ("Additive clarification... may increment
MINOR only when it does not widen existing authority" — this change
*narrows* authority, which is compatible with the same MINOR-bump
discipline PBRD-001 v1.0→v1.1 and RDGO-001 v1.0→v2.0 already used for
comparable additive-tightening changes). If the selected mechanism requires
a genuinely new artifact family (a full principal-registry contract), a
**new companion contract** (§40) is preferable to inflating RIHAC-001
itself, mirroring the existing HPSE-001/HHCE-001 split.

## 40. RIASC evolution

**Yes.** `provenance` (§7 of RIASC-001) needs new fields for whichever proof
representation is selected (§33) — at minimum a `principal_id` field
(replacing/supplementing the bare `approver_id` string) and a proof/signature
field. Because RIASC-001 v1.0's `provenance` object is `additionalProperties:
false` (§0), any new field is a schema change requiring a **new schema
MINOR version** at minimum (additive field, existing fields unchanged) —
possibly MAJOR if `approver_id`'s existing meaning must be redefined rather
than supplemented. Not modified this phase.

## 41. PBRD impact

**Preference: PB should NOT become a human-authentication verifier.**
PBRD-001 already receives only a validated-authority *reference* plus a
validation-evidence *projection digest* (§7 of PBRD-001) — never raw
approval prose. This is the right shape and should not change: PB's
`human_authority_binding` fact (fact #14, §4 of PBRD-001) already names
"reference plus validated evidence projection; not raw authority or a
boolean." N2's fix belongs entirely upstream of PB, inside RIHAC-001
validation (gate 5); PBRD-001 needs no field changes.

## 42. RDGO impact

**Authentication is part of Gate 3 (human authority creation), not a new
gate.** RDGO-001 §4 (Gate 3) already states "A distinct, non-defaultable
human act creates the immutable RIASC-001 approval artifact" — N2's fix is
exactly what makes that act's provenance trustworthy. Gate 5 (approval
validation, RIHAC-001 validator) is where the new proof-verification
sub-step (§34) lives, inside the existing "validate producer and human
provenance" step. **Avoid adding a twelfth gate** — the governing prompt's
own guidance not to widen gates unless semantically necessary applies; this
is a strengthening of gates 3 and 5's existing content, not a new gate.

## 43. RPAC impact

**No RPAC-001 contract evolution required.** RPAC-001 already anticipates
exactly this: RPAC-REQ-049 explicitly permits "a later policy [to] require
hardware-backed human authority for a particular effect" without amending
RPAC-001 itself, and RPAC-REQ-006's `ExecutionPrincipal` row already states
"cannot supply human authority" — consistent with, not contradicted by,
whatever N2 resolution is selected. RPAC-001 remains the transport-neutral
boundary; it does not need to know *how* human authority is established,
only that RIHAC-001 owns it (RPAC-REQ-003).

## 44. Component responsibilities

Recommended separation (design only):

```text
HumanAuthenticator        -> proves principal_id + produces a proof for a
                              specific challenge/subject digest
ApprovalAuthorityValidator -> verifies approval proof + subject + freshness
                              (RIHAC-001 §16's existing validator, extended)
PB                         -> evaluates permission from validated authority
                              reference (unchanged, §41)
```

`HumanAuthenticator` is a new component boundary; it must not be folded into
`create_runtime_invocation_approval` itself (which should remain a pure,
already-validated-input constructor) nor into the RIHAC-001 validator
(which should verify proofs, not produce them). This avoids "one giant
component," per the governing prompt's guidance (item 44).

## 45. Authentication adapter/plugin question

A pluggable `HumanAuthenticator` interface (implementations: OS
user-presence, FIDO2, software signing, external approval service) is
architecturally attractive given §26's platform-adapter need and §46's
cross-platform split, but **should not be built as a general plugin system
in v1** unless a second concrete implementation is actually required at
launch. Given §61's recommended minimal v1 (exactly one authentication
mechanism), a single concrete `HumanAuthenticator` implementation behind a
narrow interface — not a plugin registry — is sufficient and avoids
premature complexity the governing prompt (item 45) warns against.

## 46. Cross-platform strategy

Development is macOS; deployment is Linux. Comparison:

| Strategy | Portable? | Notes |
|---|---|---|
| Portable cryptographic scheme (FIDO2 CTAP2, or a portable software-signing library) | Yes | FIDO2 hardware keys and most signing libraries work identically on macOS/Linux |
| OS-specific adapters (Touch ID/LAContext vs. PAM/polkit) | No, needs per-OS code | Requires an adapter interface (§45) even for a single mechanism, since dev and deploy platforms differ |
| Hardware authenticator | Yes | CTAP2/USB/NFC/BLE FIDO2 keys are OS-neutral |
| External approval service | Yes (network-dependent) | Portable but adds the offline cost in §47 |

**Recommendation: prefer the portable cryptographic/hardware path (Option
A/B) over an OS-specific adapter (Option C) as the primary v1 mechanism**,
precisely because it avoids building and maintaining two platform adapters
for a harness that develops on one OS and deploys on another.

## 47. Offline capability

A local CLI runtime should not require Internet merely to approve.
FIDO2 hardware signing (Option B) and local software signing (Option A) both
function fully offline. OS authentication (Option C) is also offline. Only
the external-channel option (Option D) inherently requires connectivity,
which is a real cost against it for this specific use case (though it may
still be attractive as a secondary/recovery mechanism, §49).

## 48. Usability

Scored qualitatively (no mechanism selected/implemented):

| Option | Security | Friction | Latency | Portability | Recovery | Enrollment burden |
|---|---|---|---|---|---|---|
| A — signed key | Medium (weak vs. §16 alone) | Low | Low | High | Medium (key rotation) | Low |
| B — hardware | High | Medium (physical touch per approval) | Low | High | Medium (re-enroll device) | Medium (device purchase/setup) |
| C — OS auth | High (if biometric/presence) | Low–Medium | Low | Low (dual adapters) | Depends on OS mechanism | Low (device usually already has it) |
| D — external channel | High (out-of-band) | Medium–High (context switch) | Medium (network round-trip) | High | Easy (re-register channel) | Low |

## 49. Recovery/revocation

If a credential is lost or compromised: revoke the `principal_id`'s
associated credential reference (reusing HPSE-REQ-006's existing
"first-recorded revocation is monotonic and authoritative" discipline and
HHCE-REQ-011's identical pattern for hardware credentials); enroll a
replacement credential under the same `principal_id` (identity persists
across credential rotation, per HPSE-REQ-004: "`principal_id` SHALL NOT
change across signer-key rotation or revocation"); any outstanding, unused
approval created under a now-revoked credential is not retroactively
invalidated by this architecture alone unless a future revocation-binding
requirement is added — this is named as an open design question for the
contract-freeze phase (§65), not resolved here.

## 50. Multiple principals

**Recommendation: v1 need not exceed exactly one enrolled human principal.**
The governing prompt explicitly favors minimal scope and warns against
unnecessary RBAC. A single-owner harness (the common case this repository
already assumes elsewhere — one human operator, multiple named *agents*)
does not need multi-principal or role support for a first working
authentication contract; the registry design (§29) should not preclude
adding more principals later, but v1 does not require it.

## 51. Approval delegation

**Decision: NO delegation in v1**, per the governing prompt's own
instruction and consistent with RIHAC-001 §1 ("not a general consent record
and is not reusable task, session, or phase authority"). A human may not
delegate runtime-invocation approval to another human, an agent, or a
policy in the first real-runtime version. This directly forecloses ever
treating a delegated agent (§17) as authorized to approve on the human's
behalf.

## 52. Automated approval

**Decision: NO automated/policy-based auto-approval in v1.** The governing
prompt requires this explicitly, and it follows directly from RIHAC-001 §3
("Silence, timeout, inactivity, a default response... SHALL NOT create
authority"). The human-authentication architecture designed here supports
explicit human approval only; automated approval is a separate, not
currently authorized, future governance question.

## 53. Trusted session caching

Recommended v1 posture (§19, posture 3): authenticate the principal's
*enrollment* once (durable, out-of-band), but require a **fresh,
non-cacheable proof act per approval** — i.e., "authenticate once" (in the
enrollment sense) does *not* mean "many one-shot approval acts are
auto-authorized thereafter." This distinguishes authentication (who is
enrolled — may be cached/durable) from authorization (did this specific
human act, right now, for this specific invocation — must not be cached),
matching the mandatory semantic wall `authenticated human principal !=
confirmation != approval`.

## 54. Session timeout

Architecture-only, not implemented: if any session-like authenticated state
is introduced (e.g., a device pairing that reduces friction across a burst
of approvals), it needs a TTL, a lock/logout boundary, invalidation on
terminal closure, invalidation on machine sleep, and invalidation on OS
account switch — mirroring RIHAC-001 §13's existing freshness-condition
discipline (HEAD/task/policy/expiry) applied to a new freshness dimension
(authenticator-session validity) if such a session is ever adopted. Not
required if posture 3 (§19/§53) is adopted without a caching layer.

## 55. Audit

A future human-approval audit record must answer: which `principal_id`;
which authentication method; what invocation subject (existing five-member
RIHAC-001 subject); when (existing `created_at`); proof identifier
(credential/key reference, not the raw proof material); and verification
result. This mirrors RPAC-REQ-076's existing audit-evidence requirement
("which human approved") almost verbatim — N2's fix is precisely what
finally makes that existing requirement answerable truthfully.

## 56. Privacy

Do not store unnecessary human personal data. `principal_id` (a stable,
non-display identifier — §32) is sufficient; no email, legal name, or
biometric template should be persisted in PCAE's own governance store —
this mirrors HPSE-REQ-007's explicit existing design choice ("display/
reference metadata is deliberately excluded to keep personally identifying
data minimal") and HHCE-REQ-004's "no private key, PIN, bearer token...
material" rule for hardware credentials specifically.

## 57. Security invariants

Restating the governing prompt's required invariants, each independently
confirmed consistent with contract text already read this phase:

```text
caller-supplied human-looking string        -> never trusted authority
OS username alone                            -> never authenticated approval
agent identity                               -> never human principal
producer provenance                          -> never human principal
delegated subagent                           -> never human principal
canonical file alone                         -> insufficient without trusted provenance
valid structure alone                        -> insufficient
copied approval                              -> invalid outside bound subject/repo
valid authenticated principal + wrong subject -> no authority
valid approval + PB DENY                     -> no dispatch
no human approval                            -> no real dispatch
```

None of these are new inventions; all are directly supported by, or
directly implied by, RIHAC-001 §3/§18/§20, RPAC-REQ-006, and this phase's
own N2 analysis.

## 58/59/60. Architecture options and comparison

**Matrix C — Authentication options**

| Criterion | A — Signed Key | B — Hardware | C — OS Auth | D — External Channel |
|---|---|---|---|---|
| Resists same-user agent (§16) | No, unless gated (converges to B/C) | **Yes** | Yes (if presence-gated) | Yes |
| Portability (macOS dev / Linux deploy) | High | High | Low (dual adapters) | High |
| Offline | Yes | Yes | Yes | No |
| Friction | Low | Medium | Low–Medium | Medium–High |
| Existing PCAE reuse | High (registry pattern) | High (contracts) / Low (provider backend) | None | Low (outbound-only Telegram exists, not inbound) |
| Implementation effort | Medium | Medium–High (needs provider backend work already named in HHCE-001's companion plan) | High (two OS adapters) | Medium–High (new service/channel + auth) |
| Deployment suitability | Good | Good | Poor (adapter maintenance) | Good, with network dependency |
| Auditability | Good | Good | Good | Good |
| Recovery | Medium | Medium | Depends on OS | Easy |
| Trust bootstrap complexity | Low | Low (HATP precedent, §31) | Medium | Medium (channel identity binding) |

## 61. Recommended architecture

**Recommendation: a two-tier architecture, ranked, not multiple mutually
exclusive paths:**

1. **Portable principal/signature contract** (a `HumanPrincipalRegistry` +
   signed-approval proof model, §29/§33) as the durable, version-stable
   layer — this is what RIHAC-001/RIASC-001 evolve to require (§39/§40).
2. **Replaceable authentication mechanism underneath it**, with **Option B
   (hardware-backed FIDO2) as the primary v1 target** given it is the only
   option that resists §16 without a platform-specific adapter and given
   this repository already has three frozen contracts and partial source
   scaffolding (§12) for exactly this mechanism — but implementation is
   gated on the currently-unimplemented provider backend (HHCE-013's
   disclosed gap), which is real, non-trivial future work, not a detail.
   **Option A (signed key) is an acceptable interim/fallback** for
   environments without hardware-key access, provided it is explicitly
   gated behind an OS-level presence check (converging it toward Option C)
   rather than shipped as a bare software key — otherwise it does not meet
   §16 and should not be the sole v1 mechanism.

This is justified because it separates a stable, minimally-scoped contract
layer (unlikely to need MAJOR revision) from a mechanism layer that can
mature independently as HHCE-001's provider-backend work lands, without
forcing a second RIHAC-001 MAJOR revision later.

## 62. Minimal v1

Smallest human-authentication scope required before first real local
runtime:

```text
one enrolled human principal
one authentication mechanism (hardware-backed, Option B; or gated Option A
  fallback if hardware is unavailable)
explicit approval every real invocation (posture 3, §19/§53 — no reusable
  runtime authority)
no delegation (§51)
no automated approval (§52)
no API providers (unchanged from RIHAC-001 §2 exclusions)
```

## 63. Contract changes

**Matrix D — Contract evolution**

| Contract | Current version | Change required? | Nature of change | Proposed version |
|---|---|---|---|---|
| RIHAC-001 | 1.0 | Yes | Additive tightening: define principal-registry lookup + proof-verification requirement in §3/§12/§16 | v1.1 |
| RIASC-001 | 1.0 | Yes | Additive schema fields in `provenance` (principal_id, proof, credential reference) | v1.1 (or v2.0 if `approver_id` meaning must be redefined rather than supplemented — decision for the contract-freeze phase) |
| PBRD-001 | 1.1 | No | PB already receives only a reference/projection (§41) | unchanged |
| RDGO-001 | 2.0 | No | Authentication fits inside existing Gate 3/Gate 5 content (§42) | unchanged |
| RPAC-001 | 1.0 | No | RPAC-REQ-049 already anticipates this (§43) | unchanged |

## 64. New contracts

**Recommendation: yes, a separate contract is likely warranted** — a
**Human Principal Authentication Contract** (or, to keep RIHAC-001's own
naming convention, a "Runtime Approval Authentication Contract") governing
the `HumanAuthenticator` interface, the principal-registry schema (if not
directly reusing `registry.json`, §29), and the proof-format versioning
(§33). This avoids stuffing all authentication mechanism/registry
semantics into RIHAC-001, mirroring the existing HPSE-001/HHCE-001 split
(HPSE-001 governs principals/signers; HHCE-001 governs the hardware
credential registry as a distinct sibling contract) — the same
decomposition pattern this repository has already applied twice.

## 65. Schema changes

Not frozen this phase (per governing-prompt item 64: "Do not freeze schema
in this phase unless specifically justified"). Expected shape, for the
future contract-freeze phase to formalize: `provenance.principal_id`
(replacing/supplementing `approver_id`), `provenance.proof` (signature or
challenge-response evidence, format versioned), `provenance.credential_ref`
(pointer into the principal/credential registry), and a
`provenance.proof_format_version` field.

## 66. Implementation sequence

```text
A. Human-principal/authentication contract freeze (RIHAC-001 v1.1 +
   RIASC-001 v1.1 + new companion authentication contract, per §39/§40/§64)
B. Independent verification of A
C. Authentication/principal implementation (registry writer if new, or
   HPSE-001 extension; HumanAuthenticator for the selected mechanism;
   HHCE-001's provider-backend gap must close first if Option B is chosen)
D. Independent verification of C
E. B1/B7/N1/N2 authority provenance repair (bounded repair phase, now
   unblocked because N2 has a frozen contract to repair against)
F. Independent verification of E
G. Runtime Enforcement planning (unchanged prerequisite chain — still
   requires RPAC-REQ-045's later gates, POL-005 evolution boundary, and the
   two older 3S.2.1 MUST-FIX repairs at their reachability point)
```

## 67. B1/B7/N1 sequencing

**Explicit statement, per governing-prompt item 66:** no B1/B7/N1
implementation should proceed until N2's contract architecture is resolved
— i.e., not before step B of §66 above completes. This matches 3W.1R.2 §16
option 2's own framing ("re-scoped bounded repair phase... while N2 stays
open pending option 1") but this document's own recommendation is
**sequential, not parallel**: because B1's repair design (§9 of 3W.1R.2)
already anticipates authenticated provenance mattering more once N2 closes
(§36 above), doing B1/B7/N1 first and N2 second would mean re-touching the
same trust-construction code twice. Recommend step A (this document's
contract-freeze follow-on) before step E (B1/B7/N1/N2 repair), not the
reverse.

## 68. Older MUST-FIX findings

Recovered verbatim (3W.1R.1 §42, unchanged since):

1. "Malformed adapter result crashes uncaught instead of failing closed
   cleanly." (`simulate_invocation` / `RuntimeInvocationStore.write_result`)
2. "`RuntimeInvocationStore` does not sanitize `invocation_id` against path
   traversal."

**Reachability assessment:** human-principal architecture (this document)
does not change either finding's reachability. Both remain unreachable
through the current authority/PB foundation (neither imports
`runtime_adapter.simulate_invocation` nor the older `RuntimeInvocationStore`)
and remain **MUST-FIX / DEFERRED-REAL-RUNTIME**, to repair before their old
components become reachable — unaffected by, and not repaired in, this
phase.

## 69. Runtime inspect

`pcae runtime inspect`: `Observed` / `observe` / `unavailable`,
implementation `not_implemented`, 0 plugins / 0 capabilities. Classification
carried unchanged: **TRUTHFUL_WITH_LIMITATION**. No change this phase.

## 70. Delegated-authority debt

Recorded separately, per §17 above and per the governing prompt's explicit
instruction not to confuse these two control planes:

```text
human principal authentication (this document)
  != subagent capability restriction (3W.1R.2C §11's future debt)
```

The delegated-agent incident (§17) is evidence that *both* gaps exist and
are related in kind (an authority-boundary gap), but they are architecturally
independent: closing N2 does not bound subagent capability, and bounding
subagent capability does not authenticate a human. Recommended as a future
governance-hardening phase; **not designed or implemented here.**

## 71. API/network boundary

Remains **NOT READY / NOT FROZEN**, unchanged by this phase. The
human-principal authentication work designed here is deliberately
transport-independent: nothing in §29-§64 assumes or requires network
availability for its primary recommended path (Option B is fully offline,
§47), and no API-provider or network-egress capability is touched, widened,
or implied.

## 72. No-Go confirmations

- No `src/pcae` file was modified.
- No frozen contract (RIHAC-001, RIASC-001, PBRD-001, RDGO-001, RPAC-001)
  was modified.
- No biometric/keychain/PAM API was accessed.
- No hardware key was touched; no signing key was created.
- HATP was not invoked (read-only source/contract inspection only).
- No approval CLI was implemented.
- B1/B7/N1 were not repaired.
- Runtime Enforcement was not activated.
- Shell Gate was not activated.
- POL-005 was not relaxed.
- No runtime process was spawned; no subprocess, network, or credential
  call occurred.
- No Codex/Claude/OpenRouter/provider call occurred.
- No network was enabled.
- No execution was activated.
- `~/repos/pcae-deepseek-research` was not inspected, imported, relied upon,
  or modified.
- The stopped article was not read, resumed, modified, or published.

## 73. Testing

Read-only architecture phase. Evidence gathered via source inspection
(`Read`/`grep` over `src/pcae/core/runtime_authority.py`,
`hatp_class_b_topology_verifier.py`, `hatp_bootstrap.py`,
`hatp_fido2_provider.py`, `hatp_piv_provider.py`), contract analysis (all
five runtime-authority contracts plus three HATP companion contracts read
in full or by targeted section), static search (`grep`/`find` across
`docs/` and `src/pcae/`), and safe introspection (`cat .pcae/session.json`,
`pcae notify status`). No authentication attempt, real or simulated, was
performed.

## 74. Governance

Governed lifecycle: task contract created and scoped read-only (docs/tasks/
session zones only; `core`/`commands`/`cli`/`tests` zones and the five
runtime-authority contract files forbidden). This document was authored
directly by the primary agent (not a delegated fork), consistent with
3W.1R.2C's recorded lesson that phase finalization/commit/push must remain
under primary-agent control. No force, no `--no-verify`.

---

## Required matrices

### Matrix A — Human identity sources

| Source | Authenticates human? | Same-user-agent resistant? | Reusable? | Verdict |
|---|---|---|---|---|
| OS username (`$USER`/`getuser`/UID) | No | No | No | Never authority (§6) |
| Git identity (`user.name`/author) | No (self-configured) | No | No | Descriptive only (§7) |
| PCAE session/agent identity | No (self-declared roster ID) | No | No | Agent, not human (§8) |
| TAM `human_authorization` | Partial (typed claim, not authenticator) | No | Excluded by RIHAC-001 §3 | Not reusable here (§9) |
| CHGR actor field | No (records claims, doesn't authenticate) | No | Excluded by RIHAC-001 §3 | Not reusable here (§10) |
| IWC confirmer identity | Confirms an act, not the actor's identity | No (session-bound) | Excluded by RIHAC-001 §3 | Not reusable here (§11) |
| HATP `PrincipalRecord`/`SignerRecord` | Yes, in design — not yet functional (no provider backend) | Yes, if hardware-gated | Yes, as a *pattern* | Strongest precedent (§12) |
| Telegram (outbound only) | No (no inbound auth) | N/A | Not currently | Not usable as-is (§28) |
| CLI `--agent-id` | No (self-declared, fixed roster) | No | No | Agent, not human (§8) |

### Matrix B — Threat coverage

| Threat | Required control | Candidate mechanism |
|---|---|---|
| Same-user autonomous agent | Presence proof a co-resident process cannot forge | Hardware touch (Option B) or gated OS-presence (Option C) |
| Malicious repo content | Untrusted-input treatment (already frozen, RIHAC-001 §3/RDGO-001 §2) | Existing — no change needed |
| Direct object construction (today's N2) | Registry+proof verification at validation time | Any of Options A–D, gated behind §34's new validator step |
| CLI argument injection | Same as above | Same |
| Copied approval artifact | Subject/repo/task binding (already frozen) | Existing RIHAC-001 §7/§15/§18 — unaffected |
| Delegated subagent | Capability-bounding (separate control plane, §70) | Not this phase's mechanism |

### Matrix C — Authentication options

See §58-60 above (full table).

### Matrix D — Contract evolution

See §63 above (full table).

### Matrix E — Trust chain

| Stage | Input | Trusted by | Output | Authority significance |
|---|---|---|---|---|
| Enrollment | Human, local machine control (§31) | Physical/local bootstrap trust anchor | `PrincipalRecord`-equivalent | Establishes *who may ever approve*; not itself an approval |
| Challenge construction | Approval subject (5-member, RIHAC-001 §5) | Trusted PCAE coordinator | Approval-preview digest (existing, §22) | No authority; a bound artifact only |
| Proof production | Enrolled credential + challenge | `HumanAuthenticator` (new component, §44) | Signature/response proof | The actual human act — N2's missing trust root |
| Proof verification | Proof + registry lookup | `ApprovalAuthorityValidator` (RIHAC-001 §16, extended) | Validated-authority projection | Converts a claim into evidence |
| PB evaluation | Validated-authority reference | PB (unchanged, §41) | ALLOW/DENY/HUMAN_REVIEW | Permission, not authority (existing wall preserved) |
| Runtime Enforcement | Full projection (unchanged) | RE (future gate) | Single-attempt dispatch decision | Unaffected by this document |

### Matrix F — Open blocker impact

| Finding | How new architecture addresses it | Later implementation requirement |
|---|---|---|
| B1 | Unaffected directly; repair priority increases once N2 closes (§36) | HMAC-keyed seal (3W.1R.2 §9), unchanged design |
| B7 | Unaffected; different identity axis (§37) | Registry re-check at construction (3W.1R.2 §9), unchanged design |
| N1 | Complementary, not substitutive (§38) | Store-bound validation handle (3W.1R.2 §9), unchanged design |
| N2 | **Directly addressed** — this document is N2's contract-evolution answer | RIHAC-001 v1.1 + RIASC-001 v1.1 + new authentication contract (§63/§64), then implementation (§66 step C) |

---

## Final verdict

```text
HUMAN PRINCIPAL AUTHENTICATION / AUTHORITY PROVENANCE ARCHITECTURE:
COMPLETE

N2 ROOT CAUSE:
NO TRUSTED AUTHENTICATED HUMAN-PRINCIPAL SOURCE IN CURRENT RUNTIME-APPROVAL PATH

CALLER-SUPPLIED HUMAN IDENTITY:
NON-AUTHORITY

SELECTED HUMAN AUTHENTICATION:
TWO-TIER: PORTABLE PRINCIPAL/SIGNATURE CONTRACT (RIHAC-001/RIASC-001 v1.1 +
NEW COMPANION AUTHENTICATION CONTRACT) OVER A REPLACEABLE MECHANISM LAYER;
PRIMARY V1 MECHANISM RECOMMENDED = HARDWARE-BACKED (OPTION B, REUSING HATP'S
PRINCIPAL/SIGNER REGISTRY PATTERN), GATED OPTION-A SOFTWARE-KEY FALLBACK
PERMITTED ONLY IF PRESENCE-GATED

SAME-USER AGENT RESISTANCE:
MANDATORY DESIGN CONSTRAINT; ONLY OPTION B (HARDWARE) AND A PRESENCE-GATED
OPTION C/A MEET IT; A BARE OS-USERNAME CHECK, A BARE SOFTWARE KEY, OR A
PLAIN CLI PROMPT DO NOT AND ARE EXPLICITLY REJECTED

RuntimeInvocationApproval:
FUTURE PROVENANCE BOUND TO AUTHENTICATED PRINCIPAL

CANONICAL-STORE PROVENANCE:
NECESSARY BUT NOT SUFFICIENT

B1/B7/N1:
DEFERRED UNTIL AUTHENTICATION CONTRACT IS FROZEN

POL-005:
UNCHANGED

RUNTIME:
Observed / observe / unavailable

REAL EXECUTION:
NOT ACTIVATED

NEXT:
Human-Principal Authentication Contract Freeze (RIHAC-001 v1.1 + RIASC-001
v1.1 + new companion contract) — 149O.20L.7O.3W.1R.2A.1 or equivalent

HUMAN DECISION:
REQUIRED
```

## Recommended next phase

Human-Principal Authentication Contract Freeze — amend RIHAC-001 to v1.1
and RIASC-001 to v1.1, and freeze a new companion authentication contract
(§64), per §66 step A. **Not begun in this phase. Requires human
authorization.**

## Human decision required

**YES.** Stop after 3W.1R.2A. Production source modified: **NO**. Frozen
contracts modified: **NO**. Execution activated: **NO**. Release changed:
**NO**. Runtime: `Observed` / `observe` / `unavailable`, unchanged. Article
remains stopped; private research repository remains untouched, out of
scope.
