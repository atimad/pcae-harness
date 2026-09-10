# HPAC-PPA-001 v2.0 — HPAC Protected Presentation Installation and Evidence Authority Contract

## Contract identity and status

**Contract:** HPAC-PPA-001  
**Version:** 2.0  
**Status:** FROZEN — IMPLEMENTATION AND INDEPENDENT VERIFICATION PENDING  
**Frozen by:** Phase
149O.20L.7O.3W.1R.2B.1R.1.1R.30R.4R — N-16-5 Protected-Presentation
Helper Installation and Evidence-Writer Authority Contract Reconciliation
(initial freeze, `HPAC-PPA-REQ-001..075`, `PPA-INV-1..8`).  
**Evolved to v2.0 by:** Phase
149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1
— HPAC-PPA-001 Contract Evolution: Out-of-Process Presentation-Evidence Writer
Ownership Alignment (alias **N16-5-F-5-PPA-CONTRACT**) (**MAJOR** under
HPAC-PPA-REQ-069 — an authority-ownership restructure, not a within-properties
platform adapter). Resolves the blocking finding of the predecessor contract IV
**N16-5-F-5-TB-CONTRACT-IV**
(`.pcae/phase-reports/20260910-093110-…1.1.1.1.1.md`): HPAC-PAWA-HELPER-001
v1.0 §17 (HPAC-PAWA-HELPER-REQ-070) and HPAC-PAWA-001 v2.0 §42B note freeze
`presentation_evidence_write` as *invoked by the HPAC-PPA-001 presentation
helper itself*, materially conflicting with v1.0 HPAC-PPA-REQ-041
(evidence-writer capability *"held only by the trusted launcher mediator …
never sent to the helper"*), HPAC-PPA-REQ-054 (*"evidence producer is only the
launcher mediator"*), HPAC-PPA-REQ-052 (a distinct evidence-writer-issuer
module `pcae.core.protected_presentation`), and PPA-INV-2 (helper response and
evidence writer as distinct trust actions). v2.0 **moves the bounded
presentation-evidence write into the verified protected presentation helper
process** (§21), **prohibits any evidence-writer object / capability / handle /
seal / reconstructable descriptor from crossing any process boundary** (§21 /
PPA-INV-9), **re-derives PPA-INV-2 as semantic (not process-location) trust-action
separation** (§21 / PPA-INV-2 (v2.0)), and **redefines the HPAC-PPA-REQ-052
evidence-writer issuer as a protected-side-internal operation of the helper
process that is never minted, returned, serialised, or delivered**. Only typed
evidence / result crosses the boundary. **No schema change** (HPAC-PPA-REQ-097);
**no new `pawa_failure_code` / RHAMP `terminal_reason_code`**
(HPAC-PPA-REQ-098); **no `src/pcae` / `scripts` / `pyproject.toml` / `schemas`
change**; **no protected-host mutation, no ceremony, no evidence write**. Every
v1.0 requirement body is kept **byte-verbatim** — supersession is expressed only
by this evolution record, the §21 requirements, the appended `(v2.0) §N note.`
paragraphs, and the §21A delta table (append-only evolution;
HPAC-PAWA-001 v2.0 §80.5 / widen-not-weaken discipline). The single trust root
is **unchanged** (OS filesystem write authority on the out-of-band-provisioned
`<HPAC_PROTECTED_ROOT>`; HPAC-PPA-REQ-088 / PPA-INV-3). A dedicated contract IV
**N16-5-F-5-PPA-CONTRACT-IV** is derived but **NOT begun** (HPAC-PPA-REQ-103);
**N-16-5 remains NOT CLOSED**; N-16-6 / N-16-7 OPEN / UNTOUCHED.  
**Parent semantics:** HPAC-001 v2.1, especially HPAC-REQ-079/080/090..093.  
**Concrete profile:** RHAMP-001 v1.0, especially RHAMP-REQ-014..016,
082..090, 143..148.  
**Protected administration:** HPAC-PAWA-001 v1.2 (installation metadata
mutations); **HPAC-PAWA-001 v2.0 + HPAC-PAWA-HELPER-001 v1.0** for the
out-of-process privileged-operation transport that carries the v2.0
`presentation_evidence_write` (§21 / HPAC-PPA-REQ-084).  
**Scope:** the missing authority and currentness layer for installing and
pinning the fixed local protected-presentation helper, launching exactly that
helper, authenticating its one-shot response, and writing one canonical
`HPAC-PRESENTATION-EVIDENCE/2.0` record. This contract adds no UI, helper,
production writer, Gate integration, runtime capability, adapter, or effect.

Historical HPAC-PAWA-001 v1.1 and the historically BLOCKED `.30R.4` report are
not rewritten. HPAC-001 v2.1 and RHAMP-001 v1.0 already define the descriptor,
presentation evidence, attestation, display, and response semantics; this
companion contract supplies the previously absent installation/currentness and
writer-issuance specialization without changing either parent. The v1.0 freeze
record and every v1.0 requirement body are **not** rewritten by v2.0.

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved.

---

## 0. Normative language

- **HPAC-PPA-REQ-001.** `SHALL`, `SHALL NOT`, `MUST`, `MUST NOT`, `SHOULD`,
  `SHOULD NOT`, and `MAY` are normative as in the repository's other frozen
  contracts. Unknown schema or contract versions fail closed.
- **HPAC-PPA-REQ-002.** Every authority decision is fail-closed and maps to an
  existing PAWA, HPAC, or RHAMP failure code as specified in §18. Free-form
  security outcomes are prohibited.
- **HPAC-PPA-REQ-003.** Conformance grants no PB permission, policy override,
  Runtime Enforcement result, runtime capability, `DispatchEnvelope`, adapter
  admission, dispatch authority, or execution authority.

## 1. Decisive architecture

- **HPAC-PPA-REQ-004.** The executable installation model is exactly
  **out-of-band immutable helper bytes plus PAWA metadata registration**. The
  external deployment owner installs the fixed PCAE-owned helper bytes under
  the protected root. PCAE/PAWA does not copy, replace, chmod, chown, package,
  download, or execute bytes as part of the registration mutation.
- **HPAC-PPA-REQ-005.** HPAC-PAWA-001 v1.2 authorizes only one bounded metadata
  mutation family, `configure_presentation_mechanism`, under writer role
  `presentation_mechanism_installer`. It covers initial registration, rotation,
  and revocation through a closed lifecycle action; it is not executable-install
  authority.
- **HPAC-PPA-REQ-006.** Installation administrator authority and runtime
  presentation-evidence authority are distinct. PAWA installation authority
  SHALL NOT emit presentation evidence. Runtime evidence authority SHALL NOT
  install, rotate, revoke, or rewrite helper configuration.
- **HPAC-PPA-REQ-007.** The protected presentation launcher is distinct from
  both authorities: it may resolve and invoke only the current fixed helper and
  mediate one request/response. It cannot configure the installation and cannot
  write arbitrary HPAC records.

## 2. Fixed production identity and paths

- **HPAC-PPA-REQ-008.** The sole v1.0 production mechanism identity is
  `pcae-protected-local-presentation`; the sole real verifier kind remains
  `pcae-protected-local-presentation/1.0`; exact equality only.
- **HPAC-PPA-REQ-009.** The mechanism directory is exactly
  `<HPAC_PROTECTED_ROOT>/presentation-mechanisms/v2/pcae-protected-local-presentation/`.
  No repository, cwd, environment, caller, PATH lookup, symlink, or alternate
  root may redirect it.
- **HPAC-PPA-REQ-010.** Helper bytes are installed create-only at the
  content-addressed path
  `<HPAC_PROTECTED_ROOT>/presentation-helper/installations/<helper_sha256>/pcae-protected-local-presentation`,
  where `<helper_sha256>` is exactly 64 lowercase hexadecimal characters and
  equals SHA-256 of the complete executable byte stream.
- **HPAC-PPA-REQ-011.** `helper_path` in an installation record is the absolute,
  normalized path derived from §2. It is not caller-selectable. The path must
  remain beneath the same live protected-root `{device,inode}` identity.
- **HPAC-PPA-REQ-012.** The helper object and every existing ancestor from the
  protected root to it must be non-symlink; the helper must be a regular file
  with one hard link, owned by the deployment owner, and not writable by group,
  other, the configured agent principal, or an ACL granting that principal
  write. These are authoritative defense-in-depth predicates in addition to,
  never substitutes for, the digest check.

## 3. Installation-generation record

- **HPAC-PPA-REQ-013.** Each lifecycle generation is an immutable create-only
  record at
  `<mechanism-dir>/installations/<generation>/installation.json`, schema
  `HPAC-PRESENTATION-INSTALLATION/1.0`, canonicalized under HPAC-REQ-089.
- **HPAC-PPA-REQ-014.** The installation record has exactly these closed fields:

| Field | Exact meaning |
|---|---|
| `installation_schema_version` | const `HPAC-PRESENTATION-INSTALLATION/1.0` |
| `installation_id` | `^hppi-[0-9a-f]{32}$`; stable for one protected-root installation lineage |
| `mechanism_id` | const `pcae-protected-local-presentation` |
| `helper_implementation_id` | const `pcae-protected-local-presentation` |
| `helper_implementation_version` | non-empty version identifier, bound to the installed PCAE helper build |
| `helper_path` | exact absolute path derived by HPAC-PPA-REQ-010/011 |
| `helper_sha256` | SHA-256 of the complete helper bytes |
| `descriptor_digest` | exact HPAC-REQ-090 descriptor digest |
| `verifier_configuration_digest` | exact protected verifier-configuration SHA-256 from that descriptor |
| `renderer_profile` | exact versioned deterministic renderer from that descriptor |
| `generation` | positive integer; initial `1`, then previous current + 1 |
| `lifecycle_action` | closed enum `install`, `rotate`, `revoke` |
| `status` | `active` for install/rotate; `revoked` for revoke |
| `installed_at` | trusted-clock UTC RFC 3339 timestamp for this generation action |
| `supersedes` | null at generation 1; otherwise exact closed `{generation, installation_digest}` of prior current generation |
| `installation_digest` | self-excluding SHA-256 of the canonical record |

- **HPAC-PPA-REQ-015.** No installation record carries a secret, private key,
  approval, PAWA seal, evidence-writer capability, PB permission, runtime
  capability, or reusable token. Its HPAC writer-provenance sidecar is required
  and must resolve to role `presentation_mechanism_installer`, subject equal to
  the exact mechanism id, and `PRODUCTION` authority class.
- **HPAC-PPA-REQ-016.** The HPAC-REQ-090 descriptor remains at its already
  frozen path and shape. For an active installation its `mechanism_id`,
  `descriptor_digest`, `verifier_kind`, `verifier_configuration_digest`, and
  `renderer_profile` must match the installation record exactly; all four
  descriptor booleans remain true and `status == active`.

## 4. Current-generation anchor

- **HPAC-PPA-REQ-017.** The authoritative currentness record is exactly
  `<mechanism-dir>/current-generation.json`, schema
  `HPAC-PRESENTATION-CURRENT-GENERATION/1.0`, atomically replaced and read-back
  verified under the same bounded PAWA transaction.
- **HPAC-PPA-REQ-018.** It has exactly these closed fields:
  `current_generation_schema_version` (const), `installation_id`,
  `mechanism_id`, `current_generation`, `installation_digest`,
  `descriptor_digest`, `status` (`active` or `revoked`), `updated_at`, and
  `anchor_digest` (self-excluding SHA-256).
- **HPAC-PPA-REQ-019.** A generation is current only when the anchor and
  immutable installation record agree on installation id, mechanism id,
  generation, installation digest, descriptor digest, and status, and the
  current HPAC-REQ-090 descriptor agrees under §3. Any mismatch, missing record,
  stale generation, noncanonical bytes, or digest failure rejects.
- **HPAC-PPA-REQ-020.** The anchor's HPAC writer provenance must resolve to the
  same role, subject, production root, and PAWA transaction as the installation
  record and descriptor. A caller-written structurally valid anchor is not
  authority.

## 5. Administration lifecycle

- **HPAC-PPA-REQ-021.** Bootstrap is non-circular: the deployment owner first
  installs helper bytes out of band, then obtains one PAWA capability and
  registers generation 1 metadata. No protected presentation is required to
  install the protected presentation mechanism; the existing PAWA protected
  administrator is the trust anchor.
- **HPAC-PPA-REQ-022.** The only production PAWA consumer is future module
  `pcae.core.hpac_protected_presentation_admin`, called only from standalone
  `scripts/hpac_protected_presentation_admin.py`. It is not agent-, CLI-, Gate-,
  runtime-, plugin-, or repository-reachable.
- **HPAC-PPA-REQ-023.** Install, rotate, and revoke each require a fresh
  process-local PAWA capability bound to mechanism id, lifecycle action, and
  one configuration transaction. The descriptor, installation record, anchor,
  and provenance writes are one bounded multi-write operation completed exactly
  once.
- **HPAC-PPA-REQ-024.** Initial installation is create-only and requires no
  current anchor. Repeating install against a valid current lineage fails;
  first-caller-wins and silent reset are prohibited.
- **HPAC-PPA-REQ-025.** Rotation requires a current active generation G,
  immutable new helper bytes already installed at their derived content-addressed
  path, and creates G+1 with `lifecycle_action == rotate`, `status == active`,
  and exact `supersedes`. The descriptor and anchor switch to G+1 in the same
  bounded transaction. G becomes stale by derivation; it is not rewritten.
- **HPAC-PPA-REQ-026.** Revocation requires current generation G and creates
  G+1 with `lifecycle_action == revoke`, `status == revoked`, and exact
  `supersedes`; it atomically writes a revoked descriptor and revoked anchor.
  No new ceremony may start and no outstanding response/evidence may be
  accepted from any generation in that lineage while revoked.
- **HPAC-PPA-REQ-027.** Recovery from damage is an explicit deployment-owner
  reprovisioning operation using a new `installation_id` and generation 1 after
  the damaged lineage is made unavailable. There is no repository recovery,
  self-healing, environment override, first-use install, or fixture fallback.
- **HPAC-PPA-REQ-028.** Restoring an older generation record, descriptor, or
  helper alone fails current-anchor comparison. Restoring a byte-identical old
  whole protected-root snapshot is bounded by the existing HPAC/PAWA
  `{device,inode}` and deployment-owner TCB; this contract does not claim
  resistance to a deployment owner restoring the entire trusted machine state.

## 6. Helper integrity and launch

- **HPAC-PPA-REQ-029.** Before every launch, the trusted launcher resolves the
  active descriptor, current anchor, current installation record, and their
  production writer provenance; opens the fixed helper with no symlink
  traversal; validates type/link/owner/mode/ACL; hashes the opened bytes; and
  requires exact `helper_sha256`, descriptor, configuration, renderer, root,
  installation, and generation agreement.
- **HPAC-PPA-REQ-030.** Validation and execution must address the same opened
  file object or a platform-equivalent identity-preserving handle. A pathname
  re-open gap after validation is forbidden. If the platform cannot execute
  the verified object without a substitution window, implementation stops
  BLOCKED.
- **HPAC-PPA-REQ-031.** Launch is a fixed local one-shot invocation with fixed
  executable identity and fixed protocol. There is no shell, PATH lookup,
  caller argv extension, cwd lookup, network, remote endpoint, browser,
  environment-selected helper, or generic subprocess API.
- **HPAC-PPA-REQ-032.** The child environment is a closed minimal allowlist
  required by the fixed local UI platform; it carries no authority selector,
  automatic response, verifier kind, helper path, writer role, root override,
  or caller-provided secret. Unknown environment influence fails closed.
- **HPAC-PPA-REQ-033.** Launch permission is not PAWA installation authority
  and not runtime dispatch authority. It authorizes only one protected local
  human-approval ceremony and terminates with that ceremony.

## 7. One-shot request and response authenticity

- **HPAC-PPA-REQ-034.** The trusted launcher creates a fresh CSPRNG nonce of at
  least 256 bits and a private parent/child channel unavailable to the
  requesting agent. The exact canonical request binds nonce, approval id,
  challenge id, presentation digest, approval-subject digest, principal,
  invocation, attempt, expiry, mechanism id, installation id, generation,
  installation digest, descriptor digest, renderer profile, and all 13 closed
  human-visible facts.
- **HPAC-PPA-REQ-035.** The helper receives canonical request bytes over that
  channel without shell or argv interpolation of untrusted facts. The launcher
  never accepts caller-provided `approved=True`, response bytes, helper process,
  channel, or attestation.
- **HPAC-PPA-REQ-036.** The closed response binds the same nonce, approval id,
  challenge id, presentation digest, mechanism id, installation id, generation,
  installation digest, descriptor digest, renderer profile, decision, trusted
  timestamp, and a self-excluding response digest. Decision is exactly
  `APPROVE` or `REJECT`; cancel/close/EOF is no response and no approval.
- **HPAC-PPA-REQ-037.** Response authenticity is established by the conjunction
  of the verified executable object, private one-shot parent/child channel,
  unpredictable nonce, exact request/response bindings, current generation,
  and successful fixed-protocol parsing. No new signing key is required or
  implied.
- **HPAC-PPA-REQ-038.** Crash, nonzero/abnormal exit, malformed or duplicate
  response, broken pipe, timeout, expired request, nonce mismatch, binding
  mismatch, or post-launch generation/currentness change fails closed and emits
  no approval evidence.
- **HPAC-PPA-REQ-039.** Exactly one active ceremony exists per
  `(invocation_id, attempt_id)`. Unrelated ceremonies may run concurrently only
  with distinct channels, nonces, challenges, request digests, and helper
  lifecycles. Cross-request responses fail closed.

## 8. Runtime evidence-writer authority

- **HPAC-PPA-REQ-040.** The runtime evidence writer role is exactly the
  existing `protected_presentation_mechanism`. It is not a PAWA writer role and
  does not extend HPAC-PAWA-001's mutation set.
- **HPAC-PPA-REQ-041.** The evidence authority is a seal-guarded,
  process-local, non-serializable, non-copyable, restart-dead, single-use
  `HPACWriterCapability` (or repository-equivalent use of the same existing
  capability/provenance primitive), held only by the trusted launcher mediator.
  It is never sent to the helper or requesting caller.

  > **(v2.0) §8 note.** HPAC-PPA-REQ-041's *"held only by the trusted launcher
  > mediator … never sent to the helper"* is **superseded** by §21
  > (HPAC-PPA-REQ-077..079 / PPA-INV-2 (v2.0) / PPA-INV-9). Under v2.0 the
  > bounded evidence-write authorization is **process-local to the verified
  > protected presentation helper** and is performed **inside the helper
  > process** after one valid `APPROVE`; **no** `HPACWriterCapability`, HPAC
  > writer object, handle, seal, token, or reconstructable authority descriptor
  > is held by the launcher mediator, returned to it, or sent to any caller —
  > there is **no returnable writer**. Every other property of REQ-041
  > (seal-guarded, process-local, non-serialisable, non-copyable, restart-dead,
  > single-use, request-bound, generation-bound) is **preserved and tightened**:
  > the authority now also never exists on a heap shared with the requesting
  > agent interpreter. HPAC-PPA-REQ-042..046 apply unchanged to the helper-held
  > authorization (issuance binding, one create-only write, failure consumes the
  > authorization, re-entry returns stale/consumed failure, object-local state
  > cannot mint authority).
- **HPAC-PPA-REQ-042.** Issuance occurs only after §6 integrity/currentness
  validation and is canonically bound in the process-local issuance registry to
  exact capability identity, role, mechanism id, approval id, challenge id,
  request digest, installation id/generation/digest, descriptor digest,
  authority class `PRODUCTION`, and ACTIVE lifecycle.
- **HPAC-PPA-REQ-043.** The capability authorizes exactly one create-only
  `HPAC-PRESENTATION-EVIDENCE/2.0` record and its ordinary provenance sidecar at
  the HPAC-REQ-093 path after one valid `APPROVE` response. It authorizes no
  descriptor, installation, proof, lifecycle, consumption, approval, Gate,
  runtime, adapter, or arbitrary filesystem write.
- **HPAC-PPA-REQ-044.** `REJECT`, cancel, timeout, crash, malformed response, or
  any validation/currentness failure consumes or discards the ceremony-local
  writer without writing approval evidence. No failure path can preserve a
  reusable writer.
- **HPAC-PPA-REQ-045.** Evidence creation rechecks the canonical issuance and
  current active installation under one synchronization boundary before
  ACTIVE→CONSUMED. The record write and provenance attribution complete once;
  re-entry or replay returns stale/consumed authority failure.
- **HPAC-PPA-REQ-046.** Mutating object-local spent state, copying response
  bytes, reconstructing fields, serializing a descriptor, or possessing durable
  evidence cannot mint or restore writer authority. Canonical process-local
  issuance state dominates.

## 9. Evidence binding, storage, and currentness

- **HPAC-PPA-REQ-047.** The durable evidence remains exactly HPAC-REQ-091/092's
  `HPAC-PRESENTATION-EVIDENCE/2.0`; this contract adds no field. Its mechanism
  reference binds the current descriptor, while its verified attestation and
  writer issuance bind the exact installation id/generation/digest and response
  through the ceremony-local request digest.
- **HPAC-PPA-REQ-048.** Installation generation binding is verification state,
  not a caller-controlled evidence extension: the verifier resolves the
  descriptor digest through the current HPAC-PPA anchor and requires the
  ceremony-local attestation/response binding produced under that same
  generation. A generation switch before persistence or verification rejects.
- **HPAC-PPA-REQ-049.** Evidence is durable canonical input and audit material,
  not bearer authority. It becomes usable only through HPAC-REQ-093 resolution,
  RHAMP presentation-attestation verification, proof lifecycle binding, fresh
  authentication, and later one-shot consumption.
- **HPAC-PPA-REQ-050.** Evidence tied to a superseded or revoked helper
  generation is stale and cannot satisfy a new or still-pending ceremony.
  Rotation from G to G+1 before response verification supersedes the G request;
  revocation invalidates every outstanding response immediately.
- **HPAC-PPA-REQ-051.** A copied evidence record, response replay, reused nonce,
  reused request digest, second evidence write, or binding to another principal,
  transaction, operation, target, approval, invocation, attempt, challenge, or
  helper generation fails closed.

## 10. Exact producer and consumer inventory

- **HPAC-PPA-REQ-052.** Expected future production modules are exactly:
  `pcae.core.protected_presentation_installation` (schema/store/currentness),
  `pcae.core.hpac_protected_presentation_admin` (sole PAWA consumer),
  `pcae.core.protected_presentation` (sole launcher/mediator and evidence-writer
  issuer), and the PCAE-owned packaged helper implementation
  `pcae.protected_presentation_helper`. Names are exact and confer no authority
  before implementation and verification.

  > **(v2.0) §10 note.** The module names are unchanged, but the
  > **evidence-writer issuer role moves** (§21 / HPAC-PPA-REQ-081):
  > `pcae.core.protected_presentation` remains the **sole launcher / mediator**
  > and is **no longer** the evidence-writer issuer — it mints, holds, returns,
  > and serialises **no** evidence-writer authority. The bounded
  > presentation-evidence write is performed **by
  > `pcae.protected_presentation_helper` in its own verified one-shot process**
  > as the HPAC-PAWA-HELPER-001 §17 `presentation_evidence_write` operation
  > (HPAC-PPA-REQ-077 / REQ-084). The write authorization is a
  > **protected-side-internal operation of the helper process** that is never
  > minted as a returnable factory result, never serialised, and never delivered
  > across a process boundary (HPAC-PPA-REQ-081 / PPA-INV-9). No `mint_*` factory
  > returns a writer to any caller.
- **HPAC-PPA-REQ-053.** The only standalone administration entry point is
  `scripts/hpac_protected_presentation_admin.py`. It may call only the exact
  admin module. It is never a `pcae` CLI subcommand or runtime consumer.
- **HPAC-PPA-REQ-054.** Evidence producer is only the launcher mediator after a
  response from the verified helper. Canonical consumers are only the existing
  presentation resolver and HPAC verifier path, followed by frozen Gate 5/Gate
  9 consumers after the future implementation. Gates never receive a writer.

  > **(v2.0) §10 note.** HPAC-PPA-REQ-054's *"evidence producer is only the
  > launcher mediator"* is **superseded** by §21 (HPAC-PPA-REQ-077): under v2.0
  > the **sole producer** of the one `HPAC-PRESENTATION-EVIDENCE/2.0` record for
  > a ceremony is the **verified protected presentation helper process** that
  > conducted that exact ceremony, after one valid `APPROVE`. The launcher
  > mediator establishes §6 integrity / §7 request-response mediation and
  > receives a **typed acknowledgement / evidence reference only**
  > (HPAC-PPA-REQ-082 / REQ-085). The canonical-consumer clause is unchanged —
  > the presentation resolver, the HPAC verifier path, and the frozen Gate 5 /
  > Gate 9 consumers are the only consumers, and **Gates never receive a
  > writer**.
- **HPAC-PPA-REQ-055.** Agent, task/session code, repository integration,
  ordinary CLI, plugin, runtime adapter, Gate coordinator, `hpac_verifier`, and
  helper process itself may not import or call the PAWA installer factory. No
  wildcard, prefix, glob, `fnmatch`, or caller string may widen either inventory.

## 11. Administration and evidence are semantic walls

- **HPAC-PPA-REQ-056.** Administrator-installed helper != presentation;
  launched helper != approval; authenticated human != informed approval;
  presentation evidence != approval proof; approval proof != PB permission;
  PB permission != runtime capability; runtime capability != execution.
- **HPAC-PPA-REQ-057.** A valid installation record cannot satisfy
  `require_real_assurance`; a valid helper response alone cannot satisfy it; a
  valid evidence record alone cannot satisfy it. REAL authentication and REAL
  protected presentation with matching live bindings remain jointly required.
- **HPAC-PPA-REQ-058.** Deterministic NON_REAL descriptors, helpers, writers,
  evidence, fixtures, monkeypatches, or caller factories remain permanently
  unable to produce `PRODUCTION` authority or be relabelled with the real kind.

## 12. Rotation, revocation, concurrency, recovery

- **HPAC-PPA-REQ-059.** Rotation is monotonic G→G+1. The old bytes may remain
  for audit/rollback diagnosis but are never current and never selected. A
  helper-byte replacement at an existing content-addressed path causes the hash
  check to fail; it is not rotation.
- **HPAC-PPA-REQ-060.** Revocation has no automatic fallback. A revoked current
  anchor makes production protected presentation unavailable until explicit
  deployment-owner recovery/reinstallation under a new valid generation or
  installation lineage.
- **HPAC-PPA-REQ-061.** Administration mutations serialize per mechanism. The
  compare-and-write precondition includes exact prior anchor digest; concurrent
  install/rotate/revoke attempts yield at most one successful transition.
- **HPAC-PPA-REQ-062.** Runtime launch takes a currentness snapshot but must
  revalidate immediately before evidence persistence. Administration never
  waits for or trusts a runtime ceremony; runtime never delays or overrides an
  administrator rotation/revocation.

## 13. Writer provenance compatibility

- **HPAC-PPA-REQ-063.** Existing `HPAC-WRITER-PROVENANCE/1.0` is sufficient:
  its exact role/subject/root/store/record/path/digest fields can represent
  `presentation_mechanism_installer` and `protected_presentation_mechanism`
  without a schema change. Resolver-owned role allowlists give the strings
  meaning; arbitrary strings confer none.
- **HPAC-PPA-REQ-064.** Installation records, anchors, and descriptors require
  installer provenance. Presentation evidence requires evidence-writer
  provenance. The roles are mutually ineligible at resolution and no common
  role or alias is accepted.

## 14. Contract impact and versioning adjudication

- **HPAC-PPA-REQ-065.** HPAC-PAWA-001 evolves v1.1→v1.2 MINOR: one exact
  metadata mutation family and one exact consumer category, explicitly allowed
  by its MINOR rule; no MAJOR trigger fires.
- **HPAC-PPA-REQ-066.** HPAC-001 remains v2.1 byte-identical. Its existing
  descriptor, evidence, attestation, paths, roles, and protected-administrator
  extension points are specialized but not widened or redefined.
- **HPAC-PPA-REQ-067.** RHAMP-001 remains v1.0 byte-identical. It already
  requires the installation, digest, currentness, response, and N-16-6
  separation semantics; no new real kind, ceremony ordering, transport, or
  terminal reason is introduced.
- **HPAC-PPA-REQ-068.** RIHAC-001 v2.0, RIASC-001 v3.0, RDGO-001 v3.1,
  HBDC-001 v1.2, HPSE-001, HHCE-001, and every other normative contract remain
  byte-identical. HPAC-PPA-001 is the minimum companion needed to avoid
  overloading PAWA with runtime evidence authority.
- **HPAC-PPA-REQ-069.** HPAC-PPA-001 uses MAJOR.MINOR. Changing from local fixed
  helper to remote/network/browser/headless authority; making installation or
  evidence authority bearer/durable/reusable; allowing caller-selected helper,
  path, response, or writer; merging PAWA and runtime evidence authority; or
  transferring authority into PB/runtime/execution requires a new MAJOR.
- **HPAC-PPA-REQ-070.** A MINOR may add a platform adapter within these exact
  properties, tighten a bound, or add a failure mapping without remeaning an
  existing outcome. No version may retrospectively widen an issued capability,
  installation, response, evidence, proof, or approval.

  > **(v2.0) §14 note — version classification of the v2.0 evolution.** Moving
  > the presentation-evidence-writer holder from the trusted launcher mediator
  > into the verified helper process, and re-deriving PPA-INV-2's process-location
  > separation into semantic separation, **is a MAJOR** under HPAC-PPA-REQ-069
  > (*"making … evidence authority … reusable; allowing caller-selected …
  > writer; merging PAWA and runtime evidence authority; or transferring
  > authority"* — the enumerated triggers are illustrative of an
  > authority-ownership restructure, which this is). It is **not** a
  > HPAC-PPA-REQ-070 MINOR: REQ-041's parenthetical *"or repository-equivalent
  > use of the same existing capability/provenance primitive"* governs **which
  > primitive** implements the authority, **not which component holds it**, and
  > REQ-070's *"add a platform adapter within these exact properties"* cannot
  > carry a change to who the authority holder is. The v2.0 direction is the
  > correct security direction — the authority moves **further** from the agent
  > interpreter, never onto a shared heap — but v1.0 as frozen does not
  > authorise it, so a new MAJOR is required. v2.0 **widens nothing** that was
  > issued under v1.0: no v1.0 capability, installation, response, evidence,
  > proof, or approval is retrospectively broadened; the v1.0 in-process /
  > launcher-held path is **superseded and non-production**, removed in a later
  > governed slice (HPAC-PPA-REQ-099).

## 15. N-16-6 / runtime / effect boundary

- **HPAC-PPA-REQ-071.** Fixed protected-helper launch is distinct from N-16-6
  effect-adapter admission. Neither installation metadata nor launcher
  validation may be interpreted as adapter supply-chain admission.
- **HPAC-PPA-REQ-072.** This contract implements no helper, launcher, writer,
  descriptor, verifier, Gate wiring, N-16-6, N-16-7, Slice C, dispatch, runtime
  capability, or external effect. Runtime remains Observed / observe /
  unavailable with zero plugins/capabilities.

## 16. Implementation and verification sequence

- **HPAC-PPA-REQ-073.** The fresh implementation successor is exactly
  `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.4R.1` — N-16-5 Protected Human-Approval
  Presentation and Real-Assurance Consumption Implementation After Authority
  Reconciliation. Historical `.30R.4` remains BLOCKED and immutable.
- **HPAC-PPA-REQ-074.** The implementation must be followed by a fresh
  independent verification plus mandatory real CTAP2 hardware verification
  before N-16-5 may close. This contract phase does not begin either successor.

## 17. Traceability matrix

| RHAMP / HPAC source | Authority requirement | Contract artifact / role | Future symbol | Verification obligation |
|---|---|---|---|---|
| RHAMP-REQ-015/016; HPAC-REQ-080/090 | protected administrator installs/revokes descriptor | PAWA `configure_presentation_mechanism`; `presentation_mechanism_installer` | `pcae.core.hpac_protected_presentation_admin` | exact consumer, role, subject, no caller install |
| RHAMP-REQ-082/083/087/088 | fixed helper, pinned bytes, no path-only trust | installation + current-generation records | `pcae.core.protected_presentation_installation` | path/digest/root/provenance/currentness all required |
| RHAMP-REQ-084..086/143 | local one-shot protected launch | launcher boundary, private channel | `pcae.core.protected_presentation` | no shell/PATH/env/network/caller channel |
| RHAMP-REQ-144/145 | authenticated exact response | nonce/request/response/generation binding | launcher + packaged helper | malformed/replay/substitution fail closed |
| HPAC-REQ-091..093 | canonical evidence | `protected_presentation_mechanism` writer | launcher mediator + `TrustedApprovalPresentationStore` | one create-only write, provenance, replay rejection |
| RHAMP-REQ-090/157 | helper != N-16-6 | explicit no-transfer wall | none | no adapter/dispatch/effect symbols |

## 18. Failure taxonomy traceability

- **HPAC-PPA-REQ-075.** PAWA recognition/issuance failures retain the 21-code
  vocabulary. Invalid registration inputs map `operation_scope_invalid`; wrong
  bound mechanism/transaction maps `target_scope_invalid`; stale/reused writer
  maps `capability_stale`; unauthorized source maps
  `unauthorized_factory_consumer`; protected-root failures retain their exact
  codes; otherwise `internal_fail_closed`.
- **HPAC-PPA-REQ-076.** Runtime failures use RHAMP's existing closed terminal
  reasons: installation/digest/currentness/type/owner/mode/substitution failure
  → `helper_integrity_unverified`; malformed/unbound/duplicate response →
  `helper_response_untrusted`; rotation/revocation/restart supersession →
  `ceremony_superseded`; cancel/close → `ceremony_cancelled`; timeout →
  `ceremony_timed_out`; expiry → `challenge_expired`; evidence/attestation
  mismatch retains its exact presentation reason. No new PAWA or RHAMP code is
  required.

## 19. Security invariants

- **PPA-INV-1.** Out-of-band immutable bytes plus metadata pinning is the only
  installation model; PAWA never becomes generic executable authority.
- **PPA-INV-2.** Installer, launcher, helper response, and evidence writer are
  distinct trust actions with no authority transfer.
  > **PPA-INV-2 (v2.0) — re-derived, semantic separation.** Installation
  > configuration, launcher mediation, protected-UI presentation rendering,
  > human election capture, presentation-evidence persistence, and the helper's
  > typed response remain **distinct trust actions with separate preconditions,
  > separate outputs, and separate failure states and no authority transfer
  > between them**, **even when several are performed by the same verified
  > protected helper process**. None implies any other authority,
  > authentication, approval consumption, PB permission, runtime capability, or
  > execution authority; there is no automatic promotion between them. A helper
  > that rendered UI has not thereby earned `APPROVE`; a helper that captured
  > `APPROVE` has not thereby authenticated the human; a helper that wrote
  > presentation evidence has not thereby established real human authentication.
  > The v1.0 wording (four actions, "no authority transfer") is preserved; v2.0
  > removes only the implicit *separate-process / separate-holder* reading and
  > replaces it with this semantic separation (§21 / HPAC-PPA-REQ-083).
- **PPA-INV-3.** Current descriptor + installation + anchor + opened-byte digest
  + provenance are jointly required; path alone never suffices.
- **PPA-INV-4.** Runtime evidence writer is process-local, non-bearer,
  request-bound, generation-bound, and single-use.
- **PPA-INV-5.** Durable installation/evidence/audit records are not reusable
  authority.
- **PPA-INV-6.** Rotation/revocation invalidates outstanding old-generation
  responses; no deterministic fallback exists.
- **PPA-INV-7.** Protected helper launch is not N-16-6, runtime dispatch, or an
  external effect.
- **PPA-INV-8.** No contract in this reconciliation closes N-16-5 or enables
  execution.
- **PPA-INV-9. (v2.0)** The bounded presentation-evidence write is performed by
  the verified protected helper **in its own process**. No evidence-writer
  object, `HPACWriterCapability`, HPAC writer, capability token, serialised
  seal, reconstructable authority descriptor, or opaque bearer handle crosses
  **any** process boundary — not launcher→helper, not helper→launcher, not into
  any ordinary PCAE process, plugin, agent, runtime, Gate, or test fixture
  (aligned with HPAC-PAWA-001 PAWA-INV-15 / PAWA-INV-16 and
  HPAC-PAWA-HELPER-001 PAWAH-INV-1). Only typed evidence / result / a
  protected-root-relative evidence reference leaves the helper. The
  authorization is gone at helper exit.
- **PPA-INV-10. (v2.0)** The helper process that authors the
  `HPAC-PRESENTATION-EVIDENCE/2.0` record is the **same** integrity-verified
  one-shot protected helper object/process that conducted the ceremony
  (§6 / §29 / §30 / HPAC-PPA-REQ-088). A "verify helper A → run helper B →
  persist trusted evidence" split fails closed. Helper hash ≠ trust root;
  helper path ≠ trusted origin; registration metadata ≠ trust root.
- **PPA-INV-11. (v2.0)** Typed evidence / result / acknowledgement is not
  privileged authority; the caller cannot reconstruct writer authority from the
  response. A lost or absent response is **not** proof that no evidence was
  written and **never** frees a spent one-shot ceremony; once the
  evidence-write attempt boundary is crossed there is **no auto-retry**, only
  reconciliation against the protected-root canonical evidence
  (HPAC-PPA-REQ-091 / REQ-092).
- **PPA-INV-12. (v2.0)** HPAC-PPA-001 defines what constitutes a **valid**
  presentation-evidence record and a **valid** human election;
  HPAC-PAWA-HELPER-001 v1.0 §17 carries the bytes of the
  `presentation_evidence_write` operation over the protected process boundary.
  Neither contract confers the other's authority and there is no circular
  trust: the helper protocol transports, this contract adjudicates meaning and
  validity (HPAC-PPA-REQ-084).

## 20. Freeze verdict

**FROZEN:** deployment-owner PAWA authority registers only protected metadata;
helper bytes are externally installed and content-addressed; the one new PAWA
mutation is `configure_presentation_mechanism`; the one new consumer is
`pcae.core.hpac_protected_presentation_admin`; the exact installation and
current-generation schemas are frozen; runtime evidence writer role is the
distinct existing `protected_presentation_mechanism`, issued process-locally by
the trusted launcher mediator and bound to one request/current helper generation;
HPAC/RHAMP/writer-provenance remain unchanged; N-16-6 receives no authority.

## 21. (v2.0) Out-of-process presentation-evidence writer ownership

*This section is the sole normative delta of HPAC-PPA-001 v2.0. It supersedes
the named v1.0 clauses as stated; every other v1.0 requirement body is
unchanged. See §21A for the delta table.*

- **HPAC-PPA-REQ-077.** **Sole evidence producer.** The **verified protected
  presentation helper process** (`pcae.protected_presentation_helper`, admitted
  under §6 / §29 / §30) that conducts a ceremony is the **sole author** of the
  one create-only `HPAC-PRESENTATION-EVIDENCE/2.0` record and its ordinary
  provenance sidecar (HPAC-REQ-091..093 path) for that exact ceremony, written
  only after **one valid `APPROVE`** response. This supersedes HPAC-PPA-REQ-054
  (*"evidence producer is only the launcher mediator"*) and the
  launcher-holder clause of HPAC-PPA-REQ-041. `HPAC-PRESENTATION-EVIDENCE/2.0`
  has exactly one producer and it is unchanged in every other respect
  (HPAC-PPA-REQ-047 — no field added).
- **HPAC-PPA-REQ-078.** **No generic writer transfer.** The v2.0 model SHALL NOT
  be implemented by transferring a generic evidence-writer capability into or
  out of the helper. No `HPACWriterCapability`, generic HPAC writer object,
  capability token, serialised seal, reconstructable authority descriptor, or
  opaque bearer handle SHALL cross launcher→helper, helper→launcher, or the
  helper boundary into any ordinary PCAE process, plugin, agent, runtime, Gate,
  or fixture. The helper is **admitted** through the protected-process trust
  boundary (HPAC-PPA-REQ-088 / HPAC-PAWA-001 v2.0 §33C) and then performs
  **exactly one** bounded presentation-evidence persistence operation itself.
  Typed evidence / result != privileged authority (PPA-INV-9 / PPA-INV-11).
- **HPAC-PPA-REQ-079.** **Bounded helper-held write authorization.** After one
  valid `APPROVE`, the helper process holds a process-local authorization to
  perform **exactly one** create-only `HPAC-PRESENTATION-EVIDENCE/2.0` write plus
  its provenance sidecar, canonically bound to the exact ceremony
  `(invocation_id, attempt_id)`, request digest, CSPRNG nonce, approval id,
  challenge id, presentation digest, approval-subject digest, principal,
  mechanism id, installation id, generation, installation digest, descriptor
  digest, renderer profile, human election outcome actually observed, freshness
  / expiry, and helper deployment generation. It authorises **no** descriptor,
  installation, proof, lifecycle, consumption, approval, Gate, runtime, adapter,
  or arbitrary-filesystem write (HPAC-PPA-REQ-043 preserved). It is seal-guarded,
  process-local, non-serialisable, non-copyable, restart-dead, single-use, and
  **never returned, minted as a factory result, or delivered** (there is no
  returnable writer). HPAC-PPA-REQ-042 / REQ-044 / REQ-045 / REQ-046 apply
  unchanged (issuance binding; failure consumes; re-entry returns
  stale/consumed; object-local state cannot mint authority).
- **HPAC-PPA-REQ-080.** **Bounded to the exact ceremony.** The helper SHALL NOT
  author presentation evidence for an unrelated request, session, subject, or
  helper generation. Its only input is a bound, valid, authenticated ceremony
  response it **independently re-checks** (HPAC-PPA-REQ-045). The
  `presentation_evidence_write` request SHALL NOT self-assert `approved`,
  `verified`, `human_present`, or `authenticated` — those arise only from their
  designated trusted mechanisms (the ceremony's authenticated `APPROVE` for
  `approved`; the RHAMP verifier for `verified` / `authenticated`; the genuine
  authenticator for `human_present`) (HPAC-PAWA-HELPER-REQ-071 alignment).
- **HPAC-PPA-REQ-081.** **Evidence-writer issuer disposition (REQ-052).**
  `pcae.core.protected_presentation` is **no longer** the evidence-writer issuer.
  The evidence-write authorization is **redefined as a protected-side-internal
  operation of the helper process** (option C of the phase authorisation §17):
  it never crosses a process boundary and is never minted, returned, serialised,
  or delivered. `pcae.core.protected_presentation` retains only §6 / §7
  integrity, currentness, request, and response mediation and receives a typed
  acknowledgement + evidence reference only. The `pcae.protected_presentation_helper`
  packaged helper gains the bounded evidence-write as the
  HPAC-PAWA-HELPER-001 §17 `presentation_evidence_write` operation. No `mint_*`
  factory returns a writer to any caller. The exact-name / no-authority-before-
  implementation clause of HPAC-PPA-REQ-052 is preserved.
- **HPAC-PPA-REQ-082.** **Helper response != evidence authority.** The typed
  response / acknowledgement the caller receives is a **distinct artifact** from
  the durable `HPAC-PRESENTATION-EVIDENCE/2.0` record. The process may emit both
  (a) the canonical protected evidence record and (b) a typed acknowledgement /
  evidence reference, but they remain distinct with distinct semantics. The
  caller SHALL NOT be able to reconstruct writer authority from the response
  (HPAC-PAWA-HELPER-REQ-073 alignment). helper response != evidence-writer
  authority != human approval != real authentication != Gate-5 result.
- **HPAC-PPA-REQ-083.** **PPA-INV-2 re-derivation.** PPA-INV-2 is re-derived as
  **PPA-INV-2 (v2.0)** — semantic separation of installation configuration,
  launcher mediation, presentation rendering, human election capture, evidence
  persistence, evidence verification, and helper response, each with separate
  preconditions, outputs, and failure states and no automatic promotion, **even
  when several run in one verified helper process**. The v1.0 four-action
  wording is preserved; only the implicit separate-process / separate-holder
  reading is removed.
- **HPAC-PPA-REQ-084.** **Relationship to HPAC-PAWA-HELPER-001 v1.0.**
  HPAC-PPA-001 owns presentation semantics, the definition of a valid
  `HPAC-PRESENTATION-EVIDENCE/2.0` record, and human-election semantics
  (`APPROVE` / `REJECT`). HPAC-PAWA-HELPER-001 v1.0 owns the general
  protected-authority-operation transport and process-boundary semantics; its
  §17 `presentation_evidence_write` operation is **the transport implementing
  this contract's §21 evidence-persistence action** — it carries the request
  bytes and returns the typed result; it does not redefine what valid evidence
  is. There is no circular authority: the helper protocol transports, this
  contract adjudicates validity. HPAC-PPA-001 does **not** duplicate the helper
  protocol's privileged-operation vocabulary, wire format, state model, or
  peer-authentication mechanism.
- **HPAC-PPA-REQ-085.** **Launcher role after evolution.**
  `pcae.core.protected_presentation` (launcher / mediator) SHALL: verify helper
  installation / integrity / currentness (§6 / §29 / §30); establish the
  protected one-shot launch and private parent/child channel (§7); invoke
  exactly one ceremony; pass the canonical request; receive a typed
  acknowledgement / evidence reference; and reconcile uncertainty against
  protected-root canonical evidence where required (HPAC-PPA-REQ-092). The
  launcher is **not** the human approver, the evidence writer, the
  authentication-proof verifier, a generic HPAC writer, a PB, or a runtime. The
  launcher SHALL NOT regain evidence-writer authority through any compatibility
  path, fallback, or degraded mode (HPAC-PPA-REQ-099).
- **HPAC-PPA-REQ-086.** **Helper role after evolution.** The verified helper MAY:
  validate the ceremony request; present the protected UI; capture
  `APPROVE` / `REJECT`; persist the one canonical presentation-evidence record;
  return a bounded acknowledgement / evidence reference; exit. The helper MAY
  NOT: authenticate the human merely from an `APPROVE`; mint a `PRODUCTION`
  `AuthenticatedHumanPrincipal`; perform arbitrary HPAC writes; mutate unrelated
  records; perform Gate 5; grant PB permission; enable a runtime capability;
  execute arbitrary commands; or export any reusable writer authority.
- **HPAC-PPA-REQ-087.** **No authority-object export.** Consistent with
  HPAC-PAWA-001 PAWA-INV-15 / PAWA-INV-16: no presentation-evidence writer
  object, handle, seal, token, or reconstructable authority crosses from the
  protected helper into the launcher, an ordinary PCAE process, a plugin, an
  agent, or a test fixture. The helper performs the exact persistence action
  itself. Named objects **and** semantic equivalents (a field set from which a
  working authority could be reconstructed) are covered.
- **HPAC-PPA-REQ-088.** **Helper provenance / same-file-object alignment.** The
  helper that conducts the ceremony **and** performs the evidence write is the
  **same** verified protected helper object / process, admitted under the §6 /
  §29 / §30 predicates: open with no symlink traversal; validate
  type / link-count / owner / mode / ACL; SHA-256 of the complete opened byte
  stream `== helper_sha256`; the **same opened file object** (or a
  platform-equivalent identity-preserving handle) used to `exec` — no pathname
  re-open gap; if the platform cannot `exec` the verified object without a
  substitution window, the implementation **STOPS BLOCKED** (HPAC-PPA-REQ-030,
  unchanged). The trust root is **unchanged**: OS filesystem write authority on
  the out-of-band-provisioned `<HPAC_PROTECTED_ROOT>` (PPA-INV-3), never an
  in-process check, never the helper hash / path / registration metadata alone.
  No second trust root is introduced.
- **HPAC-PPA-REQ-089.** **Private channel / peer authentication — logical
  properties.** Where the launcher / helper channel is relied on it SHALL be: a
  private one-shot channel unavailable to the requesting agent; with an
  OS-authenticated peer credential resolving to the deployment-owner principal
  (never the configured agent principal); bound to the actual channel; and
  failing closed **before** the protected operation on any mismatch. Peer
  authentication is infrastructure evidence only: peer credential != human
  identity, != human approval, != a real authenticator assertion. Platform
  syscalls are an implementation profile, not frozen here (HPAC-PPA-REQ-096).
- **HPAC-PPA-REQ-090.** **Freshness / ceremony currentness — preserved.** The
  helper SHALL NOT author trusted evidence for an expired ceremony, a consumed
  ceremony, the wrong session, the wrong subject, a replayed request, a stale
  installation generation, or a mismatched presentation mechanism. Rotation
  from G to G+1 before response verification supersedes the G request;
  revocation invalidates every outstanding response immediately
  (HPAC-PPA-REQ-050 / REQ-051 preserved). No response loss makes a consumed
  ceremony reusable (HPAC-PAWA-HELPER-REQ-074 / REQ-075 alignment).
- **HPAC-PPA-REQ-091.** **Failure / uncertainty state model.** The v2.0 ceremony
  and evidence-write path aligns with the HPAC-PAWA-HELPER-001 §20 mutating
  state model; at minimum these are distinct and non-collapsing:
  `CEREMONY_REQUEST_RECEIVED` → `CEREMONY_ADMITTED` → `PRESENTATION_STARTED` →
  `HUMAN_ELECTION_CAPTURED` → `EVIDENCE_WRITE_ATTEMPT_STARTED`
  (the no-auto-retry boundary) → `EVIDENCE_COMMITTED` → `RESPONSE_EMITTED`
  (exact repository names MAY differ). Presentation started != election
  captured != evidence committed != response received. A missing response is
  **not** proof that no evidence exists. Durable transitions
  (`EVIDENCE_COMMITTED`) are reconcilable from `<HPAC_PROTECTED_ROOT>`.
- **HPAC-PPA-REQ-092.** **No auto-retry.** Once `EVIDENCE_WRITE_ATTEMPT_STARTED`
  is crossed there SHALL be no automatic retry. The launcher / caller SHALL
  reconcile against the protected-root durable canonical evidence and SHALL NOT
  resend a spent one-shot ceremony request. A create-only record write is
  naturally reconcilable; response absence != proof the ceremony did not
  complete; receipt = evidence != authority (existing PCAE no-auto-retry
  principle; `TB-ARCH` §21; HPAC-PAWA-HELPER-REQ-082).
- **HPAC-PPA-REQ-093.** **Human-approval semantics — preserved exactly.**
  `APPROVE` and `REJECT` remain the human election outcomes, derived only from
  the actual protected presentation interaction. A protocol request field such
  as `approved=true` SHALL NOT create approval. YubiKey touch = user presence
  (UP); UP != approval; presentation-helper peer identity != human approval;
  launcher request != human approval; operation admission != human approval
  (HPAC-PPA-REQ-035 / REQ-056 preserved).
- **HPAC-PPA-REQ-094.** **Human authentication remains distinct.** Presentation
  evidence != authentication proof; `APPROVE` != authenticated principal;
  UP / UV != informed approval. Human-authentication proof still requires its
  own RHAMP / HPAC verification chain (HPAC-PPA-REQ-057 preserved). The
  presentation helper does **not** become the real-authentication verifier by
  virtue of being the evidence producer.
- **HPAC-PPA-REQ-095.** **Gate 5 / PB / runtime non-expansion.** Presentation
  evidence write != Gate 5 ALLOW; Gate 5 ALLOW != PB permission; PB permission
  != runtime capability; runtime capability != execution (HPAC-PPA-REQ-056
  preserved). Nothing in v2.0 grants a runtime capability, a plugin capability,
  `DispatchEnvelope` execution authority, Gate 6+ authority, adapter admission,
  or external-effect permission (HPAC-PPA-REQ-003 / §15 preserved).
- **HPAC-PPA-REQ-096.** **Mechanism neutrality / mobile future.** v2.0 does not
  hardcode YubiKey, FIDO2, a local TTY, USB, or a particular authenticator
  brand as the universal presentation / evidence mechanism. Current protected
  local presentation (`pcae-protected-local-presentation`) remains a supported
  profile (§2, unchanged). A future mobile-only / passkey / protected-mobile
  approval profile remains possible; HPAC-PPA-001 defines semantic properties,
  not one mandatory UI technology.
- **HPAC-PPA-REQ-097.** **Schema impact — NO SCHEMA CHANGE REQUIRED.**
  `HPAC-PRESENTATION-EVIDENCE/2.0` (HPAC-REQ-091/092), `HPAC-PRESENTATION-
  INSTALLATION/1.0`, `HPAC-PRESENTATION-CURRENT-GENERATION/1.0`, and
  `HPAC-WRITER-PROVENANCE/1.0` already express every field the v2.0 model
  needs. The producer's process location is **verification state**, not a
  caller-controlled evidence field (HPAC-PPA-REQ-047 / REQ-048 pattern). v2.0
  adds, changes, and removes **no** schema field. A change of authority holder
  does not imply an evidence-schema change.
- **HPAC-PPA-REQ-098.** **Failure-code / terminal-reason non-expansion.** The
  existing 21-value `pawa_failure_code` vocabulary and RHAMP's existing closed
  `terminal_reason_code` set (HPAC-PPA-REQ-075 / REQ-076, §18) already cover the
  evolved semantics. Helper-side evidence-write integrity / currentness /
  substitution failure → `helper_integrity_unverified`; malformed / unbound /
  duplicate response → `helper_response_untrusted`; rotation / revocation /
  restart supersession → `ceremony_superseded`; cancel / close →
  `ceremony_cancelled`; timeout → `ceremony_timed_out`; expiry →
  `challenge_expired`; a stale / reused helper-held write authorization →
  `capability_stale`. **No new `pawa_failure_code`; no new RHAMP
  `terminal_reason_code`.** RHAMP-001 v1.0 is byte-unchanged.
- **HPAC-PPA-REQ-099.** **Compatibility shims — no insecure fallback.** A
  compatibility shim MAY translate an old logical evidence-write request into
  the new typed ceremony / `presentation_evidence_write` request. It SHALL NOT
  recreate the v1.0 launcher-held `HPACWriterCapability`, mint an in-process
  writer, return a handle, transfer a writer to the helper, or permit two
  production authority paths. There is exactly **one** authoritative production
  model. The v1.0 launcher-held / `mint`-style in-process evidence-writer path
  is **superseded and non-production** as of v2.0 and SHALL NOT be relied on for
  production assurance; its code removal is a later governed
  in-process-path-removal slice (HPAC-PAWA-REQ-340 sequence), not this phase.
- **HPAC-PPA-REQ-100.** **Security-claim boundary (v2.0).** The evolved model MAY
  claim resistance to: a compromised ordinary PCAE interpreter; a malicious
  plugin in an ordinary process; in-process object introspection
  (`gc.get_objects()` / `gc.get_referrers()` / `__dict__` `exec`); a fake
  unprivileged helper; a forged ceremony request; replay; and a launcher-side
  attempt to fabricate presentation evidence without the verified helper. It
  SHALL NOT overclaim against: a hostile root / admin controlling protected
  artifacts; a compromised OS kernel; or a compromised registered presentation
  helper binary after an authorized protected-root mutation. Claims are bounded
  explicitly.
- **HPAC-PPA-REQ-101.** **Cross-contract consistency — resolved.** With v2.0,
  HPAC-PPA-001 now permits **exactly** the `presentation_evidence_write` model
  frozen by HPAC-PAWA-HELPER-001 v1.0 §17 and referenced by HPAC-PAWA-001 v2.0
  §42B note / §42F, **without weakening any human-approval or human-
  authentication wall** (HPAC-PPA-REQ-093 / REQ-094 / REQ-095 preserved). The
  blocking finding of N16-5-F-5-TB-CONTRACT-IV is resolved **at contract
  level**. HPAC-001 v2.1, RHAMP-001 v1.0, HBDC-001 v1.2, RIHAC-001 v2.0,
  RIASC-001 v3.0, RDGO-001 v3.1, HPAC-PAWA-001 v2.0, HPAC-PAWA-HELPER-001 v1.0,
  and the descriptor + current-generation schemas remain **byte-unchanged**.
  Implementation still requires the resolved-trio cross-contract IV first
  (HPAC-PPA-REQ-103).
- **HPAC-PPA-REQ-102.** **No production implementation in this phase.** The v2.0
  evolution changes no `src/pcae`, `scripts`, `pyproject.toml`, or `schemas`
  file; performs no protected-host mutation, no real ceremony, and no evidence
  write. Runtime remains **Observed / observe / unavailable** with **0
  plugins / 0 capabilities**; the first governed runtime external effect remains
  **ABSENT / UNREACHABLE**. N-16-6 / N-16-7 are untouched.
- **HPAC-PPA-REQ-103.** **Required successors (derived, NOT begun).** (1) A
  dedicated contract IV, alias **N16-5-F-5-PPA-CONTRACT-IV**, independently
  verifying the v2.0 version classification, the evidence-writer ownership
  transition, the removal of the launcher-held production writer, the
  no-authority-transfer property, the semantic trust-action separation, and
  compatibility with HPAC-PAWA-001 v2.0 + HPAC-PAWA-HELPER-001 v1.0; a MAJOR
  carries its own IV — **mandatory**. (2) Then a fresh or scoped cross-contract
  IV of the resolved trio HPAC-PAWA-001 v2.0 + HPAC-PAWA-HELPER-001 v1.0 +
  HPAC-PPA-001 v2.0, specifically confirming the previously blocking conflict is
  gone. (3) Then, subject to fresh human authorization for each, the
  HPAC-PAWA-REQ-340 implementation sequence (privileged helper + protocol
  implementation; caller integration; insecure in-process authority-path
  removal; packaging / clean-install; dedicated independent security IV;
  production deployment; and only then a fresh `N16-5-FINAL-CERT` on a fresh
  CPIPC-valid successor id — never reuse a completed or blocked certification
  identity, HPAC-PAWA PAWA-INV-11). This phase begins **none** of them.
  **F-5-B2 BLOCKED; F-5 CERTIFICATION BLOCKED; N-16-5 NOT CLOSED; N-16-6 /
  N-16-7 OPEN / UNTOUCHED (N-16-7 strictly last).**

## 21A. (v2.0) Delta table

| v1.0 clause | v1.0 meaning | v2.0 disposition |
|---|---|---|
| HPAC-PPA-REQ-041 (holder) | evidence-writer `HPACWriterCapability` *"held only by the trusted launcher mediator … never sent to the helper"* | **superseded** — authorization is process-local to the **verified helper**, performed **inside the helper process**; no writer object/handle/seal held by, returned to, or sent to the launcher or any caller (no returnable writer). All other REQ-041 properties preserved and tightened (§8 note; HPAC-PPA-REQ-077..079; PPA-INV-9) |
| HPAC-PPA-REQ-041 (properties) | seal-guarded, process-local, non-serialisable, non-copyable, restart-dead, single-use, request/generation-bound | **preserved**; additionally never on a heap shared with the requesting agent interpreter |
| HPAC-PPA-REQ-042..046 | issuance binding; one create-only write; failure consumes; re-entry stale/consumed; object-local state cannot mint | **preserved**, applied to the helper-held authorization (HPAC-PPA-REQ-079) |
| HPAC-PPA-REQ-052 (issuer) | `pcae.core.protected_presentation` is *"sole launcher/mediator **and evidence-writer issuer**"* | **superseded** — issuer role removed; evidence-write is a **protected-side-internal operation of the helper process** (`pcae.protected_presentation_helper`), never minted / returned / serialised / delivered (§10 note; HPAC-PPA-REQ-081) |
| HPAC-PPA-REQ-052 (names, no-authority-before-impl) | exact module names; confer no authority before implementation | **preserved** |
| HPAC-PPA-REQ-054 | *"evidence producer is only the launcher mediator after a response from the verified helper"* | **superseded** — sole producer is the **verified helper process** that conducted the ceremony, after one valid `APPROVE`; launcher receives a typed acknowledgement / evidence reference only. Canonical-consumer clause and "Gates never receive a writer" **preserved** (§10 note; HPAC-PPA-REQ-077 / REQ-082) |
| PPA-INV-2 | installer ≠ launcher ≠ helper response ≠ evidence writer, no authority transfer (implied separate process/holder) | **re-derived as PPA-INV-2 (v2.0)** — semantic separation with separate preconditions / outputs / failure states and no automatic promotion, **even in one verified helper process**; four-action wording preserved (HPAC-PPA-REQ-083) |
| HPAC-PPA-REQ-069 / REQ-070 | MAJOR.MINOR versioning rules | **applied** — this evolution is **MAJOR** (§14 note); widens nothing issued under v1.0 |
| everything else (§0–§18, PPA-INV-1, PPA-INV-3..8) | as frozen | **byte-unchanged** |
| `HPAC-PRESENTATION-EVIDENCE/2.0` and all schemas | as frozen | **byte-unchanged** — no field added / changed / removed (HPAC-PPA-REQ-097) |
| `pawa_failure_code` (21) / RHAMP `terminal_reason_code` | as frozen | **byte-unchanged** — no new code (HPAC-PPA-REQ-098) |

## 22. (v2.0) Freeze verdict

**FROZEN (v2.0):** the one `HPAC-PRESENTATION-EVIDENCE/2.0` record for a ceremony
is authored **by the verified protected presentation helper process** that
conducted that ceremony, after one valid `APPROVE`, as the
HPAC-PAWA-HELPER-001 v1.0 §17 `presentation_evidence_write` operation; the
bounded write authorization is process-local to the helper and **no
evidence-writer object / capability / handle / seal / reconstructable descriptor
crosses any process boundary** (PPA-INV-9); `pcae.core.protected_presentation`
remains the sole launcher / mediator and is **no longer** the evidence-writer
issuer, receiving a typed acknowledgement / evidence reference only; PPA-INV-2 is
re-derived as **semantic** trust-action separation preserved even within one
verified helper process (PPA-INV-2 (v2.0)); presentation rendering, human
election capture, evidence persistence, helper response, human authentication,
Gate 5, PB permission, runtime capability, and execution remain **distinct** and
none implies another (HPAC-PPA-REQ-093..095); the single trust root is
**unchanged** (OS filesystem write authority on the out-of-band protected root;
no second trust root); **no schema change, no new failure code, no `src/pcae` /
`scripts` / `pyproject.toml` / `schemas` change, no protected-host mutation, no
ceremony**; every v1.0 requirement body is byte-verbatim; HPAC-001 v2.1,
RHAMP-001 v1.0, HBDC-001 v1.2, RIHAC-001 v2.0, RIASC-001 v3.0, RDGO-001 v3.1,
HPAC-PAWA-001 v2.0, HPAC-PAWA-HELPER-001 v1.0 byte-unchanged and now
semantically consistent (the N16-5-F-5-TB-CONTRACT-IV blocking conflict is
resolved at contract level).

Protected presentation and Gate real-assurance consumption remain **NOT
IMPLEMENTED**. The dedicated IV **N16-5-F-5-PPA-CONTRACT-IV** is derived and
**NOT begun**. N-16-5 remains **NOT CLOSED**. Runtime remains **Observed /
observe / unavailable**. First external effect remains **ABSENT / UNREACHABLE**.
N-16-6 / N-16-7 remain **OPEN / UNTOUCHED** (N-16-7 strictly last).

Protected presentation and Gate real-assurance consumption remain **NOT
IMPLEMENTED**. N-16-5 remains **NOT CLOSED**. Runtime remains **Observed /
observe / unavailable**. First external effect remains **ABSENT**.
