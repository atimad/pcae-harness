# HPAC-PPA-001 v1.0 — HPAC Protected Presentation Installation and Evidence Authority Contract

## Contract identity and status

**Contract:** HPAC-PPA-001  
**Version:** 1.0  
**Status:** FROZEN — IMPLEMENTATION AND INDEPENDENT VERIFICATION PENDING  
**Frozen by:** Phase
149O.20L.7O.3W.1R.2B.1R.1.1R.30R.4R — N-16-5 Protected-Presentation
Helper Installation and Evidence-Writer Authority Contract Reconciliation.  
**Parent semantics:** HPAC-001 v2.1, especially HPAC-REQ-079/080/090..093.  
**Concrete profile:** RHAMP-001 v1.0, especially RHAMP-REQ-014..016,
082..090, 143..148.  
**Protected administration:** HPAC-PAWA-001 v1.2.  
**Scope:** the missing authority and currentness layer for installing and
pinning the fixed local protected-presentation helper, launching exactly that
helper, authenticating its one-shot response, and writing one canonical
`HPAC-PRESENTATION-EVIDENCE/2.0` record. This contract adds no UI, helper,
production writer, Gate integration, runtime capability, adapter, or effect.

Historical HPAC-PAWA-001 v1.1 and the historically BLOCKED `.30R.4` report are
not rewritten. HPAC-001 v2.1 and RHAMP-001 v1.0 already define the descriptor,
presentation evidence, attestation, display, and response semantics; this
companion contract supplies the previously absent installation/currentness and
writer-issuance specialization without changing either parent.

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
- **HPAC-PPA-REQ-053.** The only standalone administration entry point is
  `scripts/hpac_protected_presentation_admin.py`. It may call only the exact
  admin module. It is never a `pcae` CLI subcommand or runtime consumer.
- **HPAC-PPA-REQ-054.** Evidence producer is only the launcher mediator after a
  response from the verified helper. Canonical consumers are only the existing
  presentation resolver and HPAC verifier path, followed by frozen Gate 5/Gate
  9 consumers after the future implementation. Gates never receive a writer.
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

## 20. Freeze verdict

**FROZEN:** deployment-owner PAWA authority registers only protected metadata;
helper bytes are externally installed and content-addressed; the one new PAWA
mutation is `configure_presentation_mechanism`; the one new consumer is
`pcae.core.hpac_protected_presentation_admin`; the exact installation and
current-generation schemas are frozen; runtime evidence writer role is the
distinct existing `protected_presentation_mechanism`, issued process-locally by
the trusted launcher mediator and bound to one request/current helper generation;
HPAC/RHAMP/writer-provenance remain unchanged; N-16-6 receives no authority.

Protected presentation and Gate real-assurance consumption remain **NOT
IMPLEMENTED**. N-16-5 remains **NOT CLOSED**. Runtime remains **Observed /
observe / unavailable**. First external effect remains **ABSENT**.
