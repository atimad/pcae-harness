# Phase 149O.1B.1: Human Approval Bootstrap Authority Architecture

**Phase type:** trust-boundary architecture only (Root 2B bootstrap
mechanics). No implementation, no OS changes, no contract freeze.

**Status:** completed. **Architecture verdict: HUMAN APPROVAL BOOTSTRAP
AUTHORITY ARCHITECTURE DEFINED — REPOSITORY IDENTITY PREREQUISITE
REMAINS.**

## 1. Starting Position (independently reconfirmed)

- Repository clean; `origin/main..HEAD` = 0 at phase start.
- Latest completed phase: 149O.1B — **HATP-001 NOT FROZEN — BOOTSTRAP /
  AUTHORIZATION TRUST GAP CONFIRMED**, with concrete primary-source
  evidence (not merely suspicion) that none of the three candidate
  bootstrap-boundary mechanisms is currently established: no distinct
  OS principal (agent and human both run as `atilamadai`); no external
  service/KMS; GitHub branch protection present but structurally
  insufficient (`enforce_admins=false`, sole collaborator, shared local
  SSH/`gh` credentials).
- 149O.1B selected **Bootstrap Model Class B** (separate OS security
  context) as the target architecture, over Class A (hardware
  enrollment alone — does not, by itself, answer where the enrollment
  *record* lives) and Class C (external registry/review gate — rejected
  as circular for this deployment).
- `pcae health`/`check`/`status coherence`/`doctor task-memory`/`push
  check`/`runtime inspect`/`notify status`: all healthy/coherent/clean;
  runtime Observed / observe / unavailable; Telegram configured and
  ready. `pcae phase-report reconcile --phase-id 149O.1B`: reconciled,
  receipt finalized, mutation none.
- `git log origin/main..HEAD` empty; `git status --short` clean.

## 2. Scope Discipline

Per the governing prompt, this phase does **not** reopen the Model A/B/
C/D/E signer-model comparison (149O.1A §7) or the Class A/B/C bootstrap-
model-class selection (149O.1B §6) — no primary-source evidence emerged
that contradicts either selection. This phase's entire job is Root 2B
*mechanics*: given Class B is the selected target, what concrete
security-principal topology, filesystem/ownership model, and workflow
set would actually establish it in this repository's real deployment,
and does that design mechanically block self-enrollment and
verifier-key replacement?

## 3. Existing-Infrastructure Inspection (primary source, this phase)

Before designing new principals, this phase checked what security
infrastructure already exists to build on:

- **No OS-identity check anywhere in `src/pcae`.** A repo-wide grep for
  `getuser|getuid|geteuid|whoami|getpass` across `src/pcae` (excluding
  the unrelated shell-command allowlist in `core/shell_gate.py`, which
  merely permits the read-only `whoami`/`id` *commands* to be executed
  by governed shell, not used for authorization) returns zero
  authorization-relevant matches. Confirms 149O.1B §4.1's finding is not
  an oversight — no OS-principal-aware code path exists to extend.
- **`acquire_agent_lock()`** (`src/pcae/core/agent.py:288-306`, read in
  full this phase): writes `.pcae/agent-lock.json` via ordinary
  `open(..., "x")` under the agent-writable repository tree, trusting
  the caller-supplied `agent_id` string verbatim. This is the existing
  pattern this architecture must explicitly *not* extend to the HATP
  trust store (§13).
- **Existing environment-variable config-path override precedent**:
  `src/pcae/core/notification_config.py:62` reads a `CONFIG_PATH_ENV`
  override, and `src/pcae/commands/phase_reports.py:581` /
  `core/phase_reports.py:3448` read `PCAE_NOTIFY_OUTPUT_DIR`. Both are
  legitimate for their own (non-security-critical) purposes, but they
  establish that this codebase already has a habit of honoring
  env-var path overrides. §16/§40's env/CLI-override prohibition below
  is written specifically to prevent the HATP trust-store lookup from
  acquiring the same habit.
- **No stable, protected repository-identity primitive** — investigated
  in full in §14.

No existing mechanism in this repository provides any part of the
Class-B boundary today. This architecture is designed from first
principles, consistent with 149O.1B §7's finding that the current
deployment provides nothing to extend.

## 4. Security Principals (item 3)

Three conceptually distinct roles are named, independent of how many OS
accounts eventually implement them (§7 decides that):

```
PCAE_AGENT_PRINCIPAL
  The security context under which the autonomous PCAE agent process
  executes: reads/writes the governed repository, invokes the CLI,
  constructs approval requests.

PCAE_HUMAN_APPROVER_PRINCIPAL
  The security context from which a human reviews an approval request,
  operates the hardware signing device, and produces a HATP proof
  (149O.1A Root 1, unchanged).

PCAE_BOOTSTRAP_ADMIN_PRINCIPAL
  The security context authorized to enroll approver keys, bind key to
  principal, grant/revoke repository rollback-approval authority, and
  own the protected trust store.
```

## 5. Two-Principal vs Three-Principal Model (item 58, mandatory decision)

**Two-principal:** `{agent}` vs. `{human/admin}` — one OS principal owns
enrollment, trust-store administration, *and* hardware-signer
interaction; the other executes the agent, unconditionally.

**Three-principal:** `{agent}` vs. `{human approver}` vs. `{bootstrap
admin}` — the enrollment/administration role is split from the
signing-time approval role, as two distinct OS principals.

Under **Threat A** (this architecture's governing threat model, adopted
unchanged from 149O.1A/149O.1B §2: an unattended software agent with no
separate secret or out-of-band human capability — Threat B, full
host/root compromise or a compromised human-side context, remains
explicitly excluded), splitting human-approver from bootstrap-admin
closes **no additional attack**: Threat A's attacker is the agent
principal, not either human-side principal, so separating the two
human-side roles only reduces *human*-side blast radius under Threat B
(a compromised approval-session malware scenario), which is out of
scope here. A three-principal model would add real operational
complexity — a second human-side account, its own credential
management, its own recovery procedure (§11 of 149O.1A already flags
this trade-off generically) — for a security property this phase's own
governing threat model does not require.

**Decision: two-principal model for HATP v1** (`PCAE_HUMAN_APPROVER
_PRINCIPAL` and `PCAE_BOOTSTRAP_ADMIN_PRINCIPAL` collapse into one OS
account, `PCAE_AGENT_PRINCIPAL` stays fully distinct), per item 59's
stated preference, justified here by Threat A's own scope rather than
merely "simplicity." If a future phase adopts Threat B (compromised
human-side context) as in-scope, this decision should be revisited —
recorded as **DEFERRED** (§20).

## 6. Same-User Architecture Challenge (item 8, mandatory)

Explicit negative case: can Class B hold if human and agent run as the
*same* Unix/macOS user (this repository's actual, current deployment,
per 149O.1B §4.1)? **No.** If every protected file is writable by that
one user, no filesystem-ownership or ACL fact distinguishes "the agent
process wrote this" from "the human wrote this" — the OS makes no such
distinction once both share a UID. No alternative in-OS-user boundary
(process-group isolation, capability sets, SELinux/AppArmor labels
applied at the same UID) is available in this repository's actual
deployment today, and 149O.1B's own investigation (§4.2-4.3) already
ruled out both candidate non-OS-user boundaries (external service, and
GitHub review gate) as absent/insufficient. **Distinct OS-user
separation between the agent principal and the human/admin principal is
therefore load-bearing and mandatory for Class B to mean anything** —
not merely preferred (item 7 confirmed).

## 7. Selected V1 Principal Topology (items 9, 59)

```
Agent OS principal            (e.g. "pcae-agent", illustrative name only)
  - runs the autonomous PCAE agent process
  - owns/writes the governed repository working tree under PCAE's
    existing governed-mutation rules
  - MAY read the HATP trust store (public verification material, §11)
  - MUST NOT write the HATP trust store, enroll, revoke, rotate, or
    grant authority (§10-§11)
  - MUST NOT hold privilege escalation reaching the admin principal's
    security context (§9)

Human/Admin OS principal       (the existing human operator's own
                                account, e.g. "atilamadai" today, or a
                                renamed dedicated admin account)
  - owns the HATP trust store (creates, enrolls, revokes, rotates)
  - interacts with the hardware signing device to produce HATP proofs
  - is the sole writer of trust-store state
```

This is the **minimum viable topology** (item 9): it introduces exactly
one new OS principal (the agent's), reuses the human's existing account
for both approval and administration (§5), and requires no third
account, no new external service, and no hardware beyond what 149O.1A
already selected (Root 1, unchanged).

## 8. Agent Security Context (item 4)

The agent principal needs, and receives:

```
MAY:
  - read repository (governed checkout)
  - write repository under governed mutation rules (task-scoped, per
    existing PCAE Allowed Files/Zones enforcement)
  - read non-secret HATP verification data (trust-store public
    material: enrolled principal IDs, public keys/fingerprints,
    authority scope, revocation status)
  - submit HATP approval requests (construct payload, invoke request
    interface — §17)
  - read approval-result/proof artifacts once returned (§18)
  - use ordinary git/toolchain access needed for governed work

MUST NOT:
  - write, delete, rename, or change permissions/ownership on the HATP
    trust store or its containing directory (§13)
  - enroll a key/principal, grant, revoke, or rotate authority (§13)
  - hold bootstrap-admin credentials
  - hold hardware-enrollment authority
  - possess privilege escalation (sudo/root/admin-equivalent) reaching
    the admin principal's security context (§9)
```

## 9. No Agent Sudo Escape (items 18, 61-62, load-bearing)

A distinct OS principal is meaningless if the agent principal can
`sudo`/escalate into the admin principal or root. This architecture
therefore states normatively:

> The agent OS principal SHALL NOT possess any privilege-escalation
> path (unrestricted `sudo`, setuid binaries reachable by it, group
> membership granting it admin-principal file access, or any other
> mechanism) that would allow it to modify the HATP trust store,
> impersonate the bootstrap-admin principal, or read the admin
> principal's private key material. Any `sudo` grants the agent
> principal holds for unrelated operational purposes (package
> installation, service management, etc.) SHALL be scoped by an
> explicit denylist/allowlist that excludes every HATP-protected path
> and excludes any command capable of changing file ownership/ACLs on
> those paths (`chown`, `chmod`, `setfacl` and platform equivalents) or
> impersonating the admin principal (`su`, unrestricted `sudo -u
> <admin>`).

This is a **prerequisite property**, not an implementation detail —
without it, the OS-principal separation in §7 is cosmetic. Flagged as
**BLOCKING** for any future deployment/implementation phase to verify
concretely (§19).

## 10. Human/Admin Security Context (items 5-6)

The combined human/admin principal (§5) needs:

```
- interactive login capability, used to review approval requests and
  operate the hardware signing device (149O.1A Root 1, unchanged)
- write access to the HATP trust store (enroll/revoke/rotate, §17)
- no requirement to have any special relationship to the *repository*
  working tree beyond what an ordinary developer already has today —
  administration of the trust store is a separate responsibility from
  editing repository files
```

Determined explicitly (item 5's question): **yes**, this context needs
write access to the trusted approver configuration — that write access
*is* the mechanism this whole architecture exists to grant to exactly
one principal.

## 11. Bootstrap Administrator Authority (item 6)

The bootstrap-admin role (collapsed into the human/admin principal, §5)
is authorized to:

```
- enroll approver keys (bind attested device public key -> principal_id)
- grant repository-scoped rollback-approval authority to an enrolled
  principal
- revoke an approver
- rotate a trusted key
- change verifier/trust-store configuration
```

The agent principal has no equivalent authority in any of the five
operations above (§8).

## 12. Filesystem / Trust-Store Ownership Model (items 12-18)

**Trusted registry ownership, frozen conceptually:**

```
registry owner:   human/admin OS principal
registry reader:  PCAE verifier process (whichever principal invokes
                  it — in practice, the agent principal for read-only
                  validation, and the human/admin principal for
                  administration)
registry writer:  human/admin OS principal only
```

**Repository-local trust configuration is explicitly prohibited as
authoritative** (item 13, normative): the HATP trust store SHALL NOT
live solely inside the agent-writable repository checkout or the
`.pcae/**` state tree, because both are governed-mutation-writable by
the agent principal under PCAE's existing task-scoped write rules
(§8's "write repository under governed mutation rules" is precisely the
capability that must not reach the trust store). If a repository-local
copy exists at all, it is non-authoritative/cache-only (e.g. a
periodically-refreshed, agent-readable mirror of the *public* portion
of the registry for convenience), never the record a verifier trusts.

**Trust-store location model** (item 14, platform-neutral): a directory
owned by the human/admin OS principal, outside the repository's own
tree, with permissions granting the admin principal read/write and the
agent principal read-only (or, on platforms without a natural "world
read, owner write" primitive for a *specific other principal*, a
POSIX group `pcae-hatp-readers` containing the agent principal, with
group-read/no-group-write bits, owner-write only). Illustrative
platform-neutral candidates (none frozen as final path/name — item 14):
a system-level trust directory (root-equivalent-owned, world-readable,
analogous to `/etc/ssl/certs`) or a user-level protected directory
under the admin principal's own home directory (`~admin/.../hatp/`,
mode `0750`, group-readable by the agent principal's group). Selection
between these two is deployment policy, not frozen here.

## 13. Agent Read Access / Write Denial (items 15-16)

Read access to *public* trust-store material (enrolled principal IDs,
public key fingerprints, authority scope, revocation status) is safe
for the agent principal to hold — item 15's observation, confirmed:
reading who is authorized does not let the agent grant itself
authorization. Write denial (item 16) is enforced at the OS-permission
layer: different file/directory owner (human/admin principal), agent
principal has no write bit and is not a member of any group with write
access. On Windows-family deployments, the equivalent property is an
ACL granting the agent principal's security identifier `Read` only and
the admin principal's security identifier `FullControl`, with
inheritance disabled on the trust-store directory so a later ACL change
higher in the tree cannot silently widen agent access.

## 14. Repository Identity — Investigation (items 45-51, 105-110)

**Question:** does a stable, mechanically-derived repository identity
already exist in this codebase, suitable for scoping the trust store's
`approval_authority_scope` field (149O.1A §15's repository-specific
preference) to *this* repository rather than any repository an agent
happens to be checked out into?

**Search performed this phase** (item 105):

- `.pcae/**` metadata: no repository UUID or durable identity field —
  `.pcae/session.json`, `.pcae/agent-lock.json`, and the phase-report
  artifacts all key on `repo_path` (a filesystem path) or task/phase
  identifiers, never a repository-level identity.
- `src/pcae/cltr_prototype/**` and `src/pcae/cltr/**` (`identity.py`,
  `models.py`, `compatibility.py`) do define a `repository_identity`
  field — but `identity.py:80-108`'s own docstring states plainly:
  *"never reads a filename, title, commit subject, or the live
  repository to fill in a missing field — a missing required field is
  always an `IdentityError`, never a fallback."* It is a plain,
  caller-declared string (`_validate_plain_id`), used for an unrelated
  purpose (Canonical Lifecycle Transition Record migration/derivation
  identity, where it is populated from `phase_id` — see
  `cltr/migration/cltr_derivation.py:63,150`), never derived from any
  protected, mechanical, or hardware-anchored fact. It is exactly the
  kind of "unstable, self-selected" identity item 49 warns against, not
  a suitable HATP scope anchor.
- Repository knowledge/intelligence metadata (`repository_intelligence
  /snapshot_builder.py:518`, `historical_builder.py:744`) also carries a
  `repository_identity` key, but it too is populated from caller-
  supplied `repository_context`, not from any OS/hardware/git-anchored
  source of truth.
- `git remote -v` (149O.1B §4.3) gives a remote URL, explicitly
  disqualified by item 50 (mutable, not uniquely representative of
  local authority scope) and reconfirmed here: a repository's remote can
  be repointed by anyone with local write access to `.git/config` —
  including the agent principal today.

**Classification (item 106 criteria — stable across moves; not
silently shared by unrelated clones; not caller-selectable at approval
time; protected in the authorization binding):** no existing candidate
satisfies all four. Every `repository_identity`-named field in this
codebase today is a caller-declared plain string for an unrelated
purpose, not a protected identity primitive.

**Disposition (item 108):** per the "no suitable ID exists" branch,
this phase does **not** invent a repository-identity mechanism inside
the HATP trust store, and does **not** silently fall back to
global/unscoped authority (item 110, explicitly forbidden). Instead:

> **Repository-identity is a narrow, named prerequisite for HATP-001
> contract freeze**, not resolved by this phase. A future minimal
> mechanism (illustrative, not frozen): a repository-identity value
> minted once at `pcae init` time, stored **inside the same
> admin-owned, agent-unwritable trust-store directory** this
> architecture already defines (§12) — not inside the agent-writable
> repository tree — so the identity value inherits the same
> self-enrollment protection as the rest of the registry, without
> requiring a second, independent protection mechanism.

This reuses §12's boundary rather than inventing a new one, consistent
with item 89's preference against unnecessary recursive machinery.

**Severity (item 109):** repository-specific approval authority (149O.1A
§15's preference, reconfirmed unaffected through 149O.1B §10) cannot be
mechanically represented today without this prerequisite —
**BLOCKING for HATP-001 contract freeze**, but does **not** block this
architecture phase's own completion, since architecture may name a
prerequisite without implementing it (item 108's own instruction).

**Repository-move and clone semantics (items 48-49):** the deferred
mechanism above satisfies both: a moved-but-not-recloned checkout keeps
its identity (the value lives outside the moved tree, in the fixed
admin-owned location, keyed by whatever `pcae init` bound it to); an
ordinary `git clone` of the same repository does **not** automatically
inherit rollback-approval authority, because the new checkout has no
corresponding entry in the *original* checkout's admin-owned trust
store unless the admin principal explicitly re-enrolls it — authority
does not travel with the `.git` history.

## 15. Trust Capability Matrix (item 93, mandatory)

| Capability | Agent principal | Human approver | Bootstrap admin | Hardware signer |
|---|---|---|---|---|
| Read approval request | Yes | Yes | Yes | N/A |
| Write repository (governed) | Yes | Yes (same CLI) | Yes (same CLI) | N/A |
| Read trust registry (public fields) | Yes | Yes | Yes | N/A |
| Modify trust registry | **No — OS permission denied (§13)** | No (not the writer role) | Yes | N/A |
| Enroll key | **No** | No | Yes | N/A (device only proves possession, §11) |
| Grant rollback authority | **No** | No | Yes | N/A |
| Revoke / rotate | **No** | No | Yes | N/A |
| Invoke signing request | Yes (submit payload only) | Yes | N/A | N/A |
| Satisfy physical presence | **No — mechanically impossible (Root 1, unchanged)** | Yes | N/A | N/A (device enforces) |
| Extract private key | **No — non-exportable (Root 1, unchanged)** | No | No | Sole holder |
| Change trust-store ACL/owner | **No (§9, §13)** | No (not the ACL owner unless also admin) | Yes | N/A |
| Escalate to bootstrap-admin principal | **No — no sudo path permitted (§9)** | N/A | N/A | N/A |

The bottom-left column is the entire point of this architecture: every
cell the agent principal touches under Threat A resolves to **No**,
mechanically, at the OS-permission layer, not by policy convention.

## 16. Attack Analyses (items 33-42, mandatory mechanical proofs)

**Self-enrollment (item 33):** agent principal attempts
`open(trust_store_path, "a")` or equivalent write. Trust-store directory
is owned by the human/admin principal, mode excludes agent-principal
write (§12-§13) → **OS `EACCES`/`PermissionError`, denied before any
PCAE-layer code runs.**

**Verifier-key replacement (item 34):** agent principal attempts to
overwrite an existing entry's public key. Same write path, same OS
denial — no separate mechanism is needed; §12's boundary already covers
both attacks (mirroring 149O.1A §10's observation that self-enrollment
and key-replacement resolve to one open question).

**Registry deletion (item 35):** agent principal attempts `unlink()` on
the trust-store file. Deletion requires write permission on the
*containing directory* (POSIX semantics) or `Delete`/`Modify` rights
(Windows ACL semantics) — both excluded from the agent principal by
§12's directory-level ownership. If the store somehow becomes
unavailable or corrupt regardless (disk failure, admin error), HATP
validation **fails closed**: no proof can resolve `VALID` (149O.1A §21,
unchanged).

**Permission weakening (item 36):** agent principal attempts `chmod`/
`chown`/`setfacl` on the trust-store path. These operations require
either file ownership (agent principal has none, §12) or a privilege
the agent principal is explicitly denied (§9's sudo-escape prohibition
covers exactly this). Denied.

**Parent-directory replacement (item 37):** agent principal attempts to
`rename()`/delete-and-recreate the trust-store's *containing* directory
to substitute an agent-controlled replacement. Requires write permission
on the *grandparent* directory. The architecture requires the entire
protected path chain (grandparent through the trust-store file) to be
owned by the admin principal, not merely the leaf file — closing this
attack the same way §12 closes direct-file attacks. Recorded as a
concrete implementation requirement for the future deployment phase.

**Symlink substitution (item 38):** a future verifier resolving the
trust-store path must not follow an agent-plantable symlink at any
point in the path (e.g. by opening with `O_NOFOLLOW` / verifying the
resolved real path lies under the expected admin-owned root before
trusting it). Frozen as a **future implementation requirement**, not
implemented this phase.

**Environment-variable override (item 39):** per §3's finding that this
codebase already has an env-override habit (`CONFIG_PATH_ENV`,
`PCAE_NOTIFY_OUTPUT_DIR`), this architecture explicitly does **not**
extend that habit to the HATP trust-store location. The verifier's
trust-store path SHALL be a fixed, compiled-in default with no
production environment-variable override (item 39, normative).

**CLI override (item 40):** no production CLI flag (e.g. a hypothetical
`--hatp-trust-store`) may redirect the verifier to an alternate store.
Normal runtime carries no trust-root override at all (item 40's stated
preference, adopted).

**Config search-path (item 41):** the verifier SHALL use exactly one
canonical, protected source — never a search order that checks the
current working directory, the repository tree, or any agent-writable
location before the protected admin-owned path.

**Test injection (item 42):** unit tests may inject an in-memory or
temp-directory trust store via explicit dependency injection into the
verifier's constructor/factory — never through the production CLI,
environment variable, or config-search path above. This exception is
internal to the test harness only.

## 17. Bootstrap Admin Authentication (item 43)

At Class B, the OS's own authentication (successful login as the
admin-principal OS account) **is** the administrative boundary — no
additional PCAE-layer credential ("enter admin password again") is
required or specified, since a second in-application credential check
would just be another same-process artifact indistinguishable from what
Threat A already assumes an attacker can forge. Being the OS-
authenticated admin principal is sufficient; no self-declared CLI
username or flag substitutes for it (consistent with RAE-REQ-005's
already-frozen "self-declared string" rejection).

## 18. Approval Request Transport / Registry vs. Proof Distinction (items 24-27)

The agent principal constructs and submits an approval request; the
request is agent-controlled and untrusted by itself (item 25, `agent-
supplied approval request ≠ trusted approval` — normative). The
human/admin principal's approval-side process independently
reconstructs the canonical operation payload from trusted inputs before
signing (§19), so a tampered request either produces a visibly different
payload for the human to reject, or fails verification later if altered
post-signature (Binding-digest binding, 149O.1A §13, unchanged).

**Registry vs. proof (item 27, explicit distinction):**

```
Trust store (registry):
  protected — agent-unwritable (§12-§16)

Approval proof (HATP proof, 149O.1A §12):
  may be agent-readable and agent-copyable, because its authenticity is
  independently verifiable against the (agent-unwritable) trust store's
  public key material — copying a valid proof does not let the agent
  forge a *new* valid proof for a *different* operation (Binding-digest
  binding, unchanged from 149O.1A §13).
```

Filesystem protection alone is judged sufficient for the registry under
Threat A (item 29's question); no additional registry self-signature is
required for v1, since a self-authored signature over agent-unwritable
state adds no property the OS boundary doesn't already provide, and
would itself need a key whose protection reduces to the same OS
boundary (avoiding item 89's unnecessary-recursion trap).

**Root-termination statement (item 90-91, mandatory):**

> ROOT 2B TERMINATES AT: the OS-enforced security-principal/ACL boundary
> described in §12-§13 (directory and file ownership + permission bits,
> or platform-equivalent ACL, separating the admin principal from the
> agent principal). NOT AT: another self-authored repository file, a
> second signature the same untrusted process could also forge, or a
> policy convention.
>
> The autonomous agent lacks the OS authority required to alter the
> protected HATP bootstrap trust state and cannot escalate to the
> bootstrap principal under this deployment model (§9). **If this
> repository's actual deployment cannot support this statement
> concretely — i.e., if the two OS principals are not actually distinct,
> or the agent principal retains any escalation path — Root 2B remains
> NOT RESOLVED**, exactly as it is today (§21).

## 19. Bootstrap / Enrollment Workflow (items 30-32, 98)

```
1. admin principal authenticates to its own OS account (§17)
2. admin principal connects the hardware signing device
3. admin principal verifies device attestation against the fixed
   vendor root (149O.1A §8(a), unchanged)
4. admin principal obtains the device's public key / fingerprint
5. admin principal assigns a PCAE principal_id to that key
6. admin principal assigns repository-scoped rollback-approval
   authority (scope per §14's deferred repository-identity mechanism)
7. admin principal writes the new/updated entry into the trust store,
   located at the admin-owned protected path (§12)
```

**Initial enrollment human presence (item 31):** yes, required — the
device must be physically touched during step 3-4 to prove a genuine
device with a human present performed the enrollment, not merely that
the admin principal typed a public key value into the registry by hand.

**Enrollment authorization (item 32):** physical possession of a
genuine device (proven by step 3) is necessary but not sufficient —
it is the admin principal's own act of writing steps 5-6 that grants
PCAE authority; a genuine device with no admin-principal enrollment
entry has no rollback-approval authority at all.

## 20. Approval Workflow (items 66-71, 99)

```
1. agent principal submits an approval request (operation-identity
   fields per 149O.1A §13's payload table)
2. human/admin-principal approval process loads the request
3. that process independently reconstructs the canonical operation
   payload from trusted inputs (live Decision/Binding records, not
   solely the agent's request text) — item 69's requirement that the
   human-side process, not the agent, is the source of truth for what
   is displayed
4. human reviews the reconstructed payload (repository identity once
   §14's prerequisite exists, rollback family, job_id/original_commit_
   sha or per_id/ecp_id, approve/deny) — item 66's minimum display
   fields
5. human performs the physical presence gesture on the hardware device
6. device signs the exact payload displayed and reconstructed in step 3
   (item 70 — no blind signing of an agent-precomputed opaque hash)
7. proof is returned to agent-readable storage (§18)
```

**Blind-touch risk (items 67-69, disclosed residual risk):** this
architecture cannot prove the *display* itself is tamper-proof — HATP
v1 has no trusted-display hardware requirement, only a trusted
*reconstruction* requirement (step 3). The residual risk is an
approval-side host UI compromise (malware on the human/admin principal's
own machine altering what is rendered) — this is Threat B (host
compromise on the human side), explicitly out of scope for Threat A,
and is disclosed here rather than silently assumed away.

**No approval-time authority mutation (item 102):** the approval
workflow above never writes to the trust store; a signer must already
be enrolled (§19) before step 1 can produce a valid proof. Approving
does not implicitly enroll.

## 21. Revocation, Rotation, Recovery Workflows (items 53-57, 100-101)

- **Revocation:** admin principal marks an entry `status=revoked` in
  the trust store; the agent principal cannot undo this (§13's write
  denial applies symmetrically).
- **Rotation:** admin principal enrolls a replacement key using the
  same procedure as §19, marks the old entry superseded/revoked.
- **Hardware loss:** admin principal revokes the lost key's entry and
  enrolls a replacement device via §19; no implementation detail beyond
  that is required at architecture level.
- **Bootstrap-admin loss** (item 56, load-bearing): if the sole admin
  principal's account is unavailable (locked out, credentials lost),
  HATP approval capability **fails closed** — no rollback approval can
  be produced — until administrative recovery through whatever
  organization-level OS-account-recovery procedure this deployment's
  platform already provides (outside PCAE's own scope). **No emergency
  agent-side bypass** (a hypothetical `--force-enroll`) exists or is
  permitted (item 57, normative) — recovery requires the admin security
  context, never agent authority.

## 22. Hardware Device Access / IPC Boundary (items 23, 63-65)

The agent principal does not need, and does not receive, direct access
to the hardware signing device (item 23's preference, adopted): the
human/admin principal is the sole party that interacts with the device,
consistent with §7's topology (the admin principal already owns Root 1
interaction). If a future implementation introduces a local signer/
approval daemon reachable over a Unix socket or named pipe, this
architecture requires two structurally separate interfaces:

```
sign-request interface:   agent principal MAY connect and submit a
                           request (signing still requires the admin
                           principal's physical presence per Root 1 —
                           the request channel alone grants no
                           authority, item 64)
administrative interface: reachable only by the admin principal
                           (enroll/revoke/rotate/trust-store writes) —
                           never exposed to the agent principal's
                           socket permissions (item 65)
```

Not implemented this phase; recorded as a future implementation
requirement.

## 23. Runtime Self-Check / Fail-Closed Configuration (items 72-77)

Recorded as **future implementation requirements**, not built this
phase:

- Trust-store read failure or missing store → fail closed, no VALID
  proof possible (items 72-73, consistent with 149O.1A §21).
- A future verifier/bootstrap inspection SHOULD detect unexpectedly
  agent-writable trust-store permissions and treat that as a
  configuration error (`UNSAFE_CONFIGURATION`), distinct from ordinary
  `READY`/`UNAVAILABLE` states, and kept structurally separate from
  Permission Broker's own decision vocabulary (items 75-76, mirroring
  149O.1A §17's insistence on non-overlapping vocabularies).
- If the deployment self-check detects the agent principal and the
  trust-store owner are the *same* principal (i.e., §6's mandatory
  separation is not actually established), HATP approval
  creation/validation SHALL be disabled outright rather than silently
  degrading to procedural-only trust (item 77) — this is precisely
  this repository's own current state (§24) and is exactly why HATP
  remains unavailable here today.

## 24. Current Deployment Classification (items 78-79, unchanged verdict)

This architecture phase does not change this repository's actual,
current deployment. Given §6's mandatory-separation finding and 149O.1B
§4.1's confirmation that agent and human both run as `atilamadai` today:

> **HATP BOOTSTRAP ENVIRONMENT: NOT READY.** No distinct OS principal
> has been provisioned; the architecture in §7-§13 above describes the
> target state, not the current one. This phase performed no OS
> account creation, no ACL change, no filesystem ownership change (item
> 114, confirmed via `git status --short` — zero non-`docs/` changes).

**Deployment prerequisite (item 79, frozen statement):**

> Before HATP may be operationally enabled, the autonomous PCAE agent
> SHALL execute under a security principal that cannot modify HATP
> bootstrap trust state or impersonate the bootstrap-admin principal
> (§7, §9, §12-§13), AND a canonical repository-identity mechanism
> (§14) SHALL exist, before `HATP-001 v1.0` may be frozen.

## 25. Cross-Platform Reference Deployments (items 80-84, non-normative)

- **macOS (this development host's platform):** human/admin account
  (interactive login, existing developer account) + a restricted
  `pcae-agent` service/standard account for the agent process +
  protected user- or system-level directory for the trust store,
  group-readable by the agent account. Hardware signer used from the
  human/admin session.
- **Linux:** equivalent — a separate Unix user for the agent process,
  trust store under a directory owned by the admin user with group-read
  for the agent user's group, `0750`/`0640`-equivalent permissions.
- **Windows:** a separate Windows account/service identity for the
  agent process; trust store protected by an ACL granting the agent
  account's security identifier `Read` and the admin account's
  identifier `FullControl`, inheritance disabled at the trust-store
  directory.
- **Headless server (item 84):** if no human principal and no hardware
  signer are available at all, HATP is simply unavailable — no
  fallback, no degraded procedural mode (consistent with §23's
  fail-closed requirement).

None of these are frozen as *the* deployment; they illustrate that
§7-§13's capability-terms design (item 80: "agent cannot mutate trusted
bootstrap state," not "chmod 0444") has a viable instantiation on every
major platform this project might deploy to.

## 26. Explicit Rejections (items 85-88)

- **GitHub reclassified, unchanged from 149O.1B:** branch protection is
  not HATP bootstrap authority in this architecture (item 86) — 149O.1B
  §4.3's finding (admin-bypassable, sole collaborator, shared local
  credentials) stands; not revisited or reopened here.
- **SSH/git credentials are not HATP authority** (item 88): a
  principal's ability to `git push` says nothing about its HATP
  trust-store write authority; the two are deliberately un-linked.
- **External approval service (item 85):** not selected for v1, per
  149O.1B §6's Class B selection; noted only as a possible future
  alternative if Class B's OS-separation prerequisite (§6, §24) proves
  undeployable in some future environment.

## 27. Findings

- **BLOCKING (carried forward, unchanged)**: B-149O-1, B-149O-2,
  B-149O-3, B-149O-4 remain OPEN. No repair attempted this phase.
- **BLOCKING (new, this phase)**: no stable, protected repository
  identity exists in this codebase today (§14) — required before
  `HATP-001` may be frozen, since repository-specific authority scope
  (149O.1A §15) cannot otherwise be mechanically represented. A narrow
  future prerequisite phase is recommended (§29), reusing this
  architecture's own trust-store protection boundary rather than
  inventing a second one.
- **BLOCKING (carried forward, unresolved by design)**: the distinct OS
  principal this architecture requires (§6-§7) does **not** exist in
  this repository's actual, current deployment (§24) — establishing it
  is deployment work, explicitly out of scope for this architecture-only
  phase, and remains a prerequisite before HATP can be operationally
  enabled here.
- **NON-BLOCKING**: two-principal model (§5) selected over
  three-principal for HATP v1 under Threat A's own scope — revisit only
  if a future phase adopts Threat B (compromised human-side context) as
  in-scope.
- **NON-BLOCKING**: repository-scope binding via Binding-digest
  transitive scoping (149O.1A §18) remains adequate for the *proof
  payload*; only the *registry entry's* authority scope needs §14's new
  prerequisite — the two are distinct and this phase does not conflate
  them.
- **OBSERVATION**: this codebase already has an environment-variable
  config-path-override habit (`CONFIG_PATH_ENV`, `PCAE_NOTIFY_OUTPUT_
  DIR`, §3) that a future HATP trust-store lookup implementation must
  deliberately avoid extending to itself (§16, items 39-41).
- **OBSERVATION**: no existing OS-identity-aware code path exists
  anywhere in `src/pcae` to extend (§3) — the agent-principal/
  admin-principal separation is new infrastructure, not a hardening of
  something partially built.
- **DEFERRED**: exact trust-store file format/schema beyond the
  conceptual field list (§19's enrollment record — `principal_id`,
  `device_public_key`/attestation fingerprint, `approval_authority_
  scope`, `status`, `valid_from`, `revoked_at`, issuer/bootstrap
  metadata, per 149O.1A §14); algorithm selection (149O.1A §20,
  unchanged); symlink-resolution and parent-directory-chain enforcement
  implementation mechanics (§16, items 37-38) — architecture-level
  requirements only, not implemented.

## 28. Architecture Verdict

**HUMAN APPROVAL BOOTSTRAP AUTHORITY ARCHITECTURE DEFINED — REPOSITORY
IDENTITY PREREQUISITE REMAINS.**

The Class-B boundary mechanics are now fully specified in
capability-terms (§4-§13, §15-§23): a two-principal topology (§5),
mandatory OS-user separation with no privilege-escalation path (§6,
§9), an admin-owned/agent-unwritable trust-store location model (§12),
mechanical proofs that self-enrollment and verifier-key replacement
both terminate at an OS-enforced permission denial rather than another
self-authored file (§16, §18's root-termination statement), and
complete enrollment/approval/revocation/rotation workflows (§19-§21).
This satisfies the mandatory architecture property from the governing
prompt: the agent principal can read enough to validate, and cannot
write any of {enrollment, verifier-key mapping, authority assignment,
bootstrap trust configuration} under Threat A.

What remains, per §27's two carried-forward BLOCKING findings, is (a) a
narrow repository-identity prerequisite this architecture intentionally
did not invent ad hoc (§14), and (b) actually provisioning the distinct
OS principal in a real deployment (§24) — deployment work explicitly
out of this phase's scope. Per the governing prompt's own instruction
("If repository identity is the only remaining blocker: recommend the
narrowest canonical repository-identity architecture phase" — item
124), this phase recommends resolving (a) next (§29); (b) remains a
standing deployment prerequisite independent of any further
architecture phase.

## 29. Recommended Next Phase

**149O.1B.2 — Canonical Repository Identity Architecture.**

Scope: design (architecture only) a repository-identity mechanism
suitable as the HATP trust-store's `approval_authority_scope` anchor —
per §14's disposition, a value minted once (illustratively, at `pcae
init` time) and stored inside the same admin-owned, agent-unwritable
trust-store boundary this phase already defines (§12), satisfying item
106's four criteria (stable across moves, not silently shared by
unrelated clones, not caller-selectable at approval time, protected in
the authorization binding). Once that architecture exists, a subsequent
phase should re-attempt `HATP-001 v1.0` freeze using 149O.1A's
§12-§18/§22-§24 content, 149O.1B's §6-§9, and this phase's §4-§23 as its
combined normative basis — **only after** the OS-principal separation
this phase requires (§6-§7, §24) is also actually established and
independently verified as enforced in the target deployment, per the
governing prompt's own ordering (architecture before establishment
before contract freeze).

Do not implement HATP provider code, PIV/FIDO2 adapters, trust-store
code, or any OS account/ACL change before that architecture phase (and
this phase's own findings) are independently reviewed.

## 30. Fast Green

```
python -m pytest -m fast_green -n auto -q
4391 passed
```

Exact match to entering baseline (149O.1B's own exit baseline). No
`src/pcae/**`, no `docs/contracts/**` file was modified this phase —
confirmed via `git status --short` (only this document, task-lifecycle,
`PROJECT_STATUS.md`, and `CHANGELOG.md` changed).

## 31. Governance Validation (this phase)

```
pcae health             -> healthy
pcae check               -> passed
pcae status coherence    -> coherent
pcae doctor task-memory  -> clean
pcae push check           -> clean, nothing_to_push (pre-finalization)
pcae runtime inspect      -> Observed / observe / unavailable (unchanged)
pcae notify status        -> telegram configured/enabled
pcae phase-report reconcile --phase-id 149O.1B -> reconciled, mutation none
```

## 32. Production / OS Boundary

```
git status --short           -> only docs/PHASE_149O_1B_1_..., PROJECT_
                                 STATUS.md, CHANGELOG.md, tasks/active/**,
                                 tasks/done/**, .pcae/phase-completion-*
                                 changed this phase
git diff --name-only <start>..HEAD -- src/pcae/           -> (empty)
git diff --name-only <start>..HEAD -- docs/contracts/     -> (empty)
```

No OS user was created. No filesystem ownership, ACL, or sudoers
configuration was changed. No daemon was installed. No hardware signing
was implemented. No HATP provider code was written. No
`rollback_approval_evidence.py` change was made. No AG3/AG5 wiring
occurred. No Permission Broker change was made. No RAE-001 change was
made.

## 33. Runtime Boundary

`pcae runtime inspect` before and during this phase: Observed / observe
/ unavailable — unchanged.

## 34. Chapter 149 Status

Outstanding, unchanged in scope, sharpened this phase:

- Canonical repository-identity architecture (new, this phase's own
  recommended next step)
- HATP Root 2B establishment (distinct OS principal — deployment work,
  still not performed)
- HATP contract freeze (blocked on both of the above)
- HATP contract independent verification
- HATP implementation planning
- HATP implementation
- HATP independent verification
- RAE HATP integration
- RAE re-verification
- AG3/AG5 integration planning
- AG3/AG5 integration
- integration verification
- TK1/TK2/TK3 re-affirmation

## 35. Confirmations (governing-prompt required final-report list)

- HATP-001 remains unfrozen during 149O.1B.1; architecture does not, by
  itself, justify the freeze (repository-identity prerequisite remains,
  §14/§27/§28).
- B-149O-1 through B-149O-4 remain OPEN.
- No HATP implementation was created.
- No OS account or security configuration was changed.
- No production source (`src/pcae/**`) was modified.
- No RAE integration was implemented.
- No AG3 Permission Broker integration was implemented.
- No AG5 Permission Broker integration was implemented.
- No rollback execution behavior changed.
- RAE-001 v1.0 remains unchanged. RWMPC-001 v1.0 remains unchanged.
  PBPC-001 v1.2 remains unchanged. PBPA-001 v1.0 remains unchanged.
  CHGR-001 remains unchanged.
- IWC confirmation remains distinct from approval. AESIC/AEM remain
  disclosure-only.
- No POL-001..012 meaning was changed. No POL-013+ was added.
- TK1/TK2/TK3 remain deferred.
- No Runtime Enforcement behavior changed. No Prompt Generation, Prompt
  Dispatch, or agent invocation capability was implemented. Runtime
  remains Observed, maximum capability remains observe, and execution
  availability remains unavailable (confirmed via `pcae runtime inspect`
  before and during this phase).
