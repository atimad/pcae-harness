# Phase 149O.1A: Human Approval Trusted Provenance Contract & Trust-Boundary Architecture

**Phase type:** trust-boundary architecture plus normative-contract design (contract
freeze deferred; architecture resolved, one load-bearing bootstrap decision remains).

**Status:** completed. **Architecture verdict: HUMAN APPROVAL TRUST BOUNDARY
ARCHITECTURE DEFINED — CONTRACT FREEZE REQUIRES FOLLOW-UP.**

## 1. Starting Position (independently reconfirmed)

- Repository clean; `origin/main..HEAD` = 0 at phase start.
- Latest completed phase: 149O.1 — **TRUSTED PROVENANCE ROOT NOT
  ACHIEVABLE — CURRENT TRUST MODEL INSUFFICIENT.** B-149O-1..4 all OPEN,
  independently reproduced (149O.1 §2); this phase does not re-run the
  exploit suite since no production code changed since 149O.1 (`git
  status --short` confirmed clean before and during this phase).
- `pcae health`/`check`/`status coherence`/`doctor task-memory`/`push
  check`/`runtime inspect`/`notify status`: all healthy/coherent/clean;
  runtime Observed / observe / unavailable; Telegram outbound-only,
  configured.
- `pcae phase-report reconcile --phase-id 149O.1`: reconciled, receipt
  finalized, mutation none.
- AG3/AG5 Permission Broker integration: still not implemented (unchanged
  file, re-confirmed).

## 2. Threat A (adopted unchanged from 149O.1)

> **Threat A — Ungoverned artifact construction / same-process, no-
> separate-secret construction.** The autonomous agent may write arbitrary
> local PCAE-state files, choose public field values, compute digests,
> copy schemas/formats, invoke any public in-process/library API
> (including the legitimate CHGR/RAE/Publication code paths), and invoke
> ordinary local approval/provenance interfaces available to the
> autonomous process — but is not assumed to possess any separate secret,
> credential, or out-of-band human capability.

**Threat B (full host/root/kernel compromise, stolen hardware token,
physical device compromise)** is explicitly excluded, exactly as 149O.1
scoped it. This phase's job is narrower and precise: can PCAE mechanically
distinguish "a human exercised a capability the agent cannot exercise
unattended" from "the agent constructed approval-shaped data or invoked
the legitimate interface unattended"?

## 3. RAE Threat-Model Resolution (governing-prompt requirement)

Independently re-read `docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md`
§22 (threat table) and §6 (RAE-REQ-005/006/009) directly, not merely from
149O.1's summary:

- §22 threat #2, "Agent-generated fake approval JSON," cites RAE-REQ-018
  ("evidence must anchor to an actually-published CHGR record via digest
  match") as its control, and is listed as a distinct row from threat #3
  ("Forged actor identity," disclosed STRATEGIC_GAP, RAE-REQ-005/006).
  This confirms 149O.1's reading: RAE-001 makes a genuine technical claim
  about threat #2 that is separate from, and does not depend on resolving,
  threat #3's already-disclosed identity gap.
- 149O's four attacks are direct, reproduced falsifications of threat #2's
  claimed control (RAE-REQ-018), not attacks on the already-disclosed
  threat #3 gap.
- No primary-source contradiction was found inside RAE-001 on this point;
  the contract's text is internally consistent, it is simply not
  currently *true* in implementation. Per the governing prompt's own
  instruction, this does **not** license downgrading RAE to procedural-
  only provenance. Model E (procedural-only trust) is rejected below on
  that basis, not selected as a shortcut.

**RAE threat-model conclusion:** RAE-001 SHALL be treated as requiring
technical (not merely procedural) resistance to Threat-A artifact
forgery for threat #2, unchanged from 149O.1's position.

## 4. Trust Ceiling and Root Inventory (independently re-verified, not merely cited)

This phase re-read the primary source for the three highest-leverage
inventory claims from 149O.1 rather than trusting its summary (governing-
prompt item 2):

- **`PublicationCoordinator.authorize()`** (`src/pcae/governance/publication/coordinator.py:91-113`,
  read in full this phase): constructs a `PublicationAuthorizationEvent`
  from `operator_id`/`package_id`/`invoked_at` with no verification step;
  its own docstring states callers must supply `operator_id` "from their
  own already-verified human-operator identity" — trust is assumed by
  contract convention, not checked in code. Confirmed.
- **`acquire_agent_lock()`** (`src/pcae/core/agent.py:288-306`, read in
  full this phase): writes `agent_id` verbatim from the caller-supplied
  string with `O_CREAT|O_EXCL` idempotency only; no proof-of-possession,
  no credential check. Confirmed.
- **Repo-wide grep** for `hmac|signing_key|private_key|sign(|signature|
  hardware|yubikey|secret_key|getpass|keychain|fido|pkcs11|piv` across
  `src/pcae` (excluding tests), re-run this phase: every match is either a
  docstring *disclaiming* the capability, or third-party-secret
  *redaction* logic (`notification_config.py`, `backend_invocations.py`)
  — never a credential PCAE itself uses to authenticate anything.
  Confirmed: **zero signing/hardware/credential primitives exist
  anywhere in this repository today.**
- **`pyproject.toml` dependencies** (read in full this phase): the only
  runtime dependency is `jsonschema>=4.18,<5`. No cryptography library
  (`cryptography`, `pynacl`, `python-fido2`, etc.) is present. This is a
  fact about current implementation readiness, not architecture — noted
  for the next phase's implementation-complexity assessment, not treated
  as a constraint on which model this phase may select.

**Conclusion (re-confirmed, ROOT A unavailable):** no existing,
independently-trusted (non-filesystem, non-same-process) root exists
anywhere in current PCAE architecture. This matches 149O.1 §5 exactly;
this phase found no discrepancy in the primary sources.

## 5. Required Security Property (frozen)

> A valid Human Approval Provenance Proof SHALL require exercise of a
> capability that is not available to the autonomous agent execution
> context, and the trust anchor used to verify that proof SHALL NOT be
> mutable by the autonomous agent execution context.

This single sentence names both roots this phase must solve (§7-§8) and
is the boundary all later sections are checked against.

## 6. Identity, Presence, Authentication, Authorization (governing-prompt items 4-5)

Four independent facts, kept separate throughout this architecture (no
single artifact is allowed to conflate them):

1. **Who is authorized** — a principal enrolled with rollback-approval
   authority (an enrollment fact, §14).
2. **Did a human participate** — human presence at the moment of proof
   creation (a physical/mechanical fact, §9).
3. **Principal authenticated** — the proof cryptographically identifies
   which enrolled principal produced it (§13-§15).
4. **Principal approved this exact operation** — the proof is bound to
   one concrete rollback operation, not a generic capability (§16-§18).

A stored string such as `approved_by="Alice"` satisfies none of the four.
No candidate below is accepted unless it independently satisfies all
four.

## 7. Candidate Trust Models — Evaluation

| Model | Root 1 (proof-production) verdict | Root 2 (verifier/bootstrap) verdict | Cross-platform / headless | Selected? |
|---|---|---|---|---|
| **A — Hardware-backed external signing key** (FIDO2/PIV-class device; private key never leaves device; fresh physical touch required per signature) | **Strong.** Physical touch is not software-invokable; no API simulates it; key material is non-exportable by device design. Holds even though this repo has no OS-level human/agent separation, because the boundary is physical/hardware, not OS-privilege. | Attestation sub-question strong (fixed vendor root, external constant); enrollment/authorization-mapping sub-question **not yet resolved in this repository's actual deployment** (§8). | Strong — FIDO2/PIV/CTAP2 and PKCS#11 are uniform across macOS/Windows/Linux; headless CI correctly fails closed (no device present). | **Selected** (Root 1 only; Root 2 deferred, §8/§19) |
| **B — OS credential/keychain with fresh per-use human presence** (Secure Enclave + biometric/passcode confirmation required per signing op) | Conditionally strong *only if* fresh per-use presence is mechanically enforced by the platform (149O.1's rejection was of the *weak* form — a stored key with no presence gate). | Same enrollment-mapping problem as Model A, *plus* the presence-gate itself is platform-specific (macOS Secure Enclave/Touch ID; Windows Hello/TPM; **no comparable primitive exists on Linux/headless CI** — the gate would silently degrade to Model E on that platform). | **Weak.** No uniform Linux equivalent; a Linux/CI deployment either has no gate (regression to rejected form) or requires bespoke tooling per platform, violating item 82's deployability bar without a comparably strong reason to prefer it over A. | Rejected — inferior to A on cross-platform/headless viability for no compensating strength; not "one candidate is impossible," rather A dominates B on every axis that differs. |
| **C — External approval service** (independently authenticated service issues operation-specific signed proof) | Strong in principle (service-side authentication is a real, external boundary). | Strong in principle *if* the service's own authentication is itself human-only and its issuing key is not agent-reachable. | Good — network-reachable from any platform; but introduces a new deployed service, an availability dependency, and a second system whose own trust root must independently be justified (recursion risk, item 20 permits it as a *bootstrap* option, not as the primary operational root without new infrastructure). | Rejected as the *primary* root for this phase — correct in principle, but requires standing up new infrastructure this repository has none of, which is a materially larger architectural commitment than Model A for the same security property (item 83's complexity/operational-burden axis), and 149O.1 already found no such service exists to be repurposed. Not excluded from re-consideration if the next phase's bootstrap decision (§19) selects it for Root 2's enrollment channel specifically. |
| **D — Separate local privileged approver process/user** (distinct OS user/security context holds signing capability) | Strong *if* the separation genuinely exists (different OS user, ACL-protected socket). | Strong for the same reason. | Deployment-dependent; this repository, as actually configured, runs the agent and the human under the **same OS user** (confirmed §4's grep: no `getpass.getuser()`, no `sys.stdin.isatty()` gate, no OS-user check anywhere in the governance/publication/RAE path). Item 79 explicitly forbids assuming a file-permission boundary exists when human and agent are the same OS user. | Rejected as the *primary operational* root — the separation this model requires does not exist in this repository's current deployment and would itself need to be established as a prerequisite, which is functionally identical to (and no easier than) resolving Model A's Root 2 bootstrap gap. Noted as a *legitimate candidate mechanism* for Root 2's bootstrap boundary specifically (§19), not for the operational signing root. |
| **E — Procedural-only trust** (document expected workflow; no technical enforcement) | None — provides no property at all. | None. | N/A | **Explicitly rejected**, per §3: RAE-001's threat #2 makes a genuine technical claim; no primary-source contradiction was found; downgrading to Model E would contradict the frozen contract rather than repair it. Not selected as a convenience fallback, per governing-prompt instruction. |

**Selection: HATP MODEL A — Hardware-Backed External Signing Key.**

## 8. Two Roots — Formal Statement (governing-prompt item 61, mandatory)

```
PROOF-PRODUCTION ROOT:
A FIDO2/PIV-class hardware security device's private signing key, which
never leaves the device and which the device firmware refuses to use for
a signing operation without a fresh physical human touch/presence
gesture on that specific device for that specific operation.

WHY THE AGENT CANNOT EXERCISE IT UNATTENDED:
The autonomous agent is a software process with no physical embodiment.
It can construct and submit an arbitrary payload to the device's signing
interface, but the device's firmware-level touch requirement is not
satisfiable by any software API, credential, environment variable, or
in-process capability -- there is no call the agent can make that
supplies a physical touch. This holds regardless of whether the agent
and a human operator share the same OS user, the same process family, or
the same CLI (RAE-REQ-009's already-disclosed ceiling), because the
boundary is physical/hardware-enforced, not OS-privilege-enforced. This
is the mechanical property Model B could not guarantee uniformly (S7)
and Model D could not establish without an OS boundary this repository
does not have.

VERIFICATION / BOOTSTRAP ROOT:
Two independent sub-facts, both required:
  (a) Device-genuineness: a fixed, externally-published hardware-vendor
      attestation root certificate (not derived from local PCAE state)
      used to verify a given public key/attestation chain genuinely
      originated from real hardware of a known vendor/model class, not
      a software-emulated key.
  (b) Approver-authorization mapping: a record binding one specific
      attested device's public key to one specific authorized human
      principal and rollback-approval-authority scope.

WHY THE AGENT CANNOT REPLACE OR SELF-SELECT IT:
Sub-fact (a) is external to this repository by construction: it is not
asserted by PCAE, it is a fixed constant published independently by the
hardware vendor, structurally analogous to a TLS root-CA bundle -- an
attacker/agent without possession of genuine vendor hardware cannot
produce a chain that verifies against it, regardless of local file
write access.
Sub-fact (b) is UNRESOLVED IN THIS REPOSITORY'S CURRENT DEPLOYMENT (see
S9/S19): this repository has no OS-user separation, no verified external
service, and no verified external human-gated review boundary today, so
a plain registry entry under agent-writable `.pcae/**` cannot yet serve
as sub-fact (b)'s home. This is not concealed or worked around -- it is
the reason this phase declines to freeze the contract (S19, S21).
```

## 9. Root 2 Gap — Why It Blocks Freeze (governing-prompt items 18, 78, 79, decision rule)

The approver-authorization mapping (§8 sub-fact (b)) is the load-bearing
half of Root 2. Per item 78: "If approver registry is local, define
exactly why agent cannot modify it. If no separation exists: local
registry cannot serve as trust root." Per item 79: "Do not assume file
permissions create a boundary when human and agent run as the same
user."

This repository's actual, current deployment (re-verified this phase,
§4): one OS user runs both the autonomous agent process and the human
operator's own CLI invocations; no distinct OS principal, no filesystem
ACL separation, no verified external code-review gate (e.g., mandatory
non-author human approval on a protected path), and no external
service/KMS is configured anywhere in this repository. Under Threat A,
any registry stored under ordinary agent-writable state is therefore
exactly as forgeable as every artifact 149O already broke.

Per the governing prompt's own recommended-next-phase logic: *"If
proof-production root is strong but verifier/bootstrap root remains
agent-writable → Do not freeze. Resolve bootstrap trust first."* Root 1
is strong (§8). Root 2's sub-fact (b) currently has no non-agent-writable
home. **This phase therefore does not freeze HATP-001 v1.0** (§21).

This is a deployment/bootstrap-mechanism-selection gap, not an
architecture gap: §14-§18 fully specify what the registry must contain
and what property it must have; §19 enumerates concrete, currently-
deployable mechanisms that would satisfy that property. What remains is
selecting and independently verifying exactly one of them, which the
governing prompt's own next-phase logic assigns to a dedicated
contract-freeze phase (§22).

## 10. Mandatory Dual-Attack Acceptance Model

**Attack 1 — Artifact Forgery.** Agent hand-authors Decision, CHGR
record, publication receipt, Binding, creation registration, recomputes
every public digest, but possesses no genuine hardware device signature
over the concrete operation. Expected and achieved under Model A:
**approval evidence INVALID, `approval_present=False`** — no HATP proof
exists at all; RAE's proof-presence check fails before any digest
comparison is reached.

**Attack 2 — Legitimate-Interface Abuse.** Agent constructs the exact
legitimate approval payload and invokes the real signer interface (the
device's standard CTAP2/PIV signing call) unattended. Expected and
achieved: **NO valid proof** — the device firmware blocks the operation
pending physical touch; an unattended call times out or is refused by
the device itself, not by PCAE-layer policy. This is the mandatory
acceptance criterion (item 23) and is satisfied at the hardware layer,
independent of anything PCAE's own code could get wrong.

**Self-enrollment attack (item 76).** Agent attempts to enroll an
attacker-controlled verifier key / grant itself approval authority.
Mechanically requires writing to the Root-2 registry (§8 sub-fact (b)).
Blocked **only if** the deployment has actually established one of §19's
boundary mechanisms; this phase cannot certify that today (§9) — flagged
as the exact reason freeze is deferred, not silently assumed solved.

**Verifier-key-replacement attack (item 77).** Same analysis and same
caveat as self-enrollment: blocked by the same boundary, unverified in
current deployment.

Both self-enrollment and verifier-key-replacement resolve to the same,
single open question (§9), which is intentional — the architecture does
not require two separate mechanisms, one registry-protection boundary
answers both attacks once selected.

## 11. Human Presence Mechanism (item 22)

Fresh human presence is proved by the hardware device's own firmware-
level user-presence gesture (a physical touch/tap on the device) required
for each individual signing operation. This is not a PCAE-layer claim; it
is a property of the FIDO2/PIV/CTAP2 standard the device implements. A
mere function call returning a signature is, by construction, impossible
without that gesture having occurred first.

## 12. Human Approval Provenance Proof — Conceptual Artifact

A new conceptual artifact, **`HumanApprovalProvenanceProof` (HATP
proof)**, distinct from CHGR Decision, Rollback Approval Binding, and
Permission Broker decision. It is produced once, at approval time, by
the hardware signer over a canonical payload (§13), and is consumed by
RAE's evidence validator (§17) as an additional, independent, required
fact — not a replacement for the existing Decision/Binding chain.

## 13. Required Proof Payload (item 12-13, mandatory concrete binding)

The signed payload SHALL bind, at minimum:

| Field | Bound? | Rationale |
|---|---|---|
| Rollback Approval Decision ID | Yes | Item 12 |
| Rollback Approval Decision digest | Yes | Prevents Decision mutation after signing (item 42) |
| Rollback Approval Binding ID | Yes | Item 12 |
| Rollback Approval Binding digest | Yes — **mandatory, not optional** (item 13): a proof over only `approve_rollback` would still permit a real signature paired with a fake Binding for an arbitrary operation | Binds the concrete operation, not a generic capability |
| Rollback family (AG3/AG5) | Yes | Distinguishes the two governed rollback families |
| AG3: `job_id`, `original_commit_sha` | Yes, when family=AG3 | Operation-specific |
| AG5: `per_id`, `ecp_id` | Yes, when family=AG5 | Operation-specific |
| Approver principal (enrolled identifier, §14) | Yes | Signer identity mapping |
| Repository identity | See §18 — deferred, non-blocking | No stable canonical repository identity currently exists in this codebase (only `repository_state_binding = {head_commit_sha, branch}`, a freshness fact, not an identity fact); repository scope is inherited transitively through the Binding digest binding rather than invented as a new unstable field |
| `issued_at` | Yes | §16 freshness relationship |
| Proof format version | Yes | §20 |

No generic "rollback approved" proof is valid for RAE consumption (item
46).

## 14. Signer Identity / Trusted Approver Registry (conceptual, item 17)

Conceptually, per-principal enrollment record:

```
principal_id
device_public_key / attestation_fingerprint
approval_authority_scope   (repository-specific, preferred; see S15)
status                     (active | revoked)
valid_from
revoked_at
version
```

**Not implemented this phase** (item 17 explicit prohibition). This is
exactly the artifact whose storage location is the open Root-2 question
(§9).

## 15. Approval Authority Scope (item 48)

Preferred: **repository-specific**, matching RAE's existing
`repository_state_binding` granularity — the narrowest scope this
codebase actually already models anywhere (item 48's instruction to
prefer the narrowest currently-supported scope). Global scope is
rejected as unnecessarily broad for a single-repository harness; task-
or environment-specific scope is not currently motivated by any existing
RAE/CHGR concept and is not adopted (item 51/50 — do not add binding
merely for theoretical completeness).

## 16. Freshness / TTL Relationship (item 26)

RAE's existing 24-hour Decision/Binding validity window remains
unchanged and independent. HATP's `issued_at` is defined to equal the
signing event's own timestamp (not required to equal Decision/Binding
creation time, since the human may review and sign at a moment
distinct from, but after, Decision/Binding creation) — HATP does not
introduce a second, competing expiry clock; RAE's existing freshness
checks (`repository_state_binding`, `expires_at`) continue to govern
Decision/Binding staleness exactly as today. HATP proof validity is
binary (VALID/INVALID per §17), not time-decaying, since it is bound to
an immutable Decision+Binding digest pair, not to live repository state.

## 17. Proof Verification (items 33-34)

Conceptually pure: consumes `(HumanApprovalProvenanceProof, trusted
verification material, expected operation context, approval authority
state)` → one of:

```
VALID | MISSING | MALFORMED | INVALID_SIGNATURE | UNKNOWN_SIGNER |
UNAUTHORIZED_SIGNER | REVOKED_SIGNER | WRONG_OPERATION |
WRONG_REPOSITORY | EXPIRED
```

No Permission Broker call inside verification (item 33). No overlap with
RAE `EvidenceValidationResult` or Permission Broker decision vocabulary
without an explicit future layering statement (item 34) — deferred to
implementation phase.

## 18. Repository Binding (item 49)

No stable, canonical repository identity currently exists in this
codebase (§13's table). Rather than inventing an unstable path-only
identity (explicitly discouraged, item 49), this architecture defers a
standalone `repository_identity` field: operation binding (via the
Binding-digest field, §13) already transitively scopes a proof to one
repository checkout's Decision/Binding pair, which is sufficient for
this repository's current single-repository-per-checkout deployment
model. Flagged **NON-BLOCKING** — revisit only if/when PCAE supports a
shared approver registry across multiple repository checkouts.

## 19. Bootstrap Trust — Mandatory Answers (item 19)

| Question | Answer |
|---|---|
| Who enrolls the first approver? | Not decided by this phase — this is precisely the decision 149O.1B must make (§9, §22). |
| What makes that enrollment authoritative? | Whichever boundary mechanism is selected from the three below, verified as actually enforced in this repository's real deployment. |
| What prevents the agent from enrolling itself? | The selected boundary mechanism, once verified. Not yet verified (§9). |
| What prevents the agent from replacing the trusted verifier key? | Same boundary; same caveat. |
| What independently protects the registry/configuration? | Same boundary; same caveat. |
| What happens if trusted verification configuration is missing? | Fail closed (§21): no HATP proof can be VALID; RAE evidence remains missing/invalid; `approval_present` remains `False`; `HUMAN_REVIEW` unresolved; zero rollback. |

**Candidate bootstrap-boundary mechanisms** (item 20), evaluated but not
selected — selection and verification is 149O.1B's job:

1. **Distinct OS user/principal** owning the registry file with
   restrictive filesystem ACL, separate from whatever account executes
   the autonomous agent. Not currently established in this repository
   (§4/§9 confirmed same-user deployment today).
2. **External service/KMS enrollment**, where the agent may read
   published trusted material but cannot authenticate as the enrolling
   human to mutate it. Not currently configured anywhere in this
   repository.
3. **Mandatory external human-authenticated review gate** (e.g., a
   code-hosting platform's branch protection requiring a non-author
   human reviewer on a specific protected path) enforced by a system
   external to the local checkout the agent writes to. Not verified as
   configured for this repository during this phase (this phase did not
   inspect any remote hosting-platform configuration, which is outside
   `pcae-harness`'s own repository content and thus outside this phase's
   read-only inspection scope).

None of the three is selected here; item 20 permits **hardware
enrollment** and **external service account enrollment** specifically as
legitimate bootstrap roots, and mechanism (1)/(2) above are direct
instances. Mechanism (3) is included because it is plausibly already
partially available (GitHub-hosted repositories commonly support branch
protection) but was not verified this phase and must not be assumed.

## 20. Algorithm Note (non-binding, deferred to implementation phase)

Not selected or frozen this phase (item 31 applies at contract-freeze
time, which has not occurred, §9). For the next phase's reference only:
Ed25519 and ECDSA P-256 are the two broadly-supported modern candidates
across FIDO2/PIV hardware, Python ecosystem (`cryptography` library —
**not currently a dependency**, §4), and external signer tooling.
Algorithm agility (item 30) is achieved structurally via the mandatory
proof-format version field (§13), not by picking an algorithm now.

## 21. Fail-Closed / Headless Behavior (item 71)

Where no trusted human-approval provider or verified Root-2 boundary
exists — including, honestly, this repository's own current state —
HATP cannot produce a VALID proof; RAE evidence remains
invalid/missing; `approval_present=False`; `HUMAN_REVIEW` remains
unresolved; zero rollback mutation. No normative bypass (`--trust-any-
approval`, `--skip-human-proof`) is defined or permitted (item 72). A
future test-only in-memory signer/verifier (item 73) may exist for unit
tests, explicitly dependency-injected, never a production default.

## 22. Trust Capability Matrix (item 60, mandatory)

| Capability | Autonomous agent | Human approver | Trusted signer (hardware device) | Verifier/bootstrap authority |
|---|---|---|---|---|
| Read approval artifacts | Yes | Yes | N/A | N/A |
| Write approval artifacts (Decision/Binding/receipts) | Yes | Yes (same CLI, RAE-REQ-009 ceiling) | N/A | N/A |
| Compute digests | Yes | Yes | N/A | N/A |
| Invoke signing request | Yes (may submit payload) | Yes | N/A | N/A |
| Satisfy human-presence requirement (physical touch) | **No — mechanically impossible** | Yes | N/A (device enforces, does not itself "satisfy") | N/A |
| Use private signing capability | **No — key non-exportable, presence-gated** | No (does not hold the key; triggers its use) | Yes (sole holder) | N/A |
| Read trusted verification material (vendor root, registry) | Yes (public data) | Yes | N/A | Yes |
| Replace trusted verification material | **Should be No — unverified in current deployment (S9)** | Depends on selected bootstrap mechanism | N/A | Yes, by design |
| Enroll approver | **Should be No — unverified in current deployment (S9)** | Depends on selected bootstrap mechanism | N/A | Yes, by design |
| Revoke approver | **Should be No — unverified in current deployment (S9)** | Depends on selected bootstrap mechanism | N/A | Yes, by design |

The "Should be No — unverified" cells are the honest statement of §9's
open gap: the architecture requires "No," but this phase cannot certify
it as enforced in this repository's actual deployment today.

## 23. Layering / Compatibility Assessments

- **RAE-001:** `RAE-001 COMPATIBLE AS-IS` — HATP is additive: it supplies
  the missing technical control for threat #2 without requiring any
  RAE-001 field, requirement, or lifecycle rule to change. No amendment
  proposed or made.
- **CHGR-001:** `CHGR-001 COMPATIBLE AS-IS` — CHGR continues to record
  the human governance Decision; HATP proves trusted provenance for that
  Decision/Binding pair. No amendment proposed or made.
- **IWC-001:** IWC confirmation remains distinct from approval (frozen,
  unchanged) — IWC may transport/present human interaction, but only a
  valid HATP proof establishes provenance.
- **AESIC-001/AEM-001:** remain disclosure-only; no authority-evaluation
  output constitutes a HATP proof.
- **Permission Broker (PBPC-001/PBPA-001):** no policy change; HATP only
  affects whether RAE may truthfully assert `approval_present=True`.
  Permission Broker continues to independently decide
  ALLOW/DENY/HUMAN_REVIEW.

## 24. Future Acceptance Tests (item 90, frozen for the implementation phase)

1. Full handcrafted artifact chain, no HATP proof → invalid.
2. Fake HATP proof (random signature) → invalid.
3. Attacker-selected public key not chained to vendor attestation → invalid.
4. Agent invokes legitimate signer unattended → no valid proof (device blocks).
5. Agent self-enrolls attacker key → rejected (pending S9/S19 boundary selection).
6. Agent replaces trusted verifier key → rejected (same caveat).
7. Valid proof copied to a different rollback operation → invalid (Binding-digest mismatch).
8. Modified Binding after signing → invalid.
9. Modified Decision after signing → invalid.
10. Wrong signer (valid signature, unenrolled device) → invalid.
11. Unauthorized signer (enrolled, wrong scope) → invalid.
12. Revoked signer → invalid.
13. Valid, authorized, fresh human-presence proof over the exact operation → valid.

## 25. Findings

- **BLOCKING (carried forward, unchanged)**: B-149O-1, B-149O-2,
  B-149O-3, B-149O-4 remain OPEN. No implementation occurred this phase.
- **BLOCKING (new, this phase)**: Root 2's approver-authorization-mapping
  sub-fact (§8(b)) has no verified non-agent-writable home in this
  repository's current, actual deployment (§9). This is the single
  reason contract freeze is deferred.
- **NON-BLOCKING**: Model B (OS keychain) is architecturally viable in
  principle but inferior to Model A on cross-platform/headless grounds
  (§7) — not a defect, a selection rationale.
- **OBSERVATION**: `cryptography`/hardware-signing libraries are not
  currently a project dependency (§4) — an implementation-readiness fact
  for the next phase, not an architecture blocker.
- **DEFERRED**: repository-identity binding (§18), algorithm selection
  (§20), rotation mechanics beyond "deterministic per version" (item 28,
  not elaborated further since no freeze occurred).

## 26. Architecture Verdict

**HUMAN APPROVAL TRUST BOUNDARY ARCHITECTURE DEFINED — CONTRACT FREEZE
REQUIRES FOLLOW-UP.**

Root 1 (proof-production) is fully resolved: **HATP MODEL A,
hardware-backed external signing key with firmware-enforced fresh
physical presence.** Root 2 (verification/bootstrap) is fully specified
in required-property terms (§8(b), §14, §19) but not yet bound to one
verified, currently-enforced mechanism in this repository's actual
deployment. Per the governing prompt's own decision rule, this phase
does not freeze `HATP-001` and does not create
`docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md`.

## 27. RAE Readiness

**NOT READY FOR ROLLBACK INTEGRATION** (unchanged). No trusted root is
yet implemented or verified; AG3/AG5 remain correctly unwired.

## 28. Recommended Next Phase

**149O.1B — Human Approval Trusted Provenance Contract Freeze.** Scope:
select and independently verify exactly one of §19's three (or an
equivalent) bootstrap-boundary mechanisms as actually enforced for this
repository's real deployment; only then freeze `HATP-001 v1.0` using
this phase's §12-§18/§22-§24 content as its normative basis. No signer/
provider implementation before that contract freeze and its own
independent verification, per the governing prompt's own ordering (do
not implement before contract freeze; do not freeze before Root 2 is
resolved).

## 29. Confirmations (governing-prompt required final-report list)

- RAE-001 v1.0 unchanged. RWMPC-001 v1.0 unchanged. PBPC-001 v1.2
  unchanged. PBPA-001 v1.0 unchanged. CHGR-001 unchanged.
- IWC confirmation remains distinct from approval. AESIC/AEM remain
  disclosure-only.
- No `HATP-001` contract was frozen this phase (architecture-only
  outcome; §26).
- B-149O-1..4 remain open until trusted-root implementation is delivered
  and independently verified.
- No production provenance repair was implemented by 149O.1A.
  `git status --short` confirms no `src/pcae/**` changes.
- No AG3 Permission Broker integration was implemented. No AG5
  Permission Broker integration was implemented. No rollback execution
  behavior changed.
- No POL-001..012 meaning was changed. No POL-013+ was added. TK1/TK2/
  TK3 remain deferred.
- No Runtime Enforcement behavior changed. No Prompt Generation, Prompt
  Dispatch, or agent invocation capability was implemented. Runtime
  remains Observed, maximum capability remains observe, execution
  availability remains unavailable (confirmed via `pcae runtime inspect`
  before and during this phase).
