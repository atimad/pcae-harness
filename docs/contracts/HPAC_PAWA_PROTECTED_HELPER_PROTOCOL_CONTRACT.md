# HPAC-PAWA-HELPER-001 v3.0 — HPAC-PAWA Protected One-Shot Privileged Helper Protocol Contract

## Contract identity and status

**Contract:** HPAC-PAWA-HELPER-001
**Version:** 3.0
**Status:** REPAIRED / FROZEN — PENDING INDEPENDENT RE-VERIFICATION
**Evolved to v3.0 by:** Phase
149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1
(alias **N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-CONTRACT-REPAIR**) — Writer-
Authority Repair: Helper-Process-Isolated Mutation Facades (new section 30B).
**v2.0 -> v3.0 is a MAJOR evolution**, fired explicitly by
HPAC-PAWA-HELPER-REQ-130 ("introducing any new internal writer-authority
derivation / mint mechanism, even if narrowly scoped, closed-vocabulary-bound,
and never exported, is a MAJOR change requiring explicit human authorization
and independent verification") — a literal trigger the v2.0 freeze itself
pre-declared for exactly this situation, not a re-derived judgment call. The
externally-visible wire vocabulary (§11-§17), the three operation ids, the
five certification roles, the three admin-mutation subtypes, and every
`pawa_failure_code` mapping are **UNCHANGED**; only the internal
mint-pathway architecture and the store-recognition mechanism are replaced.
See §30B.9 for the full versioning rationale (why REQ-130 controls the
classification even though the external contract surface alone would have
been MINOR-shaped).

v2.0's own §30A specification (Model D: `_mint_helper_scoped_writer_capability`
as a sibling primitive inside the shared `hpac_foundation` module) is
**preserved immutably below as history** and is **SUPERSEDED, NOT DELETED**:
a fresh independent verification
(`docs/PHASE_N16_5_F_5_TB_HELPER_WRITER_AUTHORITY_CONTRACT_IV.md`, alias
**N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-CONTRACT-IV**) found it
**NOT VERIFIED / BLOCKED** on two independently source-confirmed defects (see
§30B.1 for the verbatim reconstruction). Model D's specification MUST NOT be
implemented; the repaired Model E hybrid of §30B is the sole forward-
authorized pathway for a future implementation phase.
**Frozen by:** Phase
149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1
(alias **N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-CONTRACT-ARCH**) — Helper-Scoped
Writer Authority Architecture and Contract Evolution for Protected Canonical
Mutations. **v1.0 -> v2.0 is a MAJOR evolution** (see new section 30A): it
introduces a second, narrowly-scoped internal writer-capability mint pathway
reachable only from the helper process. Not covered by any v1.0 section-30
MINOR bullet; classified MAJOR by the same conservative discipline that
governed the HPAC-PAWA-001 v1.4 -> v2.0 jump, notwithstanding that it fires no
v1.0 section-30 MAJOR trigger literally (section 30A closes this
classification gap explicitly for future evolutions).

The v1.0 freeze record and its findings remain **immutable**. v1.0 was FROZEN
by Phase
149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1
(alias **N16-5-F-5-TB-CONTRACT**) — N-16-5 Privileged Production Authority
Trust-Boundary Contract Evolution.
**Companion of:** HPAC-PAWA-001 **v2.0** (`HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`)
— HPAC-PAWA-001 v2.0 §32 / §33 / §36–§38 / §42B / §42D / §49B / §33B now require
that every privileged production operation be performed by a distinct
out-of-process protected helper; HPAC-PAWA-HELPER-001 supplies the helper
provenance, launch, private-channel, peer-authentication, request/response,
operation-vocabulary, freshness, replay, one-shot, crash / uncertainty, and
audit-ordering semantics that were previously unspecified.
**Parent semantics:** HPAC-001 v2.1 (`HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md`);
RHAMP-001 v1.0
(`REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md`).
**Pattern precedent (reused by reference, not re-homed):** HPAC-PPA-001 v1.0
(`HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md`) §1, §2, §6, §7 — the
out-of-band immutable helper bytes + `helper_sha256` integrity pin +
same-file-object validate-and-exec + private one-shot parent/child channel +
CSPRNG ≥ 256-bit nonce + exact request/response binding + fail-closed
crash / timeout / nonce / binding semantics. HPAC-PPA-001 remains **v1.0,
byte-unchanged**; HPAC-PAWA-HELPER-001 does not amend it, re-home its
presentation semantics, or widen its consumer inventory.
**Architecture baseline:** Phase
149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1
(alias **N16-5-F-5-TB-ARCH**), `docs/PHASE_N16_5_F_5_TB_ARCH.md` §7 (selected
architecture 6C — short-lived one-shot privileged process, generalizing the
HPAC-PPA-001 verified-helper pattern), §9–§24, §28.

**Scope:** the narrow, versioned, local, one-shot **`HPAC-PAWA-HELPER/1.0`**
protocol by which a deployment-owner standalone launcher requests exactly one
bounded privileged operation from an integrity-verified protected helper
executable, the helper authenticates the request and its peer, performs exactly
one bounded operation in its own OS process, writes durable audit evidence under
`<HPAC_PROTECTED_ROOT>`, and returns typed evidence only. This contract adds no
UI, no runtime, no adapter, no Gate integration, no execution authority, no new
trust root, and no new `PawaOperation`; it implements no helper, launcher, IPC
endpoint, or caller.

Historical HPAC-PAWA-001 v1.0 / v1.1 / v1.2 / v1.3 / v1.4 freeze records and
their independent verifications remain **immutable**. The predecessor findings
preserved exactly: N16-5-F-5-B2 NOT VERIFIED / BLOCKED; N16-5-F-5-B2R-IV NOT
VERIFIED / BLOCKED; N16-5-F-5-B2R2-IMPL COMPLETE — BLOCKED; N16-5-F-5-TB-ARCH
COMPLETE.

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved.

---

## 0. Normative language

- **HPAC-PAWA-HELPER-REQ-001.** `SHALL`, `SHALL NOT`, `MUST`, `MUST NOT`,
  `SHOULD`, `SHOULD NOT`, `MAY` are normative (RFC 2119, as used throughout this
  repository's bound contracts). Every normative sentence carries a unique
  requirement ID `HPAC-PAWA-HELPER-REQ-###`, sequential from 001, no gaps, no
  duplicates. `HPAC-PAWA-HELPER-REQ-*` is an independent numbering namespace
  (HPSE-001 / RHAMP-001 / HPAC-PPA-001 precedent). Security invariants carry a
  separate `PAWAH-INV-#` label (§29).
- **HPAC-PAWA-HELPER-REQ-002.** Unknown, missing, conflicting, malformed,
  unverifiable, out-of-schema, or unrecognized-version facts **fail closed**: no
  operation is admitted, no mutation is performed, no read view is returned, no
  ceremony is entered, and a terminal failure code (§18 of HPAC-PAWA-001 §56 —
  the existing 21-code `pawa_failure_code` vocabulary) is recorded where a
  lifecycle event can be persisted. The absence of a denial is never authority.
  An ambiguity at any authority boundary fails closed.
- **HPAC-PAWA-HELPER-REQ-003.** Conformance with this protocol grants **no** PB
  permission, policy exception, Runtime Enforcement result, runtime capability,
  `DispatchEnvelope`, adapter admission, dispatch authority, Gate result, human
  APPROVE / REJECT, real assurance, or execution authority. It authorizes only
  the bounded administrative / certification-lifecycle / enumerated-read /
  ceremony-entry operations of §13.
- **HPAC-PAWA-HELPER-REQ-004.** Every authority decision maps
  **deterministically** onto an existing `pawa_failure_code` (HPAC-PAWA-001 §56,
  21 closed values) as §18 specifies. This contract introduces **no** new
  `pawa_failure_code` and **no** new RHAMP-001 `terminal_reason_code`;
  RHAMP-001 v1.0 §49 is byte-unchanged. If a future helper-protocol rejection
  genuinely has no valid mapping, that is a
  **BLOCKED-on-contract-compatibility** condition for the phase that discovers
  it — it does not silently add a code.

---

## 1. Scope

- **HPAC-PAWA-HELPER-REQ-005.** HPAC-PAWA-HELPER-001 governs **only**: (a) the
  provenance and integrity recognition of the protected helper executable;
  (b) the standalone launcher's obligations; (c) the private one-shot channel;
  (d) OS peer authentication of the launcher by the helper; (e) the closed,
  versioned, typed `HPAC-PAWA-HELPER/1.0` request and response schemas; (f) the
  closed operation vocabulary and its per-operation typed parameter structs;
  (g) freshness, replay, one-shot, and single-use semantics; (h) the explicit
  state-transition model and crash / response-loss / uncertainty behaviour;
  (i) audit-evidence ordering and content; (j) the deterministic-vs-real wall,
  mechanism neutrality, and cross-platform peer-credential profiles.
- **HPAC-PAWA-HELPER-REQ-006.** The **authority decision** — "is this a trusted
  production consumer?" — is owned by **HPAC-PAWA-001 v2.0 §32 / §33 / §33B**.
  HPAC-PAWA-HELPER-001 supplies the mechanism the answer is computed over; it
  does not itself widen, weaken, or redefine the recognition predicate. Where
  the two contracts appear to conflict, **HPAC-PAWA-001 governs** and the
  implementing phase STOPS (BLOCKED).
- **HPAC-PAWA-HELPER-REQ-007.** This contract is **contract text only**. It
  creates no helper executable, no launcher, no channel, no protected-root
  state, no audit record, no OS principal, and executes nothing. Every module,
  function, and symbol it names is a normative reference, not an import.

## 2. Non-goals

- **HPAC-PAWA-HELPER-REQ-008.** HPAC-PAWA-HELPER-001 does **not**: define a
  persistent privileged process, daemon, or system service (architecture
  candidates 6A / 6B were considered and rejected — `TB-ARCH` §6); define a
  network, socket-over-TCP, remote, or cloud transport; define a new trust root
  (§3); define a new `PawaOperation`, writer role, protected-root schema, or
  protected-root artifact beyond the one integrity-pinned helper-registration
  record of §6; define a bearer secret, signing key, MAC key, or pinned
  verification key as an authority input (§17 of `TB-ARCH`; PAWAH-INV-9);
  define human authentication, FIDO2 semantics, protected-presentation
  rendering, the human APPROVE / REJECT election, Gate 5, or counter-state
  verification logic (those stay with HPAC-001 / RHAMP-001 / HPAC-PPA-001 /
  HPAC-PAWA-001 §42B); enable any runtime capability, adapter, dispatch, N-16-6,
  N-16-7, or external effect.
- **HPAC-PAWA-HELPER-REQ-009.** HPAC-PAWA-HELPER-001 does not claim resistance
  to: a fully compromised OS root / admin account; a compromised OS kernel; a
  compromised registered helper binary or its admin-owned config after an
  authorized protected-root mutation; or a deployment owner restoring an entire
  byte-identical trusted-machine snapshot. These match HPAC-PAWA-001 §8(c) /
  §60 / PAWA-INV-6 and HBDC-001 §18, inherited unchanged (§26.2).

## 3. Trust root — single, unchanged

- **HPAC-PAWA-HELPER-REQ-010.** The **sole** trust root is the one HPAC-PAWA-001
  §4 / HPAC-PAWA-REQ-010 / HPAC-PAWA-REQ-300 already froze: **OS filesystem
  write authority over the out-of-band-provisioned `<HPAC_PROTECTED_ROOT>`**,
  owned by the deployment owner, provably not writable by the configured agent
  principal, `{device, inode}`-bound, `O_NOFOLLOW` on every component. This
  contract introduces **no** second bootstrap authority, **no** independent
  factory root, **no** global seal, secret, trust token, privileged file, magic
  environment variable, or persistent authority record.
- **HPAC-PAWA-HELPER-REQ-011.** The helper executable's registration record
  (§6) — `helper_sha256` + owner / mode / type / generation binding — is an
  **integrity-pinned artifact of the existing kind** (the HPAC-PPA-REQ-010 /
  HPAC-PPA-REQ-013 pattern for the presentation helper). Registration is **not**
  a new trust root: the helper's registration is authored only by the already
  enumerated deployment-owner PAWA metadata authority, under
  `<HPAC_PROTECTED_ROOT>`, whose write authority is the one trust root above.
- **HPAC-PAWA-HELPER-REQ-012.** The following are **distinct** evidence /
  predicates and SHALL NOT be conflated, substituted, or treated as
  interchangeable:

  ```
  trust root                 (OS filesystem write authority over <HPAC_PROTECTED_ROOT>)
  != installed helper metadata      (the §6 registration record)
  != helper hash                    (helper_sha256 of the opened byte stream)
  != executable path                (the derived content-addressed path)
  != launcher identity              (which standalone script exec'd the helper)
  != peer credential                (the OS (uid, gid) of the channel peer)
  != operation authorization        (the request is a valid member of §13 bound to a valid session)
  ```

  A trusted production consumer is the **conjunction** of §10 (HPAC-PAWA-001
  v2.0 §32 / §33B): (1) the process was `exec`'d from the integrity-verified
  out-of-band helper executable; (2) its channel peer presents the
  deployment-owner OS principal credential; (3) HPAC-PAWA-001 §33 steps 1–8 pass
  inside the helper; (4) the request is a well-formed member of §13 bound to a
  valid, current certification / administrative session. **No single conjunct
  is sufficient** (PAWAH-INV-2).

## 4. Actors and principals

- **HPAC-PAWA-HELPER-REQ-013.** The closed actor set:

  | Actor | OS identity | Role — permitted | Role — prohibited |
  |---|---|---|---|
  | **Deployment owner / admin** | a distinct OS account that owns `<HPAC_PROTECTED_ROOT>` and its subtree, holds real filesystem write authority the configured agent principal provably lacks | provisions the protected root; installs and registers helper bytes out of band; runs the standalone launcher | is **not** the human approver, the HPAC proof verifier, the writer authority object, the PB, the runtime, or a generic privileged shell |
  | **Standalone launcher** | runs as the deployment owner; a `scripts/…` entry point importing **no** agent-reachable code | builds the canonical typed request; resolves + integrity-verifies the helper; creates the private one-shot channel; `exec`s the helper; sends exactly one request; receives typed evidence | SHALL NOT perform the privileged mutation / read / ceremony entry itself; SHALL NOT hold or receive an `HPACWriterCapability` / `HPACStoreAuthority` / handle; SHALL NOT accept a caller-provided `approved=True`, response bytes, helper process, channel, or attestation; possession of / access to the launcher is **not** authority |
  | **Privileged one-shot helper** | `exec`'d child of the launcher; deployment-owner UID; its own OS process and interpreter, loading **only** its own minimal privileged code — no agent / plugin / repository import | verifies its peer credential; runs HPAC-PAWA-001 §33 steps 1–8; validates the typed request; performs **exactly one** bounded §13 operation; writes audit evidence; emits typed evidence; **exits** | SHALL NOT import the in-process PAWA factory module, `pcae.core.hpac_protected_admin_writer`, or any agent-reachable code (§8 of `TB-ARCH` T3); SHALL NOT return an authority object; SHALL NOT perform more than one operation per `exec`; SHALL NOT self-modify its registration |
  | **Configured agent principal** | the OS identity the autonomous PCAE agent / runtime is configured to execute as (HPAC-PAWA-001 §2 / §9 / `HPAC-PAWA-AGENT-EXCLUSION/1.0`) | ordinary agent work in the main PCAE interpreter | SHALL NOT hold the channel fd; SHALL NOT import the helper or the writer module; SHALL NOT be the launcher's or helper's OS principal (two-principal topology, §61 of HPAC-PAWA-001); on a single-account host the topology is **absent** → REAL issuance **ineligible**, fail closed (PAWA-INV-7) |
  | **Human approver / authenticated human** | a real person at the protected presentation / the genuine authenticator | produces the human APPROVE / REJECT and FIDO2 UP / UV **only** through the HPAC-PPA-001 ceremony and the registered real authentication mechanism | is **never** the launcher's or helper's OS principal; an OS peer credential is **never** human identity or human approval (§10.4, PAWAH-INV-8) |

- **HPAC-PAWA-HELPER-REQ-014.** **Installer ≠ launcher ≠ helper ≠ evidence
  writer ≠ human approver ≠ authenticated human ≠ PB ≠ runtime** (§16 of
  `TB-ARCH`; HPAC-PPA-INV-2 pattern). Where **one OS principal** performs
  multiple deployment roles (e.g. the deployment owner is also the installer
  and runs the launcher), the **semantic authority of each role stays
  distinct**: authority SHALL NOT be inferred merely because the same
  administrator owns two files or runs two scripts. Each role's authority is
  established by its own predicate (§6 for the helper, §8 for the launcher, §10
  for the peer, §13 for the operation).

## 5. Platform-profile abstraction

- **HPAC-PAWA-HELPER-REQ-015.** The contract fixes **one logical trust model**
  with **platform-specific backends** (HPAC-PAWA-001 §63 discipline: "one
  common logical protocol + trust contract … preferred over two authority
  models"). The **normative properties are frozen**; the concrete mechanism
  that realizes each property on a given OS is an **implementation profile**
  and MAY differ between macOS and Linux without a contract change, provided
  every frozen property below holds.
- **HPAC-PAWA-HELPER-REQ-016.** Frozen logical properties, portable across the
  macOS development host and the Linux (Dell Ubuntu) deployment target:

  | Property | Portable requirement | Permitted platform profiles (informative) |
  |---|---|---|
  | Filesystem-permission trust root | `O_NOFOLLOW` on every component; `{device, inode}` binding; deployment-owner ownership; agent-unwritable | POSIX `open(2)` `O_NOFOLLOW`; `fstat` device/inode |
  | Helper-executable integrity | open-with-no-symlink; type / link-count / owner / mode / ACL validation; SHA-256 of the complete opened byte stream == registered `helper_sha256`; **same opened file object** used to `exec` (no pathname re-open gap) | `O_NOFOLLOW` open + `fexecve(2)` (Linux, macOS ≥ 10.15) or a platform-equivalent identity-preserving exec of the validated descriptor; if a platform cannot exec the verified object without a substitution window, the implementation **STOPS BLOCKED** (HPAC-PPA-REQ-030) |
  | One-shot `exec` of the verified executable | no shell, no `PATH` lookup, no caller-argv extension, no `cwd` lookup, no network, no environment-selected helper, no generic subprocess API | direct `posix_spawn` / `fork`+`fexecve` of the validated descriptor |
  | Private one-shot channel | created by the launcher; endpoint not inherited by, reachable by, or shared with any agent-principal process; carries canonical request/response bytes only | `socketpair(AF_UNIX, SOCK_STREAM)` inherited only across the `exec`; or an `AF_UNIX` socket at a `0700` deployment-owner-owned directory |
  | Peer-credential authentication | the helper obtains the authenticated OS `(uid, gid[, pid])` of the channel peer from the **kernel**, not from any peer-supplied field; unforgeable by an ordinary configured-agent process under the §26 threat model; bound to the actual channel; evaluated **before** operation admission | Linux `SO_PEERCRED` / `getsockopt(SO_PEERCRED)`; macOS `LOCAL_PEERCRED` / `getpeereid(3)`. These are **not** assumed byte-for-byte equivalent; each profile yields at least the peer `(uid, gid)` |
  | Closed minimal child environment | a closed allowlist required by the fixed local platform; **no** authority selector, automatic response, verifier kind, helper path, writer role, root override, operation selector, or caller secret in env or argv; unknown env fails closed | HPAC-PPA-REQ-032 pattern |

- **HPAC-PAWA-HELPER-REQ-017.** A new platform profile (a third OS, or a
  changed peer-credential syscall on an existing OS) is a **MINOR** evolution
  **iff** it realizes every §16 frozen property with no re-meaning (§30); a
  profile that cannot (e.g. a platform with no kernel-authenticated peer
  credential, or no substitution-free exec of a verified descriptor) is
  **BLOCKED**, not a downgrade.

## 6. Helper installation, provisioning, and integrity recognition

- **HPAC-PAWA-HELPER-REQ-018.** The helper-executable installation model is
  **exactly** the HPAC-PPA-REQ-004 model: **out-of-band immutable helper bytes
  plus protected-root metadata registration**. The deployment owner installs
  the fixed PCAE-owned helper bytes under `<HPAC_PROTECTED_ROOT>` out of band.
  PCAE / PAWA / this protocol does **not** copy, replace, `chmod`, `chown`,
  download, package, or execute bytes as part of any registration mutation.
- **HPAC-PAWA-HELPER-REQ-019.** Helper bytes are installed **create-only** at a
  content-addressed path
  `<HPAC_PROTECTED_ROOT>/pawa-helper/installations/<helper_sha256>/hpac-pawa-privileged-helper`,
  where `<helper_sha256>` is exactly 64 lowercase hexadecimal characters and
  equals SHA-256 of the complete executable byte stream. The path is derived,
  not caller-selectable (HPAC-PPA-REQ-010 / REQ-011 pattern), and MUST remain
  beneath the same live protected-root `{device, inode}` identity.
- **HPAC-PAWA-HELPER-REQ-020.** The helper object and every existing ancestor
  from the protected root to it MUST be non-symlink; the helper MUST be a
  regular file with exactly one hard link, owned by the deployment owner, mode
  `0755` (executable), not writable by group, other, the configured agent
  principal, or an ACL granting that principal write (HPAC-PPA-REQ-012). These
  are authoritative defense-in-depth predicates **in addition to, never
  substitutes for**, the digest check (PAWAH-INV-3).
- **HPAC-PAWA-HELPER-REQ-021.** The helper-registration record is an immutable
  create-only record at
  `<HPAC_PROTECTED_ROOT>/pawa-helper/installations/<generation>/helper-installation.json`,
  schema `HPAC-PAWA-HELPER-INSTALLATION/1.0`, canonicalized under HPAC-REQ-089,
  with exactly these closed fields:

  | Field | Exact meaning |
  |---|---|
  | `helper_installation_schema_version` | const `HPAC-PAWA-HELPER-INSTALLATION/1.0` |
  | `installation_id` | `^hpahi-[0-9a-f]{32}$`; stable for one protected-root installation lineage; **equal to** the PAWA `installation_id` of the same root (bound, not independent) |
  | `helper_implementation_id` | const `hpac-pawa-privileged-helper` |
  | `helper_implementation_version` | non-empty version identifier bound to the installed PCAE helper build |
  | `helper_path` | exact absolute normalized path derived by HPAC-PAWA-HELPER-REQ-019 |
  | `helper_sha256` | SHA-256 of the complete helper bytes |
  | `protocol_version` | const `HPAC-PAWA-HELPER/1.0` |
  | `supported_operations` | the exact closed §13 operation-id set the installed helper build implements — a subset of, and validated against, §13; an operation not listed here fails closed on that helper generation |
  | `generation` | positive integer; initial `1`, then previous current + 1 |
  | `lifecycle_action` | closed enum `install`, `rotate`, `revoke` |
  | `status` | `active` for install / rotate; `revoked` for revoke |
  | `installed_at` | trusted-clock UTC RFC 3339 timestamp for this generation action |
  | `supersedes` | null at generation 1; otherwise exact closed `{generation, helper_installation_digest}` of the prior current generation |
  | `helper_installation_digest` | self-excluding SHA-256 of the canonical record |

- **HPAC-PAWA-HELPER-REQ-022.** The authoritative currentness record is
  `<HPAC_PROTECTED_ROOT>/pawa-helper/current-generation.json`, schema
  `HPAC-PAWA-HELPER-CURRENT-GENERATION/1.0`, atomically replaced and read-back
  verified under the same bounded PAWA transaction (HPAC-PPA-REQ-017 pattern),
  with closed fields `current_generation_schema_version` (const),
  `installation_id`, `helper_implementation_id`, `current_generation`,
  `helper_installation_digest`, `helper_sha256`, `protocol_version`, `status`
  (`active` | `revoked`), `updated_at`, and `anchor_digest` (self-excluding
  SHA-256). A generation is **current** only when this anchor and the immutable
  generation record agree on every shared field; any mismatch, missing record,
  stale generation, noncanonical bytes, or digest failure rejects
  (HPAC-PPA-REQ-019).
- **HPAC-PAWA-HELPER-REQ-023.** The helper-registration and
  current-generation records require deployment-owner PAWA writer provenance
  (`HPAC-WRITER-PROVENANCE/1.0`, sufficient without a schema change —
  HPAC-PPA-REQ-063). A caller-written structurally valid record is **not**
  authority. The PAWA mutation family that authors these records is specified in
  HPAC-PAWA-001 v2.0 §42 (`configure_privileged_helper`, role
  `privileged_helper_installer` — see HPAC-PAWA-001 v2.0); this protocol
  contract does not itself define the PAWA writer role.
- **HPAC-PAWA-HELPER-REQ-024.** **Bootstrap is non-circular** (HPAC-PPA-REQ-021
  / PAWA-INV-4 pattern): the deployment owner installs helper bytes out of band,
  then obtains one PAWA capability and registers generation 1. No privileged
  helper operation, ceremony, human authentication, or prior PCAE principal is
  required to register the helper. The already-recognized deployment-owner PAWA
  anchor is the trust anchor. First-caller-wins, self-install, repository
  install, environment install, and deterministic-fixture promotion are
  prohibited.
- **HPAC-PAWA-HELPER-REQ-025.** **Rotation** is monotonic `G → G+1`: new
  immutable helper bytes installed at their derived content-addressed path;
  a new generation record `lifecycle_action == rotate`, `status == active`,
  exact `supersedes`; the current-generation anchor switches to `G+1` in the
  same bounded transaction; `G` becomes stale by derivation, not rewritten
  (HPAC-PPA-REQ-025 / REQ-059). Replacing helper bytes at an existing
  content-addressed path causes the hash check to fail — it is not rotation.
- **HPAC-PAWA-HELPER-REQ-026.** **Revocation** creates `G+1` with
  `lifecycle_action == revoke`, `status == revoked`, exact `supersedes`, and an
  atomically-written revoked anchor. While revoked, **no** helper launch
  succeeds and **no** outstanding response from any generation in that lineage
  is accepted (HPAC-PPA-REQ-026 / REQ-060). There is no automatic fallback;
  recovery is explicit deployment-owner reprovisioning under a new
  `installation_id` and generation 1 (HPAC-PPA-REQ-027).
- **HPAC-PAWA-HELPER-REQ-027.** **Rollback prevention:** restoring an older
  generation record or an older helper binary **alone** fails current-anchor
  comparison (HPAC-PPA-REQ-028). Restoring a byte-identical whole
  protected-root snapshot is bounded by the existing HPAC / PAWA
  `{device, inode}` and deployment-owner TCB; this contract does **not** claim
  resistance to a deployment owner restoring the entire trusted machine state
  (§26.2).
- **HPAC-PAWA-HELPER-REQ-028.** **Pre-launch integrity recognition (every
  launch, no exception):** the launcher SHALL, before every `exec`, resolve the
  current-generation anchor, the current generation record, and their PAWA
  writer provenance; open the fixed helper with **no symlink traversal**;
  validate type / link-count / owner / mode / ACL; hash the **opened** bytes;
  and require exact agreement of `helper_sha256`, `protocol_version`,
  `installation_id`, `generation`, and `status == active` across the opened
  bytes, the generation record, and the anchor. Any mismatch, missing record,
  stale generation, noncanonical bytes, digest failure, symlink, wrong owner /
  mode / type, or revoked status → **fail closed**, no `exec`, `pawa_failure_code`
  per §18.
- **HPAC-PAWA-HELPER-REQ-029.** **Same-file-object / anti-TOCTOU (frozen
  property, not a mechanism):** the helper that is executed SHALL be the **same
  file object** whose integrity / ownership / type properties the launcher
  verified — validation and execution address one opened descriptor (or a
  platform-equivalent identity-preserving handle), and a **pathname re-open
  after validation is forbidden** (HPAC-PPA-REQ-030). If the platform cannot
  execute the verified object without a substitution window, the implementation
  **STOPS BLOCKED**. The contract freezes this **property**; the concrete
  syscall (`fexecve`, `execveat` with `AT_EMPTY_PATH`, or a documented
  platform-equivalent) is an implementation profile (§5).
- **HPAC-PAWA-HELPER-REQ-030.** A copied or lookalike executable resembling the
  registered helper is **a different file** — a different `helper_sha256`, or,
  if the bytes match exactly, a file object not opened from beneath the current
  live protected-root `{device, inode}` — and fails §28 (`TB-ARCH` T5).

## 7. The helper's in-process recognition (HPAC-PAWA-001 §33 1–8)

- **HPAC-PAWA-HELPER-REQ-031.** After it is `exec`'d and before it admits any
  operation, the helper SHALL run, **in its own interpreter**, HPAC-PAWA-001
  §33 **steps 1–8** verbatim as required conjuncts: canonical
  `<HPAC_PROTECTED_ROOT>` resolution and symlink rejection (§25);
  `HPAC-PAWA-AGENT-EXCLUSION/1.0` load + live account resolution +
  `live uid == provisioned_uid` + live group enumeration (§32A) yielding
  `ConfiguredAgentAuthorityIdentity`; the configured-agent exclusion negative
  boundary (`_effective_write_access` / `_ancestor_chain_safe` **against the
  configured-agent identity**, not `os.geteuid()` — finding F-1); `{device,
  inode}` root-identity binding; descriptor trust (closed schema / digest /
  `protected_root_identity` / ownership / mode / `provenance_ref` /
  `state == ACTIVE`); `current-generation.json` incl. `agent_exclusion_digest`
  with `descriptor.generation == current_generation`; the not-configured-agent
  current-context check (§31); the `O_EXCL | O_NOFOLLOW` positive write probe
  under `.authority/` (§28). Removing any one re-opens a named §20 threat; no
  single conjunct is sufficient (HPAC-PAWA-001 PAWA-INV-3).
- **HPAC-PAWA-HELPER-REQ-032.** **Configured-agent identity vs ambient root
  (finding F-1 / F-5-B1, preserved and executed inside the helper).** The
  helper process principal is the deployment owner and MAY run with elevated
  (`sudo` / root EUID) privilege. The **negative boundary** in step 3 / step 7
  SHALL still be evaluated against the **configured PCAE agent principal**
  resolved live from `HPAC-PAWA-AGENT-EXCLUSION/1.0` — **never** against
  `os.geteuid()`, an ambient root EUID, a `SUDO_*` variable, or a caller
  parameter. `euid == 0` inside the helper mints **nothing** (HPAC-PAWA-001 §34,
  PAWA-INV-1). The helper SHALL distinguish `helper process principal` from
  `configured PCAE agent principal` and SHALL NOT treat ambient EUID root as
  proof that the configured agent cannot write protected state — that fact comes
  only from the live `_effective_write_access` / `_ancestor_chain_safe`
  evaluation against the resolved agent identity.
- **HPAC-PAWA-HELPER-REQ-033.** The helper SHALL NOT `import` the in-process
  PAWA factory module (`pcae.core.hpac_protected_admin_writer`), the
  `production_writer` / `certification_writer` /
  `recognized_certification_read_authority` symbols, or any agent-reachable
  module. The step 1–8 recognition **logic** is realized by helper-local code
  (it MAY share a small non-agent-reachable OS-primitives library with the
  installer scripts) that loads no attacker-controllable code (`TB-ARCH` T3).

## 8. Launcher requirements

- **HPAC-PAWA-HELPER-REQ-034.** The launcher SHALL:
  1. build the **canonical typed request** (§11) — operation, certification /
     administrative session, subject binding, CSPRNG nonce ≥ 256 bits, expiry,
     echoed `installation_id` / `generation`, self-excluding `request_digest`;
  2. perform §6 pre-launch integrity recognition of the helper;
  3. create the **private one-shot channel** (§9), whose endpoint no
     agent-principal process holds;
  4. `exec` the verified helper as a one-shot child with a **closed minimal
     environment** and **no** shell / `PATH` / argv-selected operation / helper
     path / authority selector;
  5. send **exactly one** canonical request over the channel;
  6. receive **exactly one** typed response (§12) and, on `PERFORMED`, the
     typed evidence reference / read payload — **never** an authority object.
- **HPAC-PAWA-HELPER-REQ-035.** The launcher SHALL NOT: perform the privileged
  mutation / read / ceremony entry itself; hold, receive, construct, or forward
  an `HPACWriterCapability` / `HPACStoreAuthority` / `CertificationReadAuthority`
  / handle; accept a caller-provided `approved=True`, decision, response bytes,
  helper process, channel, attestation, operation result, or evidence digest;
  send more than one request per `exec`; retry a request whose response was
  lost after the mutation-attempt boundary (§21); or expose the channel fd to
  agent-principal code.
- **HPAC-PAWA-HELPER-REQ-036.** The launcher is **not** the human approver, the
  HPAC proof verifier, the writer authority, the PB, a runtime capability, or a
  generic privileged shell (HPAC-PPA-REQ-033 pattern). **Launcher possession /
  access alone is not authority**: the helper still independently runs §7 and
  §10, and the operation still must be a valid §13 member. A forged launcher
  without the protected root and without the deployment-owner peer credential
  cannot obtain any operation.
- **HPAC-PAWA-HELPER-REQ-037.** The **only** launchers are the standalone
  deployment-owner entry points enumerated by HPAC-PAWA-001 v2.0 §38 / §38A /
  §38B — `scripts/hpac_certification_admin.py` (certification-lifecycle reads /
  writes / ceremony entry; sole consumer `pcae.core.hpac_certification_coordinator`)
  and the standalone principal-administration / bootstrap / recovery script(s)
  for the §42 administrative mutations. Neither is a `pcae` CLI subcommand, a
  plugin, a runtime provider, a Gate consumer, a repository hook, or a task
  callback, and neither is on any agent / runtime / Gate import path directly or
  transitively. No wildcard, prefix, glob, `fnmatch`, or caller string may widen
  this inventory (PAWAH-INV-2, HPAC-PAWA-001 PAWA-INV-9).

## 9. Private one-shot channel

- **HPAC-PAWA-HELPER-REQ-038.** The channel is created **by the launcher**,
  before `exec`, as a **private parent/child** endpoint pair. Its endpoints are
  inherited **only** across the `exec` of the verified helper; **no**
  agent-principal process, plugin, or repository code holds, can open, or can
  reach either endpoint. If an `AF_UNIX` socket path is used it is under a
  `0700` deployment-owner-owned directory beneath `<HPAC_PROTECTED_ROOT>`.
- **HPAC-PAWA-HELPER-REQ-039.** The channel carries **only** the canonical
  request bytes (launcher → helper) and the canonical response bytes (helper →
  launcher). No file descriptor other than the channel and the verified helper
  descriptor is passed to the helper. No authority object, no
  `HPACStoreAuthority`, no `HPACWriterCapability`, no seal, and no channel fd is
  transmitted **in either direction** (HPAC-PAWA-001 §45 preserved:
  process-local capabilities are "never transmitted over IPC / socket / network
  / pipe").
- **HPAC-PAWA-HELPER-REQ-040.** Exactly **one** active request/response
  exchange exists per channel per `exec`. Unrelated helper invocations MAY run
  concurrently only with **distinct** channels, nonces, request digests, and
  helper processes; a cross-channel or cross-request response **fails closed**
  (HPAC-PPA-REQ-039 pattern).
- **HPAC-PAWA-HELPER-REQ-041.** Possession of the channel fd **alone** is
  **not** authority (§3, `TB-ARCH` §9): the helper still runs §7 (§33 1–8) and
  §10 (peer credential) and validates the §13 operation before admitting
  anything.

## 10. Peer authentication

- **HPAC-PAWA-HELPER-REQ-042.** Before it admits any operation, the helper
  SHALL obtain the **kernel-authenticated** OS `(uid, gid[, pid])` of the
  channel peer (§5 platform profile — `SO_PEERCRED` / `LOCAL_PEERCRED` /
  `getpeereid`), **not** from any peer-supplied protocol field, and SHALL
  require:
  1. the peer `uid` is the **deployment-owner** OS principal for this
     deployment (the owner of `<HPAC_PROTECTED_ROOT>` — resolved from the
     filesystem, not from the request);
  2. the peer `uid` is **not** the configured agent principal
     (`ConfiguredAgentAuthorityIdentity`, §7);
  3. the credential is **bound to the actual channel** the request arrived on
     (not a credential from a different connection);
  4. on the two-principal topology, (1) and (2) are distinct accounts; where
     the topology is **absent** (single-account host, or the agent holds
     protected-root write authority) → REAL issuance **ineligible**, fail closed
     (HPAC-PAWA-001 §61 / PAWA-INV-7).
- **HPAC-PAWA-HELPER-REQ-043.** Peer authentication is a **required conjunct**,
  evaluated **before** operation admission and **before** any protected-store
  read the request would drive. It is neither sufficient alone (§7 and §13 also
  required) nor omissible.
- **HPAC-PAWA-HELPER-REQ-044.** **OS peer credential ≠ human identity ≠ human
  approval ≠ informed intent** (PAWAH-INV-8; §14 of `TB-ARCH`). A successful
  peer-credential check establishes only "the process on the other end of this
  private channel is the deployment-owner OS principal" — it does **not**
  establish that a human authorized the operation, that a human is present, or
  that a human approved anything. The human APPROVE / REJECT is produced only by
  the HPAC-PPA-001 ceremony (§16).
- **HPAC-PAWA-HELPER-REQ-045.** A peer whose credential is unavailable,
  unauthenticated, forgeable under the §26 threat model, not the deployment
  owner, the configured agent principal, or not bound to the channel →
  **fail closed** (`unauthorized_factory_consumer` / `current_context_is_agent`
  per §18), **no** operation admitted.

## 11. Request schema — `HPAC-PAWA-HELPER-REQUEST/1.0`

- **HPAC-PAWA-HELPER-REQ-046.** The request is a **closed, versioned,
  canonically serialized** structure (canonicalization under HPAC-REQ-089).
  **Unknown fields fail closed.** Exactly these fields:

  | Field | Type / constraint | Meaning |
  |---|---|---|
  | `request_schema_version` | const `HPAC-PAWA-HELPER-REQUEST/1.0` | exact match required |
  | `protocol_version` | const `HPAC-PAWA-HELPER/1.0` | exact match against the current registered generation (§6) |
  | `operation` | closed enum — a member of the §13 vocabulary | no arbitrary string; unknown → `operation_scope_invalid` |
  | `operation_version` | const per operation (e.g. `enroll_principal/1.0`) | an unrecognized operation version → DENY (`operation_scope_invalid`) |
  | `role` | present **only** for `certification_write` (§14); a member of the closed five-role allowlist | any non-member (incl. `hpac_lifecycle_terminator`, wildcard, prefix, arbitrary string) → `operation_scope_invalid` |
  | `session_id` | nonempty string; the `certification_session_id` (certification ops) or the administrative-transaction id (`enroll_credential` etc.) | bound; a mismatch → `target_scope_invalid` |
  | `principal_id` / `credential_id` / `proof_id` | subject binding as the operation requires; resolved and validated by the helper against the canonical stores under the real OS context | not-resolvable / revoked / not-mechanism-neutral / not-bound-to-session → `operation_scope_invalid` / `target_scope_invalid` |
  | `operation_params` | a **closed typed struct per operation** (§13) — **never** a free path string, expression, shell command, module name, JSON-patch blob, or executable path | out-of-struct / extra key → `operation_scope_invalid` |
  | `request_id` | monotonic within `session_id` | a duplicate for a one-shot op after consumption → `capability_stale` |
  | `nonce` | CSPRNG, ≥ 256 bits, fresh per request | reuse → `capability_stale` / `target_scope_invalid` per §19 |
  | `expiry` | trusted-clock deadline (RFC 3339 UTC) | the helper validates freshness against its own trusted clock; past deadline → `capability_stale` |
  | `installation_id` | echoed | cross-checked against the live protected root; mismatch → `descriptor_installation_mismatch` |
  | `generation` | echoed | cross-checked against the current-generation anchor; mismatch / stale → `descriptor_generation_stale` |
  | `request_digest` | **self-excluding** SHA-256 of the canonical record | mismatch → `operation_scope_invalid` |

- **HPAC-PAWA-HELPER-REQ-047.** **Forbidden in a request** (`TB-ARCH` §11 /
  §28; PAWAH-INV-5): an arbitrary Python expression; a module name / import
  path; a shell command; an executable path; a role string beyond the
  enumerated five; a generic / free filesystem path; an unrestricted JSON
  mutation payload; a caller-provided `approved=True`, decision, response bytes,
  helper process, channel, attestation, or evidence digest; a caller-selected
  authority class, seal, or `_bind_configured_agent_identity` argument.
- **HPAC-PAWA-HELPER-REQ-048.** The request carries **no authority**. It is a
  bounded description of one requested operation. `request for operation` **≠**
  `permission to perform arbitrary related operations`; `a well-formed request`
  **≠** `an admitted operation` (admission additionally requires §7, §10, and
  §13 validation).

## 12. Response schema — `HPAC-PAWA-HELPER-RESPONSE/1.0`

- **HPAC-PAWA-HELPER-REQ-049.** The response is a **closed, versioned,
  canonically serialized** structure. Exactly these fields:

  | Field | Type / constraint | Meaning |
  |---|---|---|
  | `response_schema_version` | const `HPAC-PAWA-HELPER-RESPONSE/1.0` | |
  | `protocol_version` / `request_id` / `nonce` | echoed; **must match** the request exactly | any mismatch → the launcher fails closed, treats the exchange as no-result, and reconciles per §21 |
  | `decision` | closed enum `PERFORMED` \| `REJECTED` | on `REJECTED`, `terminal_code` is set |
  | `terminal_code` | present iff `REJECTED`; an existing `pawa_failure_code` (§18) | free-form outcomes prohibited |
  | `evidence_ref` | present iff `PERFORMED` and the operation wrote a record; the protected-root-relative reference to the audit record the helper wrote (§17) | **not** an authority object |
  | `evidence_digest` | present iff `evidence_ref`; SHA-256 of that canonical audit record | the launcher / caller reconciles against this |
  | `result_payload` | present **only** for `certification_read` (§15) and a `ceremony_entry` acknowledgement; the enumerated §15 record contents, or a ceremony-entry ack | **never** an `HPACStoreAuthority`, `HPACWriterCapability`, handle, seal, or any object from which privileged authority could be reconstructed |
  | `trusted_timestamp` | helper's trusted-clock UTC RFC 3339 | |
  | `state_reached` | the §20 state the operation reached (`RESPONSE_EMITTED` is implied; the durable one is `EVIDENCE_WRITTEN` or an earlier fail-closed state) | informative; the durable protected-root record is authoritative, not this field |
  | `response_digest` | **self-excluding** SHA-256 of the canonical record | |

- **HPAC-PAWA-HELPER-REQ-050.** The response conveys **evidence, not
  authority**: `typed result` **≠** `writer capability`; `receipt / evidence`
  **≠** `authority`; `successful helper admission` **≠** `reusable authority`
  (`TB-ARCH` §10). The caller cannot replay, extend, or convert a `PERFORMED`
  response into a second operation or a privileged object.
- **HPAC-PAWA-HELPER-REQ-051.** **Response absence is never proof.** A missing,
  truncated, or mismatched response is **never** proof that no state transition
  occurred (§21). `RESPONSE_EMITTED` (a helper-side state) is **not**
  `human observed response` and is not `caller received response`.

## 13. Closed operation vocabulary

- **HPAC-PAWA-HELPER-REQ-052.** The `operation` field is a **closed enum**.
  There is **no** generic "HPAC operation", "helper op", "file write",
  "registry mutation", "store method", "shell command", "Python expression",
  "executable path", "JSON patch", or "role-driven generic dispatch". Every
  member below has: a stable operation id; an exact `operation_version`; an
  exact permitted caller/consumer context; exact preconditions; exact state
  reads; exact state writes; an exact typed `operation_params` struct; an exact
  result; exact evidence; exact failure semantics; a replay / single-use rule;
  and an audit rule. **Unknown operation → DENY. Unrecognized operation version
  → DENY. Prefix / wildcard / extension matching → DENY.** (PAWAH-INV-5.)
- **HPAC-PAWA-HELPER-REQ-053.** The closed vocabulary, `HPAC-PAWA-HELPER/1.0`:

  | Operation id | Family | Consumer (HPAC-PAWA-001 v2.0) | Bounded action | Result / evidence | Replay rule |
  |---|---|---|---|---|---|
  | `admin_mutation` with `operation_params.mutation ∈ { enroll_principal, revoke_principal, enroll_credential, revoke_credential, initialize_credential_sidecar_state, configure_presentation_mechanism, configure_privileged_helper }` | §14.1 administrative mutation | the standalone principal-admin / bootstrap / recovery launcher (HPAC-PAWA-001 v2.0 §38 / §80.2) | exactly **one** HPAC-PAWA-001 §42 bounded mutation, performed by the helper under `<HPAC_PROTECTED_ROOT>` | `PERFORMED` + `evidence_ref` / `evidence_digest` of one `HPAC-PAWA-ISSUANCE-EVIDENCE/1.0` record the helper wrote | single-use per `(request_id, nonce)`; a consumed request cannot be re-admitted |
  | `certification_write` with `role ∈` the closed five (§14.2) | §14.2 certification-lifecycle write | `pcae.core.hpac_certification_coordinator` via `scripts/hpac_certification_admin.py` (HPAC-PAWA-001 v2.0 §38A) | exactly **one** five-role lifecycle write (HPAC-PAWA-001 §42B per-role authority) | `PERFORMED` + `evidence_ref` / `evidence_digest` | single-use per `(role, subject, session_id, request_id)` |
  | `certification_read` | §15 enumerated read | the same §38A / §38B coordinator | return the enumerated §15 record contents for the bound session | `PERFORMED` + `result_payload` (record contents); audit `operation = "certification_read_authority"` | idempotent read; each call re-runs §7 / §10 / §13 validation |
  | `ceremony_entry` | §16 ceremony hand-off | the same §38A / §38B coordinator | hand the canonical ceremony request to the HPAC-PPA-001 presentation helper for **exactly one** ceremony in the bound session | `PERFORMED` + `result_payload` = ceremony-entry acknowledgement (a reference to the started HPAC-PPA-001 ceremony) — **no** authority object, **no** ceremony outcome | single-use per `session_id`; a second `ceremony_entry` for the same session → `capability_stale` |
  | `presentation_evidence_write` | §17 presentation evidence | invoked **by the HPAC-PPA-001 presentation helper itself** post-ceremony (HPAC-PAWA-001 §42B / HPAC-PAWA-REQ-248; HPAC-PPA-REQ-041) | exactly **one** create-only `HPAC-PRESENTATION-EVIDENCE/2.0` write after one valid `APPROVE` | `PERFORMED` + `evidence_ref` / `evidence_digest` | single-use per ceremony `(invocation_id, attempt_id)` |

- **HPAC-PAWA-HELPER-REQ-054.** The helper SHALL reject an `operation` not in
  the current registered generation's `supported_operations` (§6) even if it is
  a valid §13 member — a helper build implements a declared subset, and an
  unimplemented operation on that build fails closed (`operation_scope_invalid`).
- **HPAC-PAWA-HELPER-REQ-055.** Adding a new operation id, a new
  `operation_params` field, or a new operation family is a **MINOR** evolution
  **only if** it is explicitly enumerated, typed, bounded, single-use / bounded
  per its rule, consumed only by an already-enumerated HPAC-PAWA-001 consumer,
  and fires **no** HPAC-PAWA-001 §152 or §30 MAJOR trigger; otherwise it is a
  **MAJOR** (§30). A generic, free-form, or wildcard operation is **never**
  permitted at any version (PAWAH-INV-5).

## 14. Family details

### 14.1 Administrative-mutation family

- **HPAC-PAWA-HELPER-REQ-056.** The `admin_mutation` operation performs exactly
  one HPAC-PAWA-001 §42 mutation class. The helper — not the launcher, not the
  main interpreter — performs the compare-and-write under
  `<HPAC_PROTECTED_ROOT>` through the existing canonical stores'
  writer-transaction semantics (expected-current compare-and-write, read-back
  verified). No `HPACWriterCapability` is returned to the launcher; the caller
  receives `PERFORMED` + the evidence reference.
- **HPAC-PAWA-HELPER-REQ-057.** `operation_params` for each mutation is a
  **closed typed struct**: exactly the target id(s) and the closed enumerated
  parameters HPAC-PAWA-001 §42–§44 / §80.2 already define for that mutation
  (e.g. `enroll_principal` → `{ transaction_id }`; `revoke_credential` →
  `{ credential_id }`; `configure_presentation_mechanism` →
  `{ mechanism_id, lifecycle_action ∈ {install, rotate, revoke}, transaction_id }`;
  `configure_privileged_helper` →
  `{ helper_installation_generation, lifecycle_action ∈ {install, rotate, revoke},
  transaction_id }`). No free path, no expression, no JSON blob.
- **HPAC-PAWA-HELPER-REQ-058.** `request for operation` **≠** `permission to
  perform arbitrary related operations`; `successful helper admission` **≠**
  `reusable authority`; `typed result` **≠** `writer capability`;
  `receipt / evidence` **≠** `authority` (`TB-ARCH` §10). A `PERFORMED`
  `admin_mutation` authorizes nothing further.

### 14.2 Five-role certification-lifecycle family

- **HPAC-PAWA-HELPER-REQ-059.** The `certification_write` operation's `role`
  field is a member of the **closed five-role allowlist**, **exactly**:

  ```
  { hpac_challenge_coordinator,
    hpac_assertion_recorder,
    human_authentication_proof_verifier,
    hpac_gate5_binder,
    hpac_rhamp_counter_state_verifier }
  ```

  No wildcard, no prefix, no `fnmatch`, no arbitrary role argument, no future
  role implicitly authorized. `hpac_lifecycle_terminator` is **explicitly NOT**
  a member — a rejected or expired ceremony fails closed with no production
  write; a genuine future need for a production terminator write requires a new
  governed contract evolution (HPAC-PAWA-001 §42B / HPAC-PAWA-REQ-246,
  PAWA-INV-13 — preserved verbatim; this contract does not re-derive or weaken
  it).
- **HPAC-PAWA-HELPER-REQ-060.** Each `certification_write` invocation performs
  **exactly one** of the HPAC-PAWA-001 §42B per-role bounded actions, in the
  helper process, on the canonical stores, with the exact per-role permitted
  store / action, prohibited actions, issuance prerequisites, capability
  bindings `(role, subject, session_id)`, and cardinality **one** that
  HPAC-PAWA-001 §42B HPAC-PAWA-REQ-247 freezes. `subject` is the `proof_id` for
  the four lifecycle roles and the `credential_id` for
  `hpac_rhamp_counter_state_verifier`.
- **HPAC-PAWA-HELPER-REQ-061.** Per-role preserved semantics (informative
  summary; HPAC-PAWA-001 §42B / §68A / `TB-ARCH` §19 are authoritative):

  | Role | Bounded op | Preserved wall |
  |---|---|---|
  | `hpac_challenge_coordinator` | issue one session-bound challenge | `challenge issuance ≠ human approval ≠ proof validity ≠ Gate 5`; no caller-selected / pre-marked "trusted" challenge material; fresh canonical generation; expiry |
  | `hpac_assertion_recorder` | record one validated assertion lifecycle object | `recorded assertion ≠ valid assertion`; recording asserts **no** signature validity / UP / UV / human identity / approval / proof validity — evidence ingestion is separated from verification |
  | `human_authentication_proof_verifier` | create the canonical proof + record `STATE_PROOF_VERIFIED` | issues / recognizes the verified proof result **only after all required RHAMP checks pass** (challenge, credential binding, signature, UP, UV, currentness, revocation, counter state); `deterministic test mechanism ≠ real human authentication`; helper peer identity ≠ human identity |
  | `hpac_gate5_binder` | bind one trusted verifier-issued principal to the actual Gate 5 invocation | `Gate5 ALLOW ≠ PB permission ≠ human approval ≠ consumed authority ≠ runtime capability ≠ adapter admission ≠ external-effect permission`; SHALL NOT manufacture the principal or the Gate result; the N16-5 authority path **terminates** at the Gate-5 assurance result |
  | `hpac_rhamp_counter_state_verifier` | one authorized post-verification bounded counter transition on an **accepted** canonical counter decision | the **sole** counter-state mutation authority; SHALL NOT reset / arbitrarily set counters, modify credential identity / revocation, touch an unrelated credential, or trust a caller-provided "counter accepted"; `counter evidence ≠ human approval ≠ PB permission ≠ execution`; monotonicity / currentness owned by RHAMP-001; pre-ceremony counter **read** (§15) ≠ this transition |

- **HPAC-PAWA-HELPER-REQ-062.** **FACTORY ≠ CONSUMER, CONSUMER ≠ MINTER**
  (HPAC-PAWA-001 §15 preserved): a `PERFORMED` `certification_write` does not
  permit the coordinator (or anything it calls) to remint, delegate, convert to
  generic authority, serialise, store, or reissue anything. A second
  `certification_write` re-runs the full §7 / §10 / §13 sequence in a fresh
  helper process.

## 15. Typed enumerated read vocabulary (`certification_read`)

- **HPAC-PAWA-HELPER-REQ-063.** The `certification_read` operation returns
  **only reads**, over an **explicitly enumerated closed** set of canonical
  protected-store records **for the bound session** — the exact HPAC-PAWA-001
  v2.0 §42D set:
  - the `PrincipalRecord` for the bound `principal_id` and the `CredentialRecord`
    for the bound `credential_id` (and its canonical provenance) via
    `HumanPrincipalRegistryStore`;
  - the credential's RHAMP sidecar (`RHAMP-FIDO2-CREDENTIAL/1.0`) and its
    **current** counter-state record (`RHAMP-COUNTER-STATE/1.0`) via the
    existing sidecar / counter-state stores — **read only**;
  - the **current-generation** protected-presentation installation record, the
    HPAC-REQ-090 mechanism descriptor, and the trusted-approval-presentation
    record via `ProtectedPresentationInstallationStore` /
    `PresentationMechanismDescriptorStore` / `TrustedApprovalPresentationStore`;
  - the PAWA anchor / descriptor / `HPAC-PAWA-AGENT-EXCLUSION/1.0` and the
    §6 helper-registration records that the §7 recognition already reads.
- **HPAC-PAWA-HELPER-REQ-064.** Each read result specifies an **exact record
  type**, **exact permitted fields**, **exact purpose**, and the **exact bound
  session / subject**. `certification_read` SHALL NOT permit: an arbitrary
  filesystem read; an open-ended HPAC store enumeration beyond the enumerated
  set; a wildcard field selection; a read of OS secrets, keychain / keyring
  material, a FIDO2 PIN, Telegram or other application secrets, or a private
  key; a read of an unrelated principal / credential / proof / session; a
  `proofs/v2` read outside a bound session; or **any** write, create, replace,
  `chmod`, `chown`, or execute (HPAC-PAWA-001 §42D / HPAC-PAWA-REQ-284).
- **HPAC-PAWA-HELPER-REQ-065.** **Repeated typed reads SHALL NOT reconstruct
  unrestricted store authority.** The enumeration is by exact record identity
  bound to the session; a caller cannot iterate it into a generic read broker,
  and the helper returns record **contents**, not a store handle or an
  `HPACStoreAuthority`. If a future least-privilege need genuinely requires a
  broader bounded read, the phase that discovers it SHALL state and justify the
  **minimum** bounded form and evolve this contract explicitly (§30) — it does
  **not** widen the set silently.
- **HPAC-PAWA-HELPER-REQ-066.** The `certification_read` result is
  **non-authoritative except for the exact evidentiary claim its schema
  defines** (PAWAH-INV-4): "this is the current content of record X for session
  S as read under the deployment owner's real OS context at time T". It does
  not assert validity, approval, human presence, or assurance.

## 16. Ceremony-entry semantics (`ceremony_entry`)

- **HPAC-PAWA-HELPER-REQ-067.** `ceremony_entry` is a **separate typed
  operation** whose **only** effect is to hand the canonical ceremony request
  to the **existing HPAC-PPA-001 v1.0 protected-presentation helper** for
  **exactly one** ceremony in the bound session. It passes the canonical
  ceremony request bytes (HPAC-PPA-REQ-034 shape) — **not** a Python
  `HPACStoreAuthority`, not a handle, not a seal.
- **HPAC-PAWA-HELPER-REQ-068.** `ceremony_entry` preserves every wall verbatim
  (`TB-ARCH` §14 / §20; HPAC-PAWA-001 §68B):

  ```
  ceremony entry  != approval
  ceremony entry  != authentication
  ceremony entry  != Gate-5 ALLOW
  ceremony entry  != PB permission
  ceremony entry  != execution
  ceremony entry  != FIDO2 user presence / user verification
  ceremony entry  != a real authenticator assertion
  ceremony entry  != real assurance
  ```

  The operation may **only** initiate the already-defined protected
  presentation flow; it **never** produces its outcome. The presentation helper
  remains a **distinct semantic component** (HPAC-PPA-001) even though the
  one-shot-verified-helper process **infrastructure pattern** is shared.
- **HPAC-PAWA-HELPER-REQ-069.** The `ceremony_entry` result
  (`result_payload`) is a ceremony-entry **acknowledgement** — a reference to
  the started HPAC-PPA-001 ceremony — and nothing more. The human APPROVE /
  REJECT election and the `HPAC-PRESENTATION-EVIDENCE/2.0` write are conducted
  by HPAC-PPA-001, unchanged.

## 17. Presentation-evidence write semantics (`presentation_evidence_write`)

- **HPAC-PAWA-HELPER-REQ-070.** `presentation_evidence_write` is invoked **by
  the HPAC-PPA-001 presentation helper itself**, post-ceremony, after **one
  valid `APPROVE` response**, to author **exactly one** create-only
  `HPAC-PRESENTATION-EVIDENCE/2.0` record and its ordinary provenance sidecar at
  the HPAC-REQ-093 path. This is the **existing**
  `mint_protected_presentation_evidence_writer` semantics (HPAC-PAWA-001 §42B /
  HPAC-PAWA-REQ-248; HPAC-PPA-REQ-041 / REQ-043) restated as a helper operation
  — the sole author of `HPAC-PRESENTATION-EVIDENCE/2.0` is unchanged.
- **HPAC-PAWA-HELPER-REQ-071.** The `presentation_evidence_write` request
  SHALL NOT be able to **self-assert**:

  ```
  approved = true
  verified = true
  human_present = true
  authenticated = true
  ```

  Those facts arise **only** from their designated trusted mechanisms (the
  HPAC-PPA-001 ceremony's authenticated `APPROVE` response for `approved`; the
  RHAMP verifier for `verified` / `authenticated`; the genuine authenticator
  for `human_present`). The helper writes the evidence record only from a
  bound, valid, authenticated ceremony response it independently re-checks
  (HPAC-PPA-REQ-045).
- **HPAC-PAWA-HELPER-REQ-072.** `REJECT`, cancel, timeout, crash, malformed
  response, or any validation / currentness failure → **no** evidence write,
  fail closed (HPAC-PPA-REQ-044). No failure path preserves a reusable writer —
  there is no returnable writer.
- **HPAC-PAWA-HELPER-REQ-073.** The §20 protected-presentation evidence-writer
  **boundary** (installer ≠ launcher ≠ helper response ≠ evidence writer;
  PPA-INV-2), the human-election writer boundary, and the "sole author of
  `HPAC-PRESENTATION-EVIDENCE/2.0`" rule are **unaffected in substance**.
  `presentation_evidence_write` does not merge presentation rendering, human
  authentication, certification-writer authority, and Gate-5 binding.
**Cross-contract note (HPAC-PPA-001) — an explicit question for the dedicated
contract IV, not a normative requirement of this contract.** HPAC-PPA-001
  v1.0's evidence-writer authority (HPAC-PPA-REQ-041) is today described as an
  `HPACWriterCapability` "held only by the trusted launcher mediator … never
  sent to the helper". Under the HPAC-PAWA-001 v2.0 out-of-process model that
  authority is minted **and consumed inside the already-out-of-process
  presentation helper** (which HPAC-PPA-001 §6 / §7 already mandates as an
  integrity-verified one-shot process) and **no** writer object crosses back to
  the launcher mediator. Whether this is (a) within HPAC-PPA-REQ-041's "or
  repository-equivalent use of the same existing capability/provenance
  primitive" and HPAC-PPA-REQ-070's "add a platform adapter within these exact
  properties" — a tightening, since the authority moves *further* from the agent
  interpreter, not closer — or (b) a re-meaning of "never sent to the helper"
  that needs a **fresh aligned HPAC-PPA-001 successor**, is an **explicit
  question for the dedicated contract IV (N16-5-F-5-TB-CONTRACT-IV)** and, if
  (b), a **fresh governed HPAC-PPA-001 evolution phase** (derived, **not
  begun** — HPAC-PAWA-001 v2.0 §80.5 / HPAC-PAWA-REQ-334 discipline; this phase
  does **not** silently edit HPAC-PPA-001). Until that determination,
  `presentation_evidence_write` is frozen here as a **specification** consistent
  with option (a); the `mint_protected_presentation_evidence_writer` in-process
  path remains as-is (removed only in the later governed in-process-path-removal
  slice).

## 18. Freshness

- **HPAC-PAWA-HELPER-REQ-074.** Every request carries an `expiry` (trusted-clock
  deadline) and a per-request CSPRNG `nonce` ≥ 256 bits. The helper validates
  freshness against **its own** trusted clock; a request past `expiry` →
  **fail closed** (`capability_stale`), **no** operation admitted, regardless of
  every other conjunct passing.
- **HPAC-PAWA-HELPER-REQ-075.** Certification-lifecycle objects preserve **all
  existing** currentness / replay semantics owned by their canonical contracts —
  challenge expiry and single-use, proof expiry, presentation-evidence
  single-use (HPAC-PPA-001), counter currentness (RHAMP-001). This protocol
  introduces **no** new TTL and the helper SHALL NOT bypass any existing one; a
  stale / replayed / expired lifecycle object → the owning contract's existing
  rejection, and no trusted proof / no production assurance results
  (HPAC-PAWA-001 §44A / HPAC-PAWA-REQ-257 — preserved).

## 19. Replay

- **HPAC-PAWA-HELPER-REQ-076.** The helper SHALL distinguish, and treat
  distinctly:

  | Request state | Helper behaviour |
  |---|---|
  | **fresh** — new `(request_id, nonce)`, within `expiry`, all conjuncts pass | admit exactly once |
  | **consumed** — a one-shot op whose `(request_id, nonce)` already reached `MUTATION_ATTEMPT_STARTED` or beyond (§20) | **DENY** (`capability_stale`); a consumed request **cannot** be accepted again, even if its response was lost |
  | **duplicate** — same `(request_id, nonce)` re-presented while the first is still in flight in another helper process | **DENY** (`capability_stale` / `target_scope_invalid`); at most one helper process may admit a given `(request_id, nonce)` |
  | **expired** — past `expiry` | **DENY** (`capability_stale`) |
  | **unknown** — malformed, unknown-field, unknown operation / version | **DENY** (`operation_scope_invalid`) |
  | **conflicting replay** — a `(request_id, nonce)` reused with different `operation` / `session_id` / subject | **DENY** (`target_scope_invalid`) |

- **HPAC-PAWA-HELPER-REQ-077.** **A lost response does not make the original
  request unused.** Once a one-shot operation crosses `MUTATION_ATTEMPT_STARTED`
  (§20), its `(request_id, nonce)` is spent whether or not the caller received
  the response. The caller MUST reconcile against the protected-root evidence
  record (§21), **not** resend.
- **HPAC-PAWA-HELPER-REQ-078.** `certification_read` is idempotent — a repeated
  read with the same binding re-runs §7 / §10 / §13 and returns the current
  record contents; it is not "consumed", but each call is a fresh helper
  process with full recognition.

## 20. State-transition model

- **HPAC-PAWA-HELPER-REQ-079.** Every **mutating** operation
  (`admin_mutation`, `certification_write`, `presentation_evidence_write`)
  follows this frozen ordered state model (names adapted to repository
  conventions; a `certification_read` / `ceremony_entry` follows the
  non-mutating subset through `ADMITTED` then `RESULT_EMITTED`):

  ```
  REQUEST_RECEIVED
    -> REQUEST_AUTHENTICATED     (peer credential §10 + nonce + request/response binding + freshness §18)
    -> OPERATION_ADMITTED        (§7 steps 1-8 + operation/role/session/subject validation §13)
    -> MUTATION_ATTEMPT_STARTED  (the no-auto-retry boundary is now crossed)
    -> MUTATION_COMMITTED        (atomic canonical record compare-and-write, read-back verified, under <HPAC_PROTECTED_ROOT>)
    -> EVIDENCE_WRITTEN          (the durable audit record §17/§22 is finalized)
    -> RESPONSE_EMITTED          (the typed response is sent over the channel)
  ```

- **HPAC-PAWA-HELPER-REQ-080.** What each transition proves, frozen:

  | State | Proves | Does NOT prove |
  |---|---|---|
  | `REQUEST_AUTHENTICATED` | the peer is the deployment owner over this channel; the request is fresh and well-bound | that the operation is valid or admissible |
  | `OPERATION_ADMITTED` | §7 1–8 passed and the operation / role / session / subject are valid | that the mutation succeeded |
  | `MUTATION_ATTEMPT_STARTED` | the helper has begun the write; **the no-auto-retry boundary is crossed** | that the mutation committed |
  | `MUTATION_COMMITTED` | the canonical record was written and read-back verified | that the response was delivered or observed |
  | `EVIDENCE_WRITTEN` | a durable audit record exists whose digest the response carries | that a human approved anything |
  | `RESPONSE_EMITTED` | the helper sent a typed response | that the caller received it or a human observed it |

- **HPAC-PAWA-HELPER-REQ-081.** Durable transitions (survive a crash and are
  reconcilable from `<HPAC_PROTECTED_ROOT>`): `MUTATION_COMMITTED` and
  `EVIDENCE_WRITTEN`. `REQUEST_RECEIVED` … `MUTATION_ATTEMPT_STARTED` are
  process-local and leave **no protected-root effect** if the helper dies
  before `MUTATION_COMMITTED`.
- **HPAC-PAWA-HELPER-REQ-082.** **No automatic retry** once
  `MUTATION_ATTEMPT_STARTED` is crossed, **unless** the operation contract
  proves the mutation **idempotent or reconcilable** (a `certification_read` is
  freely repeatable; a create-only record write is naturally reconcilable —
  see §22). The launcher / caller SHALL reconcile against the protected-root
  durable evidence, never resend a spent one-shot request (existing PCAE
  no-auto-retry principle preserved; `TB-ARCH` §21).

## 21. Crash / response-loss / uncertainty semantics

- **HPAC-PAWA-HELPER-REQ-083.** Helper crash / abnormal exit / broken pipe /
  timeout behaviour, by the state reached:

  | Crash point | Protected-root effect | Caller obligation |
  |---|---|---|
  | before `REQUEST_AUTHENTICATED` | none | fail closed; the request is unused; a fresh request MAY be built |
  | after `REQUEST_AUTHENTICATED`, before `OPERATION_ADMITTED` | none | as above |
  | after `OPERATION_ADMITTED`, before `MUTATION_ATTEMPT_STARTED` | none | as above |
  | after `MUTATION_ATTEMPT_STARTED`, before `MUTATION_COMMITTED` | **none** (no committed record) | the `(request_id, nonce)` is **spent**; do **not** retry it; reconcile — absence of a committed record ⇒ no effect; a **new** request (new id + nonce) is required to proceed |
  | after `MUTATION_COMMITTED`, before `EVIDENCE_WRITTEN` | a committed record exists **without** matching finalized evidence | **INDETERMINATE / RECONCILIATION REQUIRED** — a `BLOCKED` reconcile condition, **not** a silent success and **not** a retry; a deployment-owner reconciliation step confirms the committed record and finalizes or quarantines the evidence (§22) |
  | after `EVIDENCE_WRITTEN`, before `RESPONSE_EMITTED` | committed record + finalized evidence exist | reconcile against the evidence record (its digest is what the lost response would have carried); the operation **succeeded**; do not retry |
  | after `RESPONSE_EMITTED`, response lost in transit | committed record + finalized evidence exist | as above — response loss is **never** proof the mutation did not happen |

- **HPAC-PAWA-HELPER-REQ-084.** **Unknown outcome remains unknown until
  reconciled.** The caller SHALL NOT infer success or failure from a missing
  response alone (§12.51). Reconciliation is against the **durable
  protected-root evidence record**, whose presence/absence and digest are
  authoritative.
- **HPAC-PAWA-HELPER-REQ-085.** No-auto-retry applies **wherever replay could
  duplicate a protected mutation** (§20.82). A `certification_read` MAY be
  re-issued freely (fresh helper, fresh recognition).

## 22. Audit-write ordering and content

- **HPAC-PAWA-HELPER-REQ-086.** For every **mutating** operation the helper
  SHALL use ordering model **A — evidence durably staged before the mutation,
  finalized after commit** (of the three models the architecture allowed;
  `TB-ARCH` §21 required this section be precise rather than freeze the phrase
  "audit failure means the mutation did not occur"):
  1. before `MUTATION_ATTEMPT_STARTED`, the helper durably writes a **staged**
     audit record (`state = "staged"`) under
     `<HPAC_PROTECTED_ROOT>` binding the request digest, operation, role,
     session, subject, nonce, and expiry;
  2. if the staged write fails → **abort before any mutation**, fail closed
     (`internal_fail_closed`), no protected-root mutation occurs;
  3. the helper performs the one mutation (`MUTATION_COMMITTED`);
  4. the helper **finalizes** the staged record (`state = "committed"`, adding
     the committed-record digest) — `EVIDENCE_WRITTEN`;
  5. a crash between (3) and (4) leaves a `staged` record plus a committed
     canonical record → the **INDETERMINATE / RECONCILIATION REQUIRED** state
     of §21 (a deployment-owner reconciliation finalizes or quarantines it);
     it is **never** reported as success and **never** auto-retried.
- **HPAC-PAWA-HELPER-REQ-087.** This contract does **not** claim "audit-write
  failure means the mutation did not occur" unconditionally — it **guarantees
  the ordering** in §86 that makes a pre-mutation staged-evidence failure abort
  before any mutation, and makes a post-commit finalization failure a detectable
  reconciliation condition rather than a silent success.
- **HPAC-PAWA-HELPER-REQ-088.** Each audit record uses the **existing**
  `HPAC-PAWA-ISSUANCE-EVIDENCE/1.0` schema (`operation` / `context_annotation`
  fields; `operation = "certification_read_authority"` for `certification_read`)
  — **no** new schema. It records the §55 field set of HPAC-PAWA-001 plus, as
  **non-authoritative** facts (never authority fields): `role`, `session_id`,
  bound `principal_id` / `credential_id` / `proof_id`, the operation and its
  state, the request and response digests, and (as a non-authoritative
  annotation) the peer `uid` and whether `sudo` / ambient-root was in effect.
  It SHALL NOT serialise a `_seal`, an authority object, or anything from which
  a working capability or authority could be reconstructed (HPAC-PAWA-001 §119,
  PAWA-INV-10). **Audit evidence is not authority.**
- **HPAC-PAWA-HELPER-REQ-089.** `certification_read` and `ceremony_entry`
  (non-mutating) write one audit record at `RESULT_EMITTED` recording the read
  scope / ceremony reference and result; no staged-then-finalized ordering is
  required because there is no mutation to bracket.

## 23. No-auto-retry rule (frozen)

- **HPAC-PAWA-HELPER-REQ-090.** `EFFECT_ATTEMPT_STARTED` / `MUTATION_ATTEMPT_STARTED`
  means **the no-auto-retry boundary has been crossed** (HPAC-PAWA-001 §29–§30
  discipline; RDGO-001 dispatch semantics pattern). It does **not** prove the
  effect / mutation happened. Nothing in this contract enables `adapter.dispatch()`
  or any external effect. A caller, launcher, or coordinator SHALL NOT resend a
  spent one-shot request; the only forward path after an uncertain one-shot
  outcome is **reconciliation against the durable protected-root record**
  followed, if needed, by a **new** governed request with a fresh id and nonce.

## 24. No privileged authority-object export (frozen invariant)

- **HPAC-PAWA-HELPER-REQ-091.** **No production privileged authority object may
  cross from the protected helper boundary into the ordinary PCAE interpreter
  or the launcher.** This covers, by name **and by semantic equivalence**:

  ```
  HPACWriterCapability
  HPACStoreAuthority                      (a recognized / production instance)
  ProductionWriterHandle                  (and any repository-equivalent writer handle)
  the §42B certification-lifecycle capability   (certification_writer output)
  the read-authority handle               (CertificationReadAuthority)
  the presentation-evidence writer         (mint_protected_presentation_evidence_writer output)
  any generic writer / authority object
  any transferable object whose possession enables an equivalent privileged operation
  any "capability token", opaque handle, serialized seal, or reconstructable field set
      from which a bearer writer could be recreated outside the helper
  ```

- **HPAC-PAWA-HELPER-REQ-092.** The caller receives **only**:
  `decision` (`PERFORMED` / `REJECTED` + `terminal_code`); `evidence_ref` /
  `evidence_digest` (a protected-root-relative reference + digest); and, for
  `certification_read` / `ceremony_entry`, `result_payload` = the enumerated
  record contents or a ceremony-entry acknowledgement. Nothing else. There is
  **no** "capability token" workaround that recreates a bearer writer outside
  the helper (PAWAH-INV-1).
- **HPAC-PAWA-HELPER-REQ-093.** The **privileged side owns the operation**
  (`TB-ARCH` §8): the helper performs the exact mutation / read / ceremony
  entry itself; the main interpreter and the launcher never receive authority
  to perform the mutation later. `successful helper admission` **≠** `reusable
  authority`; `typed result` **≠** `writer capability`;
  `receipt / evidence` **≠** `authority`.

## 25. No generic privileged broker (frozen invariant)

- **HPAC-PAWA-HELPER-REQ-094.** The helper SHALL NOT be, become, or be
  reachable as a **generic privileged broker**. Normatively prohibited
  (`TB-ARCH` §28; PAWAH-INV-5):

  ```
  arbitrary filesystem path mutation
  arbitrary command execution
  arbitrary shell execution
  arbitrary Python execution / eval / exec of caller bytes
  arbitrary store-method dispatch
  arbitrary / caller-driven role minting
  unrestricted registry editing
  generic secret retrieval
  generic environment modification
  unrestricted process launch
  a "run this operation by name" or "apply this JSON patch" entry point
  ```

  Every permitted operation is explicitly enumerated (§13), typed (§11), bounded
  (§14–§17), and contract-bound. `operation_params` is a **closed typed struct
  per operation**, never a path string, expression, or JSON mutation payload.

## 26. Deterministic-vs-real wall, and bounded security claims

### 26.1 Deterministic-vs-real

- **HPAC-PAWA-HELPER-REQ-095.** **`deterministic test mechanism ≠ real human
  authentication`** and **`a test helper speaking the protocol ≠ production
  authority`** (HPAC-PAWA-001 §68A / HPAC-PAWA-REQ-263 / REQ-265; HPAC-PPA-REQ-058).
  A process that speaks `HPAC-PAWA-HELPER/1.0` is production authority **only**
  if it is the integrity-verified out-of-band executable (§6) launched by an
  enumerated deployment-owner launcher (§8) whose peer credential is the
  deployment owner (§10) — a test double is a **different file** and fails §28.
- **HPAC-PAWA-HELPER-REQ-096.** The **only** permitted test injection point is a
  disclosed, one-leading-underscore, documented-fixture-only, keyword-only seam
  (HPAC-PAWA-001 §166 / §265 / §287 discipline), and a guard test SHALL assert
  **no non-test module** passes it into any helper / launcher path. The
  disclosed seams (`_production_test_fixture`, a directly-imported
  `_PRODUCTION_WRITER_FACTORY_SEAL`, `_topology_probe`, `_protected_root`,
  `_test_decision_source`, an in-process launch shim) remain **NON-PRODUCTION**;
  this contract legitimizes none of them.
- **HPAC-PAWA-HELPER-REQ-097.** A deterministic authenticator, a deterministic
  presentation, a fixture launcher, a fixture peer credential, or a fixture
  helper **remains permanently unable** to produce `PRODUCTION` authority or be
  relabelled with the real kind (HPAC-PPA-REQ-058). `verify_human_authentication
  (require_real_assurance=True)` still requires every resolved record's
  `authority_class is PRODUCTION` **and** the real authentication-mechanism id
  **and** the real presentation-mechanism id — the helper only makes those
  PRODUCTION records **reachable**; it does not relax the check (HPAC-PAWA-001
  §68A / HPAC-PAWA-REQ-263).

### 26.2 Bounded security claims

- **HPAC-PAWA-HELPER-REQ-098.** **The protocol protects against:** ordinary
  same-interpreter PCAE process compromise; a malicious plugin inside the
  ordinary process; Python object-graph introspection (`gc.get_objects` /
  `gc.get_referrers`); `import` / module / `sys.modules` manipulation; an
  ordinary configured-agent OS account; protocol replay; a fake helper started
  by an unprivileged process (fails the §28 hash / owner / same-file check); a
  fake launcher without the protected root and the deployment-owner peer
  credential (fails §7 / §10); forged request fields (closed schema,
  self-excluding digests, fail-closed on unknown fields).
- **HPAC-PAWA-HELPER-REQ-099.** **The protocol does NOT claim protection
  against:** a hostile root / admin who controls the protected files or the
  registered helper binary; a compromised OS kernel; a compromised registered
  helper binary after an authorized protected-root mutation; a deployment owner
  restoring a byte-identical whole trusted-machine snapshot; a single-account
  host (there the two-principal topology is absent → REAL issuance
  **ineligible**, fail closed — genuine protection **requires** the
  two-principal deployment). These bounds match HPAC-PAWA-001 §8(c) / §60 /
  PAWA-INV-6, HBDC-001 §18, and `TB-ARCH` §4 / §26, inherited unchanged.

## 27. Mechanism neutrality and the mobile future

- **HPAC-PAWA-HELPER-REQ-100.** The helper's existence and trust are bound to
  **OS process + OS filesystem + OS peer-credential** facts — **not** to
  possession of any physical authenticator (`TB-ARCH` §15 / §36). The protocol
  SHALL NOT hardcode YubiKey, FIDO2, USB, a specific AAGUID, one hardware brand,
  a local TTY, or `pcae-protected-local-presentation/1.0` as a prerequisite for
  the helper's operation. The helper **consumes** mechanism-neutral verified
  human-authentication results and a mechanism-neutral protected APPROVE per the
  HPAC / RHAMP / HPAC-PPA contracts; it hardcodes **no** authenticator.
- **HPAC-PAWA-HELPER-REQ-101.** A future **mobile-only / passkey**
  authentication-and-approval path stays open: it would deliver a verified
  authentication result and a protected APPROVE to the same `certification_write`
  / `ceremony_entry` / `certification_read` operations **unchanged**. Local TTY
  or a physical YubiKey SHALL NOT be a prerequisite for ordinary
  non-effecting PCAE development (HPAC-PAWA-001 §266).
- **HPAC-PAWA-HELPER-REQ-102.** The canonical `PrincipalRecord` stays
  mechanism-neutral; `human principal ≠ credential`; the helper does not bind
  the certification family to a mechanism.

## 28. Cross-platform profiles

- **HPAC-PAWA-HELPER-REQ-103.** One logical protocol + trust contract, with
  **platform-specific peer-auth and launch backends** (§5). The macOS
  development host (`LOCAL_PEERCRED` / `getpeereid`; `fexecve` /
  identity-preserving exec) and the Linux (Dell Ubuntu) deployment target
  (`SO_PEERCRED`; `execveat(AT_EMPTY_PATH)` / `fexecve`) are **not** assumed
  byte-for-byte equivalent; each realizes the §16 frozen properties. A
  service-manager (systemd / launchd) is **not** part of the selected one-shot
  design beyond optionally being how the deployment owner invokes the standalone
  launcher.
- **HPAC-PAWA-HELPER-REQ-104.** If a target platform cannot provide (a) a
  kernel-authenticated peer credential the ordinary agent cannot forge, or
  (b) a substitution-free exec of a verified file object, the implementation on
  that platform **STOPS BLOCKED** — it is not downgraded to a weaker check
  (HPAC-PPA-REQ-030 discipline).
- **HPAC-PAWA-HELPER-REQ-105.** No host is provisioned or mutated by this
  contract phase or by this contract text.

## 29. Security invariants (PAWAH-INV-1 .. PAWAH-INV-10)

- **PAWAH-INV-1.** **No production privileged authority object crosses from the
  protected helper into an ordinary PCAE interpreter or the launcher.** The
  caller receives typed evidence / a typed read result only; there is no
  capability token, opaque handle, or reconstructable field set that recreates
  a bearer writer outside the helper (§24).
- **PAWAH-INV-2.** **Privileged-operation admission requires the entire
  protected-consumer conjunction** — `exec`'d-from-verified-helper **and**
  deployment-owner peer credential **and** HPAC-PAWA-001 §33 steps 1–8 **and** a
  valid closed-vocabulary operation bound to a valid session. **No single
  identity / path / hash / peer / channel fact is sufficient** (§3, §7, §10,
  §13).
- **PAWAH-INV-3.** **Correct path + valid bytes is never a trusted helper:**
  owner / mode / type / no-symlink / one-hard-link + `helper_sha256` of the
  opened bytes + same-file-object exec + current-generation-anchor agreement +
  PAWA writer provenance are **jointly** required; path alone never suffices
  (§6; HPAC-PPA-INV-3 pattern).
- **PAWAH-INV-4.** **Typed evidence / result is non-authoritative except for the
  exact evidentiary claim its schema defines** — "a write happened / this is
  record X for session S read under the real OS context". It is never bearer
  authority (§12, §15, §22; HPAC-PAWA-001 PAWA-INV-10).
- **PAWAH-INV-5.** **Unknown or non-enumerated privileged operations fail
  closed.** The operation vocabulary is closed and typed; no generic file write
  / command / expression / store method / role mint / registry edit / secret
  retrieval / process launch; `operation_params` is a closed typed struct
  (§13, §25).
- **PAWAH-INV-6.** **Same-interpreter module / caller identity is not a
  production authority root.** The v1.4 `_verified_production_caller_name` /
  `_detect_caller_module` / `_PINNED_*` mechanism is **not** the recognition
  predicate under HPAC-PAWA-001 v2.0; consumer authenticity is the
  out-of-process conjunction (§3, §7, §10; HPAC-PAWA-001 v2.0 §32 / §33 step 9).
- **PAWAH-INV-7.** **No second trust root.** The one trust root is OS filesystem
  write authority over `<HPAC_PROTECTED_ROOT>`; the helper registration is an
  integrity-pinned artifact of the existing kind, not a new bootstrap authority
  (§3, HPAC-PAWA-001 HPAC-PAWA-REQ-300).
- **PAWAH-INV-8.** **Human authentication / approval / PB / runtime / effect
  semantics remain distinct.** OS peer credential ≠ human identity ≠ human
  approval; helper execution ≠ human approval; operation admission ≠ human
  approval; typed result ≠ human approval; ceremony entry ≠ APPROVE / Gate 5 /
  PB permission / execution (§10, §14.2, §16; HPAC-PAWA-001 §68 / §68A / §68B).
- **PAWAH-INV-9.** **The design requires no durable bearer secret in any
  process.** Request authenticity rests on the private one-shot channel + OS
  peer credentials + the per-request CSPRNG nonce + exact request/response
  binding + the helper's own §33 recognition — "no new signing key is required
  or implied" (HPAC-PPA-REQ-037). If a future variant needs a secret, the main
  interpreter still never receives it, and it is generated / stored under
  `<HPAC_PROTECTED_ROOT>` admin-owned / agent-unreadable (`TB-ARCH` §17).
- **PAWAH-INV-10.** **Consumed one-shot authority cannot be replayed after
  response loss, and a helper restart does not revive spent authority.** Once a
  one-shot operation crosses `MUTATION_ATTEMPT_STARTED` its `(request_id,
  nonce)` is spent; the helper process (and any authority it held) is gone at
  exit; a fresh launch re-runs the entire recognition (§19, §20, §21).
- **PAWAH-INV-11 (v2.0).** **Helper-scoped writer authority never crosses the
  helper process boundary and is unreachable before `OPERATION_ADMITTED`.**
  Specialization of PAWAH-INV-1 for the §30A mint pathway: it is minted after,
  never before, the request's own admission, and is consumed and discarded
  entirely within the minting helper process (§30A.2).
- **PAWAH-INV-12 (v2.0).** **Helper-scoped writer authority is a strict
  operation-closed subset of one closed helper operation.** The §119 mint-time
  closed enum (operation, mutation subtype, role, subject) makes cross-
  operation reuse mechanically impossible, not merely undocumented (§30A.2).
- **PAWAH-INV-13 (v2.0).** **Certification writer authority from the new
  pathway is bound to exactly one closed certification role.** A capability
  minted for role R cannot satisfy a store check gated on a different role
  (§30A.3, HPAC-PAWA-HELPER-REQ-125).
- **PAWAH-INV-14 (v2.0).** **Presentation-evidence writer authority from the
  new pathway can create exactly one evidence record**, bound to the exact
  ceremony `(invocation_id, attempt_id)` of the admitted request; the
  underlying store write remains create-only and non-forgeable-approval
  (§30A.3, HPAC-PAWA-HELPER-REQ-127).
- **PAWAH-INV-15 (v2.0).** **The new pathway cannot install executable bytes,
  `chmod`/`chown` arbitrary files, or mutate an arbitrary protected-root
  path.** Its `admin_mutation` binding covers only the existing bounded
  metadata-registration mutation classes; it is not a generic broker
  (§30A.3/§30A.5, HPAC-PAWA-HELPER-REQ-128/133).
- **PAWAH-INV-16 (v2.0).** **The new pathway is restart-dead.** The seal and
  the process-local issuance registry are process memory only; a helper
  restart destroys both, and no capability, seal reference, or mint record
  is ever persisted to disk, replay store, audit, cache, or environment
  (§30A.2, HPAC-PAWA-HELPER-REQ-123/124).
- **PAWAH-INV-17 (v2.0).** **No second protected trust root is introduced.**
  The new pathway reuses the sole existing trust root and the existing
  `HPACStoreAuthority`/`HPACWriterCapability` primitives via a second,
  strictly narrower seal; it adds no bootstrap authority, persistent record,
  environment variable, or privileged file (§30A.5, HPAC-PAWA-HELPER-REQ-132).
- **PAWAH-INV-18 (v2.0).** **A failure to derive helper-scoped writer
  authority never falls back to the legacy in-process factory.** Failure is
  terminal for that request; the caller reconciles or issues a fresh request,
  exactly as for any other mutating-operation failure — there is no implicit
  dual-authority fallback (§30A.8, HPAC-PAWA-HELPER-REQ-140).

## 30. Versioning and evolution rules

- **HPAC-PAWA-HELPER-REQ-106.** HPAC-PAWA-HELPER-001 uses contract
  `MAJOR.MINOR`. **v1.0 is the initial freeze.** Unknown versions fail closed.
  An implementation running under v1.0 SHALL require the v1.0 artifacts and
  SHALL NOT silently accept a record or protocol version it does not recognize.
- **HPAC-PAWA-HELPER-REQ-107.** A change that does **any** of the following
  requires a new **MAJOR** plus explicit human authorization and independent
  verification: introducing a persistent helper / daemon / service or a
  cross-request authority state; introducing a network / socket-over-TCP /
  remote / browser / headless transport; making any request, response, evidence,
  or read result a bearer / durable / serialisable / reusable authority;
  allowing a caller-selected helper, path, operation-by-name, response, writer
  role, or authority class; introducing a generic / free-form / wildcard
  operation or `operation_params` payload; exporting **any** authority object,
  handle, seal, or reconstructable capability field set to the launcher or the
  main interpreter; adding a second trust root, a bootstrap authority, or a
  bearer secret the main interpreter can receive; merging the helper protocol
  with human authentication, the human-APPROVE election, PB permission, runtime
  capability, dispatch, or execution authority; weakening the peer-credential
  requirement, the same-file-object exec property, or the two-principal-topology
  fail-closed; adding a certification role by wildcard / prefix / arbitrary
  argument; or authorizing a launcher / consumer not already enumerated by
  HPAC-PAWA-001 §38 / §38A / §38B.
- **HPAC-PAWA-HELPER-REQ-108.** A **MINOR** may: re-state verified behaviour;
  add a platform profile (§17) that realizes every §16 frozen property with no
  re-meaning; add one explicitly enumerated, typed, bounded operation id or
  `operation_params` field per §55 (never generic / wildcard, consumed only by
  an already-enumerated HPAC-PAWA-001 consumer, firing no §107 or HPAC-PAWA-001
  §152 MAJOR trigger); add a failure mapping onto an **existing**
  `pawa_failure_code` without re-meaning an existing outcome; tighten (never
  loosen) a bound; or clarify an implementation-profile detail — **provided no
  meaning above changes**.
- **HPAC-PAWA-HELPER-REQ-109.** No future version may retrospectively widen an
  already-admitted operation's scope, an already-registered helper's authority,
  an already-issued read result, or an already-written evidence record.

## 30A. Helper-scoped writer-authority derivation (v2.0)

This section is the v2.0 MAJOR addition. It closes the blocker documented in
`src/pcae/core/hpac_pawa_helper_store_adapter.py`'s module docstring
(N16-5-F-5-TB-REAL-HELPER-STORE-LAUNCHER-IMPL / -IV): under v1.0, the helper
had **no code path** to obtain `PRODUCTION`-class write authority against any
canonical store, because the sole existing mint primitive,
`HPACStoreAuthority._mint_production_writer_capability` (`pcae.core.hpac_foundation`),
is gated by the single module-level seal `_PRODUCTION_WRITER_FACTORY_SEAL`,
held exclusively by `pcae.core.hpac_protected_admin_writer`, which
HPAC-PAWA-HELPER-REQ-033 forbids the helper to import. This section freezes
the **narrow, second, helper-scoped mint pathway** that resolves that blocker
without importing the legacy factory, without importing or referencing
`_PRODUCTION_WRITER_FACTORY_SEAL`, and without widening `HPACWriterCapability`
into general protected-writer authority.

### 30A.1 Model comparison and selection

- **HPAC-PAWA-HELPER-REQ-115.** Four candidate models were evaluated:

  | Model | Description | Disposition |
  |---|---|---|
  | **A** — helper-local scoped capability mint | helper constructs an unexportable, operation-scoped authority object after admission, accepted only by exact canonical store methods | subsumed by D — the existing `HPACWriterCapability` / `HPACStoreAuthority` primitives already provide exactly this shape (role/subject binding, single-use, non-serializable); a bespoke parallel object type would duplicate `require_writer` / `record_write` / the process-local issuance registry for no security gain |
  | **B** — helper-only mutation facades | canonical stores expose helper-specific narrow entrypoints whose authority is established by trusted helper execution context rather than a capability object | **rejected** — requires new store-layer entrypoints on every canonical store the three blocked operations touch (`HumanPrincipalRegistryStore`, `HpacRhampCredentialSidecarStore`, `ProtectedPresentationInstallationStore`, `PresentationMechanismDescriptorStore`, `TrustedApprovalPresentationStore`, `HpacRhampCounterStateStore`), each requiring its own bespoke "am I called from the helper" check — larger semantic surface, harder to reason about uniformly, and drops the existing single-choke-point `require_writer` / `record_write` / process-local issuance-registry defense that already defends against forged / copied / reconstructed capabilities (HPAC-PAWA-REQ-102/106/107 history, §5 of this analysis) |
  | **C** — store-local internal authority constructor | each canonical store mints its own process-local permit from an already-verified helper admission context | **rejected** — duplicates the mint logic once per store (six-plus call sites vs. one), multiplies the attack surface for a forged "am I in helper context" check, and still has to answer the exact same question Model D answers in one place: how does a mint call prove `PRODUCTION`-class, helper-admitted, operation/role-scoped authority without importing the legacy factory |
  | **D** — evolved `HPACWriterCapability` | the existing writer-capability type is minted through a **second, narrower, additive** low-level primitive on `HPACStoreAuthority`, sibling to `_mint_production_writer_capability`, gated by a **new, distinct** seal owned exclusively by a new helper-only module | **SELECTED** |

- **HPAC-PAWA-HELPER-REQ-116.** **Selection rationale.** `HPACWriterCapability`
  already has every property this evolution needs: `__reduce__` raises
  `TypeError` (non-serializable, §24/PAWAH-INV-1 pattern); `role` / `subject`
  binding; `_single_use` / `_spent` (single-consumption); `_multi_write`
  (bounded multi-artifact transactions, e.g. `enroll_credential`); recognition
  by `HPACStoreAuthority.require_writer` / `record_write` keyed on **seal
  identity** (`getattr(writer, "_authority_seal", …) is self._seal`) **plus**
  process-local issuance-registry membership (`_lookup_issued_capability`) —
  not on which of the two mint entrypoints produced it. Consequently: **zero
  canonical-store code changes** are required (§25 minimum-semantic-surface
  discipline) — `require_writer` and `record_write` already accept any
  properly-issued `HPACWriterCapability` regardless of mint entrypoint. Model
  D is the only candidate that resolves the blocker with no store-layer
  change, one new low-level primitive, and full reuse of the existing
  forgery/reconstruction defenses (HPAC-PAWA-REQ-102/106/107 history).

### 30A.2 The new mint pathway — normative definition

- **HPAC-PAWA-HELPER-REQ-117.** A new low-level primitive,
  `HPACStoreAuthority._mint_helper_scoped_writer_capability`, is authorized —
  **specification only; not authored in this contract-only phase** (§31
  discipline) — as a sibling to `_mint_production_writer_capability`
  (`pcae.core.hpac_foundation`), with the same call shape
  (`role, subject, *, _factory_seal, multi_write=False`) plus the additive
  closed-vocabulary binding fields of HPAC-PAWA-HELPER-REQ-119.
- **HPAC-PAWA-HELPER-REQ-118.** **New, distinct seal.** A new module-level
  singleton, provisionally named `_HELPER_WRITER_FACTORY_SEAL` (`object()`,
  the same construction pattern as `_PRODUCTION_WRITER_FACTORY_SEAL`), is
  defined in `pcae.core.hpac_foundation` and held **exclusively** by a **new**
  helper-only module (provisionally `pcae.core.hpac_pawa_helper_writer_authority`,
  §30A.5). `_HELPER_WRITER_FACTORY_SEAL` **is not, and SHALL NOT be made,**
  the same object as `_PRODUCTION_WRITER_FACTORY_SEAL`; `hpac_protected_admin_writer`
  SHALL NOT import, reference, or gain reachability to
  `_HELPER_WRITER_FACTORY_SEAL`; the reverse import (the new helper-writer-
  authority module importing anything from `hpac_protected_admin_writer`) is
  likewise forbidden (§30A.4 / PAWAH-INV-17). The new mint entrypoint raises
  the existing `HPACAuthorityError` for any `_factory_seal` that is not
  `is _HELPER_WRITER_FACTORY_SEAL` — the identical fail-closed pattern
  `_mint_production_writer_capability` already uses for its own seal.
- **HPAC-PAWA-HELPER-REQ-119.** **Closed operation/role/subtype binding at
  mint time.** The new mint entrypoint SHALL accept only:
  - `operation` — exactly one of `admin_mutation`, `certification_write`,
    `presentation_evidence_write` (the three v1.0-blocked members of §13);
    any other value → `operation_scope_invalid`, no mint;
  - for `admin_mutation`: `mutation` — exactly one member of the closed
    HPAC-PAWA-001 §42/§80.2/§42G mutation-class enum (§14.1 of this contract);
  - for `certification_write`: `role` — exactly one member of the closed
    five-role allowlist (§14.2); `hpac_lifecycle_terminator` and any
    non-member → `operation_scope_invalid`, no mint;
  - for `presentation_evidence_write`: no `role` parameter — the role is the
    single fixed presentation-evidence-writer role (HPAC-PAWA-REQ-248 /
    HPAC-PPA-REQ-041 precedent);
  - `subject` — the exact target id the bound operation requires
    (`principal_id` / `credential_id` / `transaction_id` / `mechanism_id` for
    `admin_mutation`; `proof_id` or `credential_id` per role for
    `certification_write`; the ceremony `invocation_id`/`attempt_id` pair for
    `presentation_evidence_write`) — never a free string, path, or
    caller-selected role name (PAWAH-INV-12).

  Unknown, missing, malformed, or out-of-enum values at any of these fields
  → **fail closed**, `operation_scope_invalid`, no mint, no partial
  capability (PAWAH-INV-12/PAWAH-INV-13/PAWAH-INV-14).
- **HPAC-PAWA-HELPER-REQ-120.** **Mint precondition — post-admission only.**
  The new mint entrypoint SHALL be reachable **only after** the calling
  helper process has independently reached `OPERATION_ADMITTED` (§20) for
  **this** request in **this** process — i.e., after §7 (HPAC-PAWA-001 §33
  steps 1–8, HPAC-PAWA-HELPER-REQ-031), §10 (peer authentication), and §13
  (operation/role/session/subject validation) have all passed for the exact
  request being minted for. A mint attempt before `OPERATION_ADMITTED`, or
  from a process that never independently ran §7/§10/§13, is a **contract
  violation of the calling helper code**, not a property the mint primitive
  itself can enforce by inspecting caller state (the primitive's own
  fail-closed surface is §119/§121/§122; the ordering obligation is a
  normative requirement on the helper implementation, verified by §31's
  future ordering tests, not a runtime assertion inside
  `hpac_foundation`) (PAWAH-INV-11).
- **HPAC-PAWA-HELPER-REQ-121.** **Request, installation, and generation
  binding.** The mint call SHALL additionally require, as caller-supplied
  parameters validated against the live protected root at mint time exactly
  as `_mint_production_writer_capability`'s caller (`production_writer`)
  already validates request/session facts before minting: the bound
  `session_id`, `request_id`, `nonce`, `installation_id`, and `generation` of
  the admitted request. A mint call whose `installation_id` / `generation`
  disagrees with the live current-generation anchor at mint time →
  `descriptor_installation_mismatch` / `descriptor_generation_stale`, no
  mint. This binds the minted capability to **this** request, **this**
  installation lineage, and **this** generation — a capability minted for
  request X cannot be reused, relabelled, or reconstructed for request Y
  (§32 of the phase-authorization prompt).
- **HPAC-PAWA-HELPER-REQ-122.** **Lifetime and consumption.** Every capability
  minted by the new pathway is `single_use=True`. `admin_mutation`'s
  multi-artifact `enroll_credential` transaction reuses the existing
  `multi_write=True` / `complete_multi_write` semantics byte-for-byte
  (HPAC-PAWA-REQ-106/107) — no new transaction model is introduced. There is
  **no** TTL beyond process lifetime plus single-use consumption: the
  capability cannot outlive the one-shot helper process (PAWAH-INV-16), and
  `require_writer` / `record_write` already reject a second use
  (`capability_stale`). No indefinite or reusable authority is created
  (§34/§35 of the phase-authorization prompt).
- **HPAC-PAWA-HELPER-REQ-123.** **Process-locality and store recognition —
  unchanged.** `HPACStoreAuthority.require_writer` and `record_write` are
  **not modified** by this evolution: they continue to key acceptance on
  `self._seal` identity plus process-local issuance-registry membership
  (`_lookup_issued_capability`), independent of which of the two mint
  entrypoints produced the capability. A capability minted by the new
  pathway is, to every canonical store, an ordinary properly-issued
  `HPACWriterCapability` — this is precisely why zero store-layer changes are
  required (§30A.1). Restart-dead: the seal object and the issuance registry
  are process memory; a helper restart destroys both (PAWAH-INV-16).
- **HPAC-PAWA-HELPER-REQ-124.** **No export, no persistence.** The
  HPAC-PAWA-HELPER-REQ-091/092/093 (§24) and PAWAH-INV-1 no-export rule
  applies identically to a capability minted by the new pathway: it SHALL
  NOT cross the channel, appear in a response field, be logged, be staged in
  the §22 audit record, or be written to any file, cache, or environment
  variable. It is consumed by exactly one `record_write` (or one bounded
  `complete_multi_write` transaction) inside the same helper process that
  minted it, then discarded at process exit (PAWAH-INV-11/PAWAH-INV-16).

### 30A.3 Per-family scoping guarantees

- **HPAC-PAWA-HELPER-REQ-125.** **Certification-role mechanical exclusivity.**
  A capability minted for `certification_write` with `role = R` carries
  `role = R` in its existing `role` slot; the per-role store methods already
  validate the presented capability's `role` against the exact store action
  (this is existing store-layer behaviour, unchanged — §14.2/§42B). A
  capability minted for role `hpac_challenge_coordinator` therefore
  mechanically cannot satisfy a store method gated on
  `hpac_gate5_binder`, and vice versa, for any of the five roles
  (PAWAH-INV-13; threat #4/#27/#28 of §37).
- **HPAC-PAWA-HELPER-REQ-126.** **`admin_mutation` subtype exclusivity.** A
  capability minted for `mutation = M` carries the exact scoped `role` /
  `subject` the existing §42 per-mutation store call already requires for
  `M` (e.g. the registry-writer role bound to a `principal_id` for
  `enroll_principal`, the presentation-installer role bound to a
  `mechanism_id` for `configure_presentation_mechanism`) — no broader "any
  admin mutation" authority is ever minted; the mint call's own §119 closed
  enum is the enforcement point, not a post-hoc filter (§19 of the
  phase-authorization prompt; PAWAH-INV-12).
- **HPAC-PAWA-HELPER-REQ-127.** **Presentation-evidence create-only /
  single-purpose.** A capability minted for `presentation_evidence_write` is
  bound to the exact ceremony `(invocation_id, attempt_id)` of the admitted
  request (§119); the target record path is the existing HPAC-REQ-093
  create-only path derived from that binding — the existing
  `HPAC-PRESENTATION-EVIDENCE/2.0` store write is already create-only
  (fails on an existing record) and already rejects a request that
  self-asserts `approved` / `verified` / `human_present` / `authenticated`
  (HPAC-PAWA-HELPER-REQ-071, unchanged). This evolution supplies **only** the
  missing writer authority; the create-only, non-overwrite, non-forgeable-
  approval semantics are unchanged (§22/§23 of the phase-authorization
  prompt; PAWAH-INV-14).
- **HPAC-PAWA-HELPER-REQ-128.** **Helper-installation authority excluded.**
  The new mint pathway's `admin_mutation` binding covers
  `configure_privileged_helper` **only** to the extent HPAC-PAWA-001 §42/§80.2
  already bounds it — the existing bounded metadata-registration mutation
  (§6 of this contract). It grants **no** authority to install, replace,
  `chmod`, `chown`, or otherwise mutate the helper executable bytes
  themselves, and no authority over any path outside the closed §57
  `operation_params` struct for that mutation (§20/§42 of the
  phase-authorization prompt; PAWAH-INV-15).

### 30A.4 REQ-033 disposition (Option B — narrow, additive clarification)

- **HPAC-PAWA-HELPER-REQ-129.** HPAC-PAWA-HELPER-REQ-033's own text is
  **unchanged** — no MAJOR/MINOR re-meaning of an existing requirement
  (§30/HPAC-PAWA-HELPER-REQ-108's "without re-meaning an existing outcome").
  This requirement is an **additive clarification** (phase-authorization
  §40 Option B) of REQ-033's already-precise scope, made necessary because
  this evolution is the first case where the exact boundary matters
  operationally:
  1. `pcae.core.hpac_foundation` — the shared module defining
     `HPACWriterCapability`, `HPACStoreAuthority`, and their low-level
     primitives — is **not** "the in-process PAWA factory module" REQ-033
     names (that name refers exclusively to
     `pcae.core.hpac_protected_admin_writer`). `hpac_foundation` is already
     imported by the v1.0-approved, independently-verified
     `hpac_pawa_helper_store_adapter.py` and `hpac_pawa_helper_entrypoint.py`
     — direct repository evidence that importing it for the closed type
     surface does not, and never did, violate REQ-033. This clause makes
     that reading **explicit** rather than leaving it to be re-derived by
     every future reader.
  2. `_PRODUCTION_WRITER_FACTORY_SEAL` (`pcae.core.hpac_foundation`) is
     **explicitly, additionally named** as forbidden to the helper: the
     helper SHALL NOT `import`, reference, alias, copy, or otherwise gain a
     reference to that exact object, by any path. Reusing it would mint
     **unrestricted-role** legacy authority — precisely the "second
     general-purpose factory" the phase-authorization prompt (§12) treats
     as presumptively unacceptable — and would defeat this entire evolution's
     narrowing guarantees (§119/§125/§126/§127).
  3. The new mint pathway (§30A.2) lives in a **new** module (§30A.5), gated
     by a **new**, distinct seal, never shared with, imported by, or
     importing from `hpac_protected_admin_writer`. It realizes exactly the
     "helper-local code … that loads no attacker-controllable code" REQ-033
     already anticipates for the §7 recognition logic, extended by this
     evolution to the writer-authority-derivation logic for the three
     v1.0-blocked operations only.
- **HPAC-PAWA-HELPER-REQ-130.** **§30 MAJOR-trigger enumeration gap closed.**
  HPAC-PAWA-HELPER-REQ-107 is extended, additively, with one further MAJOR
  trigger for future evolutions: *introducing any new internal writer-
  authority derivation / mint mechanism, even if narrowly scoped, closed-
  vocabulary-bound, and never exported* is a **MAJOR** change requiring
  explicit human authorization and independent verification. (This closes,
  for the future, the exact classification question this v2.0 evolution
  itself had to resolve by analogy to the HPAC-PAWA-001 v1.4→v2.0 precedent
  rather than by a literal REQ-107/REQ-108 bullet.)

### 30A.5 Module ownership and no-second-trust-root

- **HPAC-PAWA-HELPER-REQ-131.** The new low-level mint primitive
  (`_mint_helper_scoped_writer_capability`) is owned by
  `pcae.core.hpac_foundation` (the existing shared authority-primitives
  module — sibling to `_mint_production_writer_capability`, same class,
  same file). The new seal (`_HELPER_WRITER_FACTORY_SEAL`) is likewise
  defined in `hpac_foundation`. The new **caller** of that primitive — the
  module that holds the seal and invokes the mint with the §119/§121
  bindings derived from the helper's own already-completed §7/§10/§13
  recognition — is a **new**, helper-only module (provisionally
  `pcae.core.hpac_pawa_helper_writer_authority`), imported **only** by the
  privileged one-shot helper's own dispatch code (§7 of this contract), never
  by `hpac_protected_admin_writer`, never by any agent-reachable module,
  never by the launcher (§26 threat model). This is a **specification for
  the implementation phase** (§31 discipline) — no such module is created by
  this contract-only phase.
- **HPAC-PAWA-HELPER-REQ-132.** **No second trust root (PAWAH-INV-17).** The
  new mint pathway introduces no new bootstrap authority, no new persistent
  record, no new environment variable, and no new privileged file. It is a
  second **entrypoint** into the one already-existing `HPACStoreAuthority` /
  `HPACWriterCapability` primitive pair, gated by a second seal that is
  strictly narrower in what it can mint (§119's closed enum vs.
  `_mint_production_writer_capability`'s arbitrary `role: str`). The sole
  trust root remains OS filesystem write authority over
  `<HPAC_PROTECTED_ROOT>` (§3, unchanged).
- **HPAC-PAWA-HELPER-REQ-133.** **No generic broker (PAWAH-INV-15).** The new
  mint entrypoint's signature is itself a closed enum surface (§119); it
  cannot be composed into an arbitrary store writer, an arbitrary filesystem
  writer, an arbitrary Python executor, or an operation-vocabulary extension
  mechanism — every one of the prohibitions in §25 of this contract applies
  identically to capabilities minted by the new pathway, which is why no new
  prohibition text is required there.

### 30A.6 Replay ordering, currentness, and no-auto-retry (unchanged, reaffirmed)

- **HPAC-PAWA-HELPER-REQ-134.** **Replay-ordering placement.** The new mint
  call is placed strictly between `OPERATION_ADMITTED` and
  `MUTATION_ATTEMPT_STARTED` in the §20 state model:

  ```
  REQUEST_RECEIVED -> REQUEST_AUTHENTICATED -> OPERATION_ADMITTED
    -> [helper-scoped writer capability minted, this section]
    -> MUTATION_ATTEMPT_STARTED -> MUTATION_COMMITTED -> EVIDENCE_WRITTEN -> RESPONSE_EMITTED
  ```

  A mint attempted outside this window (before `OPERATION_ADMITTED`, or a
  second mint attempt after `MUTATION_ATTEMPT_STARTED` for the same
  request) → fail closed, `capability_stale` / `operation_scope_invalid`
  (§119/§121 already reject a stale/duplicate request binding; no new
  failure code is required — see HPAC-PAWA-HELPER-REQ-137).
- **HPAC-PAWA-HELPER-REQ-135.** **Currentness after mint.** If the
  installation/generation anchor rotates between mint and the store write
  (§18/§19 of this contract remain the authority for this), the existing
  canonical-store write path's own currentness checks (unchanged by this
  evolution) reject the write; the mint call's own §121 binding does not
  itself re-check currentness a second time at write time — that remains
  the existing store/record layer's responsibility, exactly as it is today
  for a legacy-minted capability (§33 of the phase-authorization prompt).
- **HPAC-PAWA-HELPER-REQ-136.** **No-auto-retry preserved.** §20–§23 of this
  contract are unaffected: a spent single-use capability from the new
  pathway cannot be reused for a retry; the caller reconciles against the
  durable protected-root evidence exactly as for every other mutating
  operation (§36 / §37 of the phase-authorization prompt).
- **HPAC-PAWA-HELPER-REQ-137.** **Failure-code mapping — no new code.** Every
  new failure mode introduced by this section maps onto the **existing** 21
  `pawa_failure_code` values, with **no** new code added (REQ-004 preserved):
  scoped-authority derivation denied at mint (§119 closed-enum violation) →
  `operation_scope_invalid`; role/subtype mismatch at mint or at store-write
  time → `target_scope_invalid`; a consumed / re-presented capability →
  `capability_stale`; a stale helper context (installation/generation
  disagreement at mint time, §121) → `descriptor_installation_mismatch` /
  `descriptor_generation_stale`; an internal mint-primitive invariant
  failure (e.g. a non-`PRODUCTION` authority class reaching the mint call)
  → `internal_fail_closed`.

### 30A.7 Deterministic-vs-real separation (reaffirmed)

- **HPAC-PAWA-HELPER-REQ-138.** The new mint entrypoint requires
  `self.authority_class is HPACAuthorityClass.PRODUCTION`, identical to
  `_mint_production_writer_capability`'s own existing check. A
  `FIXTURE_NON_REAL`-class `HPACStoreAuthority` — the only class a
  deterministic test / fixture helper context can ever hold — SHALL raise
  `HPACAuthorityError` and mint nothing. A deterministic test helper
  therefore remains **permanently unable** to obtain real writer authority
  through either mint entrypoint (§26.1 of this contract, HPAC-PAWA-HELPER-
  REQ-095/097, unchanged).

### 30A.8 Cross-contract impact and two-path coexistence

- **HPAC-PAWA-HELPER-REQ-139.** **HPAC-PAWA-001 v2.0 and HPAC-PPA-001 v2.0
  remain byte-unchanged.** Per HPAC-PAWA-HELPER-REQ-006, the "authority
  decision" (is this a trusted production consumer) stays owned by
  HPAC-PAWA-001 §32/§33/§33B, unaffected by this section; this evolution
  supplies only the mechanism by which an already-admitted helper operation
  obtains the writer authority HPAC-PAWA-001 §42F/§42G's out-of-process
  delivery model (`HPAC-PAWA-REQ-321`) already describes as happening
  "in its own process" without specifying the low-level primitive — this
  section is that specification, fully contained within
  HPAC-PAWA-HELPER-001's own scope (§1 REQ-005). HPAC-PPA-001's
  `presentation_evidence_write` cross-contract question (§17 of this
  contract, "an explicit question for the dedicated contract IV") is
  **unaffected and unresolved by this section** — it remains a question for
  N16-5-F-5-TB-CONTRACT-IV or its successor.
- **HPAC-PAWA-HELPER-REQ-140.** **Legacy path unchanged; two-path
  coexistence, explicit retirement condition.** The legacy in-process
  `production_writer` / `certification_writer` /
  `mint_protected_presentation_evidence_writer` factories
  (`pcae.core.hpac_protected_admin_writer`) are **not removed, retired, or
  altered** by this contract. During migration, the legacy in-process path
  and the new helper-scoped path **coexist**, but are consumed by disjoint
  principals: the legacy path is reachable only from same-interpreter
  production callers (unchanged, unmigrated); the new path is reachable
  only from the privileged one-shot helper process itself. **No operation
  may fall back from the new helper-scoped path to the legacy in-process
  path on failure** — a helper-scoped mint failure is terminal for that
  request (fail closed per §30A.6), never silently retried against the
  legacy factory (PAWAH-INV-18; §46/§47 of the phase-authorization prompt).
  Retirement of the legacy in-process path is explicitly **out of scope**
  for this phase and requires its own future governed phase, sequenced no
  earlier than: this contract → contract IV → helper writer implementation
  → helper writer implementation IV → typed caller migration (§45 of the
  phase-authorization prompt).


## 30B. Writer-Authority Repair (v3.0): Helper-Process-Isolated Mutation Facades (Model E)

This section is the v3.0 MAJOR addition. It repairs the two defects a fresh
independent verification found in v2.0's §30A (Model D), preserved there
immutably. Section 30A's text above is **not** edited by this section; it
remains the historical record of the specification that was frozen, found
NOT VERIFIED, and is now superseded.

### 30B.1 Predecessor status and defect reconstruction (immutable finding, reproduced verbatim from source)

`docs/PHASE_N16_5_F_5_TB_HELPER_WRITER_AUTHORITY_CONTRACT_IV.md` reached
**COMPLETE — NOT VERIFIED / BLOCKED** on Model D. Its central finding (§7 of
that document), independently source-confirmed against
`src/pcae/core/hpac_foundation.py`:

> `_mint_production_writer_capability` (`hpac_foundation.py:753-780`) … calls
> **none** of `_run_recognition_sequence`, `_detect_caller_module`,
> `_verified_production_caller_name`, or `AUTHORIZED_FACTORY_CONSUMERS` — that
> machinery exists **one layer up**, in `hpac_protected_admin_writer.py`'s
> `production_writer()` factory wrapper, not in the primitive itself. The
> primitive's only caller-facing gate is object-identity equality against
> `_PRODUCTION_WRITER_FACTORY_SEAL`, which is confirmed at
> `hpac_foundation.py:124` to be a **bare, unprotected module-level global**:
> `_PRODUCTION_WRITER_FACTORY_SEAL = object()`. … any ordinary Python code
> that already has `hpac_foundation` imported (which the contract's own
> `HPAC-PAWA-HELPER-REQ-129`/§30A.4 discloses is already true of
> agent-reachable code, since `hpac_foundation` is shared with the
> agent-reachable read-path module `hpac_pawa_helper_store_adapter.py`) can
> read `_PRODUCTION_WRITER_FACTORY_SEAL` via ordinary `getattr` and pass it to
> `_mint_production_writer_capability` directly, skipping the entire §33
> eleven-step recognition sequence.

And its threat-matrix-completeness finding (§15 of that document), quoted
verbatim — the **two clear gaps**:

> 1. **No threat-matrix row addresses "ordinary process invokes the
>    low-level mint primitive directly, bypassing the higher-level factory's
>    recognition sequence"** — the closest rows (row #1, "ordinary caller
>    constructs a scoped authority object directly"; row #22, "ordinary
>    caller influences a helper-local registry/seal") do not cover this
>    distinct attack shape: reading (not influencing) an already-instantiated
>    real seal and calling the mint primitive with it. …
> 2. **No threat-matrix row addresses "role/subject field mutation on an
>    already-legitimately-issued capability by its own holder"** — the actual
>    mitigation for this exists (registry-bound scope dominates mutable
>    fields, §8 above), but no row names the attack.

**HPAC-PAWA-HELPER-REQ-141.** These two defects, and the NOT VERIFIED /
BLOCKED verdict itself, are preserved immutably as the record this repair
answers. This section does not re-litigate whether Model D's specification
text was internally coherent (it was, per the IV's own §1-§14 verdicts) —
only its two identified BLOCKING defects.

**HPAC-PAWA-HELPER-REQ-142.** Model D's mint pathway (`REQ-115` through
`REQ-140`, `PAWAH-INV-11..18`, §30A) remains, as of this repair, **absent**
from `src/pcae/**` (independently re-confirmed by repo-wide grep at repair
time: `_mint_helper_scoped_writer_capability`, `_HELPER_WRITER_FACTORY_SEAL`,
and `hpac_pawa_helper_writer_authority` do not exist anywhere under
`src/pcae/**`). It is **superseded specification history**, not a live
pathway; it SHALL NOT be implemented. A future implementation phase
implements **this** section's Model E hybrid instead.

### 30B.2 Model re-comparison and selection (Model E — hybrid of B and C)

Phase-authorization §12 permits an "other" model (Model E) only if it is
**both stronger and simpler** than a repaired A/B/C/D, by combining B's and
C's strengths. Re-evaluated at repair time, against the root cause identified
above (the failure was **architectural placement** — a same-interpreter
object-identity seal can never be a real trust boundary once attacker-
reachable Python shares that interpreter — not a missing individual check):

| Model | Description | Disposition at repair time |
|---|---|---|
| **A** — helper-local scoped capability mint | (as §30A.1) an unexportable, operation-scoped authority object constructed post-admission | still subsumed; does not by itself address *where* the mint code executes |
| **pure repaired D** — tightened seal + a caller-identity check moved into `_mint_production_writer_capability` itself (the IV's own §19 characterization) | adds a frame/module-provenance check *inside* the primitive, still living in the shared `hpac_foundation` module | **rejected**: this is still an in-process, same-interpreter check — stronger than a bare seal, but still a convention-strength control the phase-authorization's own standard (§13: *"failure must rely on non-forgeable/process-local trust state, not a convention"*) treats as insufficient once the gating code shares a process with attacker-reachable code. It repeats Model D's root-cause mistake at one layer's remove. |
| **pure B** — helper-only mutation facades (canonical stores expose helper-specific entrypoints) alone | (as §30A.1) new store-layer entrypoints per canonical store | **rejected alone**: solves *where the mint call is reachable from* (process boundary) but, without a distinguishing authority type, still hands the store the **same** `HPACWriterCapability` class Model D produced — the store still cannot mechanically tell a helper-scoped from a legacy-broad capability (defect 2 persists) |
| **pure C** — store-local internal authority constructor, one per store | (as §30A.1) each store mints its own permit from a verified helper-admission context | **rejected alone**: gives every capability a distinguishing authority family (closes defect 2) but does not by itself relocate the *mint-eligibility gate* out of a shared, agent-reachable module (defect 1 persists) unless *also* confined to the helper process |
| **E (SELECTED)** — hybrid of B + C: **helper-process-isolated mutation facades**, each minting **and** performing its bounded mutation in one call, entirely inside the already-isolated one-shot helper subprocess (B's placement), where each facade's authority is a distinct, non-shared-base-recognized authority family with an explicit store-side recognition predicate (C's typing) | three narrow, closed, typed facades: `mint_and_perform_admin_mutation`, `mint_and_perform_certification_write`, `mint_and_perform_presentation_evidence_write` | **SELECTED** — closes both defects **simultaneously**: defect 1 by moving mint-eligibility to a real OS-process boundary (not a bigger in-process convention); defect 2 by giving the store a mechanical, non-isinstance way to recognize which pathway produced a capability |

**HPAC-PAWA-HELPER-REQ-143.** **Selection rationale.** Model E is simpler
than a fully generalized Model B (only three facades, not one per canonical
store call site — reusing the existing five-store read enumeration of §15 is
not required because these are write-only facades bound to the exact three
v1.0-blocked operations) and stronger than either B or C alone, because it
answers the phase-authorization's own diagnostic question directly: *"how
does a mint call prove `PRODUCTION`-class, helper-admitted,
operation/role-scoped authority without importing the legacy factory"* — by
(a) never being reachable outside the helper subprocess at all (a hard OS
boundary, not a checkable token) and (b) being typed so the store's
acceptance predicate does not have to trust convention to distinguish it from
legacy authority.

### 30B.3 Mint eligibility and the OS-process trust mechanism

**HPAC-PAWA-HELPER-REQ-144.** **Physical relocation, not a new convention.**
The three facades, their sole seal, and the low-level mint entrypoint they
call are defined in a **new module**, `pcae.core.hpac_pawa_helper_writer_authority`
(the module name provisionally reserved by REQ-131 for a "caller"; under this
repair it is the **exclusive owner of the mint primitive itself**, not merely
its caller — this supersedes REQ-131's Model-D-specific location choice for
the repaired pathway; REQ-131's own text is unchanged, historical). This
module is imported **only** by the privileged one-shot helper's own dispatch
code (`pcae.core.hpac_pawa_helper_operations`'s `CLOSED_DISPATCH_TABLE`, which
already executes exclusively inside the `exec`'d helper child per
HPAC-PAWA-HELPER-REQ-031) — **never** by `pcae.core.hpac_foundation`, **never**
by `pcae.core.hpac_protected_admin_writer`, **never** by any read-path,
CLI, plugin, or runtime module, and **never** by the launcher (§26 threat
model). This is a specification for the implementation phase (§31
discipline); no such module is created by this contract-only repair.

**HPAC-PAWA-HELPER-REQ-145.** **The mint-eligibility boundary is OS-process
absence-of-shared-memory, not an in-process check.** Because the new module
is never imported on any code path reachable from the configured agent
principal's own process, its module-level seal object (an `object()`,
constructed once per process at import time, exactly like
`_PRODUCTION_WRITER_FACTORY_SEAL`) is **never instantiated in, and therefore
never readable from, the agent's own interpreter** — there is no shared
address space across which a `getattr` could ever retrieve it, unlike the
v2.0 defect where the seal-defining module (`hpac_foundation`) was already
loaded in the agent's own process for unrelated (read-path) reasons.
"Ordinary configured-agent Python" is excluded by **literal absence of the
object**, not by a name, a leading underscore, an import-discipline
convention, or a checkable-but-forgeable token. This is the exact standard
phase-authorization §13 requires ("non-forgeable/process-local trust state,
not a convention") and directly repairs defect 1 (§30B.1): there is no
`getattr`-style bypass across a genuine OS process boundary the way there was
across modules sharing one interpreter.

**HPAC-PAWA-HELPER-REQ-146.** **Process-local seal retained, defense-in-depth
only, never the sole boundary (PAWAH-INV-19).** Inside the helper process,
each facade MAY additionally gate its own call into the mint primitive with a
process-local seal — created **fresh per helper-process invocation**, closed
over the facade's own call frame, **never** a module-level global, **never**
exported, and destroyed at process exit. This mirrors defense-in-depth
practice elsewhere in this codebase (e.g. the process-local issuance registry
added to `require_writer` after a bare seal-identity check was found
insufficient, `hpac_foundation.py:825-834`) but is explicitly **not** treated
as sufficient by itself — the primary boundary is §145's OS-process
exclusion, and this contract states that explicitly rather than leaning on
the seal the way v2.0's Model D did (which would repeat Model D's mistake at
a smaller scale, per phase-authorization guidance).

**HPAC-PAWA-HELPER-REQ-147.** **No second trust root (PAWAH-INV-17,
reaffirmed).** The real trust root remains OS filesystem write authority over
`<HPAC_PROTECTED_ROOT>` (§3), re-validated on every mint via `_ensure_root` /
`_validate_production_boundary` exactly as today. Each facade still calls
down into `HPACStoreAuthority` (or a narrowly-scoped sibling construction
path) which still re-checks that boundary; the facade module introduces no
independent root, credential, or bootstrap authority of its own.

### 30B.4 Store recognition mechanism — distinct, non-isinstance authority families

**HPAC-PAWA-HELPER-REQ-148.** **Three new, distinct authority classes.**
`HelperAdminMutationAuthority`, `HelperCertificationWriteAuthority` (closed
over the five-role vocabulary of §14.2 with **no** role wildcard —
PAWAH-INV-13 tightened), and `HelperPresentationEvidenceAuthority` are
specification-only new types (not authored in this contract-only phase),
each constructed **exclusively** by its own facade in the new module (§30B.3)
under that facade's own process-local seal. None subclasses the legacy
`HPACWriterCapability` in a way that would let it satisfy a bare
`isinstance(x, HPACWriterCapability)` check; if a shared base class is used
at all for code reuse (e.g. a common non-serializable-slots mixin), the
store's recognition predicate SHALL use an exact-type or sealed-family check
(`type(x) is HelperCertificationWriteAuthority`, never `isinstance(x,
SharedBase)`), so that neither direction of confusion is possible: a
helper-scoped authority can never satisfy legacy broad-writer recognition,
and a legacy broad writer can never satisfy a helper-scoped recognition
predicate.

**HPAC-PAWA-HELPER-REQ-149.** **Store-side recognition predicates.** Each
authority family has its own explicit recognition predicate —
`recognize_helper_admin_mutation(store, authority, *, mutation, subject)`,
`recognize_helper_certification_write(store, authority, *, role, subject,
session_id)`, `recognize_helper_presentation_evidence_write(store, authority,
*, invocation_id, attempt_id)` — that is **not** a bare
`isinstance(x, HPACWriterCapability)` test and does **not** delegate to
`require_writer`'s existing role/subject-registry check as its *only*
mechanism (though it MAY reuse the existing process-local issuance registry
as an *additional* defense-in-depth layer, exactly as §146 permits for the
seal). This is the mechanical, structural answer to defect 2 (§30B.1): the
store no longer has "no concept of which mint entrypoint produced this
capability" — the **type itself** is the provenance marker, checked at
recognition time, not a decorative field on a shared object.

**HPAC-PAWA-HELPER-REQ-150.** **Target/request/installation-generation/
currentness binding enforced at the recognition predicate.** Each recognition
predicate SHALL check, as explicit fields compared against the live
protected-root state at recognition time (not merely at mint time, closing
the gap that a mint-time-only check would leave to the store layer to
enforce identically to the legacy path per §30A.6): the bound `session_id` /
`request_id` / `nonce`; the `installation_id` and `generation` against the
current-generation anchor; and the exact operation/role/subtype/subject the
authority was minted for. Any mismatch → the existing `pawa_failure_code`
mapping (§30B.7), never a partial or best-effort acceptance.

**HPAC-PAWA-HELPER-REQ-151.** **No shared-base `isinstance` escape
(PAWAH-INV-20).** A capability minted for `certification_write` role R (type
`HelperCertificationWriteAuthority`) cannot satisfy
`recognize_helper_admin_mutation`, `require_writer` (the legacy path), or any
other family's predicate, because acceptance requires an exact-type match,
not a shared ancestor. This directly answers the IV's characterization of
Model D's own capability shape as "classification D … same runtime class with
a different provenance, indistinguishable to the store" (§30B.1) — the
repaired design is classification **A/B** from the IV's own §10 list (a
genuinely distinguishable type), not classification D.

### 30B.5 Per-operation facade specification

**HPAC-PAWA-HELPER-REQ-152.** Each facade both **mints and performs** its
exact bounded mutation in **one call**, entirely within the helper subprocess
— there is **no** generic `helper_write(store, method, args)` broker (banned
identically to §25 / PAWAH-INV-15). `operation_params` for each facade is the
**same closed typed struct** already frozen by §57 (admin mutations) / §14.2
(certification roles) / §17 (presentation evidence) — no new field, no new
shape, no wire-visible change (consistent with the "external vocabulary
unchanged" versioning premise of §30B.9).

**HPAC-PAWA-HELPER-REQ-153.** `mint_and_perform_admin_mutation(mutation,
subject, *, session_id, request_id, nonce, installation_id, generation)`
mints a `HelperAdminMutationAuthority` scoped to exactly one member of the
closed §57 mutation enum and performs that one HPAC-PAWA-001 §42 mutation
class, identically in effect to §14.1's existing description, through the
same canonical stores' writer-transaction semantics.

**HPAC-PAWA-HELPER-REQ-154.** `mint_and_perform_certification_write(role,
subject, *, session_id, request_id, nonce, installation_id, generation)`
mints a `HelperCertificationWriteAuthority` scoped to exactly one member of
the closed five-role allowlist (§14.2 — `hpac_lifecycle_terminator` is still
explicitly not a member) and performs that one HPAC-PAWA-001 §42B per-role
bounded action.

**HPAC-PAWA-HELPER-REQ-155.** `mint_and_perform_presentation_evidence_write(
invocation_id, attempt_id, *, session_id, request_id, nonce, installation_id,
generation)` mints a `HelperPresentationEvidenceAuthority` scoped to the exact
ceremony `(invocation_id, attempt_id)` and performs the one create-only
`HPAC-PRESENTATION-EVIDENCE/2.0` write after one valid `APPROVE`
(HPAC-PAWA-HELPER-REQ-070/071/072 unchanged).

**HPAC-PAWA-HELPER-REQ-156.** **Certification-role mechanical exclusivity
(restated for the new family, PAWAH-INV-13 tightened).** A
`HelperCertificationWriteAuthority` minted for role R carries `role = R`
immutably (no caller-reachable setter); `recognize_helper_certification_write`
rejects any role mismatch. Mirrors and tightens REQ-125.

**HPAC-PAWA-HELPER-REQ-157.** **`admin_mutation` subtype exclusivity
(restated).** A `HelperAdminMutationAuthority` minted for `mutation = M`
carries exactly the scoped subject the existing §42 per-mutation store call
requires for `M`; no broader "any admin mutation" authority is ever minted.
Mirrors and tightens REQ-126.

**HPAC-PAWA-HELPER-REQ-158.** **Presentation-evidence create-only /
single-purpose (restated).** Unchanged from REQ-127; the
`HelperPresentationEvidenceAuthority` adds only the missing writer authority,
never altering the existing create-only / non-forgeable-approval semantics.

**HPAC-PAWA-HELPER-REQ-159.** **Helper-installation authority excluded
(restated).** Unchanged from REQ-128: the `admin_mutation` facade's
`configure_privileged_helper` binding covers only the existing bounded
metadata-registration mutation — no authority to install, replace, `chmod`,
`chown`, or otherwise mutate helper executable bytes.

### 30B.6 Replay ordering, currentness, and no-auto-retry — reuse, not reinvention

**HPAC-PAWA-HELPER-REQ-160.** **Replay-ledger integration.** Each facade's
post-mint consumption step SHALL plug into the **same** durable, cross-process
replay reservation-then-commit protocol already implemented in
`src/pcae/core/hpac_pawa_helper_replay_state.py` for read operations (the
`(installation_id, generation, request_id, nonce)`-keyed reservation records
under `<HPAC_PROTECTED_ROOT>/pawa-helper/`) — **no parallel replay mechanism**
is introduced for the new write facades (PAWAH-INV-24). The mint call is
placed identically to §30A.6's placement, strictly between
`OPERATION_ADMITTED` and `MUTATION_ATTEMPT_STARTED`:

```
REQUEST_RECEIVED -> REQUEST_AUTHENTICATED -> OPERATION_ADMITTED
  -> [replay reservation via hpac_pawa_helper_replay_state, this section]
  -> [facade mint-and-perform, §30B.5]
  -> MUTATION_ATTEMPT_STARTED -> MUTATION_COMMITTED -> EVIDENCE_WRITTEN -> RESPONSE_EMITTED
```

**HPAC-PAWA-HELPER-REQ-161.** **Currentness (restated, unchanged
responsibility split).** Identically to REQ-135: if the installation/
generation anchor rotates between the facade's mint-and-perform call and the
canonical-store write's own currentness check, the existing store/record
layer's own check (unchanged) rejects the write; the facade's own §150
binding does not re-check currentness a second time at store-write commit.

**HPAC-PAWA-HELPER-REQ-162.** **No-auto-retry preserved (restated).**
Identically to REQ-136: a spent single-use facade-minted authority cannot be
reused for a retry; the caller reconciles against durable protected-root
evidence exactly as for every other mutating operation.

**HPAC-PAWA-HELPER-REQ-163.** **Failure-code mapping — no new code
(restated, extended).** Every new denial mode this section introduces maps
onto the **existing** 21 `pawa_failure_code` values: authority-family type
mismatch at recognition (§149) → `target_scope_invalid`; a mint attempt
outside the §160 replay window → `capability_stale`; closed-enum violation
at mint (§150/§119-equivalent) → `operation_scope_invalid`; installation/
generation disagreement at mint → `descriptor_installation_mismatch` /
`descriptor_generation_stale`; an internal facade invariant failure (e.g. a
non-`PRODUCTION` authority class reaching a facade) → `internal_fail_closed`.
No new `pawa_failure_code` is added (REQ-004 preserved).

### 30B.7 Deterministic-vs-real separation (reaffirmed)

**HPAC-PAWA-HELPER-REQ-164.** Each facade requires
`self.authority_class is HPACAuthorityClass.PRODUCTION` before minting,
identical in spirit to `_mint_production_writer_capability`'s own check. A
`FIXTURE_NON_REAL`-class authority — the only class a deterministic test
helper context can ever hold — SHALL raise and mint nothing through any of
the three facades. Restates REQ-138 for the new family.

### 30B.8 Two-path coexistence and no-fallback (extended)

**HPAC-PAWA-HELPER-REQ-165.** **Legacy path and superseded Model D both
remain not implemented / not to be implemented.** The legacy in-process
`production_writer` / `certification_writer` /
`mint_protected_presentation_evidence_writer` factories
(`pcae.core.hpac_protected_admin_writer`) are **not removed, retired, or
altered** by this repair (unchanged from REQ-140). Model D's specification
(§30A) is superseded and MUST NOT be implemented (§30B.1). The **only**
forward-authorized new pathway is this section's Model E hybrid.

**HPAC-PAWA-HELPER-REQ-166.** **No fallback on facade failure
(PAWAH-INV-23).** A facade mint-and-perform failure is **terminal** for that
request; the caller reconciles or issues a fresh request exactly as for any
other mutating-operation failure. There is no implicit fallback to the
legacy in-process factory and no implicit fallback to an ad hoc
reimplementation of Model D's superseded specification. Extends PAWAH-INV-18
to name the superseded pathway explicitly.

### 30B.9 Versioning rationale — why v3.0, not v2.1

**HPAC-PAWA-HELPER-REQ-167.** Considered purely against the external-surface
MINOR criteria of §108 (a bounded addition, no wire schema change, no new
operation id, no new failure code, consumed only by already-enumerated
consumers), this repair would be MINOR-shaped: §11-§17's wire schemas, the
three operation ids, the five certification roles, the three admin-mutation
subtypes, and the `pawa_failure_code` mapping are all byte-unchanged.
**However**, HPAC-PAWA-HELPER-REQ-130 (added by v2.0 specifically to close
this future classification question) states, without qualification, that
*"introducing any new internal writer-authority derivation / mint mechanism,
even if narrowly scoped, closed-vocabulary-bound, and never exported, is a
MAJOR change requiring explicit human authorization and independent
verification."* This repair does exactly that (it replaces Model D's
specification with Model E's). REQ-130 is a literal, already-frozen,
unconditional trigger — honoring it is more conservative and more faithful to
this repository's evolution discipline than re-deriving a MINOR classification
from the external-surface criteria alone. **Decision: v2.0 -> v3.0, MAJOR.**

**HPAC-PAWA-HELPER-REQ-168.** No `src/pcae/**` code exists implementing
either Model D or Model E as of this repair (confirmed by repo-wide grep,
§30B.1); this MAJOR version bump governs a **specification** change only,
identically in scope to how v1.0 -> v2.0 governed a specification-only MAJOR
change (§30A).

### 30B.10 PAWA and PPA cross-contract impact adjudication

**HPAC-PAWA-HELPER-REQ-169.** **HPAC-PAWA-001 remains v2.0, byte-unchanged**
by this repair. The authority decision ("is this a trusted production
consumer?") stays owned by HPAC-PAWA-001 §32/§33/§33B (REQ-006, unchanged);
this repair supplies only a corrected mechanism for the *derivation* of
writer authority *after* that decision, fully contained within
HPAC-PAWA-HELPER-001's own delegated scope. No trust-predicate or authority-
family concept HPAC-PAWA-001 itself defines is altered, widened, or narrowed
by this section — the three new authority-family types are internal to
HPAC-PAWA-HELPER-001's own mechanism layer. **Finding: no HPAC-PAWA-001
evolution needed.**

**HPAC-PAWA-HELPER-REQ-170.** **HPAC-PPA-001 remains v2.0, byte-unchanged**
by this repair. §17's open cross-contract question (whether
`presentation_evidence_write`'s authority-derivation location is within
HPAC-PPA-REQ-041/070's existing bounds, or needs a fresh HPAC-PPA-001
evolution) is **unaffected and unresolved by this section** — it remains
exactly the question §17 already assigns to a dedicated contract IV
(N16-5-F-5-TB-CONTRACT-IV or its successor). This repair's
`HelperPresentationEvidenceAuthority` facade (§30B.5) changes only *where the
mint primitive is defined and what type it produces*, not *which process
performs the write* (already the out-of-process presentation helper, per
HPAC-PPA-001 §6/§7, unchanged) — so it does not itself newly bear on that
open question either way. **Finding: no HPAC-PPA-001 evolution needed by this
repair; the pre-existing open question is explicitly carried forward, not
silently dropped, per phase-authorization §56/§57's "if a trust predicate or
authority family changes leak upward, evolve narrowly" discipline — this
repair concludes no such leak occurs.**

### 30B.11 Threat matrix (v3.0 — merged and extended; §44 of the phase-authorization prompt)

Rows 1-30 are reproduced unchanged from the v2.0 architecture record
(`docs/PHASE_N16_5_F_5_TB_HELPER_WRITER_AUTHORITY_CONTRACT_ARCH.md` §10) —
every mitigation cited there for "all"/"A/D"/"D" models applies identically
to the Model E hybrid, since Model E reuses the same `HPACWriterCapability`-
family primitives (`__reduce__`, `__slots__`, single-use/`_spent`, the
existing response schema) for its own new authority types. Rows 31-40 are new
to this repair: rows 31-32 close the two predecessor-IV gaps (§30B.1); rows
33-40 name the attack shapes the Model E hybrid architecture itself
introduces and must defend. **Final count: 40** — the ≥36 floor of
phase-authorization §44 is met by 30 inherited + 2 predecessor-gap closures +
8 architecture-specific rows the hybrid design newly requires (process-
boundary-as-primary-vs-seal-as-defense-in-depth split; per-family
non-isinstance recognition; no-shared-base escape; module-relocation
boundary; replay-reuse-not-reinvention; no-fallback-to-superseded-D-or-legacy;
second-broad-trust-root rejection for the new family cluster; and the
module-boundary REQ-033 disposition itself) — not a padded count.

| # | Attack | Affected model(s) | Mitigation (frozen) | Future test |
|---|---|---|---|---|
| 1 | Ordinary caller constructs a scoped authority object directly | A/D | `HPACWriterCapability.__init__` requires `_seal is _WRITER_CONSTRUCTOR_SEAL`, never exported; the new mint entrypoint is the only path (§30A.2) | guard test: no non-mint construction succeeds |
| 2 | Request forges `operation` | all | §119 closed enum at mint time; unknown → `operation_scope_invalid`, no mint | vocabulary-closure test |
| 3 | Certification role A capability used for role B store action | B/C/D | `role` field bound at mint (§119); per-role store checks unchanged (§125) | role-mismatch rejection test |
| 4 | Admin subtype A capability used for subtype B | all | §119/§126 closed subtype binding | subtype-mismatch rejection test |
| 5 | Authority reused for a second request | all | single-use (`_spent`), request-bound (§121); `capability_stale` on reuse | replay test |
| 6 | Authority reused after helper restart | all | process-local seal + registry destroyed at exit (§123, PAWAH-INV-16) | restart-dead test |
| 7 | Authority serialized into the response | all | §124/PAWAH-INV-11; `__reduce__` raises; response schema (§12) has no authority field | export-guard test |
| 8 | Authority persisted to disk | all | §124; never written to replay store/audit/env/cache | persistence-guard test |
| 9 | Authority copied/deepcopied | all | `__reduce__` raises `TypeError`; `__slots__` prevents arbitrary attribute injection | copy-guard test |
| 10 | Authority reconstructed from response fields | all | response carries only `decision`/`evidence_ref`/`evidence_digest`/`result_payload` (§12, unchanged) — no reconstructable field set | field-inventory test |
| 11 | Arbitrary target id substituted | all | §119 `subject` bound to the exact resolved target; store-layer target validation unchanged | subject-binding test |
| 12 | Generation rotated after mint | all | §121 binds installation/generation at mint; §30A.6/§30B.6 store-write-time currentness check (existing, unchanged) rejects a rotated-generation write | currentness test |
| 13 | Helper installation changed after mint | all | same as #12 (installation_id bound at §121) | installation-mismatch test |
| 14 | Replay conflict after mint | all | §20/§21 state model unchanged; `MUTATION_ATTEMPT_STARTED` boundary unaffected by which mint entrypoint produced the capability | conflicting-replay test |
| 15 | Partial write then automatic retry | all | §20-23 no-auto-retry unchanged; §136/§162 reaffirms | no-auto-retry test |
| 16 | Presentation evidence overwritten | D/E (presentation_evidence_write) | existing create-only store semantics unchanged (§127/§158); this phase supplies authority only | overwrite-rejection test |
| 17 | Presentation evidence written without a genuine APPROVE | D/E | HPAC-PAWA-HELPER-REQ-071 unchanged — request cannot self-assert `approved=true` | self-assertion-rejection test |
| 18 | Generic filesystem path supplied to the mint call | all | §119 has no free-path field; `subject` is a resolved id, never a path | schema-closure test |
| 19 | Arbitrary canonical store selected | all | store recognition unchanged/extended (§123/§149); the mint call itself selects no store | dispatch-mapping test |
| 20 | Generic mutation callable invoked via the new pathway | all | §133/PAWAH-INV-15; §119/§150 closed enum is the only mint surface | no-generic-broker test |
| 21 | Helper imports the legacy `hpac_protected_admin_writer` factory | all | REQ-033 unchanged, reaffirmed by §30A.4/§30B.4(REQ-033 disposition below) | import-allowlist test |
| 22 | Ordinary caller influences a helper-local registry/seal | all | §30A.5/§30B.3: new module never imported by agent-reachable code | process-isolation regression |
| 23 | Helper response leaks a permit | all | §12/§124 unchanged — response schema has no capability field | response-schema test |
| 24 | Exception / log leaks authority | all | §124 — no logging of capability objects | log-redaction test (future) |
| 25 | Authority survives helper exit | all | PAWAH-INV-16 — process memory only | restart-dead test (shared with #6) |
| 26 | Deterministic test authority accepted as REAL | all | §138/§164 — `authority_class is not PRODUCTION` → `HPACAuthorityError` | deterministic-vs-real test |
| 27 | Admin authority used for certification write | all | disjoint `operation` binding at mint (§119); disjoint **type** for E (§148) | cross-operation-rejection test |
| 28 | Certification authority used for admin mutation | all | same as #27 | cross-operation-rejection test (shared) |
| 29 | Evidence authority used for a general store write | D/E | `subject`/`role` bound to the exact ceremony (§127/§155); no general-write role is ever minted | scope-rejection test |
| 30 | New helper authority becomes a second broad trust root | all | §132/PAWAH-INV-17 | no-second-root structural test |
| **31** | **Ordinary process invokes the low-level mint primitive directly, reading (not influencing) an already-instantiated real seal** — predecessor-IV gap #1, §30B.1 | D (superseded) | **E**: the mint primitive and its seal are never loaded into any process that shares memory with agent-reachable code (§145) — the primitive is simply **absent** from that process's address space, not merely gated by a readable attribute | process-import-graph structural test: no agent-reachable module transitively imports `hpac_pawa_helper_writer_authority` |
| **32** | **Role/subject field mutation on an already-legitimately-issued capability by its own holder** — predecessor-IV gap #2, §30B.1 | all | recognition is keyed on registry/type membership, never on the object's own mutable fields (§149-§151, extends the existing `hpac_foundation.py:825-834` registry-dominates-mutable-fields pattern to the new families) | field-mutation-after-issuance rejection test |
| 33 | Facade treats its own process-local seal (§146) as sufficient by itself, omitting the §145 process-boundary check | E | contract text explicitly designates §145 as primary and §146 as defense-in-depth-only (PAWAH-INV-19); a structural test asserts the contract does not describe the seal as sufficient alone | contract-text assertion test (no "seal alone suffices" claim present) |
| 34 | A helper-scoped authority object is accepted by a bare `isinstance(x, HPACWriterCapability)` check somewhere in the store layer | E | §148/§151 (PAWAH-INV-20): recognition predicates use exact-type/sealed-family checks, never base-class `isinstance`; a structural/guard test enumerates every acceptance predicate | isinstance-escape structural test |
| 35 | A legacy broad `HPACWriterCapability` is accepted by a helper-scoped recognition predicate (the reverse-direction confusion) | E | §151 explicitly two-directional; exact-type check rejects a legacy instance at a helper-scoped predicate | reverse-confusion rejection test |
| 36 | The new mint primitive is left inside (or later moved back into) the shared `hpac_foundation` module, recreating defect 1 at the next evolution | E | §144/REQ-033 disposition below designates the module boundary as a normative property of this contract, not an implementation accident, so a future regression is a **contract violation**, not merely a code-review miss | module-location structural test (asserts the mint primitive's defining module, not merely its caller, is helper-process-exclusive) |
| 37 | A future facade failure silently falls back to Model D's superseded specification (rather than the legacy factory) as an "obvious" repair path | E | §166/PAWAH-INV-23 explicitly names Model D's specification as a forbidden fallback target, not only the legacy factory | no-fallback-to-superseded-model test |
| 38 | The new write facades invent a second, parallel replay/reservation mechanism instead of reusing the existing durable ledger | E | §160/PAWAH-INV-24: facades SHALL reuse `hpac_pawa_helper_replay_state`'s existing reservation-then-commit protocol; a structural test asserts no new replay-record schema is introduced | single-replay-mechanism structural test |
| 39 | The three new authority-family types are treated, in aggregate, as a second general-purpose broad trust root (rather than three narrow, disjoint families) | E | §147/§169 — no second trust root; each family's mint-time closed enum (§150) is a strict subset, never a union, of the legacy factory's arbitrary `role: str` surface | no-second-root structural test (extended to the three-family cluster) |
| 40 | REQ-033's module-exclusivity boundary is satisfied by convention (e.g. a code comment) rather than a checkable structural property | E | the REQ-033 disposition below requires the boundary to be independently verifiable by import-graph analysis, not by a docstring claim alone | import-graph independent-verifiability test |

### 30B.12 Store-recognition matrix (authority family x canonical mutation surface — all non-listed cells DENY)

| Authority family | `admin_mutation` write | `certification_write` (per-role) write | `presentation_evidence_write` | any other/unlisted store write |
|---|---|---|---|---|
| `HelperAdminMutationAuthority` | **PERMIT** (exact bound mutation subtype only, §150/§157) | DENY | DENY | DENY |
| `HelperCertificationWriteAuthority` | DENY | **PERMIT** (exact bound role only, §150/§156) | DENY | DENY |
| `HelperPresentationEvidenceAuthority` | DENY | DENY | **PERMIT** (exact bound ceremony only, §150/§158) | DENY |
| legacy `HPACWriterCapability` (broad production, unmigrated callers) | PERMIT (unchanged, existing role/subject registry check, §123) | PERMIT (unchanged) | PERMIT (unchanged) | DENY (role/subject-registry-bound, unchanged) |
| any other object / forged shell | DENY | DENY | DENY | DENY |

### 30B.13 Certification five-role matrix (diagonal = PERMIT, off-diagonal = DENY)

| minted for \ store gate | `hpac_challenge_coordinator` | `hpac_assertion_recorder` | `human_authentication_proof_verifier` | `hpac_gate5_binder` | `hpac_rhamp_counter_state_verifier` |
|---|---|---|---|---|---|
| `hpac_challenge_coordinator` | **PERMIT** | DENY | DENY | DENY | DENY |
| `hpac_assertion_recorder` | DENY | **PERMIT** | DENY | DENY | DENY |
| `human_authentication_proof_verifier` | DENY | DENY | **PERMIT** | DENY | DENY |
| `hpac_gate5_binder` | DENY | DENY | DENY | **PERMIT** | DENY |
| `hpac_rhamp_counter_state_verifier` | DENY | DENY | DENY | DENY | **PERMIT** |

`hpac_lifecycle_terminator` is not a row or column — it is not a member of
the closed five-role allowlist (§59, unchanged) and any attempted mint or
recognition against it is DENY at the closed-enum boundary (§150), never
reaching this matrix.

### 30B.14 Admin-mutation subtype matrix (diagonal = PERMIT, off-diagonal = DENY)

| minted for \ store gate | `enroll_principal` | `revoke_principal` | `enroll_credential` | `revoke_credential` | `initialize_credential_sidecar_state` | `configure_presentation_mechanism` | `configure_privileged_helper` |
|---|---|---|---|---|---|---|---|
| `enroll_principal` | **PERMIT** | DENY | DENY | DENY | DENY | DENY | DENY |
| `revoke_principal` | DENY | **PERMIT** | DENY | DENY | DENY | DENY | DENY |
| `enroll_credential` | DENY | DENY | **PERMIT** (`multi_write=True`, §122 unchanged) | DENY | DENY | DENY | DENY |
| `revoke_credential` | DENY | DENY | DENY | **PERMIT** | DENY | DENY | DENY |
| `initialize_credential_sidecar_state` | DENY | DENY | DENY | DENY | **PERMIT** | DENY | DENY |
| `configure_presentation_mechanism` | DENY | DENY | DENY | DENY | DENY | **PERMIT** | DENY |
| `configure_privileged_helper` | DENY | DENY | DENY | DENY | DENY | DENY | **PERMIT** (metadata-registration only, §159; never the helper executable bytes themselves) |

### 30B.15 REQ-033 disposition (v3.0 — further narrowed; REQ-033's and REQ-129's own text unchanged)

**HPAC-PAWA-HELPER-REQ-171.** HPAC-PAWA-HELPER-REQ-033's own text (§7) and
HPAC-PAWA-HELPER-REQ-129's own text (§30A.4) remain **byte-unchanged** — this
is a further **additive clarification**, the second one REQ-033 has
received, made necessary because this repair is the first case where the
exact **module boundary of the mint primitive itself** (not merely its
caller) matters operationally:

1. REQ-129 already established that `pcae.core.hpac_foundation` is not "the
   in-process PAWA factory module" REQ-033 names, and that the helper may
   import it for its closed type surface. That reading is **unaffected** by
   this repair.
2. **New clarification**: REQ-033's prohibition on the helper importing
   "any agent-reachable module" for the §7 recognition logic is now
   understood to apply with equal force to **the writer-authority-derivation
   logic this repair adds** — and, going further than REQ-129 had to for
   Model D, this repair holds that the **defining module of the low-level
   mint primitive itself**, not only its immediate caller, SHALL be a module
   that is never imported on any code path reachable from the configured
   agent principal's own process. Model D's defect (§30B.1) arose precisely
   because its mint primitive was specified to live in `hpac_foundation` — a
   module REQ-129 correctly established as agent-reachable for reads. This
   repair's facades and their mint primitive therefore live in the **new**,
   genuinely helper-process-exclusive module (§30B.3), not in
   `hpac_foundation`.
3. This is **not** "reintroducing a second factory" in the sense the v1.0/
   v2.0 contract forbade (§30A.5's own no-second-trust-root rationale
   applies unchanged): there remains exactly **one** production-authority
   trust root (§3, OS filesystem write authority) and **one** canonical
   `HPACWriterCapability`-family construction discipline per store
   (`require_writer`/`record_write`, unchanged, §123). What changes is
   **where the helper-scoped facade code executes and is defined** — a
   deployment/module-boundary fact — not the introduction of a second
   authority root, a second bootstrap mechanism, or a second independently-
   trusted party. The facade still terminates in the same
   `HPACStoreAuthority` primitives, still re-validates the same
   `<HPAC_PROTECTED_ROOT>` boundary, and still produces objects the same
   `require_writer`-family discipline (extended per §149) recognizes.
4. **Independent verifiability requirement (closes threat-matrix row 40).**
   This module-boundary property SHALL be independently checkable by static
   import-graph analysis (e.g. "no module reachable from
   `pcae.cli`/`pcae.runtime`/any plugin entrypoint transitively imports
   `pcae.core.hpac_pawa_helper_writer_authority`"), not asserted only by a
   docstring or a code comment — mirroring the existing guard-test pattern
   already used for `_PRODUCTION_TEST_FIXTURE_SEAL` (§26.2) and
   `_HELPER_WRITER_FACTORY_SEAL` (§30A.5).

## 30C. Security invariants added by v3.0 (PAWAH-INV-19 .. PAWAH-INV-24)

- **PAWAH-INV-19.** **The OS-process boundary is the primary mint-eligibility
  gate; a process-local seal is defense-in-depth only, never the sole
  boundary.** The new mint primitive and its seal are defined in a module
  never imported on any agent-reachable code path; any additional
  process-local seal check inside the helper is supplementary, not
  load-bearing by itself (§30B.3).
- **PAWAH-INV-20.** **Helper-scoped authority families are recognized by
  exact-type / sealed-family check, never bare `isinstance` against a shared
  base class.** No helper-scoped authority can satisfy legacy broad-writer
  recognition, and no legacy broad writer can satisfy a helper-scoped
  recognition predicate, in either direction (§30B.4).
- **PAWAH-INV-21.** **No authority-minting code is ever loaded into the
  shared, agent-reachable `hpac_foundation` module.** The mint primitive and
  its seal live exclusively in a helper-process-exclusive module; this is an
  independently verifiable import-graph property, not a naming convention
  (§30B.3, §30B.15).
- **PAWAH-INV-22.** **Cross-role, cross-subtype, and cross-operation
  isolation for the new authority families is enforced by construction (the
  closed enum at mint, §150), never by a post-hoc filter.** Tightens
  PAWAH-INV-12/13 for the new families (§30B.4/§30B.5).
- **PAWAH-INV-23.** **No fallback from a repaired-pathway facade failure to
  the superseded Model D specification or to the legacy in-process factory.**
  A facade failure is terminal for that request (§30B.8).
- **PAWAH-INV-24.** **Replay ordering for the new facades reuses the
  existing durable cross-process replay ledger; no parallel replay mechanism
  is introduced.** (§30B.6).

## 31. Testability requirements (specifications for future phases — not authored now)

- **HPAC-PAWA-HELPER-REQ-110.** The frozen contract SHALL be independently
  testable. The following verification classes are **specifications for the
  contract IV, the helper + protocol implementation phase, and the dedicated
  security IV** (`TB-ARCH` §22 / §34) — **not** tests authored in this
  contract-only phase (HPAC-PAWA-001 HPAC-PAWA-REQ-158 / 217 / 273 / 307
  discipline):
  - **contract structural tests** — every `HPAC-PAWA-HELPER-REQ-###` id
    contiguous from 001, no gaps / duplicates; every `PAWAH-INV-#` referenced
    appears in §29 once; every cross-reference to HPAC-PAWA-001 / HPAC-PPA-001 /
    HPAC-001 / RHAMP-001 resolves;
  - **exact operation-vocabulary tests** — the §13 enum is closed; an unknown
    operation / version / a prefix / a wildcard / a generic `operation_params`
    is denied; `supported_operations` gating;
  - **peer-auth tests** — a non-deployment-owner peer, a configured-agent peer,
    an unauthenticated or channel-unbound credential is refused; peer check
    precedes admission and precedes any protected-store read;
  - **helper-provenance tests** — wrong owner / mode / type / symlink / hash /
    stale generation / revoked status → no exec; a lookalike is a different
    file;
  - **same-file-object exec tests** — validation and exec address one
    descriptor; a pathname re-open is rejected; a platform without
    substitution-free exec STOPS BLOCKED;
  - **four-factory migration tests** — `production_writer` /
    `certification_writer` / `recognized_certification_read_authority` /
    `mint_protected_presentation_evidence_writer` no longer return an authority
    object; there is **no in-process authority object to attack** (the
    predecessor bypass PoCs become regression locks);
  - **five-role closure tests** — exactly the five; `hpac_lifecycle_terminator`
    / a wildcard / a prefix denied;
  - **typed-read restriction tests** — only the §15 enumerated records; no
    arbitrary path / key / table / dump / open-ended query / wildcard field;
    repeated reads do not reconstruct store authority;
  - **replay tests** — fresh / consumed / duplicate / expired / unknown /
    conflicting-replay dispositions (§19); a lost response does not free a
    spent request;
  - **crash / uncertainty tests** — the §20 / §21 transition model; the
    INDETERMINATE / RECONCILIATION-REQUIRED state; no auto-retry across
    `MUTATION_ATTEMPT_STARTED`;
  - **no-authority-export tests** — the response / read result carries no
    `HPACStoreAuthority` / `HPACWriterCapability` / handle / seal / reconstructable
    field set; `__reduce__` on any helper-side handle raises;
  - **fake-helper / forged-launcher / ordinary-agent negative tests** — none
    can mint a `PRODUCTION` capability, apply a counter transition, write any
    record, manufacture a human APPROVE / a Gate result / a PB / RE / runtime
    decision, or reach an external effect;
  - **clean-installed-package tests** — helper bytes as an inert wheel data
    artifact; out-of-band install; §6 metadata registration on a fresh macOS
    and (later) Ubuntu host;
  - **cross-platform profile tests** — `SO_PEERCRED` and `LOCAL_PEERCRED` /
    `getpeereid` backends realize the §16 frozen properties;
  - **deterministic-vs-real tests** — a fixture helper / launcher / peer /
    authenticator never yields `PRODUCTION` authority or `require_real_assurance`.
- **HPAC-PAWA-HELPER-REQ-111.** The implementation phase and its IV SHALL map
  every load-bearing §6 / §7 / §8 / §9 / §10 / §11 / §12 / §13 / §20 / §22 / §24
  clause to exact production-source and test evidence (HPAC-PAWA-001 §73 / §304
  discipline; no prose-only security guarantee).

## 32. Contract-only scope and no-go boundaries

- **HPAC-PAWA-HELPER-REQ-112.** This freeze changes **no** production source,
  **no** `scripts/`, **no** `pyproject.toml`, **no** dependency; creates **no**
  helper, launcher, channel, protected-root state, registration record, audit
  record, OS principal, or ceremony; performs **no** protected-host mutation and
  **no** authentication. The **only** repository changes in the freeze phase are
  this contract file, the companion HPAC-PAWA-001 v1.4 → v2.0 evolution,
  contract-guard reconciliation, a contract-verification test suite, and the
  canonical phase / status / changelog / task artifacts (HPAC-PAWA-001
  HPAC-PAWA-REQ-307 discipline, widened by this MAJOR's explicit companion
  authorization).
- **HPAC-PAWA-HELPER-REQ-113.** Runtime remains `not_implemented` / `Observed` /
  `observe` / `unavailable`; 0 plugins / 0 capabilities; the first governed
  runtime external effect remains **ABSENT / UNREACHABLE**. N-16-6 and N-16-7
  remain **OPEN and untouched**; N-16-7 strictly last. This contract contains
  **no** runtime-enablement clause and unblocks neither.
- **HPAC-PAWA-HELPER-REQ-114.** The **fresh** implementation successors —
  contract IV (alias N16-5-F-5-TB-CONTRACT-IV), helper + protocol
  implementation, caller integration, in-process authority-path removal (no
  compatibility shim may preserve the insecure in-process path), packaging /
  clean-install, dedicated security IV, production deployment, and a fresh
  `N16-5-FINAL-CERT` on a fresh CPIPC-valid successor id (never reuse a
  completed or blocked certification identity — HPAC-PAWA-001 PAWA-INV-11) —
  are **NOT begun** by this contract phase; each requires its own explicit human
  authorization (`TB-ARCH` §33 / §34).
- **HPAC-PAWA-HELPER-REQ-114A (v2.0 freeze-phase scope).** The v2.0 freeze
  phase (N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-CONTRACT-ARCH) changes **only**
  this contract file, contract-structural / source-fact test files, the
  phase architecture document, and the canonical phase / status / changelog /
  task artifacts. Unlike the v1.0 freeze (which had a companion HPAC-PAWA-001
  v1.4 → v2.0 MAJOR evolution), this v2.0 evolution requires **no** change to
  HPAC-PAWA-001 (remains v2.0, byte-unchanged) or HPAC-PPA-001 (remains v2.0,
  byte-unchanged) — the new mechanism is fully contained within
  HPAC-PAWA-HELPER-001's own delegated scope (HPAC-PAWA-HELPER-REQ-006,
  §30A.8). No production source, `scripts/`, `pyproject.toml`, or dependency
  changes; no helper, launcher, channel, protected-root state, registration
  record, audit record, OS principal, or ceremony created; no protected-host
  mutation; no authentication performed.

## 33. Requirement inventory

**Requirement count (v2.0):** HPAC-PAWA-HELPER-001 v2.0 defines **141**
requirements, `HPAC-PAWA-HELPER-REQ-001` through `HPAC-PAWA-HELPER-REQ-140`
inclusive plus `HPAC-PAWA-HELPER-REQ-114A`, sequential from v1.0's 114 with one
lettered insertion (`114A`, inserted adjacent to its parent `114` rather than
renumbering the immutable v1.0 sequence — the same discipline this repository
uses elsewhere for a late insertion that must not renumber a frozen
historical id block), no gaps, no duplicates within the v1.0 block
(001–114) or the v2.0 block (115–140).

**Invariant count (v2.0):** 18 — `PAWAH-INV-1` through `PAWAH-INV-10` (v1.0,
§29) plus `PAWAH-INV-11` through `PAWAH-INV-18` (v2.0, §29).

**Requirement count (v3.0):** HPAC-PAWA-HELPER-001 v3.0 defines **172**
requirement items total: the v2.0 block (140 base items, `REQ-001` through
`REQ-140`, plus lettered `114A` = 141 items) unchanged, plus
`HPAC-PAWA-HELPER-REQ-141` through `HPAC-PAWA-HELPER-REQ-171` (31 new,
§30B), sequential and contiguous from v2.0's 140, no gaps, no duplicates
within the new block (141-171 = 31 items; 141 + 31 = 172 total).

**Invariant count (v3.0):** 24 — `PAWAH-INV-1` through `PAWAH-INV-18` (v1.0/
v2.0, §29, unchanged) plus `PAWAH-INV-19` through `PAWAH-INV-24` (v3.0,
§30C).

## 34. Contract self-consistency statement

This contract, at v2.0: (a) introduces no implementation dependency, in either
direction, on `src/pcae/**` or `scripts/**` — it references existing,
existing-to-be-extended, and planned modules / functions / symbols by name in
normative text only, and imports / executes nothing; (b) does not amend
HPAC-001 v2.1, RHAMP-001 v1.0, HBDC-001 v1.2, HPAC-PAWA-001 v2.0, HPAC-PPA-001
v2.0, RIHAC-001 v2.0, RIASC-001 v3.0, RDGO-001 v3.1, or any other pre-existing
contract's byte content — this v2.0 evolution is fully self-contained
(§30A.8, HPAC-PAWA-HELPER-REQ-139/HPAC-PAWA-HELPER-REQ-114A); it is the
**MAJOR successor** authorized by Phase
N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-CONTRACT-ARCH; (c) creates no protected
state, OS principals, filesystem permissions, helper executables, registration
records, channels, requests, responses, audit records, protected-store reads,
capability instances, seals, or ceremonies — §30A is specification only, no
`hpac_foundation` / helper-module change is made by this contract-only phase;
(d) is internally traceable — every `HPAC-PAWA-HELPER-REQ-###` id is
sequential from 001 through 140 (plus the lettered `114A`) with no gaps and no
duplicates, and every `PAWAH-INV-#` (1..18) appears in §29 exactly once; (e)
is internally consistent — the authority decision stays with HPAC-PAWA-001
v2.0 §32 / §33 / §33B, unchanged and unaffected by §30A; this contract owns
only the mechanism, including the new §30A mechanism; the closed operation
vocabulary (§13) covers exactly the four factory families HPAC-PAWA-001
§36–§38 / §42B / §42D define, no more, and §30A's mint-time enum (§119) is a
**strict subset** of that vocabulary (the three v1.0-blocked operations only)
— no circular authority definition (§30A grounds every mint in the helper's
own already-completed §7/§10/§13 admission, never the reverse); the single
trust root and the no-second-root invariant (PAWAH-INV-7 / PAWAH-INV-17)
match HPAC-PAWA-001 HPAC-PAWA-REQ-300; the five-role closure (§14.2) reuses
HPAC-PAWA-001 §42B / PAWA-INV-13 verbatim and weakens nothing, and §30A's
role-scoping (PAWAH-INV-13) tightens it further, never loosens it; (f) leaves
runtime `not_implemented` / `Observed` / `observe` / `unavailable` and the
first external effect ABSENT.

**v3.0 self-consistency addendum (§30B):** this MAJOR evolution (a) introduces
no implementation dependency on `src/pcae/**` or `scripts/**` beyond
specification-only normative references — no `hpac_foundation` change, no new
module, is made by this contract-only repair; (b) does not amend HPAC-001
v2.1, RHAMP-001 v1.0, HBDC-001 v1.2, HPAC-PAWA-001 v2.0, or HPAC-PPA-001 v2.0
(§30B.10 impact adjudication: both remain byte-unchanged, independently
confirmed via `sha256sum` matching their pre-repair values); (c) is internally
traceable — `HPAC-PAWA-HELPER-REQ-141` through `REQ-171` are sequential with
no gaps or duplicates, and `PAWAH-INV-19` through `PAWAH-INV-24` each appear
in §30C exactly once; (d) resolves both defects the predecessor IV found
(§30B.1) without re-opening any dimension that IV's own subsystem verdict
table (§17 of that document) already marked VERIFIED; (e) supersedes, without
deleting, v2.0's §30A Model D specification, which MUST NOT be implemented.

## 35. Freeze verdict

**FROZEN:** the privileged production operation is performed by a **short-lived
one-shot protected helper process**, `exec`'d from an integrity-verified
out-of-band admin-owned executable by an enumerated deployment-owner standalone
launcher over a private one-shot channel; the helper authenticates its peer's
OS credential, runs HPAC-PAWA-001 §33 steps 1–8 in its own interpreter,
validates a closed typed `HPAC-PAWA-HELPER/1.0` request bound to a valid
session, performs **exactly one** bounded operation from the closed vocabulary
(`admin_mutation` | `certification_write` over the closed five roles |
`certification_read` over the enumerated record set | `ceremony_entry` |
`presentation_evidence_write`), writes durable audit evidence under
`<HPAC_PROTECTED_ROOT>` with evidence-staged-before-mutation ordering, returns
**typed evidence only** — **no** `HPACWriterCapability` / `HPACStoreAuthority` /
handle / seal ever crosses back — and exits. The trust root is unchanged (OS
filesystem write authority over the out-of-band-provisioned protected root); no
second trust root; no bearer secret; no new `PawaOperation`; no new
`pawa_failure_code`; no RHAMP-001 edit; the exact five-role certification
closure, the deterministic-vs-real wall, mechanism neutrality, the mobile-only
future path, the non-bearer / restart-dead semantics, and every
human-authentication / approval / PB / runtime / effect wall are preserved
verbatim.

**v2.0 additionally FREEZES (§30A):** a second, narrowly-scoped internal
writer-capability mint pathway (`HPACStoreAuthority._mint_helper_scoped_writer_capability`,
specification only), gated by a new, distinct seal
(`_HELPER_WRITER_FACTORY_SEAL`) never shared with the legacy
`_PRODUCTION_WRITER_FACTORY_SEAL`, owned exclusively by a new helper-only
module never imported by `hpac_protected_admin_writer` or any agent-reachable
module — resolving, at the specification level, the writer-authority
blocker `hpac_pawa_helper_store_adapter.py` documents for `admin_mutation`,
`certification_write`, and `presentation_evidence_write`. Selected model: **D
(evolved `HPACWriterCapability`, via a second additive low-level mint
entrypoint)** — Models A/B/C evaluated and not selected (§30A.1). REQ-033
disposition: **Option B**, narrow additive clarification, REQ-033's own text
unchanged (§30A.4). Zero canonical-store code changes required. No new trust
root, no new `pawa_failure_code`, no IPC export, no persistence, no legacy-
factory fallback. Contract structural / source-fact tests only — **no
production implementation** (`_mint_helper_scoped_writer_capability` and its
caller module do not yet exist).

Helper implementation, launcher, IPC, caller migration, in-process authority
path removal, packaging, security IV, deployment, and a fresh final
certification remain **NOT BEGUN**. `admin_mutation`, `certification_write`,
and `presentation_evidence_write` remain **ARCHITECTED / NOT IMPLEMENTED** —
still blocked in production until a fresh contract IV plus implementation.
N-16-5 remains **NOT CLOSED**. Runtime remains **Observed / observe /
unavailable** with **0 plugins / 0 capabilities**. First governed runtime
external effect remains **ABSENT / UNREACHABLE**.

**v3.0 additionally FREEZES (§30B): REPAIRED / FROZEN — PENDING INDEPENDENT
RE-VERIFICATION** (never claimed VERIFIED by this repair itself). v2.0's
§30A Model D specification is preserved as history and is **superseded, not
implemented, and must not be implemented**. The repaired pathway — **Model E,
a hybrid of Model B (helper-only mutation facades) and Model C (store-local
scoped permits)** — is selected: three narrow, closed, typed facades
(`mint_and_perform_admin_mutation`, `mint_and_perform_certification_write`,
`mint_and_perform_presentation_evidence_write`), each minting and performing
its bounded mutation in one call, entirely inside the already-isolated
one-shot helper subprocess, where the mint-eligibility boundary is the OS
process's absence of shared memory with agent-reachable code (not a
same-interpreter seal-identity convention), and each mint produces one of
three distinct, non-shared-base-recognized authority types
(`HelperAdminMutationAuthority`, `HelperCertificationWriteAuthority`,
`HelperPresentationEvidenceAuthority`) recognized at the store layer by
exact-type / sealed-family check, never bare `isinstance`. This repairs both
defects the predecessor IV found NOT VERIFIED / BLOCKED (§30B.1): ordinary-
process mint exclusion is now a real process boundary, and store recognition
can now mechanically distinguish helper-scoped from legacy-broad authority.
Threat matrix: **40 rows** (30 inherited + 2 predecessor-gap closures + 8
architecture-specific new rows, §30B.11). REQ-033 disposition: a further
additive clarification (§30B.15) — REQ-033's and REQ-129's own text
unchanged — that the mint primitive's defining module, not only its caller,
SHALL be helper-process-exclusive and independently import-graph-
verifiable. Zero canonical-store recognition-mechanism ambiguity remains
undisclosed. No new trust root, no new `pawa_failure_code`, no IPC export,
no persistence, no legacy-factory or superseded-Model-D fallback. HPAC-PAWA-
001 v2.0 and HPAC-PPA-001 v2.0 both remain byte-unchanged (§30B.10). Contract
structural / source-fact tests only — **no production implementation**
(none of the three facades, their authority types, or their defining module
exist yet). `DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` for
this repair phase, preserved.
