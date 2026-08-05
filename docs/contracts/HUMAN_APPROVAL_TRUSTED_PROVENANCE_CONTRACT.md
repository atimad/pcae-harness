# Human Approval Trusted Provenance Contract

## Contract identity and status

**Contract:** HATP-001
**Version:** 1.0
**Status:** FROZEN
**Frozen by:** Phase 149O.1B.3 — Human Approval Trusted Provenance
Contract Freeze
**Depends on:** RAE-001 v1.0 (`ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md`,
unamended), CHGR-001 v1.3 (`CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md`,
unamended), IWC-001 v1.2 (`INTERACTIVE_WORKFLOW_CONTRACT.md`, unamended),
RWMPC-001 v1.0 (`REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_CONTRACT.md`,
unamended), PBPA-001 v1.0 (`PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md`,
unamended), PBPC-001 v1.2 (`PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md`,
unamended)
**Structural precedent (non-normative):** TAMC-001 v1.0 / TAMPC-001 v1.1
`human_authorization` record shape — reused for structural inspiration
only, never composed, subclassed, or wrapped (§29 below).
**Architecture basis:** `docs/PHASE_149O_1A_HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT_AND_TRUST_BOUNDARY_ARCHITECTURE.md`,
`docs/PHASE_149O_1B_HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT_FREEZE.md`,
`docs/PHASE_149O_1B_1_HUMAN_APPROVAL_BOOTSTRAP_AUTHORITY_ARCHITECTURE.md`,
`docs/PHASE_149O_1B_2_CANONICAL_REPOSITORY_IDENTITY_ARCHITECTURE.md`.
Where this contract's own text diverges from those documents' prose,
this contract is normative; no divergence is introduced by this freeze.

HATP-001 v1.0 is the sole normative contract answering: when may PCAE
treat a rollback approval as backed by trusted human provenance? It
defines the proof artifact, the human-presence and hardware-provider
requirements that proof depends on, the bootstrap/enrollment authority
that makes a signer's identity meaningful, the repository-scope
mechanism that prevents authority from leaking across copies, and the
closed verification vocabulary a consumer must use. It is additive to
RAE-001, CHGR-001, IWC-001, RWMPC-001, PBPA-001, and PBPC-001 — it
amends none of them, and none of them require amendment to be
consumed by this contract (§29-§34).

This is contract text only. It defines a proof-artifact shape, a
bootstrap trust-store shape, and a closed verification vocabulary as
normative prose; it does not author a JSON Schema file, does not
implement a signer, verifier, or registry, does not create an OS
principal or ACL, does not wire AG3/AG5 to the Permission Broker, and
does not set `approval_present=True` anywhere in production. It grants
no runtime, lifecycle, or execution capability.

## 0. Normative Language

The key words "SHALL", "SHALL NOT", "MUST", "MUST NOT", "REQUIRED",
"SHOULD", "SHOULD NOT", "MAY", and "OPTIONAL" in this document are to
be interpreted per RFC 2119. Every normative sentence carries a unique
requirement ID, `HATP-REQ-###`, sequential from 001, no gaps, no
duplicates (§45).

## 1. Purpose

**HATP-REQ-001.** This contract exists to close the trust gap RWMPC-001
identified (`RWMPC-REQ-027`): AG3 and AG5 truthfully report
`approval_present=False` because no trusted evidence source exists for
human rollback approval. HATP-001 defines that trusted evidence source
at the provenance layer — it does not itself decide permission,
approve a rollback, or execute anything.

**HATP-REQ-002.** HATP-001 governs the question "was this concrete
approval genuinely produced by an authorized human, using a capability
the autonomous agent does not possess, for this exact operation, in
this exact repository deployment?" — and only that question.

## 2. Scope

**HATP-REQ-003.** HATP-001 SHALL govern trusted provenance of human
approval: the proof artifact, its production, its verification, the
bootstrap authority that gives a signer identity meaning, and the
repository-scope binding that authority is valid under.

**HATP-REQ-004.** HATP-001 SHALL NOT govern rollback execution,
Permission Broker decisions, mutation freshness, RAE lifecycle
semantics (evidence issuance/use/revocation/supersession), CHGR
Decision semantics, or generic agent execution. Those remain governed
exclusively by RAE-001, PBPA-001/PBPC-001, RWMPC-001, and CHGR-001
respectively (§30-§34).

**HATP-REQ-005.** A `HumanApprovalProvenanceProof` is necessary but not
sufficient for a rollback to proceed. Sufficiency additionally requires
valid RAE-001 evidence and an ALLOW decision from the Permission
Broker (§29, §34).

## 3. Definitions

**HATP-REQ-006.** The following terms are frozen for this contract and
SHALL NOT be redefined by any consumer:

- **Human/Admin OS principal** — the OS security principal that owns
  the HATP protected bootstrap trust store; combines the human-approver
  and bootstrap-administrator roles for v1 (§13, §19).
- **Agent OS principal** — the OS security principal the autonomous
  PCAE agent process executes as (§13).
- **Hardware provider** — a device/software component satisfying the
  `HATP_HARDWARE_PROVIDER_V1` profile (§10).
- **Repository-instance identity (`repository_id`)** — the Layer-1
  identifier from CRI Model A (§17-§18, 149O.1B.2 §9).
- **Protected deployment binding** — the Layer-2 admin-owned record
  binding `repository_id` to a canonical deployment root and an
  authorized principal (§18).
- **`HumanApprovalProvenanceProof`** — the HATP proof artifact (§19).
- **Trusted bootstrap store** — the admin-owned, agent-unwritable
  registry of enrolled principals, keys, and deployment bindings (§14).

## 4. Threat Model

**HATP-REQ-007.** HATP-001 is frozen against **Threat A**, verbatim
from Phase 149O.1A §2 and reconfirmed unchanged through 149O.1B.2: the
autonomous agent may write ordinary agent-authorized repository/state
files, read HATP public verification state, construct approval
requests, construct arbitrary unsigned artifacts, compute digests,
invoke ordinary public PCAE APIs, invoke the HATP signing-request
interface, and copy/replay public approval artifacts — but is not
assumed to possess any separate secret, credential, or out-of-band
human capability.

**HATP-REQ-008.** Under Threat A, the agent MUST NOT be able to:
satisfy the required physical human presence; extract the protected
signing private key; enroll itself as an approver; modify protected
bootstrap state; replace the trusted verifier key/principal mapping;
grant itself repository rollback authority; impersonate the Human/Admin
OS principal; or escalate privileges into bootstrap authority.

## 5. Non-Goals

**HATP-REQ-009.** HATP-001 v1.0 does not promise protection from: host
root/kernel compromise; compromise of the Human/Admin account itself;
physical theft of the hardware device plus legitimate device
interaction; hardware firmware compromise; vendor attestation-root
compromise; or an authorized human intentionally approving a harmful
operation. These constitute **Threat B**, out of scope, unless a
different frozen contract already requires otherwise.

## 6. Security Layering

**HATP-REQ-010.** The following layering is frozen and MUST NOT be
collapsed or reordered by any consumer:

```
HATP-001            proves trusted human provenance
RAE-001              proves rollback-specific approval evidence,
                     binding, freshness, and lifecycle
Permission Broker    decides permission (PBPA-001/PBPC-001)
RWMPC                governs mutation boundary/freshness
```

**HATP-REQ-011.** The following semantic distinctions are frozen and
MUST be preserved by every consumer: human presence &ne; principal
identity; principal identity &ne; approval authority; approval
authority &ne; approval decision; a valid HATP proof &ne; valid RAE
evidence; valid RAE evidence &ne; Permission Broker `ALLOW`; Permission
Broker `ALLOW` &ne; execution occurred.

## 7. Root Architecture Summary

**HATP-REQ-012.** Three trust roots are frozen, per 149O.1A/149O.1B/
149O.1B.1/149O.1B.2, and are not reopened by this contract:

- **Root 1 (Proof Production):** HATP MODEL A — a hardware-backed
  external signing capability with a non-exportable private key and
  fresh physical human-presence enforcement per operation (§9-§11).
- **Root 2A (Device/Provider Genuineness):** externally anchored
  provider/device attestation (§12).
- **Root 2B (Bootstrap/Authorization Authority):** Bootstrap Model
  Class B — a separate OS security context, two-principal v1 topology
  (§13-§16).

**HATP-REQ-013.** Repository scope is frozen per CRI Model A
(149O.1B.2 §9): Layer 1, a repository-local random `repository_id`
conferring no authority by itself, and Layer 2, an admin-owned
protected deployment binding that is the sole source of repository-
scoped HATP authority (§17-§18).

## 8. Human Principal

**HATP-REQ-014.** Each enrolled human approver SHALL be identified by a
stable `principal_id`, distinct from any human-readable display name.
`principal_id` SHALL NOT change across key rotation (§23).

**HATP-REQ-015.** `principal_id` alone confers no rollback authority;
authority is a separate protected-bootstrap-state fact (§16, §41).

## 9. Human Presence

**HATP-REQ-016.** Each HATP approval proof SHALL require a fresh
human-presence event enforced by the approved hardware provider for
that specific proof-production operation. A provider/profile
permitting unattended or repeated signing without a fresh presence
event per signature SHALL NOT be HATP-compliant.

**HATP-REQ-017.** The relationship between human presence and proof is
strictly one-to-one for v1: one human-presence action SHALL produce at
most one HATP proof. An indefinite authenticated signing session (e.g.
"unlock once, sign many") SHALL NOT be HATP-compliant. A future
contract version MAY define a different bounded model only with
explicit justification against Threat A; no such model is defined by
v1.0.

**HATP-REQ-018.** The mandatory legitimate-signer-abuse property: an
agent that prepares an exact valid payload and invokes a genuine,
enrolled signer, without a fresh human physical-presence event, SHALL
NOT obtain a valid HATP proof. This property is restated as a
mandatory future acceptance test (§44, attack #6).

## 10. Hardware Provider Profile

**HATP-REQ-019.** HATP-001 freezes a conceptual provider profile,
**`HATP_HARDWARE_PROVIDER_V1`**, defined by required security
properties, not by vendor or protocol branding. A compliant provider
SHALL support: (a) a protected, non-exportable private key; (b) fresh
human-presence enforcement per signing operation; (c) signing/assertion
over an operation-specific payload suitable for HATP's canonical
payload (§20); (d) a stable key/credential identity usable for
enrollment (§8, §22); and (e) verification using independently trusted
public/provider material that does not originate from the proof itself
(§25, §80 of the governing prompt / §22 below).

**HATP-REQ-020.** Generic FIDO2 and generic PIV are not declared
interchangeable by this contract. A future implementation SHALL
demonstrate, for its chosen protocol and profile, that it actually
satisfies `HATP_HARDWARE_PROVIDER_V1`'s exact signing/assertion
requirement (HATP-REQ-019(c)) before being accepted as compliant.
HATP-001 does not promise arbitrary-payload signing capability from a
protocol that does not provide it.

**HATP-REQ-021.** A local software signing key (no hardware-backed
non-exportable key, no independent presence enforcement) SHALL NOT
silently substitute for a required hardware signer. Such a substitution
is compliant only if it independently satisfies every
`HATP_HARDWARE_PROVIDER_V1` property and is explicitly named by a
future contract version/profile (§26 "no software-key downgrade").

**HATP-REQ-022.** A future test-only provider MAY exist for verification
tooling. It SHALL be impossible for ordinary runtime configuration to
select a test-only provider as production authority by accident (e.g.
no default-enabled test provider, no silent fallback).

## 11. Device Attestation

**HATP-REQ-023.** Device/provider attestation MAY establish that a
device or provider belongs to an accepted hardware class. It SHALL NOT
by itself establish PCAE principal identity, rollback approval
authority, or repository authorization. Those are separately
established by bootstrap enrollment (§15-§16) and the protected
deployment binding (§18).

**HATP-REQ-024.** A valid vendor attestation alone, without a matching
protected-bootstrap-state enrollment, does not grant PCAE approval
authority (mirrors §43-§44 of the governing prompt).

**HATP-REQ-025.** An attestation proof SHALL NOT self-select an
arbitrary attestation root. The trusted provider root(s) MUST originate
outside the approval proof and outside agent-writable repository
state (§25).

## 12. Bootstrap Security Boundary

**HATP-REQ-026.** Root 2B is frozen as **Bootstrap Model Class B**: a
separate OS-enforced security context, per 149O.1B §6 and 149O.1B.1
§4-§7. HATP bootstrap trust SHALL terminate at an OS-enforced security
principal/ACL boundary — never at another agent-writable repository
sidecar file, another signature the same untrusted process could also
forge, or a mere policy convention (§18 of the governing prompt; 149O.1B.1
§18 root-termination statement).

**HATP-REQ-027.** The Agent OS principal SHALL NOT possess any
privilege-escalation path (unrestricted `sudo`, reachable setuid
binaries, group membership granting Human/Admin file access, or any
equivalent mechanism) sufficient to alter HATP protected bootstrap
state or assume the Human/Admin principal's identity.

## 13. OS Principal Model

**HATP-REQ-028.** The frozen v1 principal topology is exactly two
principals: an **Agent OS principal** and a **Human/Admin OS
principal**. The Human/Admin OS principal combines the human-approver
and bootstrap-administrator roles for v1 (149O.1B.1 §5 — a three-
principal split closes no additional attack under Threat A and is
explicitly deferred, not adopted).

**HATP-REQ-029.** HATP bootstrap trust SHALL NOT be considered
operationally ready when the Agent OS principal and the Human/Admin
functions execute under the same OS security principal, unless an
independently equivalent protection mechanism is proven. The current
repository deployment (same OS user for both roles) is therefore
**NOT READY** (§37).

## 14. Trusted Bootstrap Store

**HATP-REQ-030.** HATP freezes the conceptual existence of a **trusted
bootstrap store**: the authoritative record of enrolled principals,
keys, provider profiles, and repository authorizations. It SHALL be
owned/administered by the Human/Admin OS principal, readable by the
verifier as required, and NOT writable, replaceable, or deletable by
the Agent OS principal.

**HATP-REQ-031.** Protection under HATP-REQ-030 MUST cover, at the OS/
filesystem layer: file mutation, file replacement, unlink, rename,
parent-directory replacement, permission weakening, and ACL
modification (§25 of the governing prompt).

**HATP-REQ-032.** The authoritative trusted bootstrap store SHALL NOT
reside solely in ordinary agent-writable repository state. A
repository-local representation MAY exist only as a non-authoritative
cache/reference copy, never as the trust anchor itself (149O.1B.1 §12).

**HATP-REQ-033.** A future implementation SHALL fail safely against an
agent-controlled substitution of the authoritative trust-store path via
symlink or equivalent path substitution.

**HATP-REQ-034.** Normal runtime SHALL NOT be able to redirect the
authoritative trust store through an untrusted environment variable.

**HATP-REQ-035.** The normal agent-facing CLI SHALL NOT accept an
override flag (e.g. `--hatp-trust-store`, `--trusted-key`) that
bypasses protected configuration. Test-only/internal injection
mechanisms, if any, are a separate, non-production surface and remain
outside this restriction.

## 15. Approver Enrollment

**HATP-REQ-036.** Only the Human/Admin bootstrap authority may: enroll
an approver, grant repository approval authority, replace a key,
rotate a key, revoke a key, revoke a principal, or change a protected
deployment binding.

**HATP-REQ-037.** Initial enrollment follows the conceptual procedure
frozen by 149O.1B.1 §19: the Human/Admin principal authenticates to its
own OS account, verifies the hardware/provider identity, obtains the
signer's public/credential identity, assigns a `principal_id`, assigns
repository-specific rollback authority, registers the protected
deployment binding, and writes the protected HATP trust state. No step
in this procedure is performable by the Agent OS principal.

**HATP-REQ-038.** Enrollment establishes who may approve. It does not
itself approve any rollback (§37 of the governing prompt).

**HATP-REQ-039.** A signer SHALL already be enrolled and authorized
before producing a valid approval proof. Proof creation SHALL NOT
implicitly grant signer authority (no approval-time authority
mutation).

**HATP-REQ-040.** The autonomous agent SHALL NOT be able to establish
or expand its own human-approval authority by supplying a public key,
principal identifier, registry entry, or approval artifact
(self-enrollment prohibition). Mandatory future acceptance behavior:
agent creates an attacker key, attempts trusted enrollment, is denied
by the OS bootstrap authority boundary (§32 of the governing prompt;
§44 attack #7 below).

**HATP-REQ-041.** The agent SHALL NOT be able to replace a trusted key/
principal mapping in the bootstrap store (verifier-key-replacement
prohibition). Mandatory future acceptance behavior: agent attempts
replacement, is denied by the OS bootstrap authority boundary (§44
attack #8).

**HATP-REQ-042.** The agent SHALL NOT be able to delete or otherwise
remove trusted bootstrap state (registry-deletion prohibition; §44
attack #9). If bootstrap state is missing or corrupt for any reason,
HATP verification is unavailable, and the proof SHALL be treated as
`MISSING` or `MALFORMED` — never as trivially valid (§27, §36).

## 16. Approval Authority

**HATP-REQ-043.** A repository-scoped `principal &rarr; rollback
authority` mapping SHALL come exclusively from the protected bootstrap
state (§18 of the governing prompt), never from proof content alone.

**HATP-REQ-044.** Valid device possession (a genuine hardware signature
from an unenrolled key) is **UNAUTHORIZED**, not merely unverified —
device possession is not authority (§43 of the governing prompt).

**HATP-REQ-045.** Valid device attestation alone (§44 of the governing
prompt) does not grant PCAE approval authority; see HATP-REQ-024.

## 17. Repository Identity

**HATP-REQ-046.** HATP-001 adopts **CRI Model A** (149O.1B.2 §9) as its
repository-scope dependency: Layer 1 is a repository-local, randomly
generated, persistent `repository_id`. Repository identity is owned by
this contract; a separate Canonical Repository Identity contract is not
required before this freeze (149O.1B.2 §20, reconfirmed §36 below).

**HATP-REQ-047.** `repository_id` SHALL be: stable across normal
commit/branch activity; stable across a legitimate path rename or move;
not derived solely from filesystem path; not derived solely from Git
remote URL; not derived solely from Git HEAD or object history; not
itself an approval credential; not authority-bearing by itself; and not
caller-selectable at approval time (149O.1B.2 §5).

**HATP-REQ-048.** A future PCAE identity-aware initialization MAY
generate `repository_id` without requiring human approval, because
identity creation alone grants no HATP authority. No such
initialization is implemented by this phase (§47 of the governing
prompt).

**HATP-REQ-049.** Repository-local storage of `repository_id` is
acceptable because it is not a secret and not a trust root. Future
architecture SHALL treat it as PCAE-owned local metadata, not as
committed/cloned authoritative shared identity.

**HATP-REQ-050.** Repository-instance identity state introduced by a
future implementation MUST NOT automatically propagate through normal
Git clone. A future implementation SHALL add its concrete storage
location to `.pcae/.gitignore` (or repository-conventional equivalent)
as part of its own scope; this phase freezes the requirement, not the
exact filename (149O.1B.2 §12, independently reconfirmed by 149O.1B.2's
own fresh grep sweep that `.pcae/**` is only partially gitignored
today).

**HATP-REQ-051.** **Mandatory statement (verbatim requirement):**
Possession, knowledge, copying, or modification of `repository_id`
SHALL NOT by itself grant HATP approval authority.

## 18. Protected Deployment Binding

**HATP-REQ-052.** HATP trust state SHALL separately bind `repository_id`
to a canonical local deployment identity/root, under Human/Admin
control (Layer 2 of CRI Model A). This protected deployment binding is
what prevents authority transfer through copy or clone, and is
load-bearing (§50, §75 of the governing prompt).

**HATP-REQ-053.** A future implementation SHALL resolve the canonical
deployment root deterministically, accounting for absolute path,
symlink resolution, and platform normalization — never trusting a raw
caller-supplied path string.

**HATP-REQ-054.** `repository_id` and the protected deployment
registration are normatively separate facts. `repository_id` MAY
survive a legitimate move; HATP deployment authority MAY require
Human/Admin re-binding after the canonical root changes.

**HATP-REQ-055.** **Path move:** `repository_id` is preserved; the
protected deployment binding MAY become invalid; HATP SHALL be
unavailable until an admin-authorized rebind occurs. This is intentional
and acceptable.

**HATP-REQ-056.** **Path rename:** the same semantics as HATP-REQ-055
apply whenever the canonical deployment locator changes.

**HATP-REQ-057.** **Full directory copy:** copying an entire repository,
including its `repository_id`, SHALL NOT transfer HATP authority,
because the copied deployment lacks a matching protected deployment
registration.

**HATP-REQ-058.** **Git clone:** a normal clone SHALL NOT automatically
inherit HATP repository authority.

**HATP-REQ-059.** **Fork:** a fork SHALL NOT automatically inherit HATP
local approval authority.

**HATP-REQ-060.** **Git worktree:** per 149O.1B.2 §13, each worktree
SHALL receive a distinct repository-instance identity and SHALL require
separate bootstrap enrollment to obtain HATP authority.

**HATP-REQ-061.** **Repository-ID theft:** if a second, unauthorized
deployment (Repository B) copies an authorized Repository A's
`repository_id`, this SHALL NOT confer authority, because the protected
deployment binding will not match Repository B's canonical root.

**HATP-REQ-062.** **Same-ID cross-deployment:** even with an identical
local `repository_id` present in two deployments, the wrong deployment
SHALL be treated as unauthorized.

**HATP-REQ-063.** **Mandatory statement (verbatim requirement):**
repository-local metadata alone SHALL NOT be sufficient to transfer
HATP authorization to a new local deployment.

**HATP-REQ-064.** **Backup restore:** restoring the same trusted
deployment MAY retain or recover authority. Restoring to a different
canonical root SHALL require Human/Admin re-binding.

**HATP-REQ-065.** **Repository reidentity:** a future explicit
reidentity operation MAY generate a new `repository_id`. It SHALL NOT
automatically inherit prior HATP authority. No such operation is
implemented by this phase.

**HATP-REQ-066.** **Repository-ID mutation, missing, malformed, or
unknown:** if `repository_id` changes unexpectedly, is missing, is
malformed, or does not match any protected registry entry, the
protected registry lookup fails and HATP SHALL be treated as
unavailable/`UNAUTHORIZED` — fail closed in every case.

## 19. Human Approval Provenance Proof

**HATP-REQ-067.** The proof artifact is named **`HumanApprovalProvenanceProof`**,
distinct from the CHGR Decision, the RAE Binding, and the Permission
Broker decision (149O.1A §12).

**HATP-REQ-068.** Every proof SHALL carry a `proof_version` field. This
contract freezes `proof_version = 1` as the only version this contract
defines.

## 20. Canonical Payload

**HATP-REQ-069.** A `HumanApprovalProvenanceProof` payload SHALL bind, at
minimum, the following fields:

```
principal_id
signer_key_id              (credential/key fingerprint)
provider_profile           (e.g. "HATP_HARDWARE_PROVIDER_V1")
repository_id
decision_record_id         (CHGR record_id, per RAE-REQ-017's
                             governance_record_reference)
decision_record_digest     (CHGR record_digest)
binding_id                 (RAE evidence_id)
binding_digest             (the Binding record's own content-integrity
                             digest, per RAE-REQ-055)
rollback_site              (AG3 | AG5, family-locked per RAE-REQ-020/021)
job_id, original_commit_sha              (required when rollback_site=AG3)
per_id, ecp_id                           (required when rollback_site=AG5)
issued_at
proof_version
```

**HATP-REQ-070.** The proof payload SHALL NOT include the raw canonical
local deployment path. Deployment verification is performed separately
by the protected registry (§18), not carried in the portable proof.

**HATP-REQ-071.** A proof over a generic action label (e.g.
`approve_rollback`) without the concrete operation fields (HATP-REQ-069)
is insufficient and SHALL be treated as `WRONG_OPERATION` or
`MALFORMED`.

**HATP-REQ-072.** Mutation of the referenced Decision content after
proof creation SHALL invalidate the proof (verified via
`decision_record_digest`).

**HATP-REQ-073.** Mutation of the referenced Binding content after
proof creation SHALL invalidate the proof (verified via
`binding_digest`).

**HATP-REQ-074.** Changing `repository_id` after proof creation SHALL
invalidate the proof.

## 21. Proof Creation

**HATP-REQ-075.** Canonical serialization of the signed payload SHALL be
deterministic: signature/assertion verification MUST NOT depend on
arbitrary JSON key ordering, locale, newline convention, or ambiguous
timestamp rendering. A future implementation SHALL define one exact
canonical serialization (e.g. sorted-key, fixed-encoding JSON with a
fixed timestamp format) before proof creation is implemented; none is
implemented by this phase.

**HATP-REQ-076.** A future implementation SHALL define enough
provider/signature semantics for interoperable verification, without
claiming unsupported protocol behavior (§20). No concrete algorithm is
frozen by this contract; a future profile revision MAY do so once
compatible with the selected hardware/provider (HATP-REQ-020).

**HATP-REQ-077.** A `HumanApprovalProvenanceProof` SHALL NOT establish
signer trust merely by carrying its own public key. The signer MUST
resolve through the protected bootstrap state (§14-§16), never through
proof self-assertion.

## 22. Proof Verification

**HATP-REQ-078.** The closed HATP verification-status vocabulary is
frozen as:

```
VALID
MISSING
MALFORMED
INVALID_SIGNATURE
UNKNOWN_SIGNER
UNAUTHORIZED_SIGNER
REVOKED_SIGNER
INVALID_ATTESTATION
USER_PRESENCE_NOT_PROVEN
WRONG_OPERATION
WRONG_REPOSITORY
WRONG_DEPLOYMENT
EXPIRED
```

This vocabulary SHALL NOT be extended informally by a consumer, and
SHALL NOT reuse Permission Broker decision names (`ALLOW`/`DENY`/
`HUMAN_REVIEW`) or RAE-001's own vocabulary (`VALID | MISSING |
INVALID | STALE | REVOKED | UNAUTHORIZED_APPROVER | WRONG_SCOPE |
SUPERSEDED`) — the two vocabularies are structurally distinct and MUST
NOT be conflated (mirrors RAE-REQ-036's own separation from the
Permission Broker's vocabulary).

**HATP-REQ-079.** A proof is `VALID` only when every applicable term
succeeds, conjunctively, with no partial success: proof structurally
valid; provider profile accepted; signature/assertion valid; required
human presence proven; device/provider attestation valid where
required; signer key known; principal mapping valid; principal
authority valid; `repository_id` matches the proof; protected
deployment registration matches the current deployment;
`decision_record_digest` matches; `binding_digest` matches; operation
identity matches; proof time valid; signer not revoked.

**HATP-REQ-080.** Missing trusted bootstrap state SHALL cause
verification to fail closed (§42).

**HATP-REQ-081.** **Cross-repository replay:** a proof produced under
one `repository_id`/deployment SHALL NOT validate under another
(`WRONG_REPOSITORY` or `WRONG_DEPLOYMENT`).

**HATP-REQ-082.** **Same-ID replay defense:** a copied repository that
reproduces an authorized repository's local `repository_id` SHALL still
fail verification if the protected deployment binding differs
(`WRONG_DEPLOYMENT`).

**HATP-REQ-083.** **Operation replay:** a valid proof copied to another
operation (different Decision/Binding/rollback identity fields) SHALL
be `WRONG_OPERATION`, invalid for the new operation.

## 23. Freshness

**HATP-REQ-084.** RAE-001's existing 24-hour freshness window
(`expires_at`, RAE-REQ-043) remains the approval-evidence TTL. HATP-001
SHALL NOT create a conflicting, longer approval lifetime; HATP
proof-level validity (§22) is binary, not itself a second decaying TTL.

**HATP-REQ-085.** `issued_at` supports proof integrity and chronology
ordering. A future-dated `issued_at` (later than the verifier's current
time, beyond an implementation-defined clock-skew tolerance) SHALL be
treated as `EXPIRED`/invalid.

## 24. Key Rotation

**HATP-REQ-086.** A future implementation SHALL define a deterministic
old-key/new-key transition procedure. No agent-driven rotation is
permitted; rotation is a Human/Admin bootstrap-authority action only
(§36).

## 25. Key Revocation

**HATP-REQ-087.** The protected bootstrap state MAY revoke a signer
key. A revoked signer SHALL NOT be able to create a new usable approval
proof. Whether a proof produced *before* revocation remains usable at
*consumption* time is governed by HATP-REQ-088 (authority-at-
consumption-time takes precedence).

## 26. Authority Revocation

**HATP-REQ-088.** The protected bootstrap state MAY revoke a
principal's repository rollback authority. The frozen v1 semantic is:
authority MUST remain valid **at proof-consumption (verification)
time**, not merely at proof-creation time. A proof whose signer or
principal has since been revoked SHALL verify as `REVOKED_SIGNER` (or
equivalent), regardless of validity at the time of signing.

**HATP-REQ-089.** A repository deployment-root change (§18) SHALL
require Human/Admin administrative rebind. The agent cannot rebind
itself.

## 27. Failure Semantics

**HATP-REQ-090.** Every undefined, missing, malformed, unauthorized, or
otherwise non-`VALID` verification outcome SHALL result in HATP
unavailability for that operation, never in a default-allow or
best-effort partial trust outcome.

**HATP-REQ-091.** If a future implementation determines that the
required OS principal separation or protected trust-store ownership is
not satisfied for the current deployment, the HATP environment SHALL be
treated as UNSAFE/unavailable. No procedural fallback (e.g. "trust
anyway with a warning") is permitted.

**HATP-REQ-092.** **Same-user runtime:** while the Agent OS principal
and Human/Admin functions execute under the same OS security principal,
HATP SHALL remain NOT READY, per HATP-REQ-029. This is this
repository's current, confirmed state (§37).

**HATP-REQ-093.** **Headless runtime:** in the absence of a hardware
signer or a Human/Admin approval context, HATP approval SHALL be
reported unavailable. No software fallback is permitted (see also
HATP-REQ-021).

## 28. Verification-Time Trust Boundary

**HATP-REQ-094.** Verification of a `HumanApprovalProvenanceProof` SHALL
be performed by trusted PCAE code that itself has no write access to
the trusted bootstrap store, mirroring RAE-001's own read/write
separation discipline; this is an implementation constraint recorded
now so a future implementation phase does not violate it silently.

## 29. RAE-001 Compatibility

**HATP-REQ-095.** RAE-001 v1.0 is **COMPATIBLE AS-IS**, independently
reconfirmed this phase (§40). HATP-001 supplies an *additional*
required condition — a valid `HumanApprovalProvenanceProof` — before
`approval_present` MAY be derived `True`; it changes no RAE-001 field,
requirement, or lifecycle rule. RAE-001's existing
`governance_record_reference` (`record_id`/`record_digest`),
`evidence_id`, `rollback_operation_reference`
(`job_id`/`original_commit_sha` for AG3, `per_id`/`ecp_id` for AG5),
and `expires_at` (24h, RAE-REQ-043) are reused by reference in
HATP-REQ-069, not redefined.

**HATP-REQ-096.** The frozen future integration rule: RAE-001
provenance is trusted **if and only if** a HATP proof is `VALID` (§22)
**and** RAE-001's own Decision/Binding/lifecycle requirements
independently pass. Neither condition substitutes for the other. No
production integration is implemented by this phase.

## 30. CHGR-001 Relationship

**HATP-REQ-097.** CHGR-001 v1.3 remains the human-governance Decision
layer, unchanged. HATP-001 proves independent human provenance for the
concrete operation a CHGR Decision records; it does not replace, extend,
or reinterpret CHGR-001's Decision Template, Confirmation, or
Publication semantics.

## 31. IWC-001 Boundary

**HATP-REQ-098.** IWC-001 v1.2's Interactive Decision Session
confirmation remains distinct from HATP approval. IWC-001 MAY eventually
transport or present the human-side reconstructed payload for review
(§45-§46 "blind-touch defense", "request is untrusted") but is never
itself approval evidence — only a `VALID` HATP proof combined with valid
RAE-001 evidence is.

## 32. AESIC-001 / AEM-001 Boundary

**HATP-REQ-099.** AESIC-001 v1.3 and AEM-001 v1.0 remain disclosure-only.
Neither is a source of approval authority, and HATP-001 introduces no
dependency on either beyond the general disclosure-only posture already
frozen for both.

## 33. TAMC-001 / TAMPC-001 Boundary

**HATP-REQ-100.** No TAM `human_authorization` composition is
introduced by HATP-001. TAMC-001 v1.0's `human_authorization` record
shape is reused only as non-normative structural precedent (matching
RAE-001's own precedent-only reuse, RAE-REQ-precedent note), never
composed, subclassed, or wrapped by a HATP artifact.

## 34. RWMPC-001 / PBPA-001 / PBPC-001 Boundary

**HATP-REQ-101.** HATP-001 does not alter mutation freshness or
execution ownership (RWMPC-001 v1.0, unamended).

**HATP-REQ-102.** HATP-001 introduces no change to POL applicability
(PBPA-001 v1.0, unamended). POL-004 continues to interpret only the
truthful `approval_present` fact supplied after RAE-001/HATP-001
validation; HATP-001 supplies an input to that fact, never a permission
decision itself.

**HATP-REQ-103.** HATP-001 introduces no change to `pcae push`
consumption of the Permission Broker Foundation (PBPC-001 v1.2,
unamended).

**HATP-REQ-104.** A `VALID` HATP proof does not itself transform an
existing `HUMAN_REVIEW` Permission Broker result into `ALLOW`. A fresh
Permission Broker evaluation is required after fresh RAE-001/HATP-001
validation (§99-§101 of the governing prompt).

## 35. Open Rollback-Evidence Findings

**HATP-REQ-105.** B-149O-1 through B-149O-4 remain **OPEN**. This
contract freeze does not repair them. Their future closure requires:
HATP implementation, RAE-001/HATP-001 integration, AG3/AG5 Permission
Broker wiring, and independent adversarial verification — none of which
occur in this phase.

**HATP-REQ-106.** Mapping preserved from 149O.1B §12 (unchanged): B-149O-1
(fake CHGR + fake receipt) closes only once no valid hardware-backed
HATP proof can be forged; B-149O-2 (real Decision + fake Binding + fake
registration) closes only once the Binding digest is covered by a valid
HATP proof; B-149O-3 (fully handcrafted artifact chain) closes for the
same reason as B-149O-1; B-149O-4 (fresh attacker key) closes only once
the attacker key is mechanically absent from the protected bootstrap
registry and verification enforces `UNAUTHORIZED_SIGNER`.

## 36. Repository Identity Contract Ownership

**HATP-REQ-107.** Reconfirmed from 149O.1B.2 §20: no separate Canonical
Repository Identity contract is required before this freeze. HATP-001
normatively owns the repository-identity semantics necessary for its own
approval-authority scope (§17-§18). This ownership SHALL NOT be read as
generalizing `repository_id` semantics to all PCAE subsystems; any other
subsystem wishing to depend on `repository_id` MUST do so through an
explicit, separately governed dependency declaration.

## 37. Current Deployment Readiness

**HATP-REQ-108.** Contract freeze does NOT imply deployment readiness.
The following status is frozen as the accurate description of this
repository's state at the moment of this freeze, and MUST be reproduced
verbatim by any status surface reporting HATP readiness until it
changes:

```
HATP CONTRACT:              FROZEN
HATP IMPLEMENTATION:        NOT IMPLEMENTED
CLASS-B OS BOUNDARY:        NOT PROVISIONED
REPOSITORY IDENTITY:        NOT IMPLEMENTED
HATP BOOTSTRAP ENVIRONMENT: NOT READY
```

## 38. Threat-Capability Matrix

**HATP-REQ-109.** The following capability matrix is frozen as
normative-supporting reference. "Yes" denotes the capability is
possessed under Threat A / the frozen v1 architecture; "No" denotes it
is denied.

| Capability | Agent OS principal | Human/Admin OS principal | Hardware provider |
|---|---|---|---|
| construct approval request | Yes | Yes | N/A |
| read repository identity (`repository_id`) | Yes | Yes | N/A |
| modify repository-local `repository_id` | Yes (grants no authority; causes deployment-binding mismatch, §18) | Yes | N/A |
| read protected trust registry | No (public verification surface only) | Yes | N/A |
| modify protected trust registry | No | Yes | N/A |
| enroll approver | No | Yes | N/A |
| grant rollback authority | No | Yes | N/A |
| invoke signer request | Yes (request only, not completion) | Yes | Yes (accepts request) |
| satisfy physical presence | No | Yes | Enforces |
| extract private key | No | No (non-exportable) | No (non-exportable) |
| change trust-store ACL | No | Yes | N/A |
| escalate to Human/Admin context | No | N/A | N/A |

**HATP-REQ-110.** Note on the "modify repository-local `repository_id`"
row: the agent MAY, under some future implementation, be able to write
its own repository-local identifier, but doing so grants no authority
and generically causes protected-deployment-mismatch fail-closed
behavior (§18, HATP-REQ-051/HATP-REQ-063), never elevated trust.

## 39. Mandatory Future Acceptance Attack Matrix

**HATP-REQ-111.** The following twenty acceptance attacks are frozen as
the minimum set a future implementation's independent verification MUST
exercise, each with the stated expected outcome:

1. Fully handcrafted RAE chain without a HATP proof &rarr; invalid.
2. Fake HATP signature/proof &rarr; invalid.
3. Attacker-selected public key presented as signer &rarr; invalid
   (`UNKNOWN_SIGNER`).
4. Unenrolled genuine hardware key &rarr; invalid (`UNAUTHORIZED_SIGNER`).
5. Valid device attestation but unauthorized principal &rarr; invalid.
6. Agent invokes a genuine signer without physical touch &rarr; no proof
   produced (`USER_PRESENCE_NOT_PROVEN`).
7. Agent self-enrollment attempt &rarr; denied by OS bootstrap authority
   boundary.
8. Agent verifier-key-replacement attempt &rarr; denied by OS bootstrap
   authority boundary.
9. Trust-store deletion/replacement attempt &rarr; denied by OS bootstrap
   authority boundary.
10. Environment/CLI trust-root redirection attempt &rarr; rejected.
11. Valid proof copied to another operation &rarr; invalid
    (`WRONG_OPERATION`).
12. Valid proof copied to another repository &rarr; invalid
    (`WRONG_REPOSITORY`).
13. Repository ID copied to an unauthorized deployment &rarr; invalid
    (`WRONG_DEPLOYMENT`).
14. Entire repository copied to another deployment &rarr; HATP
    unavailable for the copy.
15. Decision modified after proof creation &rarr; invalid.
16. Binding modified after proof creation &rarr; invalid.
17. Signer revoked &rarr; invalid (`REVOKED_SIGNER`).
18. Authority revoked &rarr; invalid.
19. Future-dated proof &rarr; invalid (`EXPIRED`).
20. Valid authorized human touch for an enrolled repository/operation
    &rarr; `VALID`.

## 40. Compatibility Reconfirmation

**HATP-REQ-112.** Independently reconfirmed this phase, by direct
header inspection of each contract file (§40 of the governing prompt):
RAE-001 v1.0 `COMPATIBLE AS-IS`; CHGR-001 v1.3 `COMPATIBLE AS-IS`;
RWMPC-001 v1.0 no amendment; PBPA-001 v1.0 no amendment; PBPC-001 v1.2
no amendment; IWC-001 v1.2 no amendment; AESIC-001 v1.3 / AEM-001 v1.0
no amendment; TAMC-001 v1.0 / TAMPC-001 v1.1 no amendment.

## 41. Full Requirement Traceability

**HATP-REQ-113.** Every security property named in the frozen
architecture (149O.1A, 149O.1B, 149O.1B.1, 149O.1B.2) maps to at least
one normative requirement above: fresh physical human presence
(HATP-REQ-016), no unattended signer success (HATP-REQ-017/018),
protected bootstrap trust store (HATP-REQ-030-035), agent cannot
self-enroll (HATP-REQ-040), agent cannot replace verifier key
(HATP-REQ-041), no privilege escalation into bootstrap authority
(HATP-REQ-027), `repository_id` is not authority (HATP-REQ-051),
protected deployment binding (HATP-REQ-052), copy/clone does not
transfer authority (HATP-REQ-057-063), cross-repository replay
rejection (HATP-REQ-081-083), proof cannot self-select trust key
(HATP-REQ-077), exact operation binding (HATP-REQ-069/071), fail-closed
unsafe deployment (HATP-REQ-090-093). No load-bearing behavior is left
only in non-normative prose.

## 42. Blocking-Condition Check

**HATP-REQ-114.** Independently checked against the governing phase
prompt's own blocking-condition list (§129):

| Blocking condition | Resolved? | Where |
|---|---|---|
| Human presence bypassable by unattended agent | No — HATP-REQ-016/017/018 mechanically require a fresh presence event per proof | §9 |
| Trusted bootstrap state agent-writable | No — HATP-REQ-030/031/032 require OS-enforced Human/Admin-only ownership | §14 |
| Agent has a privilege-escalation route to Human/Admin context | No — HATP-REQ-027 forbids it | §12 |
| Self-enrollment prevention only an application convention | No — HATP-REQ-040 requires OS bootstrap-boundary enforcement, not app convention | §15 |
| Verifier-key-replacement prevention only an application convention | No — HATP-REQ-041, same boundary | §15 |
| `repository_id` alone can confer authority | No — HATP-REQ-051/046-047 | §17 |
| Repo copy/clone can silently inherit HATP authority | No — HATP-REQ-057-063 | §18 |
| Deployment-binding semantics ambiguous | No — HATP-REQ-052-054 fix the Layer-1/Layer-2 separation | §18 |
| Proof can self-select trusted signer | No — HATP-REQ-077 | §21 |
| Proof does not bind concrete operation | No — HATP-REQ-069/071 | §20 |
| Wrong repository can replay a proof | No — HATP-REQ-081/082 | §22 |
| RAE integration contradicts frozen RAE semantics | No — HATP-REQ-095/096 reuse RAE fields by reference, add no amendment | §29 |
| Provider profile assumes unsupported arbitrary-signing behavior | No — HATP-REQ-020 explicitly forbids overclaiming | §10 |

No condition in this list is unresolved. This contract is FROZEN v1.0.

**HATP-REQ-115.** The one factual condition this contract does **not**
require resolved before freezing — because contract freeze is
architectural/normative, not an implementation-readiness claim — is
actual current provisioning of the Class-B OS boundary in this
repository's live deployment. That remains NOT READY (§37, HATP-REQ-092)
and is explicitly not a blocking condition for the *contract text*
itself (§20, §84-§85, §125 of the governing prompt).

## 43. Requirement Sequence Verification

**HATP-REQ-116.** This contract defines requirements `HATP-REQ-001`
through `HATP-REQ-116` inclusive (this requirement), sequential, no
gaps, no duplicates, one per normative sentence or closed table,
mirroring RAE-001's `RAE-REQ-001`..`RAE-REQ-081` convention.

## 44. Versioning

**HATP-REQ-117.** This contract is versioned `1.0`, frozen only because
every Blocking condition identified by the governing phase prompt
(§42 above) is resolved. A future amendment (e.g. to define a concrete
signature algorithm, HATP-REQ-076, or a concrete canonical serialization,
HATP-REQ-075) SHALL proceed through a governed contract-amendment phase,
never through silent reinterpretation of this text.

## 45. Contract Freeze Verdict

```
HATP-001 v1.0 FROZEN
— HUMAN APPROVAL TRUST BOUNDARY COMPLETE
```

## 46. Implementation Readiness Status

```
HATP architecture:           DEFINED
HATP contract:                FROZEN (this contract, Phase 149O.1B.3)
HATP implementation:          NOT IMPLEMENTED
Class-B OS boundary:          NOT PROVISIONED
Repository identity:          NOT IMPLEMENTED
RAE / HATP integration:       NOT IMPLEMENTED
AG3 / AG5:                    UNWIRED
```

This contract's freeze does not imply deployment readiness or coverage
exists. No signer, verifier, registry, or repository-identity file is
implemented in production; no OS account, ACL, or sudoers configuration
is created; no `approval_present` derivation is changed; AG3 and AG5
remain unwired to the Permission Broker.

## 47. Recommended Next Phase

```
149O.1C — Human Approval Trusted Provenance Contract Independent Verification
```

The independent verifier SHALL attack, at minimum: every item in the
mandatory acceptance attack matrix (§39); the human-presence rule (§9);
the hardware-provider profile precision (§10); the bootstrap-boundary
enforcement claims (§12-§15); the repository-identity/deployment-binding
separation and every copy/clone/worktree/rename scenario (§17-§18); the
canonical payload's operation-binding completeness (§20); the closed
verification vocabulary's conjunctive semantics (§22); the freshness/
revocation-at-consumption-time rule (§23, §26); and the RAE-001/CHGR-001/
IWC-001/AESIC-001/TAMC-001/RWMPC-001/PBPA-001/PBPC-001 compatibility
reconfirmations (§29-§34).
