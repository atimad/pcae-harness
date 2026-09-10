# HPAC-PAWA-HELPER-001 v1.0 — HPAC-PAWA Protected One-Shot Privileged Helper Protocol Contract

## Contract identity and status

**Contract:** HPAC-PAWA-HELPER-001
**Version:** 1.0
**Status:** FROZEN — IMPLEMENTATION AND INDEPENDENT VERIFICATION PENDING
**Frozen by:** Phase
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

## 33. Requirement inventory

**Requirement count (v1.0):** HPAC-PAWA-HELPER-001 v1.0 defines **114**
requirements, `HPAC-PAWA-HELPER-REQ-001` through `HPAC-PAWA-HELPER-REQ-114`
inclusive, sequential, no gaps, no duplicates.

**Invariant count:** 10 — `PAWAH-INV-1` through `PAWAH-INV-10` (§29).

## 34. Contract self-consistency statement

This contract, at v1.0: (a) introduces no implementation dependency, in either
direction, on `src/pcae/**` or `scripts/**` — it references existing and
planned modules / functions / symbols by name in normative text only, and
imports / executes nothing; (b) does not amend HPAC-001 v2.1, RHAMP-001 v1.0,
HBDC-001 v1.2, HPAC-PPA-001 v1.0, RIHAC-001 v2.0, RIASC-001 v3.0, RDGO-001
v3.1, or any other pre-existing contract's byte content; it is the **new
companion** authorized by Phase N16-5-F-5-TB-CONTRACT alongside the
HPAC-PAWA-001 v1.4 → v2.0 MAJOR evolution; (c) creates no protected state, OS
principals, filesystem permissions, helper executables, registration records,
channels, requests, responses, audit records, protected-store reads, or
ceremonies; (d) is internally traceable — every `HPAC-PAWA-HELPER-REQ-###` id is
sequential from 001 through 114 with no gaps and no duplicates, and every
`PAWAH-INV-#` (1..10) appears in §29 exactly once; (e) is internally consistent
— the authority decision stays with HPAC-PAWA-001 v2.0 §32 / §33 / §33B, this
contract owns only the mechanism; the closed operation vocabulary (§13) covers
exactly the four factory families HPAC-PAWA-001 §36–§38 / §42B / §42D define, no
more; the single trust root and the no-second-root invariant (PAWAH-INV-7)
match HPAC-PAWA-001 HPAC-PAWA-REQ-300; the five-role closure (§14.2) reuses
HPAC-PAWA-001 §42B / PAWA-INV-13 verbatim and weakens nothing; (f) leaves
runtime `not_implemented` / `Observed` / `observe` / `unavailable` and the
first external effect ABSENT.

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

Helper implementation, launcher, IPC, caller migration, in-process authority
path removal, packaging, security IV, deployment, and a fresh final
certification remain **NOT BEGUN**. N-16-5 remains **NOT CLOSED**. Runtime
remains **Observed / observe / unavailable** with **0 plugins / 0
capabilities**. First governed runtime external effect remains **ABSENT /
UNREACHABLE**.
