# HPAC-PAWA-001 v1.2 — HPAC Production Protected Administration Writer Anchor Contract

## Contract identity and status

**Contract:** HPAC-PAWA-001
**Version:** 1.2
**Status:** FROZEN
**Frozen by:** Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2 — HPAC-PAWA-001 v1.0
Production Protected-Admin Writer Anchor Contract Freeze (initial freeze,
`HPAC-PAWA-REQ-001..163`, `PAWA-INV-1..11`).
**Evolved to v1.1 by:** Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A.2 —
HPAC-PAWA-001 v1.1 Configured-Agent-Principal Resolution Source Contract Freeze
(**MINOR**; sole normative delta; adds the `HPAC-PAWA-AGENT-EXCLUSION/1.0`
protected recognition-input artifact — §32A — and the `agent_exclusion_digest`
field on `HPAC-PAWA-CURRENT-GENERATION/1.0` — §20A; names the configured-agent
resolution source in §2 / §9 / §10 / §33; `HPAC-PAWA-REQ-164..218`;
`PAWA-INV-12`; no `src/pcae` change; no new `pawa_failure_code`; no descriptor
schema change; HPAC-001 v2.1, RHAMP-001 v1.0, HBDC-001 v1.2 byte-unchanged;
the v1.0 freeze record is **not** rewritten — v1.1 is append-only evolution).
**Evolved to v1.2 by:** Phase
149O.20L.7O.3W.1R.2B.1R.1.1R.30R.4R — N-16-5 Protected-Presentation
Helper Installation and Evidence-Writer Authority Contract Reconciliation
(**MINOR**; adds exactly one protected-presentation configuration mutation
family, one exact admin-only consumer category, and mechanism/configuration
transaction issuance scope; executable bytes remain out-of-band
administrator-installed and runtime presentation evidence remains outside PAWA
under HPAC-PPA-001 v1.0; no new `pawa_failure_code`, no change to R1-HYBRID,
non-bearer, one-operation, root, or recognition semantics; no production
implementation; fresh IV required).
**v1.0 → v1.1 delta:** §7A (delta table), §32A, §20A, §80 (S-1), §94 (history),
§95A (R1/R2/R3/R4 disposition). Incorporates the three
`.1R.30R.2A.1` independent-verification corrections: **C-1** (R1-HYBRID
identity model), **C-2** (anchor-digest rollback binding), **S-1** (explicit
MINOR versioning rule); **C-3** (a dedicated v1.1 contract IV,
`.1R.30R.2A.3`) is recommended downstream (§95A, §96A).
**Adjudication baseline (v1.1):** Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A —
Configured-Agent-Principal Resolution Source Contract-Compatibility Adjudication
(verdict **B — HPAC-PAWA-001 v1.1 MINOR**; resolution **R1**), independently
**VERIFIED WITH CORRECTIONS** by Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A.1
(R1 direction sound; corrected R1-PURE → **R1-HYBRID**; C-1 / C-2 / C-3 / S-1).
**Adjudication baseline:** Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R — HPAC-REQ-022/023
Production Protected-Admin Writer Anchor: Architecture and Contract Adjudication
(`docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_HPAC_REQ_022_023_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_ARCHITECTURE_AND_CONTRACT_ADJUDICATION.md`);
independently verified by Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.1 — Independent
Verification of the .1R.30R Production Protected-Admin Writer Anchor Adjudication
(`docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_1_INDEPENDENT_VERIFICATION_OF_THE_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_ADJUDICATION.md`;
verdict **ADJUDICATION VERIFIED**, three non-blocking findings F-1 / F-2 / F-3
handed to this phase).
**Independent verification:** Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.4 (of the
`.1R.30R.3` writer-anchor + registry + mechanism implementation). A dedicated
contract-freeze IV of this document MAY be folded into `.1R.30R.4` at the
authorizing operator's discretion, matching the `.1R.29` → `.1R.31` precedent.
**Scope:** the positive production recognition mechanism for the external
deployment-owner protected administration authority required by HPAC-REQ-022/023,
and the conditions under which a bounded **PRODUCTION** `HPACWriterCapability`
may be minted — the *mechanism* HPAC-001 v2.1 §7 deliberately deferred while
freezing only the *policy*. HPAC-PAWA-001 defines: deployment-owner recognition
= filesystem write authority on the protected root + not-configured-agent-principal
+ a root-identity-bound `.authority/` descriptor; the one-time out-of-band
provisioning / bootstrap procedure and its bounds; the
`HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0` closed schema including an explicit
monotonic `generation` and rollback-prevention rule (finding F-3); the positive
validation sequence and per-predicate identity matrix (finding F-1); PRODUCTION
`HPACWriterCapability` minting, operation / principal / credential scope,
process-local non-bearer lifetime, restart invalidation, one-operation lifetime;
descriptor rotation / revocation / machine migration / reprovisioning; the
non-agent-importable admin writer module + consumer-inventory guard obligation;
the failure taxonomy and its deterministic mapping onto RHAMP-001 v1.0 §49; the
audit-evidence model; the security-claim boundaries.
**Production surface (future — not created by this contract; realised by
`.1R.30R.3`, finding F-2):** `src/pcae/core/hpac_foundation.py` (a new
`PRODUCTION` writer path exercised through the existing seal discipline; schema
byte-unchanged), a new non-agent-importable admin writer module (recommended
`src/pcae/core/hpac_protected_admin_writer.py`), a new out-of-band provisioning
script (recommended `scripts/hpac_protected_root_admin.py`),
`src/pcae/core/human_principal_registry.py` (production writer path exercised;
`CredentialRecord` byte-unchanged), and the new authority descriptor artifact
under `<HPAC_PROTECTED_ROOT>/.authority/`.
**Related contracts:** HPAC-001 v2.1
(`HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md` — the parent; HPAC-PAWA-001 fills
its §7 mechanism gap and changes none of its text; HPAC-001 stays **v2.1**,
`HPAC-AUTHORITY-CONSUMPTION` stays `/2.1`), RHAMP-001 v1.0
(`REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md`
— RHAMP-REQ-047 points to this anchor as "the trust anchor … external to PCAE";
RHAMP-001 stays **v1.0, byte-unchanged**; the failure taxonomy maps onto
RHAMP-001 §49 with **no new `terminal_reason_code`**), HBDC-001 v1.2
(`HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` — **precedent, not a shared authority
root**; the two-OS-principal protected-root writer boundary,
HBDC-REQ-001..021 / HBDC-REQ-056/066, re-applied under HPAC's independent
namespace), RIHAC-001 v2.0 / RIASC-001 v3.0 (unaffected; §12 cond 7 consumes
HPAC evidence, wire shape unchanged), HPSE-001 v1.1 / HHCE-001 (independent
`*-REQ-###` namespace precedent, admin-ceremony pattern precedent only),
REPRC-001 v1.0 / PBNDE-001 v1.0 / RHAMP-001 v1.0 (the companion-contract shape
this contract follows exactly — a companion born to avoid a parent cascade),
CPIPC-001 v1.0 (`CANONICAL_PHASE_ID_PARSING_CONTRACT.md` — successor phase-ID
grammar).

HPAC-PAWA-001 is a **companion** contract. It introduces **no** HPAC-001 schema
change, **no** HPAC-001 version bump, **no** RHAMP-001 / RIHAC-001 / RIASC-001 /
HBDC-001 change, **no** RDGO-001 state-machine change, no gate reorder, no
first-effect-boundary move, no merge of the
authentication / presence / verification / informed-intent / approval /
PB-permission / Runtime-Enforcement / runtime-capability / execution concerns.
The current lineage is **HPAC-PAWA-001 v1.0 → v1.1 → v1.2**, both evolutions
MINOR. The v1.2 companion HPAC-PPA-001 v1.0 is new; every pre-existing contract
other than HPAC-PAWA-001 remains byte-unchanged.

This is a contract-freeze document. It creates no protected root, installs no
descriptor, mints no writer capability, writes no registry, implements no writer
factory, provisioning script, or consumer-inventory guard, touches no hardware,
resolves no OS account, reads no OS account database, and enables execution on
no path. The v1.1 and v1.2 evolutions add normative text only — no
`hpac_pawa_agent_exclusion.py`, no `resolve_configured_agent_identity()`, no
`agent-exclusion.json` schema helper, no `pwd` / `grp` call. Runtime remains
`not_implemented` / `Observed` / `observe` / `unavailable`; 0 plugins /
0 capabilities. The first external effect remains **ABSENT**.

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved.

---

## 0. Normative language

`SHALL`, `SHALL NOT`, `MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, `MAY` are
normative (RFC 2119, as used throughout this repository's bound contracts). Every
normative sentence carries a unique requirement ID `HPAC-PAWA-REQ-###`,
sequential from 001, no gaps, no duplicates. `HPAC-PAWA-REQ-*` is an independent
numbering namespace (HPSE-001 / RHAMP-001 precedent). Security invariants carry a
separate `PAWA-INV-#` label (§92). Unknown, missing, conflicting, malformed, or
unverifiable facts **fail closed**: no descriptor is trusted, no positive
recognition succeeds, no `PRODUCTION` `HPACWriterCapability` is minted, no
registry mutation occurs, and a terminal failure code (§56) is recorded where a
lifecycle event can be persisted. The absence of a denial is never authority. An
ambiguity at any authority boundary fails closed.

---

## 1. Position under HPAC-001 v2.1 — companion, not amendment

- **HPAC-PAWA-REQ-001.** HPAC-PAWA-001 fills exactly one HPAC-001 v2.1 gap: the
  *mechanism* of the §7 positive production protected-admin writer anchor
  (HPAC-REQ-022's owner-recognition half, HPAC-REQ-023's bootstrap-anchor half).
  It SHALL NOT redefine, relax, widen, or reinterpret any HPAC-001 requirement,
  wall, schema, digest rule, assurance level, or trust boundary. Where
  HPAC-PAWA-001 and HPAC-001 appear to conflict, **HPAC-001 governs** and the
  implementing phase STOPS (BLOCKED).
- **HPAC-PAWA-REQ-002.** The HPAC-001 extension points HPAC-PAWA-001 fills are
  exactly: (a) HPAC-REQ-022's "owned and writable only by an OS/equivalent
  protected administration principal unavailable to ordinary same-user agent
  execution" — the concrete recognition predicates (§25–§32); (b) HPAC-REQ-023's
  "externally established deployment-owner administration principal … terminates
  bootstrap without circular PCAE self-authorization" — the concrete out-of-band
  provisioning procedure and the `.authority/` descriptor that anchors it
  (§11–§24); (c) the `HPACWriterCapability` type's `PRODUCTION` minting path,
  left `raise HPACAuthorityError("no production HPAC writer is implemented in
  this foundation phase")` by `hpac_foundation.py` — the scope / lifetime / seal
  discipline of the production capability (§36–§49); (d) HPAC-REQ-024's
  "available only in the protected administration context and never as an
  ordinary `pcae` CLI … A same-UID agent invocation SHALL be denied" — the
  non-agent-importable module + consumer-inventory guard obligation (§37–§39);
  (e) HPAC-REQ-080's "only the external protected deployment administration
  principal may configure" — the configuration-authority binding (§9, §11).
- **HPAC-PAWA-REQ-003.** Every existing normative contract is byte-unchanged by
  this freeze. The `.1R.30R.2` finalization SHALL independently prove
  `git diff --name-only <entry> HEAD -- docs/contracts` names exactly the
  HPAC-PAWA-001 file and `git diff <entry> HEAD -- src/pcae` is empty.
- **HPAC-PAWA-REQ-004.** HPAC-PAWA-001 v1.0 makes NON_REAL / `FIXTURE_NON_REAL`
  authority objects **no more upgradeable** than HPAC-001 v2.1 already makes
  them. A `FIXTURE_NON_REAL` `HPACStoreAuthority`, its fixture writer, and
  `ProtectedAdminCapability` remain permanently non-real and never reach the
  `PRODUCTION` writer path this contract freezes (§41).
- **HPAC-PAWA-REQ-005.** HPAC-001 stays **v2.1**; `HPAC-AUTHORITY-CONSUMPTION`
  stays `/2.1`; RHAMP-001 stays **v1.0**. This contract is additive and
  authority-preserving: it opens a *positive* path where today there is only a
  wall, without removing, relaxing, widening, or re-meaning any existing wall.
  Per the REPRC-001 / PBNDE-001 / RHAMP-001 precedent, a **new companion
  contract** is the correct home; a MINOR or MAJOR to HPAC-001 would force
  re-independent-verification of an actively-referenced frozen contract and a
  parent cascade (RIHAC-001 §12 cond 7 names "HPAC-001 v2.1" literally;
  RHAMP-001 pins "HPAC-001 v2.1").

## 2. Terminology

- **Configured agent principal** — the OS identity under which the autonomous
  PCAE agent/runtime is *configured to execute* for this deployment, resolved
  from canonical PCAE agent configuration (HBDC-001 §3's `PCAE_AGENT_PRINCIPAL`
  for a Class-B deployment; §9 of this contract). It is **not** `os.geteuid()`
  of whatever process happens to be running (finding F-1). **v1.1** names the
  concrete canonical resolution source: the `HPAC-PAWA-AGENT-EXCLUSION/1.0`
  protected record (§32A).
- **Configured-agent-principal resolution source** (v1.1) — the
  `HPAC-PAWA-AGENT-EXCLUSION/1.0` record at
  `<HPAC_PROTECTED_ROOT>/.authority/agent-exclusion.json` (§32A): a protected,
  deployment-owner-provisioned, agent-unwritable, installation- and
  generation-bound record that names the configured agent principal's
  **symbolic OS account** and pins its **`provisioned_uid`**. `(uid, gids)` is
  resolved **live** from the OS account database at every §33 recognition. It
  is the source HPAC-PAWA-REQ-021 requires the implementation to name; it is
  **not** the invoking process, not the deployment owner, not a human
  principal, not a logical `agent_id`, not caller input, not a mutable
  environment variable, not a static `(uid, gids)` snapshot.
- **`ConfiguredAgentAuthorityIdentity`** (v1.1) — the OS authority identity
  `(uid, gids)` that corresponds to the configured PCAE agent principal for the
  purpose of evaluating protected-root write authority in §33 steps 3 and 7,
  obtained by resolving the resolution source live. Its authority basis is
  **live effective filesystem write access**, never the uid integer itself.
- **Deployment-owner protected administration authority** (short: *deployment
  owner*) — HPAC-REQ-023's "externally established deployment-owner
  administration principal": the OS identity that owns `<HPAC_PROTECTED_ROOT>`
  and its `.authority/` subtree out of band, is a **distinct account** from the
  configured agent principal, and holds real filesystem write authority the
  configured agent principal provably lacks. It is a **filesystem-ownership
  role**, not a persistent cryptographic principal identity and not a civil
  identity.
- **`<HPAC_PROTECTED_ROOT>`** — `HPACStoreAuthority.production().root`, resolved
  by `resolve_hpac_protected_root()` from a fixed platform-keyed constant
  (macOS `/Library/Application Support/PCAE/HPAC/protected-root`, Linux
  `/etc/pcae/hpac/protected-root`). No override input is accepted (HPAC-REQ-022;
  `hpac_foundation.py`).
- **Authority namespace** — `<HPAC_PROTECTED_ROOT>/.authority/` (the existing
  `_AUTHORITY_DIR`), which already holds the `HPAC-STORE-AUTHORITY/1.0` manifest,
  `HPAC-WRITER-PROVENANCE/1.0` records, and the writer lock. §12.
- **Authority descriptor** — the `HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0` record
  (§13–§14) that declares the deployment owner and carries the monotonic
  `generation` (§20). Its schema is **byte-unchanged** in v1.1.
- **Agent-exclusion record** (v1.1) — the `HPAC-PAWA-AGENT-EXCLUSION/1.0`
  record (§32A), a sibling of the authority descriptor in the same `.authority/`
  namespace, transitively bound to it by shared `installation_id` and by the
  `HPAC-PAWA-CURRENT-GENERATION/1.0` anchor's `agent_exclusion_digest` (§20A).
- **Current-generation anchor** — the `HPAC-PAWA-CURRENT-GENERATION/1.0` record
  (§20 / §20A). **v1.1** adds one field, `agent_exclusion_digest`, so the single
  monotonic atomic-replace anchor is authoritative for **both** the descriptor
  and the agent-exclusion record.
- **Positive write probe** — an operation-based proof (§28–§30) that *the
  current administrative invocation* holds real OS-authorized write capability
  over the authority namespace *now* — distinct from the *negative* boundary
  check that the configured agent principal *cannot* write it.
- **PRODUCTION `HPACWriterCapability`** — an `HPACWriterCapability` whose
  `authority_class is HPACAuthorityClass.PRODUCTION`, minted only by the §33
  positive validation sequence, bound as §41–§49 require.
- **Admin writer module** — the new non-agent-importable module (recommended
  `src/pcae/core/hpac_protected_admin_writer.py`) that exports the `PRODUCTION`
  writer factory. §37.
- **Provisioning** / **bootstrap** — the one-time out-of-band creation of
  `<HPAC_PROTECTED_ROOT>`, the store-identity manifest, the authority descriptor
  at `generation` 1, and a durable provenance entry, performed by the deployment
  owner. §23.
- **Trusted computing base (TCB)** — §8.

## 3. Scope and non-goals

- **HPAC-PAWA-REQ-006.** HPAC-PAWA-001 governs **only** the production
  protected-admin *writer anchor* — recognition of the deployment owner and the
  minting of a bounded `PRODUCTION` `HPACWriterCapability`. It does not redefine
  human approval identity, RHAMP-001 authentication, the protected presentation
  mechanism, Permission Broker permission, Runtime Enforcement, runtime
  capability, adapter admission, or execution authority.
- **HPAC-PAWA-REQ-007.** HPAC-PAWA-001 does not create real protected state, real
  OS principals, real filesystem permissions, or a real writer capability. It
  does not authorize `.1R.30R.3` (implementation), `.1R.30R.5` (protected
  presentation), N-16-6, N-16-7, or Slice C. Each of those requires its own
  separately authorized governed phase.
- **HPAC-PAWA-REQ-008.** HPAC-PAWA-001 does not itself satisfy any governing
  election / human-authorization condition. A real deployment-owner provisioning
  remains a real out-of-band administrative act, required regardless of this
  text existing (HBDC-REQ-069 discipline).
- **HPAC-PAWA-REQ-009.** HPAC-PAWA-001 does not claim resistance to a fully
  compromised OS root / admin account (§8, §60). It does not claim cryptographic
  executed-source attestation. It does not add a signing key, a pinned
  verification key, an OS keychain / keyring secret, a network service, a cloud
  token, or an external identity provider (§62, §64).

## 4. Real `mechanism` for deployment-owner recognition — the trust root

- **HPAC-PAWA-REQ-010.** The deployment-owner recognition trust root is
  **OS filesystem write authority on the out-of-band-provisioned
  `<HPAC_PROTECTED_ROOT>`**, owned by the deployment owner, provably not
  writable by the configured agent principal. This is the identical trust root
  HBDC-001 v1.2 froze and Phase 149O.20C independently verified for the
  structurally identical HATP Class-B Protected Root writer boundary
  (HBDC-REQ-001..021; `hatp_deployment_binding_admin.py`: "Real security
  boundary: OS filesystem write permission on the Protected Root, never an
  in-process check").
- **HPAC-PAWA-REQ-011.** Recognition is a **composition** of four required
  conjuncts (§33), each contributing a distinct security property; removing any
  one re-opens a named threat (§20 attack matrix). No single conjunct — least of
  all the descriptor file's mere presence at the correct path — is sufficient
  (§18, PAWA-INV-3).
- **HPAC-PAWA-REQ-012.** No cryptographic principal identity, enrolled FIDO2
  credential, civil identity, `sudo` invocation, `euid == 0`, environment
  variable, repository / task / Git / session identity, OS username, or
  "first process / user to run enrollment" is, in whole or in part, the
  deployment-owner recognition predicate (§34, §35, PAWA-INV-1, PAWA-INV-6).

## 5. What HPAC-PAWA-001 does NOT redefine (walls preserved)

- **HPAC-PAWA-REQ-013.** All HPAC-001 v2.1 walls are preserved verbatim:

  ```
  root / euid 0             != deployment-owner authority
  sudo invocation           != deployment-owner authority
  OS username               != any principal
  same UID                  != protected-admin authority
  configured agent identity != deployment-owner authority
  session identity          != protected-admin authority
  file under protected root != trusted provenance
  valid descriptor bytes    != trusted anchor
  trusted writer capability != AuthenticatedHumanPrincipal
  writer capability         != approval proof
  writer capability         != PB permission
  writer capability         != Runtime Enforcement result
  writer capability         != runtime capability
  writer capability         != DispatchEnvelope
  writer capability         != execution
  ```

- **HPAC-PAWA-REQ-014.** The `PRODUCTION` writer capability authorizes **only**
  the bounded administrative mutations of §42. It never approves a runtime
  operation, never satisfies Gate 5 / 6 / 7 / 8 / 9 / 10, never creates a
  `DispatchEnvelope`, never overrides a no-go, and never transitions the runtime
  out of `Observed` / `observe` / `unavailable` (§67, §68, PAWA-INV-8).

## 6. Contract-home and companion-contract determination

- **HPAC-PAWA-REQ-015.** The adjudication (`.1R.30R` §16) and its IV
  (`.1R.30R.1` §20, §27.3) independently concluded: **NEW COMPANION CONTRACT
  REQUIRED**, not (A) leave the mechanism implementation-defined [would hide
  normative trust decisions in code — phase-prompt §35], not (C/D) an HPAC-001
  MINOR/MAJOR [additive, authority-preserving; a bump cascades], not (E) BLOCKED
  [no circularity, no MAJOR redesign, no remote infrastructure, no reusable
  same-UID bearer secret; HBDC-001 is a direct IV'd precedent]. This contract
  freezes that verdict.
- **HPAC-PAWA-REQ-016.** File home:
  `docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`,
  independent `HPAC-PAWA-REQ-###` namespace (HPSE-001 precedent). HPAC-PAWA-001
  is **not** one of HMIC-001's bound contracts and its bytes do not participate
  in any `implementation_scope_digest`; that disposition MAY be revisited by a
  future amendment (HBDC-REQ-047..049 precedent), never silently.

## 7. Contract purpose (normative statement)

- **HPAC-PAWA-REQ-017.** HPAC-PAWA-001 specifies the positive production
  recognition mechanism for the external deployment-owner protected
  administration authority required by HPAC-REQ-022/023, and the conditions
  under which a bounded PRODUCTION `HPACWriterCapability` may be minted. It does
  NOT redefine: human approval identity; RHAMP authentication; PB permission;
  Runtime Enforcement; runtime capability; execution authority; adapter
  admission.
- **v1.1 note.** The purpose is **unchanged**. v1.1 does **not** add human
  authentication, runtime approval, PB authority, or widened writer authority;
  it does not change Runtime Enforcement and does not enable execution. It
  *implements* — does not widen — a recognition input v1.0 already requires
  (§32A). The `PRODUCTION` `HPACWriterCapability` still authorizes only the §42
  bounded administrative mutations.

## 7A. v1.0 → v1.1 normative delta table

| Area | v1.0 | v1.1 | Compatibility | Reason |
|---|---|---|---|---|
| configured-agent resolution source | "canonical PCAE agent configuration / lock semantics" — a source that **did not exist** in `src/pcae` (finding F-1) | the `HPAC-PAWA-AGENT-EXCLUSION/1.0` protected record at `.authority/agent-exclusion.json` (§32A), explicitly named in §2 / §9.1 / §10 / §33 | **MINOR** — tightens an unresolvable predicate to a resolved one (HPAC-PAWA-REQ-153, S-1) | §9 / §73 already required the implementation to *name* the source; it must be *created*, and a §33 predicate consults it — a normative delta, not code detail (`.1R.30R.2A` §7.2) |
| exclusion record | none; the descriptor's `configured_agent_exclusion_binding` recorded only *kind* + *basis* | a sibling closed record (`symbolic_account` + `provisioned_uid` + installation / root / generation / provenance / digest / state) — §32A.1 | additive; MINOR (S-1) | a closed, generation-bound, agent-unwritable protected artifact — the correct home per `.1R.30R.2A` §7.4 / §7.6 |
| account-instance binding | n/a | **R1-HYBRID** (C-1): `symbolic_account` **and** `provisioned_uid`; live `getpwnam(name).pw_uid == provisioned_uid` at every §33 recognition | tightening; MINOR | closes the delete → recreate-under-a-new-uid silent-rebind path; resolves `.1R.30R.2A` §6-vs-§12.2 internal inconsistency (`.1R.30R.2A.1` §7.7) |
| live group resolution | n/a | the account's **current** primary + supplementary groups enumerated **live** at every §33 recognition; never persisted as authority (§32A.6, PAWA-INV-12) | additive; MINOR | detects post-provisioning privilege-group drift; a static gid snapshot is unsafe (`.1R.30R.2A.1` §7.4) |
| `HPAC-PAWA-CURRENT-GENERATION/1.0` schema | closed 6-field set | closed 7-field set — adds `agent_exclusion_digest` (§20A); schema id kept `/1.0` (internal monotonic anchor; contract version governs its shape) | additive; MINOR (§29 adjudication) | C-2 — binds the exclusion record's currentness into the single monotonic anchor |
| exclusion-record rollback | n/a | independent rollback **impossible** (§20A / §32C): a restored superseded record whose digest ≠ the anchor fails closed (`agent_principal_unknown`) | tightening; MINOR | C-2 — a bare `generation`-integer equality is not sufficient (`.1R.30R.2A.1` §7.11) |
| `HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0` schema | closed 13-field set | **byte-unchanged** | no change | §14 / HPAC-PAWA-REQ-037 preserved — the account identity lives in the sibling record, not the descriptor |
| positive write probe (§28) | `O_EXCL \| O_NOFOLLOW` create-and-unlink of a sentinel under `.authority/`, live invoking process | **unchanged** | no change | v1.1 does not replace the positive current-context probe |
| §33 recognition sequence | 11 steps | **11 steps** — steps 2 / 3 / 7 gain explicit atomic `HPAC-PAWA-AGENT-EXCLUSION/1.0` substeps (§33) | no step-count change; MINOR | HPAC-PAWA-REQ-045 preserved; the resolution is atomic with unit A1 |
| `pawa_failure_code` taxonomy | 21 closed values → RHAMP §49 #1 / #2 / #40 / #41 | **21 closed values, unchanged**; every v1.1 rejection maps onto #3 / #4 / #14 / #19 / #21 (§42A); RHAMP map unchanged | no change | no vocabulary expansion assumed for a MINOR |
| provisioning | root + manifest + `deployment-owner.json`@gen1 + `current-generation.json`@1 + provenance | **also** `agent-exclusion.json` (create-only) + `agent_exclusion_digest` into the anchor (§32B) | additive; MINOR; still **non-circular** | one extra filesystem write + one OS-account-DB read (PAWA-INV-4) |
| rotation / reprovision | descriptor rotation only | **also** an explicit `set-agent-exclusion` rotation when the agent OS account changes (§32B.4) | additive; MINOR | account rename / deletion / replacement is always a deliberate protected act |
| versioning rule | HPAC-PAWA-REQ-152 / 153 | **also** S-1 (§80.1 / HPAC-PAWA-REQ-211): a closed generation-bound protected recognition-input artifact that resolves an already-required predicate is a MINOR | additive; codifies the classification | so future readers do not re-derive it from the absence of a MAJOR trigger (`.1R.30R.2A.1` §10.2, S-1) |
| implementation traceability | §73 | **also** HPAC-PAWA-REQ-207 (v1.1 clause → symbol → test → guard map) + HPAC-PAWA-REQ-208 / 209 (new `hpac_pawa_agent_exclusion.py` surface + guards) | additive spec for `.1R.30R.3.1` | no prose-only security guarantee (RHAMP-REQ-164 discipline) |
| contract IV | v1.0 IV MAY fold into `.1R.30R.4` | v1.1 IV is a **dedicated** `.1R.30R.2A.3` (C-3), foldable into `.1R.30R.3.2` only at explicit operator discretion (§76 / HPAC-PAWA-REQ-210, §96A) | recommendation | a new protected authority input warrants its own IV (`.1R.30R.2A.1` §13.2) |

## 8. Trusted computing base

- **HPAC-PAWA-REQ-018.** The OS filesystem protection model for the
  out-of-band-provisioned `<HPAC_PROTECTED_ROOT>` is part of the trusted
  computing base. The contract assumes: (a) the configured agent principal lacks
  write authority to `<HPAC_PROTECTED_ROOT>` and every ancestor up to the point
  the agent has no write at all; (b) the deployment-owner protected
  administration context possesses the required OS write authority; (c) a fully
  compromised OS root / admin boundary is **outside this contract's threat
  model** unless a parent contract says otherwise.
- **HPAC-PAWA-REQ-019.** HPAC-PAWA-001 SHALL NOT be represented as, and its
  implementation SHALL NOT claim, resistance to root compromise, executed-source
  cryptographic attestation, or hardware assurance. It establishes
  admin-controlled, agent-unwritable **filesystem authority** only (HBDC-REQ-041
  discipline).
- **HPAC-PAWA-REQ-020.** The attacker MAY control: repository content; the agent
  process; any same-UID process on a single-account host; environment variables;
  cwd; CLI arguments; writable user configuration (`~/.config/pcae/**`); task
  metadata; agent identity (`--agent-id`); session metadata; Git state. The
  attacker MUST NOT be able to mint a `PRODUCTION` `HPACWriterCapability`, write
  the `HumanPrincipalRegistry`, or create / replace / revoke any protected
  artifact under `<HPAC_PROTECTED_ROOT>`.

## 9. Configured agent principal — source of truth (finding F-1)

- **HPAC-PAWA-REQ-021.** The configured agent principal SHALL be resolved from
  **canonical PCAE agent configuration / lock semantics**, never from caller
  input, an environment variable, a CLI flag, `--agent-id`, repository state, or
  the live `os.geteuid()` of the running process. For a Class-B deployment this
  is HBDC-001 §3's `PCAE_AGENT_PRINCIPAL` (a distinct OS account); the
  implementation SHALL name the exact canonical resolution source in its
  `.1R.30R.3` contract-production traceability (§73).
- **HPAC-PAWA-REQ-022.** Identity form: an OS-principal identifier sufficient to
  parameterize the effective-write-access check — a `(uid, gids)` pair on POSIX,
  or the platform-appropriate equivalent — resolved from the configured
  principal, **not** the invoking process's live ids. `_effective_write_access`
  already accepts `uid` / `gids` as parameters, so the negative boundary check
  SHALL be evaluated against the **configured agent principal's** ids on the
  production-writer path, and the *positive* write probe (§28) SHALL be evaluated
  against the **invoking process's** live capability — different identities, both
  well-defined (finding F-1).
- **HPAC-PAWA-REQ-023.** If the configured agent principal is unavailable,
  ambiguous, or cannot be mapped to an OS principal where the check needs one,
  the recognition SHALL **fail closed** (`agent_principal_unknown`, §56). It
  SHALL NOT default to `os.geteuid()`, to "no agent", or to a permissive
  outcome.
- **HPAC-PAWA-REQ-024.** A caller SHALL NOT supply `agent_id=None`, an empty
  principal, or any override to bypass the configured-agent exclusion. Any such
  input is rejected before recognition (`agent_principal_unknown` /
  `operation_scope_invalid`).
- **HPAC-PAWA-REQ-025.** On a **single-account** host where the configured agent
  principal and the interactive human share one OS uid, the negative boundary
  check cannot discriminate them: if that uid can write
  `<HPAC_PROTECTED_ROOT>`, `_validate_production_boundary` raises and **no
  `PRODUCTION` authority is available at all** — the fail-closed outcome, not a
  downgrade (PAWA-INV-7). HPAC-PAWA-001 v1.0 REAL production writer issuance
  requires the two-OS-principal topology (§61).

### 9.1 Named resolution source (v1.1)

- **HPAC-PAWA-REQ-164.** The "canonical PCAE agent configuration / lock
  semantics" of HPAC-PAWA-REQ-021 is, concretely, the
  **`HPAC-PAWA-AGENT-EXCLUSION/1.0` protected record** frozen at §32A. It is the
  exact resolution source HPAC-PAWA-REQ-021 requires the `.1R.30R.3.1`
  implementation to name in its contract-production traceability (§73). No other
  source — not `os.geteuid()`, not `.pcae/agent-lock.json`, not the agent
  registry, not `PCAE_AGENT_PRINCIPAL` read from `os.environ`, not a systemd
  `User=` / launchd `UserName` / `run_as` deployment fact, not `DeploymentBinding`,
  not the `HPAC-STORE-AUTHORITY/1.0` manifest — is, in whole or in part, the
  configured-agent-principal resolution source.
- **HPAC-PAWA-REQ-165.** `ConfiguredAgentAuthorityIdentity` (§2) SHALL be
  produced only by resolving §32A's record: validate the record (§32A), read its
  `symbolic_account`, resolve that account live through the OS account database,
  require the live uid to equal the record's `provisioned_uid` (§32A / C-1), and
  enumerate the account's **current** primary + supplementary groups live
  (§32A / C-1). The result parameterizes `_effective_write_access` /
  `_ancestor_chain_safe` on the §33 step-3 negative boundary and is one operand
  of the §33 step-7 not-configured-agent current-context check.
- **HPAC-PAWA-REQ-166.** The `.1R.30R.3.1` production `production_writer(...)`
  signature SHALL carry **no** `configured_agent_uid`, `configured_agent_gids`,
  `symbolic_account`, `agent_account`, or account-name parameter. Resolution is
  internal to the recognition sequence. A single leading-underscore,
  documented-fixture-only keyword-only seam (`_configured_agent_identity_source`
  or a repository-derived equivalent; `None` in production ⇒ resolve from the
  record) is the **only** permitted test injection point, and a guard test
  (§75) SHALL assert no non-test module ever passes it.
- **HPAC-PAWA-REQ-167.** HPAC-PAWA-REQ-023's fail-closed rule extends verbatim to
  the v1.1 source: a missing / malformed / wrong-owner / wrong-mode /
  installation-mismatched / generation-stale / non-`ACTIVE` record, an
  unresolvable `symbolic_account`, or a live uid `!=` `provisioned_uid`
  → `agent_principal_unknown`; a resolved agent that holds protected-root write
  authority → `agent_has_protected_write_authority`. It SHALL NOT default to
  `os.geteuid()`, to "no agent", or to a permissive outcome. No new
  `pawa_failure_code` (§42A / §56).

## 10. Per-predicate identity matrix (finding F-1)

- **HPAC-PAWA-REQ-026.** Every recognition predicate SHALL state exactly which
  identity it is evaluated against, which authority source establishes that
  identity, whether it is caller-controlled, and its failure behavior. The
  normative matrix:

  | Predicate | Subject identity evaluated | Authority source | Caller-controlled? | Failure behavior |
  |---|---|---|---|---|
  | canonical-root resolution (§25) | none — a fixed compiled-in path | `resolve_hpac_protected_root()` | **no** — takes no input | `protected_root_missing` / `protected_root_untrusted` |
  | configured-agent exclusion (§26) | the **configured agent principal** (`PCAE_AGENT_PRINCIPAL`), NOT `os.geteuid()` | canonical PCAE agent configuration / lock (§9) — concretely the `HPAC-PAWA-AGENT-EXCLUSION/1.0` record (§32A): `symbolic_account` + `provisioned_uid`, `(uid, gids)` resolved live | **no** — resolved from protected state, not caller input | `agent_principal_unknown`; `agent_has_protected_write_authority` |
  | protected-root ownership / ancestors (§26) | the configured agent principal (as the party proven *excluded*); the root's `st_uid` as the party proven *owner* | filesystem `stat` + `_effective_write_access` / `_ancestor_chain_safe` | **no** | `protected_root_untrusted` |
  | descriptor trust (§27) | the descriptor's declared `deployment_owner_role` + its binding to the current root identity | `.authority/` descriptor bytes + `HPAC-STORE-AUTHORITY/1.0` manifest `{device,inode}` + `HPAC-WRITER-PROVENANCE/1.0` digest | **no** — resolved from protected state, not caller input | `descriptor_missing` / `descriptor_malformed` / `descriptor_wrong_owner` / `descriptor_wrong_mode` / `descriptor_root_identity_mismatch` / `descriptor_installation_mismatch` / `descriptor_generation_stale` / `descriptor_revoked` |
  | positive write authority (§28) | the **current invoking OS process** | a live `O_EXCL\|O_NOFOLLOW` create-and-unlink probe under `.authority/` | **no** — an operation, not a claim | `write_probe_failed` |
  | not-configured-agent current context (§31) | the **current invoking OS process** vs. the configured agent principal | the `HPAC-PAWA-AGENT-EXCLUSION/1.0`-resolved `ConfiguredAgentAuthorityIdentity` (§9.1 / §32A) + live process identity (`_current_agent_identity()`) | **no** | `current_context_is_agent` |
  | agent-exclusion record trust (§32A) | the `HPAC-PAWA-AGENT-EXCLUSION/1.0` record's closed fields + its binding to the current root, installation, and generation anchor | `.authority/agent-exclusion.json` canonical bytes + `record_digest` + `installation_id` + `{device,inode}` + `HPAC-PAWA-CURRENT-GENERATION/1.0` `agent_exclusion_digest` (§20A) | **no** — resolved from protected state, not caller input | `agent_principal_unknown` (every record fault — absent / malformed / wrong-owner / wrong-mode / installation-mismatch / generation-stale / non-`ACTIVE` / unresolvable `symbolic_account` / uid-pin mismatch: the configured agent principal cannot be trustworthily resolved, §42A) |
  | writer-factory consumer (§32) | the importing / calling **source module** | static consumer inventory (§39) + admin-writer-module import boundary | **no** — a build-time / import-time fact | `unauthorized_factory_consumer` |
  | descriptor / provisioning owner (§17) | the filesystem `st_uid` / `st_gid` / mode of the descriptor and its directory | filesystem `stat` | **no** | `descriptor_wrong_owner` / `descriptor_wrong_mode` |
  | deployment / installation identity (§16) | the protected-root `{device, inode}` bound in the store-identity manifest and the descriptor's `installation_id` | `HPAC-STORE-AUTHORITY/1.0` manifest + descriptor | **no** | `descriptor_installation_mismatch` / `descriptor_root_identity_mismatch` |

- **HPAC-PAWA-REQ-027.** The phrase "current user" SHALL NOT appear in the
  implementation's recognition logic or its contract-production traceability as
  an authority term. Every predicate names one of: *the configured agent
  principal*, *the current invoking OS process*, *the protected-root owner*, *the
  descriptor owner*, *the importing source module*, or *a fixed compiled-in
  path*.

## 11. Protected root

- **HPAC-PAWA-REQ-028.** The protected root SHALL be exactly
  `resolve_hpac_protected_root()`'s fixed platform-keyed output. It SHALL be:
  canonical; outside every repository; outside repository authority; outside the
  configured agent principal's write authority (root and every ancestor up to a
  point the agent has no write at all — HBDC-REQ-017); provisioned out of band by
  the deployment owner (HBDC-REQ-011/012 discipline); resolved without cwd, repo,
  environment, task, or caller influence; and protected against symlink / path
  substitution on every component (`reject_symlink` / `_reject_symlink_components`
  / `O_NOFOLLOW`).
- **HPAC-PAWA-REQ-029.** No caller-supplied root, no environment variable, no CLI
  flag, no constructor parameter, and no repository-local file SHALL override the
  protected root in the production-writer path. `_validate_production_boundary`
  already raises `"production HPAC authority cannot be redirected"` on any
  mismatch; HPAC-PAWA-001 SHALL NOT introduce any redirect path. A future MINOR
  MAY let the deployment owner point at an *already-protected* canonical
  location validated against trusted installation configuration — **not** caller
  input; v1.0 does not do even that (the path is compiled in).
- **HPAC-PAWA-REQ-030.** Agent-side / recognition code SHALL fail closed — not
  auto-provision, not silently degrade to a partial check — if the protected
  root is absent, malformed, agent-writable, symlinked, or fails the
  `{device, inode}` identity binding (HBDC-REQ-021 discipline;
  `protected_root_missing` / `protected_root_untrusted`).

## 12. `.authority/` namespace

- **HPAC-PAWA-REQ-031.** The dedicated authority namespace is
  `<HPAC_PROTECTED_ROOT>/.authority/` (the existing `_AUTHORITY_DIR`). Its
  canonical members relevant to this contract: `manifest.json`
  (`HPAC-STORE-AUTHORITY/1.0`, exists today), `provenance/<key>.json`
  (`HPAC-WRITER-PROVENANCE/1.0`, exists today), and a new
  `deployment-owner.json` (`HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0`, §13–§14).
- **HPAC-PAWA-REQ-032.** The authority namespace SHALL be resolved only as a
  fixed subpath of the canonical protected root — no symlink traversal on any
  component; no repository shadow path; no alternate / fallback path; no
  environment or caller override. Directory mode SHALL exclude group-write and
  other-write (`mode & (S_IWGRP | S_IWOTH) == 0`; `_ensure_root` sets `0700`);
  ownership SHALL be the deployment owner; the configured agent principal SHALL
  hold no write permission (direct, group, or ACL) to it or any descendant
  (`_relative_record_path` production branch already enforces
  not-agent-writable descendants).
- **HPAC-PAWA-REQ-033.** A hard link to any `.authority/` file from an
  agent-writable directory, or an agent ability to delete / rename the directory
  entry naming an `.authority/` file, SHALL be treated as a compliance failure
  equivalent to a direct write (HBDC-REQ-019/020 discipline).

## 13. Descriptor identity

- **HPAC-PAWA-REQ-034.** The deployment-owner protected-administration anchor
  descriptor has schema identity **`HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0`** and
  canonical path `<HPAC_PROTECTED_ROOT>/.authority/deployment-owner.json`. It is
  the single canonical descriptor for the deployment; there is no descriptor
  list, no per-repository descriptor, and no alternate location.
- **HPAC-PAWA-REQ-035.** The descriptor is canonicalised exactly per
  HPAC-REQ-089's rule (NFC-normalised, `sort_keys`, `(",",":")` separators,
  UTF-8; `canonical_json_bytes` / `read_canonical_json_document`) and stored as a
  single-link regular file, create-only for a given `generation`
  (`write_atomic_create_only`), read-back verified.

## 14. Closed descriptor schema

- **HPAC-PAWA-REQ-036.** `HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0` is a **closed**
  object with exactly these fields, in this set (no additional, no missing;
  `set(document) != {…}` → `descriptor_malformed`):

  | Field | Type / value |
  |---|---|
  | `artifact_schema_version` | const `HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0` |
  | `descriptor_digest` | 64 lowercase hex — SHA-256 over the canonical bytes of this object with `descriptor_digest` set to the empty string (self-excluding) |
  | `anchor_id` | opaque `hpaw-<hex32>` — stable identity of this deployment's anchor across generations |
  | `installation_id` | opaque `hpawi-<hex32>` — identity of this physical installation; changes on a legitimate machine migration / reprovision (§22) |
  | `protected_root_identity` | the exact `{device, inode}` object of `<HPAC_PROTECTED_ROOT>` at provisioning time — MUST equal the live root identity and the `HPAC-STORE-AUTHORITY/1.0` manifest's `root_identity` at every validation (§16) |
  | `authority_namespace` | const `.authority` |
  | `deployment_owner_role` | a closed token from the vocabulary `{ HPAC_PROTECTED_ADMIN }` (grammar `^[A-Z][A-Z0-9_]*$`; §16.2 HBDC precedent — one member; no wildcard / `all` / `root` value is ever valid) |
  | `configured_agent_exclusion_binding` | a closed object `{ "excluded_principal_kind": const "PCAE_CONFIGURED_AGENT_PRINCIPAL", "exclusion_basis": const "OS_FILESYSTEM_WRITE_AUTHORITY" }` — records *that* the configured agent principal is the excluded party and *how* the exclusion is established, without embedding a mutable uid a caller could reinterpret |
  | `generation` | non-negative integer ≥ 1 — the monotonic generation (§20) |
  | `created_at` | RFC3339 UTC timestamp from a trusted clock at provisioning / rotation time (`_TIMESTAMP_RE`) |
  | `supersedes` | `null` for `generation` 1; otherwise a closed object `{ "previous_generation": <int ≥ 1, < generation>, "previous_descriptor_digest": <64 hex> }` (§20, §21) |
  | `provenance_ref` | the `HPAC-WRITER-PROVENANCE/1.0` record key for this descriptor write (§19) |
  | `state` | a closed token from `{ ACTIVE, REVOKED, SUPERSEDED }` (§51) |

- **HPAC-PAWA-REQ-037.** The descriptor SHALL NOT include any mutable
  human-readable authority fact a caller could reinterpret: no free-form
  "authorized" string, no operator name, no email, no civil identity, no uid /
  gid integer as an authority input (the exclusion binding records *kind* and
  *basis*, not a mutable id), no boolean "is_admin", no capability field, no
  path other than the const `authority_namespace`.
- **HPAC-PAWA-REQ-038.** Validation of the descriptor SHALL check: exact closed
  field set; `artifact_schema_version` const; recomputed `descriptor_digest`
  equality; `anchor_id` / `installation_id` grammar; `protected_root_identity`
  equality with the live root and the store manifest; `authority_namespace`
  const; `deployment_owner_role` in the closed vocabulary;
  `configured_agent_exclusion_binding` exact closed shape; `generation` an
  integer ≥ 1; `created_at` grammar; `supersedes` shape and monotonicity (§20);
  `provenance_ref` resolves to a valid `HPAC-WRITER-PROVENANCE/1.0` record whose
  `root_identity_digest` matches the current root; `state == ACTIVE`. Any failure
  → the corresponding §56 code; no `PRODUCTION` writer.

## 15. Descriptor is not human identity

- **HPAC-PAWA-REQ-039.** The descriptor establishes an **installation /
  deployment administrative authority anchor** — a filesystem-ownership role and
  its currentness. It does **not** prove: the current human's civil identity;
  current human presence; runtime approval intent; that a specific human
  installed it. It is an administrative trust-root artifact only. The *human
  principal being enrolled* still performs the full RHAMP-001 FIDO2 ceremony
  (UP+UV `makeCredential`) — that is credential registration, governed by
  RHAMP-001, entirely separate from deployment-owner recognition (PAWA-INV-2).

## 16. Root / installation identity binding

- **HPAC-PAWA-REQ-040.** "Root-identity-bound" is concrete and narrow: the
  descriptor is trusted **only** when it resolves at the canonical path under the
  canonical protected root whose `{device, inode}` identity matches **both** the
  live `stat` of `<HPAC_PROTECTED_ROOT>` **and** the
  `HPAC-STORE-AUTHORITY/1.0` manifest's `root_identity`
  (`hpac_foundation.py`: `"HPAC root was copied or replaced; root identity
  binding failed"`), and whose `provenance_ref` record's `root_identity_digest`
  matches the current root. "Machine identity" as a vague concept SHALL NOT be
  used.
- **HPAC-PAWA-REQ-041.** A descriptor (or a whole `<HPAC_PROTECTED_ROOT>`) copied
  to another installation carries a `protected_root_identity` /
  `root_identity_digest` / `installation_id` that will not match the new root's
  live identity → `descriptor_root_identity_mismatch` /
  `descriptor_installation_mismatch`; it does **not** automatically validate
  (§22, §53, PAWA-INV-5).

## 17. Descriptor ownership / mode

- **HPAC-PAWA-REQ-042.** The normative property first, adapters second (macOS /
  Linux — §63): the descriptor file and the `.authority/` directory SHALL be
  owned by the deployment owner; SHALL NOT be group- or other-writable; SHALL
  grant the configured agent principal no write access by mode, group, or ACL;
  and SHALL be readable by the party performing recognition. If the descriptor's
  or the namespace's permissions become weaker than this contract permits at any
  validation point, recognition SHALL **fail closed** (`descriptor_wrong_mode` /
  `descriptor_wrong_owner`) — it SHALL NOT "repair" them and SHALL NOT proceed.
- **HPAC-PAWA-REQ-043.** POSIX-only semantics SHALL NOT be hardcoded where a
  cross-platform abstraction is needed; the implementation MAY use
  `_effective_write_access`'s existing platform-gated ACL sub-check and mode-bit
  logic, which already span macOS and Linux (HBDC-001 spans both).

## 18. No path-only trust

- **HPAC-PAWA-REQ-044.** Normatively: **correct path + valid closed structure
  `!=` trusted descriptor.** Trust additionally requires all of: ownership /
  mode (§17); root-identity binding (§16); current generation (§20);
  provisioning provenance (§19); `state == ACTIVE`; and — for a `PRODUCTION`
  writer to be minted — the configured-agent exclusion (§26), the positive write
  probe (§28), and the not-configured-agent current-context check (§31). "Its
  writability is the proof" — only the deployment owner can install or replace
  it; the file itself is **not a bearer secret** (`.1R.30R` §8).

## 19. Descriptor provenance

- **HPAC-PAWA-REQ-045.** Each descriptor write (provisioning or rotation) SHALL
  emit an `HPAC-WRITER-PROVENANCE/1.0` record (the existing idiom;
  `record_write`) under `<HPAC_PROTECTED_ROOT>/.authority/provenance/`, binding
  `store_id`, `authority_class` (`production`), `root_identity_digest`, the
  descriptor's relative path, the descriptor `record_digest`, and the writer
  role. The descriptor's `provenance_ref` names this record; validation resolves
  and verifies it (§14, §38). A new cryptographic signing key SHALL NOT be
  required (the adjudication rejected Candidate C for v1 — §64).
- **HPAC-PAWA-REQ-046.** Additionally, provisioning SHALL append a durable
  provenance / audit event to the deployment tree (the HBDC
  `append_provenance_event` idiom) recording: `anchor_id`, `installation_id`,
  `generation` (= 1), `protected_root_identity`, `descriptor_digest`, the
  trusted-clock timestamp, and the administrative result (§59).

## 20. Descriptor generation (finding F-3)

- **HPAC-PAWA-REQ-047.** `generation` is a **monotonic, installation-local,
  strictly increasing integer**. Initial generation (created by provisioning,
  §23) is exactly **1**. Every rotation (§50) SHALL write a descriptor whose
  `generation` is exactly `previous.generation + 1`. `generation` SHALL be
  unique per `installation_id`; two descriptors with the same
  `(installation_id, generation)` and different bytes is a
  `descriptor_installation_mismatch` fail-closed condition.
- **HPAC-PAWA-REQ-048.** The **current generation** for an installation is
  anchored by a protected, monotonically-advanced state record —
  `<HPAC_PROTECTED_ROOT>/.authority/current-generation.json`, closed schema
  `HPAC-PAWA-CURRENT-GENERATION/1.0`, fields exactly `{ artifact_schema_version`
  (const), `record_digest` (self-excluding SHA-256), `installation_id`,
  `current_generation` (int ≥ 1), `descriptor_digest` (the digest of the
  descriptor at `current_generation`), `updated_at` `}`. It is written
  create-only at provisioning (`current_generation = 1`) and updated only by an
  **atomic replace** performed by the deployment owner during a rotation, whose
  new `current_generation` SHALL be exactly `old + 1` (monotonic;
  `descriptor_generation_stale` on any attempt to set it equal-or-lower).
- **HPAC-PAWA-REQ-049.** Recognition (§33) SHALL load `current-generation.json`,
  verify its closed schema / digest / `installation_id`, and require the resolved
  descriptor's `generation` to **equal** `current_generation` and its
  `descriptor_digest` to equal the recorded one. A descriptor whose `generation`
  is below `current_generation` → `descriptor_generation_stale`; above → treated
  as `descriptor_malformed` / `descriptor_installation_mismatch` (a descriptor
  ahead of the anchored current generation is not a valid state). `generation` is
  **not advisory**.
- **HPAC-PAWA-REQ-050.** If safe rollback prevention (§21) cannot be implemented
  because the protected store cannot provide monotonic atomic-replace with
  read-back for `current-generation.json`, the implementing phase records it as
  an implementation prerequisite and **STOPS (BLOCKED)** rather than shipping an
  advisory generation.

## 20A. Current-generation schema delta — `agent_exclusion_digest` (v1.1, C-2)

- **HPAC-PAWA-REQ-168.** Under **HPAC-PAWA-001 v1.1** the
  `HPAC-PAWA-CURRENT-GENERATION/1.0` record's closed field set gains **exactly
  one** additive field, `agent_exclusion_digest` — the 64-lowercase-hex SHA-256
  `record_digest` of the `HPAC-PAWA-AGENT-EXCLUSION/1.0` record (§32A) that is
  current for this installation and generation. The v1.1 closed field set is
  therefore **exactly** `{ artifact_schema_version` (const), `record_digest`
  (self-excluding SHA-256), `installation_id`, `current_generation` (int ≥ 1),
  `descriptor_digest`, `agent_exclusion_digest` (64 hex), `updated_at` `}` — no
  additional, no missing.
- **HPAC-PAWA-REQ-169.** The artifact keeps its schema identifier
  **`HPAC-PAWA-CURRENT-GENERATION/1.0`** — it is **not** bumped to `/1.1` and no
  new schema id is minted (§29 adjudication). Rationale: the record is a purely
  **internal, installation-local monotonic anchor**; it is never cross-referenced
  by an opaque schema id, never copied between installations as an authority
  claim, and is written only create-only-at-provisioning / atomic-replace-only
  by the deployment owner. **HPAC-PAWA-001 v1.1 is the authority for its
  required shape**: a v1.1 recognition SHALL require `agent_exclusion_digest`
  present and well-formed; a record missing the field is a v1.0-era anchor on a
  host that has not completed v1.1 provisioning / rotation and SHALL
  **fail closed** (`agent_principal_unknown`) — never a silent downgrade to a
  digest-unbound check. Adding a closed additive field to an internal monotonic
  anchor whose shape the contract version governs is a **MINOR** (§80, S-1).
- **HPAC-PAWA-REQ-170.** `agent_exclusion_digest` is written at provisioning
  (§32B.1), and re-stamped by an **atomic replace** of `current-generation.json`
  whenever the agent-exclusion record is rotated (§32B.4) or whenever a descriptor
  rotation (§50) re-writes the anchor. Its `current_generation` is advanced
  monotonically exactly as HPAC-PAWA-REQ-048 requires; it SHALL NOT be set to an
  equal-or-lower `current_generation` (`descriptor_generation_stale`).
- **HPAC-PAWA-REQ-171.** §33 recognition SHALL require the digest of the
  **currently loaded and validated** `HPAC-PAWA-AGENT-EXCLUSION/1.0` record to
  equal `current-generation.json`'s `agent_exclusion_digest`. A restored older
  agent-exclusion record whose digest does not match → **fail closed**
  (`agent_principal_unknown`); it does **not** become current merely because its
  bytes are restored (§32C). Bare `generation`-integer equality between the two
  records is **not** an acceptable substitute for the digest binding (C-2).
- **HPAC-PAWA-REQ-172.** HPAC-PAWA-REQ-050's BLOCKED discipline extends: if the
  protected store cannot provide monotonic atomic-replace-with-read-back for the
  v1.1 `current-generation.json` field set, the implementing phase records it as
  a prerequisite and **STOPS (BLOCKED)** rather than shipping an unbound digest.

## 21. Descriptor rollback prevention (finding F-3)

- **HPAC-PAWA-REQ-051.** Explicit rule: **a previously superseded valid
  descriptor SHALL NOT become current again merely because its bytes are
  restored.** Restoring `deployment-owner.json` at `generation` `N` while
  `current-generation.json` records `current_generation` `M > N` yields
  `descriptor_generation_stale` — no `PRODUCTION` writer.
- **HPAC-PAWA-REQ-052.** Restoring **both** `deployment-owner.json` at
  `generation` `N` **and** `current-generation.json` at `current_generation`
  `N` (a full paired rollback) requires filesystem write to `.authority/` — i.e.
  being the deployment owner (or root — §60, in the TCB). Within the model's
  trust boundary this is the deployment owner deliberately reverting their own
  installation; it is not an *agent* rollback (the agent cannot write there). The
  contract does not claim to prevent the deployment owner from rolling back their
  own installation, and does not need to: PAWA protects against the *agent*, the
  *same normal-user domain*, and *repository / caller / env / cwd* influence
  (§60), not against a party who already holds protected-root write authority.
- **HPAC-PAWA-REQ-053.** A restored snapshot of an *old whole protected root* is
  additionally caught by the `{device, inode}` root-identity binding (§16) unless
  it is a byte-identical restore to the original device/inode — mirroring
  HBDC-REQ-046.

## 22. Machine migration / reprovisioning

- **HPAC-PAWA-REQ-054.** Legitimate migration / reprovisioning and
  rollback / replay have **distinct** semantics and SHALL NOT be conflated:
  - **Legitimate migration** — the deployment owner performs an explicit
    out-of-band `provision` on the new host / new protected root: a **new
    `installation_id`**, a fresh `{device, inode}` root identity, `generation`
    reset to 1, a fresh `current-generation.json`, a fresh provenance chain. The
    `anchor_id` MAY be carried forward (the same logical deployment) or minted
    fresh (operator's choice, recorded).
  - **Rollback / replay** — restoring files without a new `installation_id` and
    without a new root identity → caught by §16 / §20 / §21 → fail closed.
- **HPAC-PAWA-REQ-055.** Copying protected files alone is **never** sufficient to
  establish authority on a new machine (HBDC-REQ-044/045 discipline). A
  migration is always a deliberate out-of-band administrative act, never a
  silent acceptance of copied bytes.

## 23. Initial out-of-band bootstrap

- **HPAC-PAWA-REQ-056.** The one-time provisioning procedure SHALL: (a) occur
  outside ordinary PCAE agent authority — a standalone script (recommended
  `scripts/hpac_protected_root_admin.py provision`), never a `pcae` CLI
  subcommand, never agent-invocable, run by an operator logged in as the
  deployment owner; (b) require OS-protected administrative write authority to
  the protected-root location and its parent; (c) create `<HPAC_PROTECTED_ROOT>`
  `0700` if not already provisioned; (d) create the `HPAC-STORE-AUTHORITY/1.0`
  manifest (create-only) establishing `store_id` and the `{device, inode}` root
  identity; (e) create the `HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0` descriptor at
  `generation` 1 with a fresh `anchor_id` and `installation_id`; (f) create
  `current-generation.json` at `current_generation` 1; (g) set correct
  ownership / mode on every created path; (h) append the durable provisioning
  provenance / audit record (§46); (i) complete **without any existing
  `HPACWriterCapability`** — `write_atomic_create_only` / `_ensure_directory` are
  filesystem primitives; the bootstrap is a filesystem provisioning act by the
  OS deployment owner, outside PCAE's authority model entirely (PAWA-INV-4,
  non-circular).
- **HPAC-PAWA-REQ-057.** Provisioning SHALL NOT require, consult, or create a
  FIDO2 credential, an enrolled human principal, an `AuthenticatedHumanPrincipal`,
  a RHAMP-001 ceremony, a Permission Broker decision, a Runtime Enforcement
  result, or any runtime capability. The first-credential FIDO2 enrollment
  (RHAMP-REQ-048) happens *after* the anchor exists and *consumes* it (§71).

## 24. Bootstrap repeatability

- **HPAC-PAWA-REQ-058.** Bootstrap is **not silently repeatable** over an
  existing valid installation. A second `provision` against an existing
  `<HPAC_PROTECTED_ROOT>` with a valid `HPAC-STORE-AUTHORITY/1.0` manifest and a
  valid `ACTIVE` descriptor SHALL either **fail closed** (`duplicate_bootstrap`,
  §56) or explicitly enter the distinct rotation / reprovisioning procedure
  (§50, §52) — never a silent authority reset, never a `generation` reset over a
  live installation. The manifest and `current-generation.json` are create-only;
  a create against an existing name raises `HPACDuplicateError`
  (`hpac_foundation.py`).
- **HPAC-PAWA-REQ-059.** An idempotent no-op is permitted only when a repeated
  `provision` is byte-identical to the existing installation's descriptor and
  generation state (mirroring `ensure_repository_identity` /
  HBDC-REQ-059's idempotent-preserve discipline); any field difference is a
  `duplicate_bootstrap` conflict.

## 25. Recognition predicate 1 — canonical root

- **HPAC-PAWA-REQ-060.** Positive validation SHALL require the exact canonical
  `<HPAC_PROTECTED_ROOT>` — `self.root == resolve_hpac_protected_root().absolute()`
  (`_validate_production_boundary` already enforces this). No caller-, repo-,
  env-, or cwd-selected replacement. If a configurable root is ever introduced
  (not in v1.0), it SHALL be validated against trusted installation
  configuration, never caller input (§29). Missing / not-a-directory /
  symlinked / manifest-absent → `protected_root_missing`.

## 26. Recognition predicate 2 — configured-agent exclusion (finding F-1)

- **HPAC-PAWA-REQ-061.** Positive validation SHALL require proof that the
  **configured PCAE agent principal** (§9, resolved from canonical configuration,
  **not** `os.geteuid()`) does **not** hold the OS filesystem write authority
  over `<HPAC_PROTECTED_ROOT>` and its safe-ancestor chain required to mutate the
  anchor. Concretely: `_effective_write_access(root, configured_agent_uid,
  configured_agent_gids)` returns `False` and `_ancestor_chain_safe(root,
  configured_agent_uid, configured_agent_gids)` returns `True`.
- **HPAC-PAWA-REQ-062.** This SHALL NOT be expressed as `current_euid !=
  some_agent_uid`, as `os.geteuid() != 0`, or as any comparison of the *invoking
  process's* live ids against a constant, **unless** that exact mapping is
  independently canonical for the deployment (it is not, in the general case).
  The evaluated identity is the *configured* principal; the check is *effective
  write access*, not a declared-mode-bit or id-equality shortcut.
- **HPAC-PAWA-REQ-063.** If the configured agent principal cannot be resolved →
  `agent_principal_unknown` (fail closed, §23 of this contract / F-1). If the
  configured agent principal *does* hold protected-root write authority →
  `agent_has_protected_write_authority` (fail closed; this deployment is not
  eligible for a `PRODUCTION` writer — §61).

## 27. Recognition predicate 3 — descriptor trust

- **HPAC-PAWA-REQ-064.** Positive validation SHALL require: the canonical
  descriptor resolves at `<HPAC_PROTECTED_ROOT>/.authority/deployment-owner.json`
  (no-follow, single-link regular file, exact canonical bytes); its closed schema
  validates (§14, §38); its `protected_root_identity` matches the live root and
  the store manifest (§16); its `generation` equals the anchored
  `current_generation` and its digest matches (§20); its ownership / mode satisfy
  §17; its `provenance_ref` resolves to a valid `HPAC-WRITER-PROVENANCE/1.0`
  record for the current root (§19); and `state == ACTIVE` (§51). Any failure →
  the corresponding §56 code.

## 28. Recognition predicate 4 — positive write authority

- **HPAC-PAWA-REQ-065.** Positive validation SHALL require **operation-based
  proof** that the *current administrative invocation* holds actual
  OS-authorized write capability over the exact canonical
  `<HPAC_PROTECTED_ROOT>/.authority/` namespace **now**. This SHALL NOT be
  defined solely as `os.access(path, W_OK)` (which honours only real-uid mode
  bits and ignores ACLs / effective ids), nor as an id comparison.
- **HPAC-PAWA-REQ-066.** The write probe SHALL be an `O_CREAT | O_EXCL |
  O_NOFOLLOW` create of a randomly-named sentinel
  (`.probe-<hex>`) directly under `.authority/`, followed by `write` of a small
  fixed payload, `fsync`, `close`, and `unlink` — mirroring
  `write_atomic_create_only`'s `os.link(..., follow_symlinks=False)` +
  directory-`fsync` idiom. Success (create + write + unlink all succeed) proves
  real write authority, not a mode-bit guess. `EACCES` / `EPERM` / `EROFS` /
  any failure → `write_probe_failed`; no `PRODUCTION` writer.

## 29. Write-probe target

- **HPAC-PAWA-REQ-067.** The probe target SHALL be a **dedicated ephemeral
  sentinel object** under `.authority/`, never arbitrary production state, never
  the descriptor, never `current-generation.json`, never the manifest, never a
  provenance record. The probe SHALL NOT follow symlinks, SHALL create with
  `O_EXCL` (no destructive overwrite), and SHALL verify actual
  create / write / fsync / close / remove semantics. Cleanup failure (the
  sentinel cannot be unlinked) SHALL be handled explicitly and treated as
  `write_probe_failed` / `protected_root_untrusted` — never ignored, never left
  behind silently.
- **HPAC-PAWA-REQ-068.** The probe SHALL NOT mutate the descriptor, the current
  generation, the manifest, or any registry / proof / lifecycle / consumption
  record. It is read-authority evidence only.

## 30. Write-probe TOCTOU

- **HPAC-PAWA-REQ-069.** The recognition sequence SHALL be ordered to prevent
  obvious check / use substitution: (1) resolve and validate the canonical root
  and its `{device, inode}` identity; (2) resolve and validate the descriptor
  and current generation against the **same resolved** root; (3) perform the
  write probe against the **same resolved** `.authority/` path (no
  re-resolution); (4) mint the `PRODUCTION` capability **immediately, within the
  same process and call context**; the capability is process-local and
  short-lived.
- **HPAC-PAWA-REQ-070.** The contract SHALL NOT promise absolute TOCTOU
  elimination. It defines the trusted OS boundary (the filesystem permission
  model, §8) and fail-closed conditions: the capability's authority SHALL be
  **re-verified at every `record_write` / `_write`** (`require_writer` +
  `_ensure_root` + `_validate_production_boundary` already re-run on every
  mutation), so a mid-flight permission change is caught at the next
  `_ensure_root`, and the registry's `expected_current` compare-and-write
  rejects a stale write. A probe → mint → write race cannot *widen* authority.

## 31. Recognition predicate 5 — not configured agent

- **HPAC-PAWA-REQ-071.** Positive validation SHALL require an explicit **negative
  assertion** that the current administrative context is **not** the configured
  PCAE agent principal — evaluated against the canonical configured-agent
  identity source (§9), never a caller-supplied boolean, never `--agent-id`,
  never an environment variable. On a two-principal deployment this is the
  configured-principal exclusion (the invoking process runs as the deployment
  owner, a distinct account); on a single-account host it collapses with §25 to
  the "no `PRODUCTION` root" fail-closed outcome.
- **HPAC-PAWA-REQ-072.** There is nothing for a same-UID agent to forge here —
  the check reads canonical configuration and the live OS process identity; a
  same-UID agent cannot make `_effective_write_access` return `False` for the
  configured agent principal while that principal *does* have write, and cannot
  pass the §28 probe without write.
- **HPAC-PAWA-REQ-201.** **(v1.1)** The comparison is concrete: at §33 step 7 the
  live `_current_agent_identity()` `(uid, gids)` is compared against the
  `ConfiguredAgentAuthorityIdentity` resolved from `HPAC-PAWA-AGENT-EXCLUSION/1.0`
  at step 2. If the live uid **equals** the resolved configured-agent uid (the
  current invocation is running *as* the configured agent account) →
  `current_context_is_agent` → fail closed. The comparison SHALL NOT use a
  descriptive `agent_id` label, and SHALL NOT treat group-set equality alone as
  identity. This predicate is **distinct** from
  `agent_has_protected_write_authority` (§26, step 3), which asks whether the
  *configured* agent *would be able* to mutate the anchor: neither substitutes
  for the other (§10 matrix; finding F-1).

## 32. Recognition predicate 6 — factory consumer

- **HPAC-PAWA-REQ-073.** `PRODUCTION` capability issuance SHALL be reachable
  **only** through the protected admin writer module's factory (§36), invoked by
  an **exact authorized consumer** (§38). There is no general public API, no
  `pcae` CLI path, no agent-reachable entry point (§37). An import / call from an
  unauthorized module → `unauthorized_factory_consumer`; the consumer-inventory
  guard (§39) fails the build for any un-enumerated consumer.

## 32A. Configured-agent-principal resolution source — `HPAC-PAWA-AGENT-EXCLUSION/1.0` (v1.1)

- **HPAC-PAWA-REQ-173.** The configured-agent-principal resolution source
  (§2, §9.1) is a **load-bearing protected recognition input**: a §33 recognition
  predicate consults it, and no `PRODUCTION` `HPACWriterCapability` is minted
  unless it validates. It is frozen here as `HPAC-PAWA-AGENT-EXCLUSION/1.0` with
  canonical path
  **`<HPAC_PROTECTED_ROOT>/.authority/agent-exclusion.json`**. There is one
  canonical record per installation; no record list, no per-repository record,
  no alternate location. It is **not** repository configuration, environment
  configuration, task metadata, a human-principal record, a runtime approval
  artifact, a bearer secret, or a capability.
- **HPAC-PAWA-REQ-174.** It is a **sibling** of `deployment-owner.json` in the
  same `.authority/` namespace. The `HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0` schema
  (§14) is **byte-unchanged** by v1.1: its frozen
  `configured_agent_exclusion_binding` object keeps recording only the
  *kind* (`PCAE_CONFIGURED_AGENT_PRINCIPAL`) and *basis*
  (`OS_FILESYSTEM_WRITE_AUTHORITY`) of the exclusion; the account identity lives
  in this separate record. No uid / gid integer and no account name is added to
  the descriptor (HPAC-PAWA-REQ-037 preserved).

### 32A.1 Closed schema (v1.1, R1-HYBRID)

- **HPAC-PAWA-REQ-175.** `HPAC-PAWA-AGENT-EXCLUSION/1.0` is a **closed** object
  with exactly these fields, in this set (no additional, no missing;
  `set(document) != {…}` → the record is faulted, §42A):

  | Field | Type / value |
  |---|---|
  | `artifact_schema_version` | const `HPAC-PAWA-AGENT-EXCLUSION/1.0` |
  | `record_digest` | 64 lowercase hex — SHA-256 over the canonical bytes of this object with `record_digest` set to the empty string (self-excluding), canonicalised exactly per HPAC-REQ-089 (NFC, `sort_keys`, `(",",":")`, UTF-8) |
  | `symbolic_account` | the provisioned OS account **name** of the configured PCAE agent principal (§32A.2); grammar-bounded `^[A-Za-z_][A-Za-z0-9_.-]{0,63}$`; **not** a uid integer, **not** a display name, **not** a path |
  | `provisioned_uid` | non-negative integer — the numeric uid resolved for `symbolic_account` at protected provisioning time (§32A.3); an **account-instance continuity pin**, not the authority basis |
  | `installation_id` | opaque `hpawi-<hex32>` — MUST equal the current `HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0` `installation_id` and the current-generation record's `installation_id` |
  | `protected_root_identity` | the exact `{device, inode}` object of `<HPAC_PROTECTED_ROOT>` at provisioning time — MUST equal the live root identity and the `HPAC-STORE-AUTHORITY/1.0` manifest's `root_identity` at every validation |
  | `authority_namespace` | const `.authority` |
  | `generation` | non-negative integer ≥ 1 — the generation this record was provisioned / last rotated at (§32A.10) |
  | `created_at` | RFC3339 UTC timestamp from a trusted clock at provisioning / rotation time (`_TIMESTAMP_RE`) |
  | `supersedes` | `null` for the record's first `generation`; otherwise a closed object `{ "previous_generation": <int ≥ 1, < generation>, "previous_record_digest": <64 hex> }` |
  | `provenance_ref` | the `HPAC-WRITER-PROVENANCE/1.0` record key for this record's write (§32B) |
  | `state` | a closed token from `{ ACTIVE, SUPERSEDED, REVOKED }` |

- **HPAC-PAWA-REQ-176.** The record SHALL NOT include any other field, and in
  particular SHALL NOT include: a persisted `(uid, gids)` **group** snapshot as
  an authority input (§32A.6, PAWA-INV-12); a free-form "authorized" string; an
  operator name, email, or civil identity; a boolean "is_admin"; a capability
  field; a `deployment_owner` field (that is the descriptor's, not this
  record's); any path other than the const `authority_namespace`. A retained
  provisioning-time group list, if present anywhere for audit, is **explicitly
  non-authoritative** and SHALL NOT live in this closed record.
- **HPAC-PAWA-REQ-177.** Validation SHALL check: exact closed field set;
  `artifact_schema_version` const; recomputed `record_digest` equality;
  `symbolic_account` grammar; `provisioned_uid` a non-negative integer;
  `installation_id` grammar **and** equality with the descriptor and the
  current-generation record; `protected_root_identity` equality with the live
  root and the store manifest; `authority_namespace` const; `generation` an
  integer ≥ 1; `created_at` grammar; `supersedes` shape and monotonicity;
  `provenance_ref` resolves to a valid `HPAC-WRITER-PROVENANCE/1.0` record whose
  `root_identity_digest` matches the current root; `state == ACTIVE`; the
  record's `record_digest` equals `current-generation.json`'s
  `agent_exclusion_digest` (§20A / C-2). Any failure → `agent_principal_unknown`
  (§42A) and **no `PRODUCTION` writer**.

### 32A.2 `symbolic_account`

- **HPAC-PAWA-REQ-178.** `symbolic_account` identifies the provisioned OS
  account name associated with the configured PCAE agent principal for PAWA
  exclusion checks. Its value is: established **only** by out-of-band protected
  administration (§32B–§32C); stored under protected-root authority; **not**
  caller-controlled; **not** environment-controlled as authority; **not**
  repository-controlled; **not** derived implicitly from the current euid, the
  current shell username, or the agent-lock logical label.
- **HPAC-PAWA-REQ-179.** A logical PCAE `agent_id` string (`claude-local`,
  `codex-ox`, …) does **not** inherently map to an OS account. The semantic
  bridge is exactly: *logical PCAE configured agent principal → the protected,
  deployment-owner-provisioned `symbolic_account` binding → the `provisioned_uid`
  continuity pin → live `(uid, gids)` authority resolution*. §33 evaluates the
  **resolved OS authority identity**, never the `agent_id` label.

### 32A.3 `provisioned_uid` (C-1)

- **HPAC-PAWA-REQ-180.** `provisioned_uid` records the numeric uid resolved for
  `symbolic_account` at protected provisioning time. It is an **account-instance
  continuity check** — it detects an account being deleted and recreated under a
  new uid (§32A.5). It is **not** sufficient by itself to identify the
  configured agent principal: the `symbolic_account` lookup remains mandatory,
  and the authority basis remains **live effective filesystem write access**,
  never the uid integer (HPAC-PAWA-REQ-037 discipline preserved — this is an
  integrity pin on the name resolution, not an authority input).

### 32A.4 Live account resolution

- **HPAC-PAWA-REQ-181.** At **every** §33 recognition, the implementation SHALL
  resolve `symbolic_account` from the **trusted OS account database** and
  require: the lookup succeeds **and** the resolved live uid **equals**
  `provisioned_uid`. Otherwise → **fail closed** (`agent_principal_unknown`,
  §42A). No new `pawa_failure_code` is introduced (§42A).
- **HPAC-PAWA-REQ-182.** No result of this resolution is cached across
  `production_writer(...)` calls (HPAC-PAWA-REQ-075). The lookup and the group
  enumeration (§32A.6) run fresh every time.

### 32A.5 Account deletion / recreation / UID reuse / rename

- **HPAC-PAWA-REQ-183.** **Deletion.** `symbolic_account` absent from the OS
  account database ⇒ the configured agent principal is unresolved ⇒
  `agent_principal_unknown` ⇒ `PRODUCTION` writer issuance **denied**. There is
  **no fallback to `provisioned_uid` alone**.
- **HPAC-PAWA-REQ-184.** **Recreation under a different uid.** `symbolic_account`
  recreated with a uid `!=` `provisioned_uid` ⇒ live uid `!=` `provisioned_uid`
  ⇒ **reject** (`agent_principal_unknown`) ⇒ a deliberate protected
  reprovision / rotation (§32B.4) is required. **No automatic acceptance** of the
  new principal instance (this is exactly the R1-PURE silent-rebind path C-1
  closes).
- **HPAC-PAWA-REQ-185.** **UID reuse.** A numeric `provisioned_uid` later
  reassigned to a **different** account does not satisfy the binding: the
  `symbolic_account` lookup is mandatory and, for the original name, either
  fails (deleted) or resolves to a uid `!=` `provisioned_uid`. There is **no
  reverse-uid fallback** (no "find the account whose uid == `provisioned_uid`").
- **HPAC-PAWA-REQ-186.** **Rename.** The old `symbolic_account` no longer
  resolving ⇒ **reject** (`agent_principal_unknown`). An account rename requires
  an explicit protected reprovision / rotation of the exclusion binding (§32B.4);
  the implementation SHALL NOT silently follow the old uid to a new name.

### 32A.6 Live group resolution (C-1)

- **HPAC-PAWA-REQ-187.** The account's **current** primary **and** supplementary
  groups SHALL be enumerated **live** at every §33 recognition and fed, as the
  `gids` set, to `_effective_write_access` / `_ancestor_chain_safe`. Group
  membership SHALL NOT be persisted in the record as the authoritative current
  state (PAWA-INV-12). The contract freezes the **security property** — "the
  account's current full group membership" — not one specific OS API; the
  `.1R.30R.3.1` adapter MAY use `os.getgrouplist(name, pw_gid)` on Linux, a
  `grp` scan on macOS, or the platform equivalent (HPAC-PAWA-REQ-132
  discipline).
- **HPAC-PAWA-REQ-188.** **Group drift (decisive).** If the configured agent
  account is added, after provisioning, to a group that grants write authority
  over `<HPAC_PROTECTED_ROOT>` or a safe ancestor, the next §33 recognition
  enumerates the current groups, `_effective_write_access(root, agent_uid,
  agent_gids)` returns `True` ⇒ `agent_has_protected_write_authority` ⇒
  **fail closed**, no writer. This is the load-bearing reason the record stores a
  name and resolves live rather than snapshotting a `(uid, gids)` tuple.
- **HPAC-PAWA-REQ-189.** **Group removal.** If the configured agent account
  **loses** a group, live resolution reflects the lower authority at the next
  recognition and the deployment MAY become eligible again **with no
  reprovision**, provided every other §33 predicate is current. A reduction in
  the agent's authority strictly *strengthens* the exclusion property; §26 /
  §33 step 3 is a *live* effective-access test by design, and no
  currentness / rotation event is required for a strengthening change
  (follows `.1R.30R.2A.1` §7.5).

### 32A.7 OS account database — TCB

- **HPAC-PAWA-REQ-190.** The trusted OS account database / account-resolution
  mechanism (`pwd` / `grp` / NSS or the platform equivalent) is **inside PAWA's
  OS trusted computing base**, exactly as the OS filesystem protection model is
  (HPAC-PAWA-REQ-018, PAWA-INV-6). HPAC-PAWA-001 v1.1 SHALL NOT be represented
  as, and its implementation SHALL NOT claim, resistance to a hostile OS root /
  account administrator altering the account database — that party is already
  outside the threat model (HPAC-PAWA-REQ-128, HBDC-001 §18 inherited).

### 32A.8 No environment / no caller / no current-euid authority

- **HPAC-PAWA-REQ-191.** `PCAE_AGENT_PRINCIPAL`, `USER`, `LOGNAME`, `SUDO_USER`,
  `SUDO_UID`, or any similar environment variable SHALL NOT be the trust source
  for `symbolic_account` and SHALL NOT override the protected record. An
  environment variable MAY at most *locate* protected configuration (v1.0 §29
  discipline); it SHALL NOT *be* the identity.
- **HPAC-PAWA-REQ-192.** Future production APIs SHALL NOT accept
  `configured_agent_uid`, `configured_agent_gids`, `symbolic_account`, or a
  group set as caller-supplied authority inputs (§9.1 / HPAC-PAWA-REQ-166). The
  fixture / test seam SHALL remain explicitly non-production and guard-checked
  (§75).
- **HPAC-PAWA-REQ-193.** The current process's `os.geteuid()` / `os.getgroups()`
  are **not** the `ConfiguredAgentAuthorityIdentity` and SHALL NOT substitute
  for it in §33 step 3. `_current_agent_identity()` remains the subject of the
  §28 positive write probe and **one operand** of the §31 not-configured-agent
  comparison — never the operand of `agent_has_protected_write_authority`
  (finding F-1; the three predicates stay distinct, §10 / §31).

## 32B. Provisioning, rotation, migration of the agent-exclusion record (v1.1)

- **HPAC-PAWA-REQ-194.** **§32B.1 — initial provisioning.** Initial out-of-band provisioning (§23) additionally
  creates the `HPAC-PAWA-AGENT-EXCLUSION/1.0` record, **create-only**, alongside
  `deployment-owner.json` at the descriptor's generation. The `provision`
  procedure SHALL: resolve the administrator-selected `symbolic_account` from
  the OS account database; capture `provisioned_uid`; write the record with the
  current `installation_id` / `{device, inode}` / `generation`; emit its
  `HPAC-WRITER-PROVENANCE/1.0` record; write `agent_exclusion_digest` into
  `current-generation.json` (§20A). It requires **no** `HPACWriterCapability`,
  **no** FIDO2, **no** enrolled principal — it is a filesystem provisioning act
  plus a read of the OS account database, both outside PCAE's authority model
  (PAWA-INV-4, non-circular).
- **HPAC-PAWA-REQ-195.** **§32B.2 — account selection.** `symbolic_account` SHALL
  be an **explicit protected-administration input** during out-of-band
  provisioning (a `--agent-account <name>` argument to
  `scripts/hpac_protected_root_admin.py provision` / `set-agent-exclusion`). It
  SHALL NOT be taken implicitly from the current euid, the current shell
  username, an environment variable alone, or the agent-lock logical label
  alone.
- **HPAC-PAWA-REQ-196.** **§32B.3 — duplicate bootstrap.** A second `provision`
  against an installation that already has a valid `ACTIVE`
  `HPAC-PAWA-AGENT-EXCLUSION/1.0` record SHALL NOT silently overwrite it: it
  either **fails closed** (`duplicate_bootstrap`, §56) or explicitly enters the
  rotation procedure (§32B.4). An idempotent no-op is permitted only when the
  repeated `provision` is byte-identical to the existing record and generation
  state (HPAC-PAWA-REQ-058/059 discipline). Never a silent authority reset.
- **HPAC-PAWA-REQ-197.** **§32B.4 — rotation / reprovision.** Changing the
  configured agent OS account (a new service account, an account rename, a
  deletion / recreation, or an intentional replacement) SHALL be an **explicit
  deployment-owner action**: it writes a new `HPAC-PAWA-AGENT-EXCLUSION/1.0`
  record at `generation = old + 1` with `supersedes = { previous_generation,
  previous_record_digest }`; emits its provenance record; atomically replaces
  `current-generation.json` with the new `agent_exclusion_digest` and
  `current_generation = old + 1`; marks the old record `SUPERSEDED` (or removes
  it — the anchor is authoritative either way). No in-place silent edit. After
  rotation the old record SHALL NOT satisfy §33 (its digest no longer matches
  the anchor, §20A / §32C).
- **HPAC-PAWA-REQ-198.** **§32B.5 — machine migration.** Migration to a new
  installation / protected root re-provisions the exclusion record **freshly**
  under the migrated `installation_id` + `{device, inode}` (§22 legitimate-
  migration path). A copied `agent-exclusion.json` alone carries a non-matching
  `installation_id` / `{device, inode}` → `agent_principal_unknown`; it never
  validates (PAWA-INV-5, PAWA-INV-12).

## 32C. Coordinated / full-root rollback boundary (v1.1)

- **HPAC-PAWA-REQ-199.** **Independent exclusion-record rollback is
  impossible** once C-2 is in effect: a restored older `agent-exclusion.json`
  whose `record_digest` `!=` `current-generation.json`'s `agent_exclusion_digest`
  fails closed (§20A / HPAC-PAWA-REQ-171), and re-writing the anchor requires
  filesystem write to `.authority/` — i.e. deployment-owner (or root) authority,
  which the configured agent provably lacks.
- **HPAC-PAWA-REQ-200.** What prevents rollback of the **full old set**
  (`deployment-owner.json` + `current-generation.json` + `agent-exclusion.json`
  together) is unchanged from v1.0: the single monotonic atomic-replace
  `HPAC-PAWA-CURRENT-GENERATION/1.0` anchor (§20 / §21) plus the protected-root
  `{device, inode}` binding (§16). C-2 does **not** claim to prevent a party who
  already holds `.authority/` write authority (the deployment owner, or root in
  the TCB) from deliberately reverting their own installation as a coordinated
  set — PAWA protects against the *agent*, the *same normal-user domain*, and
  *repository / caller / env / cwd* influence (§60), not against the deployment
  owner reverting their own installation. The boundary is stated, not
  overclaimed.

## 33. Positive validation sequence

- **HPAC-PAWA-REQ-074.** The frozen order — **11 steps**, every step required;
  any failure yields **no capability** and the corresponding §56 code. The
  **v1.1 delta** is that the configured-agent-principal *resolution* (steps 2
  and 7) is now an explicit, atomic set of substeps against
  `HPAC-PAWA-AGENT-EXCLUSION/1.0` (§32A); the step **count and required
  ordering are unchanged** (§45):

  1. resolve the canonical `<HPAC_PROTECTED_ROOT>` (no input); reject
     symlink / non-dir / absent (`protected_root_missing`);
  2. resolve the canonical configured agent principal from PCAE configuration
     (§9); unresolvable / ambiguous → `agent_principal_unknown`. **(v1.1
     substeps)** load the `HPAC-PAWA-AGENT-EXCLUSION/1.0` record no-follow;
     validate its closed schema / digest / ownership / mode / `installation_id`
     / `{device, inode}` / `state == ACTIVE` (§32A.1) and its
     `record_digest == current-generation.agent_exclusion_digest` (§20A);
     resolve `symbolic_account` live and require `live uid == provisioned_uid`
     (§32A.4); enumerate the account's current primary + supplementary groups
     live (§32A.6) → `ConfiguredAgentAuthorityIdentity`. Any fault →
     `agent_principal_unknown`;
  3. validate protected-root ownership + **configured-agent** exclusion +
     safe ancestors — `_effective_write_access(root, configured_agent_uid,
     configured_agent_gids) == False` **and** `_ancestor_chain_safe(root,
     configured_agent_uid, configured_agent_gids) == True` against the
     `ConfiguredAgentAuthorityIdentity` resolved in step 2, **not**
     `_current_agent_identity()` (`_validate_production_boundary` re-scoped per
     F-1); agent-writable / indeterminate → `agent_has_protected_write_authority`
     / `protected_root_untrusted`;
  4. load `HPAC-STORE-AUTHORITY/1.0` manifest; verify `{device, inode}` root
     identity binding (`protected_root_untrusted` on mismatch);
  5. load the descriptor no-follow; validate the closed schema, digest,
     `protected_root_identity`, ownership / mode, `provenance_ref`, `state ==
     ACTIVE` (§14, §27) — corresponding `descriptor_*` code on any failure;
  6. load `current-generation.json`; validate the **v1.1 closed field set**
     (§20A); require `descriptor.generation == current_generation` and digest
     match (`descriptor_generation_stale` / `descriptor_installation_mismatch`);
  7. validate the current administrative context is **not** the configured agent
     principal (§31) — compare live `_current_agent_identity()` against the
     step-2 `ConfiguredAgentAuthorityIdentity`; equal ⇒ `current_context_is_agent`;
  8. perform the `O_EXCL | O_NOFOLLOW` positive write probe against `.authority/`
     (§28, §29) (`write_probe_failed`);
  9. verify the calling module is an authorized factory consumer (§32, §38)
     (`unauthorized_factory_consumer`);
  10. mint the process-local, operation-scoped `PRODUCTION`
      `HPACWriterCapability` (§36, §41) bound to the operation / principal /
      credential (§42–§44);
  11. record the issuance audit evidence (§55).

- **HPAC-PAWA-REQ-075.** The sequence SHALL run fresh on **every**
  `production_writer(...)` call. No result is cached across calls; no long-lived
  capability is contemplated (§45, §48). The `HPAC-PAWA-AGENT-EXCLUSION/1.0`
  load, live account resolution, uid-pin equality, and live group enumeration
  (§32A) are **inside the same atomic recognition unit** as descriptor
  validation, current-generation checking, the write probe, and the mint — they
  cannot be split such that a `PRODUCTION` capability exists without them having
  run (PAWA-INV-3, PAWA-INV-12; atomic unit A1 of `.1R.30R.3.1`).

## 34. No sudo / euid shortcut

- **HPAC-PAWA-REQ-076.** The following SHALL NOT appear as the normative positive
  predicate, in whole or in part:

  ```
  if os.geteuid() == 0: allow
  if os.getuid() == 0: allow
  if "SUDO_USER" in os.environ: allow
  if os.environ.get("SUDO_UID"): allow
  ```

  `sudo` / `root` MAY be part of the *underlying OS mechanism* by which the
  deployment owner holds filesystem write authority, but neither `euid == 0` nor
  any `SUDO_*` environment variable is, by itself, the positive recognition
  predicate. `euid == 0` alone mints **nothing** (PAWA-INV-1).
- **HPAC-PAWA-REQ-077.** `euid` / `sudo` metadata MAY be recorded as a
  **non-authoritative audit annotation** on the issuance evidence (§55) — it
  SHALL NOT be consulted by any recognition predicate.

## 35. Wrong privileged principal

- **HPAC-PAWA-REQ-078.** HPAC-REQ-023 is verified (`.1R.30R` §14.6, `.1R.30R.1`
  §11, §17.2) as an **OS-authority / installation-role construct** — "external
  OS/equivalent trust anchor", "owns the deployment-scoped protected root" — not
  a specific-human cryptographic or civil identity. Therefore: **any process that
  legitimately holds the deployment-owner OS filesystem write authority over the
  specific admin-owned `<HPAC_PROTECTED_ROOT>` and presents a valid current
  descriptor and is not the configured agent principal SATISFIES the anchor.**
  The contract does **not** claim to identify *which* human or *which* privileged
  account it is, beyond "holds the required filesystem-ownership role for this
  deployment".
- **HPAC-PAWA-REQ-079.** A *different* local admin / root without legitimate
  filesystem write to *this* deployment's protected root fails the §28 probe and
  the §26 ownership check → no capability. "Being root somewhere" is not "being
  this deployment's owner".
- **HPAC-PAWA-REQ-080.** If a future requirement demands *more* than "holds the
  deployment-owner OS filesystem write authority" — e.g. a specific enrolled
  administrative human identity for the *writer* path — that is a **MAJOR** and a
  new adjudication; v1.0 SHALL NOT silently require it and SHALL NOT claim it.

## 36. Production writer factory

- **HPAC-PAWA-REQ-081.** The `PRODUCTION` writer factory's normative role:
  given a successful §33 sequence, it mints exactly one process-local,
  operation-scoped `PRODUCTION` `HPACWriterCapability` bound to the resolved
  `PRODUCTION` `HPACStoreAuthority` instance's `_seal`, via the existing
  `_WRITER_CONSTRUCTOR_SEAL` discipline — the same seal / non-serializability /
  per-instance-identity mechanics `HPACWriterCapability` already has
  (`hpac_foundation.py`). A conceptual symbol is
  `HPACStoreAuthority.production_writer(operation, *, principal_id=None,
  credential_id=None)` or a repository-derived equivalent; the contract fixes the
  **semantics**, not the exact class or method name.
- **HPAC-PAWA-REQ-082.** The factory SHALL NOT weaken any existing
  `HPACWriterCapability` semantics. `require_writer` still checks
  `writer._authority_seal is self._seal` (identity), role / subject match, and
  `authority_class` match. `__reduce__` still raises. The `PRODUCTION` capability
  is *strictly narrower* than the fixture writer: operation-scoped and
  single-use (§49), where the fixture writer was reusable within a process.
- **HPAC-PAWA-REQ-083.** No **new broad admin token** SHALL be created. The
  existing `HPACWriterCapability` type is reused; `ProtectedAdminCapability`
  remains a legacy fixture-only marker and is **not** extended to production.

## 37. Factory module boundary

- **HPAC-PAWA-REQ-084.** The `PRODUCTION` writer factory SHALL be exported from a
  **separate admin-only production module** (recommended
  `src/pcae/core/hpac_protected_admin_writer.py`). Ordinary agent / runtime /
  Gate / `pcae` CLI code SHALL NOT import it — directly or transitively through
  any agent-reachable module.
- **HPAC-PAWA-REQ-085.** The module SHALL NOT be a `pcae` CLI subcommand, SHALL
  NOT be registered in any command dispatch table, SHALL NOT be on any plugin
  import path, and SHALL NOT be a repository-integration consumer. The
  provisioning script (§23) and the enrollment / recovery tools (§38) are
  standalone `scripts/…` entrypoints, mirroring
  `hatp_deployment_binding_admin.py` / `hatp_certification_admin.py`
  (HBDC-REQ-056/066; HMIC-REQ-079/081/082).
- **HPAC-PAWA-REQ-086.** The consumer inventory is **exact** — an enumerated
  list of specific module dotted-paths. No wildcard, no prefix, no `fnmatch`, no
  glob, no "any module under `scripts/`".

## 38. Authorized consumers

- **HPAC-PAWA-REQ-087.** The closed categories of authorized `PRODUCTION` writer
  factory consumers for v1.0/v1.1:
  - the bounded **protected principal administration** tool (principal / credential
    enroll / revoke), run by the deployment owner as a standalone script;
  - the **first-credential bootstrap / enrollment** tool (RHAMP-REQ-048;
    `.1R.30R.3`);
  - the **recovery / re-bootstrap** tool (HPAC-REQ-065, RHAMP-REQ-050;
    total-principal-loss recovery).
  HPAC-PAWA-001 v1.2 adds exactly one category: the bounded **protected
  presentation mechanism configuration** administration tool specified by
  HPAC-PPA-001 v1.0. Its exact future source consumer is
  `pcae.core.hpac_protected_presentation_admin`, reached only from the
  standalone `scripts/hpac_protected_presentation_admin.py` entry point. The
  script is not itself a wildcard consumer category. No launcher, helper,
  verifier, Gate, runtime, agent, or plugin is added to this inventory.
- **HPAC-PAWA-REQ-088.** The following SHALL NOT be authorized consumers:
  ordinary agent commands; any `pcae` CLI subcommand; Gate 5 / 6 / 7 / 8 / 9 / 10
  or any gate coordinator; the runtime adapter; any plugin runtime; repository
  callbacks / hooks; the ordinary task lifecycle; the session / handoff
  machinery; `core/agent.py`; `cli.py`; `commands/**`.

## 39. Consumer inventory guard

- **HPAC-PAWA-REQ-089.** `.1R.30R.3` SHALL add exact source / import
  consumer-inventory tests (the HBDC-REQ-056/066 pattern —
  `tests/test_hatp_deployment_binding_admin.py::test_module_not_imported_by_cli_or_agent_reachable_code`
  / `test_admin_script_exists_and_is_not_a_pcae_cli_subcommand`): a text-scan of
  `src/pcae/cli.py`, `src/pcae/commands/**`, `src/pcae/core/agent.py` (and any
  other agent-reachable entry) asserting the admin writer module's name and the
  `production_writer` symbol never appear as an import; and an assertion that the
  provisioning / enrollment / recovery operations are standalone `scripts/…`
  files, not `pcae` CLI subcommands.
- **HPAC-PAWA-REQ-090.** Any **new** production consumer of the `PRODUCTION`
  writer factory SHALL fail the guard until it is explicitly added to the §38
  inventory **and** this contract is amended to name its category. No
  glob / `fnmatch` / prefix broadening of the inventory is ever permitted
  (PAWA-INV-9).

## 40. `HPACWriterCapability` class

- **HPAC-PAWA-REQ-091.** HPAC-PAWA-001 reuses the existing `HPACWriterCapability`
  class (`hpac_foundation.py`) unchanged in shape (`__slots__ =
  ("_authority_seal", "role", "subject", "authority_class")`; `__reduce__`
  raises). The `PRODUCTION` class meaning under HPAC-PAWA-001: an
  `HPACWriterCapability` with `authority_class is HPACAuthorityClass.PRODUCTION`,
  minted only by the §33 sequence, that `HumanPrincipalRegistryStore._writer()`
  and the §42 stores will accept for exactly one bounded mutation.
- **HPAC-PAWA-REQ-092.** The `PRODUCTION` capability SHALL NOT be obtainable by
  `HPACStoreAuthority.writer()` (which continues to
  `raise HPACAuthorityError` for every non-`FIXTURE_NON_REAL` class),
  `legacy_fixture_writer()`, `object.__new__`, `copy` / `deepcopy` / `pickle`,
  or reconstruction from known field values (§47).

## 41. Capability issuance inputs

- **HPAC-PAWA-REQ-093.** The `PRODUCTION` capability's issuance binds **exactly**
  (least authority): the resolved `PRODUCTION` `HPACStoreAuthority` instance's
  `_seal`; the `role` (one of the §42 writer roles); the `subject` (the target
  `principal_id` or `credential_id`, or the enrollment-transaction id where a
  credential id does not yet exist — §44); the `operation` enum (§42); and,
  recorded in the issuance audit evidence (§55) but not as capability fields:
  `anchor_id`, `installation_id`, the descriptor `generation`,
  `protected_root_identity`, an `operation_id`, the issuance trusted-clock
  timestamp, and the issuer / factory identity.
  Under v1.2's sole additional operation family, `subject` is the exact
  presentation `mechanism_id`; issuance additionally records (but does not add
  as bearer capability fields) the exact
  `presentation_configuration_transaction_id` and requested lifecycle action
  (`install`, `rotate`, or `revoke`). No principal/credential scope is inferred
  from a mechanism subject.
- **HPAC-PAWA-REQ-094.** The capability carries the **minimum** structure needed
  for `require_writer` to bind it: `_authority_seal`, `role`, `subject`,
  `authority_class`. It does not carry the descriptor, the generation, a digest,
  a TTL field, or any serialisable authority payload.

## 42. Operation scope

- **HPAC-PAWA-REQ-095.** A `PRODUCTION` writer capability SHALL NOT authorize
  arbitrary HPAC writes. The closed set of mutation classes:
  - `enroll_principal` — create a `PrincipalRecord` (role
    `human_principal_registry_admin`);
  - `revoke_principal` — mark a `PrincipalRecord` `revoked`;
  - `enroll_credential` — create a `CredentialRecord` + its RHAMP-001 sidecar
    (`RHAMP-FIDO2-CREDENTIAL/1.0`) + counter-state (`RHAMP-COUNTER-STATE/1.0`)
    for one credential;
  - `revoke_credential` — mark a `CredentialRecord` `revoked`;
  - `initialize_credential_sidecar_state` — create the sidecar / counter-state
    for a credential where the ceremony requires it as a distinct step.
  HPAC-PAWA-001 v1.2 adds exactly one mutation family:
  - `configure_presentation_mechanism` — perform one bounded, protected
    metadata-only installation, rotation, or revocation transaction for the
    exact `mechanism_id` under HPAC-PPA-001 v1.0, using role
    `presentation_mechanism_installer`. It may write only that contract's
    installation-generation record, current-generation anchor, HPAC-REQ-090
    mechanism descriptor, and their ordinary HPAC writer-provenance sidecars.
    It SHALL NOT create, copy, replace, chmod, chown, or execute helper bytes.
- **HPAC-PAWA-REQ-096.** A `PRODUCTION` writer capability SHALL NOT authorize:
  writing an `HPAC-PROOF/2.0`, a lifecycle event, an
  `HPAC-PRESENTATION-EVIDENCE/2.0`, an `HPAC-AUTHORITY-CONSUMPTION/2.1` record,
  or any Gate-5 / Gate-9 artifact — those remain the trusted verifier's, bounded
  by `is_verifier_authenticated_principal` (RHAMP-REQ-125). It SHALL NOT issue a
  runtime approval, a PB permission, a Runtime Enforcement result, or a
  `DispatchEnvelope`.
- **HPAC-PAWA-REQ-097.** The capability binds the **protected-root target** — the
  fixed registry path plus, for credential operations, the fixed per-credential
  sidecar / counter-state paths under
  `<HPAC_PROTECTED_ROOT>/credentials/<credential_id>/`. It is not an
  "HPAC admin forever" capability.

## 43. Principal scope

- **HPAC-PAWA-REQ-098.** Where a mutation targets a principal, the capability
  SHALL be bound to the **exact** `principal_id` (via `subject`). A capability
  minted for principal `A` SHALL NOT write principal `B` (`require_writer`
  subject mismatch → reject; §56 `target_scope_invalid`).

## 44. Credential scope

- **HPAC-PAWA-REQ-099.** For a credential-specific operation on an **existing**
  credential (`revoke_credential`, `initialize_credential_sidecar_state`), the
  capability SHALL be bound to the exact `credential_id`.
- **HPAC-PAWA-REQ-100.** For `enroll_credential`, where the fresh opaque
  `hpc-<hex>` `credential_id` does not exist until the write, the capability
  SHALL be bound to the **enrollment-transaction id** (an `operation_id` reserved
  before the ceremony) and to the target `principal_id`; the registry write
  binds the new `credential_id` to that transaction. A capability SHALL NOT be
  over-bound to a `credential_id` that does not yet exist.

## 45. Process-local

- **HPAC-PAWA-REQ-101.** The `PRODUCTION` `HPACWriterCapability` is
  **process-local**: not durable, never written to disk, never serialised to
  JSON, never exported, never transmitted over IPC / socket / network / pipe.
  Its `_authority_seal` is the specific `HPACStoreAuthority` instance's private
  `object()` — meaningful only within the minting process.

## 46. Non-bearer

- **HPAC-PAWA-REQ-102.** Possession of an object with structurally identical
  fields does **not** establish authority. A capability is valid only if it was
  produced by the canonical `PRODUCTION` writer factory in this process and is
  recognised by `require_writer`'s **identity** check
  (`writer._authority_seal is self._seal`), not a value comparison. Structure is
  not authority.

## 47. Non-serializable

- **HPAC-PAWA-REQ-103.** The following SHALL be rejected or inert as authority:
  `pickle` / `copy` / `deepcopy` (`__reduce__` raises `TypeError`); JSON
  serialisation as authority (no serialiser exists; a hand-built dict is not a
  capability); reconstruction via `object.__new__` + known field values (fails
  the seal-identity check and the live root re-probe); cross-process transfer
  (a new process has a fresh `_seal`).
- **HPAC-PAWA-REQ-104.** An **audit projection** MAY serialise
  **non-authoritative facts** about an issuance (§55) — `operation_id`,
  `anchor_id`, `installation_id`, `generation`, mutation class, target id,
  timestamp, result, a non-authoritative capability identifier / digest. It
  SHALL NOT serialise the `_authority_seal`, and the projection SHALL NOT be
  reconstructable into a working capability.

## 48. Restart invalidation

- **HPAC-PAWA-REQ-105.** A process restart invalidates **all** previously minted
  `PRODUCTION` writer capabilities — a new `HPACStoreAuthority` instance has a
  fresh `_seal`, so an old capability fails `require_writer`'s identity check. A
  new administrative operation after a restart SHALL re-run the full §33 sequence
  (revalidate the anchor) and mint a fresh capability.

## 49. One-operation / short-lived

- **HPAC-PAWA-REQ-106.** The narrowest lifecycle compatible with the current
  type is frozen: a `PRODUCTION` writer capability authorizes **exactly one
  administrative operation** (one `enroll_*` / `revoke_*` /
  `initialize_credential_sidecar_state`) or **one bounded enrollment
  transaction** (the `enroll_credential` + its sidecar + its counter-state, which
  are one atomic ceremony). It SHALL NOT be reused for a second operation.
- **HPAC-PAWA-REQ-107.** The existing `HPACWriterCapability` type does not
  itself enforce single-use (a fixture writer could drive multiple `_write`
  calls). `.1R.30R.3` SHALL implement the single-use invariant — e.g. the
  factory returns a one-shot wrapper, or the admin tool process exits after one
  operation, or the capability is consumed / marked spent on first
  `record_write`. The **required invariant** for `.1R.30R.3`: after one
  successful mutation, the same capability object SHALL NOT authorize a second
  `record_write` / `_write`; a second attempt → `capability_stale` (§56). If
  implementing single-use requires a type change beyond the current `__slots__`,
  `.1R.30R.3` records it as a prerequisite and the change is additive
  (a spent flag), never a weakening.
- **HPAC-PAWA-REQ-108.** The enclosing admin tool SHALL be short-lived —
  one operation per invocation, process exits after. There is no session-wide
  reusable admin capability.

## 50. Descriptor rotation

- **HPAC-PAWA-REQ-109.** Rotation is a **distinct, explicit** deployment-owner
  operation (never implicit, never a side effect of re-running `provision` —
  §24). Rotation: writes a new `deployment-owner.json` at `generation = old + 1`
  with `supersedes = { previous_generation, previous_descriptor_digest }`; emits
  its provenance record; then atomically replaces `current-generation.json` to
  `current_generation = old + 1` with the new descriptor digest; then marks the
  old descriptor `state = SUPERSEDED` (or removes it — the current-generation
  anchor is authoritative either way).
- **HPAC-PAWA-REQ-110.** After rotation: the old `generation` SHALL NOT mint new
  capabilities (§20, §49 recognition requires `generation == current_generation`).
  Capabilities already minted against the previous generation, being
  process-local and single-use, are either already consumed or die with the
  process; any in-flight `record_write` is additionally caught by the
  `expected_current` compare-and-write on registry drift. **Prefer fail-closed:**
  an implementation MAY invalidate in-flight capabilities on a detected rotation
  rather than let them complete.

## 51. Revocation

- **HPAC-PAWA-REQ-111.** The protected-admin anchor state model is the closed
  set `{ ACTIVE, REVOKED, SUPERSEDED }`:
  - `ACTIVE` — the current, valid descriptor; recognition can succeed;
  - `SUPERSEDED` — replaced by a higher `generation` via rotation (§50);
  - `REVOKED` — the deployment owner has explicitly revoked the anchor
    (`revoked_at` set on the descriptor, or the descriptor removed and
    `current-generation.json` marked revoked); recognition **fails closed**
    (`descriptor_revoked`) and **no `PRODUCTION` writer is minted** until a new
    `provision` / rotation re-establishes an `ACTIVE` descriptor.
- **HPAC-PAWA-REQ-112.** Revocation is a deployment-owner filesystem operation
  (replace / remove / mark). A revoked anchor: no capability minting; existing
  process-local single-use capabilities are as §110.

## 52. Recovery / reprovisioning

- **HPAC-PAWA-REQ-113.** Explicit recovery procedures, each an out-of-band
  deployment-owner act, never from repository or user config:
  - **protected-root damage** (manifest / descriptor / generation record
    corrupt) → the deployment owner runs `provision --repair` (or re-`provision`
    on a fresh location), re-establishing the manifest, descriptor at a fresh
    `installation_id` / `generation` 1, and current-generation record; the old
    `{device, inode}` binding does not carry (§16), so this is a deliberate
    reprovision, not a silent restore;
  - **lost installation descriptor** → same;
  - **host migration** → §22 legitimate-migration path;
  - **deployment-owner administrative reprovisioning** → explicit rotation (§50)
    or re-provision.
- **HPAC-PAWA-REQ-114.** There is **no recovery from repository state, user
  config, an environment variable, or a NON_REAL fixture**. Total-principal-loss
  recovery (HPAC-REQ-065, RHAMP-REQ-050) repeats the RHAMP-001 bootstrap
  ceremony, which requires a `PRODUCTION` writer via this anchor — the anchor is
  a prerequisite, not a fallback (§72).

## 53. Clone / snapshot rule

- **HPAC-PAWA-REQ-115.** A copied snapshot of an old protected root does **not**
  automatically regain authority if the current installation / generation state
  says otherwise. The stable, verifiable identity is the protected-root
  `{device, inode}` bound in `HPAC-STORE-AUTHORITY/1.0` and echoed in the
  descriptor's `protected_root_identity` and `installation_id` — a copy to a new
  device / inode fails the binding (§16, §41, HBDC-REQ-046). Only a byte-identical
  restore to the original device / inode may still validate.

## 54. Audit evidence

- **HPAC-PAWA-REQ-116.** Durable audit facts SHALL be recorded for: **bootstrap /
  provisioning** (§46); **descriptor rotation** (§50 — provenance record + a
  durable event); **revocation** (§51 — a durable event); **capability
  issuance** (§55); **administrative operation result** (the registry write's
  own provenance + the RHAMP-REQ-051 enrollment-evidence record where the
  operation is an enrollment).
- **HPAC-PAWA-REQ-117.** **Audit evidence is not capability.** A provenance
  record, an issuance-evidence record, or an enrollment-evidence record proves a
  write happened; it does **not** mint, restore, or stand in for an
  `HPACWriterCapability`. An audit record SHALL NOT become bearer authority
  (PAWA-INV-10; RHAMP-REQ-052 discipline).

## 55. Capability issuance audit

- **HPAC-PAWA-REQ-118.** Each successful §33 issuance SHALL record a durable
  audit event with **exactly** these fields:
  `{ event_schema_version` (const `HPAC-PAWA-ISSUANCE-EVIDENCE/1.0`),
  `operation_id`, `operation` (the §42 mutation class), `anchor_id`,
  `installation_id`, `descriptor_generation`, `protected_root_identity`,
  `target_principal_id` (or `null`), `target_credential_id` (or `null`),
  `enrollment_transaction_id` (or `null`), `issued_at` (trusted clock),
  `issuer` (the factory identity), `result` / `status` (`issued`),
  `capability_identifier` (a non-authoritative opaque id / digest, **not** the
  seal), and optionally `context_annotation` (§77 — non-authoritative `euid` /
  `sudo` note) `}`.
- **HPAC-PAWA-REQ-119.** The issuance evidence SHALL NOT serialise the
  `_authority_seal`, any capability secret, or anything from which a working
  capability could be reconstructed.
- **HPAC-PAWA-REQ-120.** A **failed** §33 attempt SHALL record the terminal §56
  code and the same identifying context (minus a `capability_identifier`) where a
  lifecycle event can be persisted.

## 56. Failure taxonomy

- **HPAC-PAWA-REQ-121.** The closed HPAC-PAWA-001 failure vocabulary. Every
  terminal failure of provisioning, recognition, or issuance SHALL map
  **deterministically to exactly one**:

  | # | `pawa_failure_code` | Stage | Trigger |
  |---:|---|---|---|
  | 1 | `protected_root_missing` | recognition step 1 | `<HPAC_PROTECTED_ROOT>` absent / not a dir / manifest absent |
  | 2 | `protected_root_untrusted` | recognition steps 1–4 | symlink / ancestor-writable / `{device,inode}` mismatch / indeterminate permissions on the root |
  | 3 | `agent_principal_unknown` | recognition step 2 | configured agent principal unresolvable / ambiguous / unmappable — **(v1.1)** also: `HPAC-PAWA-AGENT-EXCLUSION/1.0` record absent / malformed / wrong-owner / wrong-mode / `installation_id` mismatch / `{device,inode}` mismatch / digest ≠ `current-generation.agent_exclusion_digest` / non-`ACTIVE` / `symbolic_account` unresolvable / live uid ≠ `provisioned_uid` (§32A / §42A) |
  | 4 | `agent_has_protected_write_authority` | recognition step 3 | the configured agent principal holds protected-root write authority (deployment ineligible, §61) — **(v1.1)** including where the live-resolved configured-agent `(uid, gids)` gains that authority through post-provisioning group drift (§32A.6) |
  | 5 | `descriptor_missing` | recognition step 5 | no `deployment-owner.json` at the canonical path |
  | 6 | `descriptor_malformed` | recognition step 5 | closed-schema / canonical-byte / digest / grammar failure |
  | 7 | `descriptor_wrong_owner` | recognition step 5 | descriptor / `.authority/` not owned by the deployment owner |
  | 8 | `descriptor_wrong_mode` | recognition step 5 | descriptor / `.authority/` group- or other-writable, or agent-writable by ACL |
  | 9 | `descriptor_root_identity_mismatch` | recognition steps 4–5 | descriptor `protected_root_identity` / provenance `root_identity_digest` ≠ live root |
  | 10 | `descriptor_installation_mismatch` | recognition steps 5–6 | descriptor `installation_id` ≠ current-generation record; or `(installation_id, generation)` collision; or `generation` ahead of `current_generation` |
  | 11 | `descriptor_generation_stale` | recognition step 6 | descriptor `generation` < anchored `current_generation` (rollback) |
  | 12 | `descriptor_revoked` | recognition step 5 | descriptor `state == REVOKED` or the anchor is revoked |
  | 13 | `write_probe_failed` | recognition step 8 | the `O_EXCL\|O_NOFOLLOW` create-and-unlink probe under `.authority/` failed |
  | 14 | `current_context_is_agent` | recognition step 7 | the current administrative context is the configured agent principal |
  | 15 | `unauthorized_factory_consumer` | recognition step 9 | the calling module is not an enumerated authorized consumer (§38) |
  | 16 | `operation_scope_invalid` | issuance | the requested `operation` is not in the §42 closed set, or inputs (`principal_id` / `credential_id` / transaction) are malformed / missing / `None`-bypass attempted |
  | 17 | `target_scope_invalid` | write time | the capability is used for a different `principal_id` / `credential_id` / operation than it was bound to |
  | 18 | `capability_stale` | write time | the capability is reused after its one operation, after a rotation, or after a restart |
  | 19 | `duplicate_bootstrap` | provisioning | a second `provision` against a live valid installation with any field difference |
  | 20 | `reconstruction_attempt` | write time | a forged / deserialised / `object.__new__` capability fails the seal-identity check |
  | 21 | `internal_fail_closed` | any | an unexpected fail-closed error anywhere in provisioning / recognition / issuance |

- **HPAC-PAWA-REQ-122.** Free-form authority-decision reason strings are
  prohibited (RHAMP-REQ-129 discipline). The `.1R.30R.3` implementation SHALL
  finalise the exact code identifiers after source review; the set above is
  closed and complete for v1.0 (adding a code for a genuinely new terminal path
  is a MINOR — §80).

### 42A. v1.1 rejection cases — all map onto the existing 21 codes

- **HPAC-PAWA-REQ-202.** Every new terminal rejection introduced by the
  `HPAC-PAWA-AGENT-EXCLUSION/1.0` resolution (§32A / §32B) maps
  **deterministically onto an existing `pawa_failure_code`** — **no new
  `pawa_failure_code` is created, and the taxonomy remains 21 closed values**:

  | v1.1 rejection case | existing `pawa_failure_code` |
  |---|---|
  | exclusion record missing at the canonical path | `agent_principal_unknown` (#3) |
  | exclusion record malformed / closed-field-set / canonical-byte / `record_digest` / grammar failure | `agent_principal_unknown` (#3) |
  | exclusion record `.authority/` not deployment-owner-owned / group- or other- or ACL-agent-writable | `agent_principal_unknown` (#3) |
  | exclusion record `installation_id` / `{device, inode}` mismatch (incl. a copied record) | `agent_principal_unknown` (#3) |
  | exclusion record digest ≠ `current-generation.agent_exclusion_digest`; restored superseded record | `agent_principal_unknown` (#3) |
  | exclusion record `state != ACTIVE` | `agent_principal_unknown` (#3) |
  | `symbolic_account` unknown to the OS account database / lookup raises / duplicate passwd entry / account deleted | `agent_principal_unknown` (#3) |
  | live uid ≠ `provisioned_uid` (deletion + recreation under a new uid; account rename; UID reuse) | `agent_principal_unknown` (#3) |
  | resolved configured-agent `(uid, gids)` **can** write the protected root or a safe ancestor (incl. group drift) | `agent_has_protected_write_authority` (#4) |
  | the current invoking process resolves to the configured agent account | `current_context_is_agent` (#14) |
  | a second `provision` writes a differing exclusion record over a live valid installation | `duplicate_bootstrap` (#19) |
  | an unexpected fail-closed error in exclusion resolution | `internal_fail_closed` (#21) |

- **HPAC-PAWA-REQ-203.** If a future `HPAC-PAWA-AGENT-EXCLUSION` failure genuinely
  has **no** semantically valid mapping onto the 21 codes, that is a
  **BLOCKED-on-contract-compatibility** condition for the phase that discovers
  it (v1.1 scope assumed no vocabulary expansion) — it does not silently add a
  `pawa_failure_code`.

## 57. RHAMP terminal-reason mapping

- **HPAC-PAWA-REQ-123.** RHAMP-001 v1.0 §49's `terminal_reason_code` vocabulary
  is frozen at **41** values and RHAMP-001 SHALL NOT be edited by this phase.
  Where a PAWA failure occurs **during a RHAMP-001 first-credential enrollment /
  bootstrap ceremony** and a RHAMP lifecycle event can be persisted, the PAWA
  failure SHALL map to exactly one existing RHAMP `terminal_reason_code`:

  | PAWA failure(s) | RHAMP-001 §49 `terminal_reason_code` | # |
  |---|---|---|
  | `descriptor_missing`, `descriptor_malformed`, `descriptor_wrong_owner`, `descriptor_wrong_mode`, `descriptor_root_identity_mismatch`, `descriptor_installation_mismatch`, `descriptor_generation_stale`, `descriptor_revoked`, `agent_principal_unknown`, `duplicate_bootstrap` | `bootstrap_authority_unproven` | 1 |
  | `current_context_is_agent`, `agent_has_protected_write_authority`, `unauthorized_factory_consumer`, `write_probe_failed` | `enrollment_not_protected_admin` | 2 |
  | `protected_root_missing`, `protected_root_untrusted` | `protected_root_invalid` | 40 |
  | `operation_scope_invalid`, `target_scope_invalid`, `capability_stale`, `reconstruction_attempt`, `internal_fail_closed` | `internal_verification_error` | 41 |

- **HPAC-PAWA-REQ-124.** **No new `terminal_reason_code` is required or
  authorised.** If a future PAWA failure genuinely has no semantically valid
  RHAMP mapping, that is a **BLOCKED-on-contract-compatibility** condition for
  the phase that discovers it — it does not silently edit RHAMP-001 (§1,
  HPAC-PAWA-REQ-001).
- **HPAC-PAWA-REQ-125.** Outside a RHAMP ceremony (e.g. a standalone
  `provision` / rotation / revoke / principal-admin operation), the PAWA
  `pawa_failure_code` (§56) is the terminal record; it is **not** forced into a
  RHAMP code where no RHAMP lifecycle event exists.
- **HPAC-PAWA-REQ-204.** **(v1.1)** The PAWA→RHAMP map above is **unchanged**:
  every v1.1 rejection resolves to `agent_principal_unknown` / #3, or
  `agent_has_protected_write_authority` / #2, or `current_context_is_agent` / #2,
  or `duplicate_bootstrap` / #1, or `internal_fail_closed` / #41 — all already
  present in the §57 table rows. RHAMP-001 v1.0 §49's 41-code
  `terminal_reason_code` vocabulary is byte-unchanged; RHAMP-001 is not edited.

## 58. PAWA failure != runtime denial

- **HPAC-PAWA-REQ-126.** PAWA failures are **administrative writer failures**.
  They SHALL NOT become: Permission Broker decisions or reason ids; Runtime
  Enforcement reason ids or no-go ids; runtime-capability reasons; `Gate7Result`
  fields; a `DispatchEnvelope` rejection. The PAWA vocabulary (§56) and the
  RHAMP / PB / RE vocabularies stay separate (PAWA-INV-8; RHAMP-REQ-131
  discipline).

## 59. Out-of-band bootstrap audit

- **HPAC-PAWA-REQ-127.** Initial provisioning records, durably: `installation_id`,
  `anchor_id`, `generation` (= 1), `protected_root_identity`, `descriptor_digest`,
  the trusted-clock timestamp, and the administrative result. It does **not**
  create runtime human approval, an `AuthenticatedHumanPrincipal`, a proof, a
  presentation, a PB permission, or any runtime capability (§57 of `.1R.30R`;
  PAWA-INV-2, PAWA-INV-8).

## 60. Root TCB claim boundary

- **HPAC-PAWA-REQ-128.** Explicit statement: a fully privileged OS administrator
  **within the trusted protected-root boundary** can alter protected
  administrative state by design — that party *is* (or can act as) the deployment
  owner. HPAC-PAWA-001 protects against: the **configured agent principal**; the
  **same normal-user domain** on a two-principal deployment; **repository /
  caller / environment / cwd / task / Git / session** influence. It does **not**
  attempt to defend against a hostile root TCB unless parent architecture says
  otherwise (HBDC-001 §18 limit, inherited; PAWA-INV-6 scope).

## 61. Same-UID / two-principal requirement

- **HPAC-PAWA-REQ-129.** Deployment requirement: the configured agent principal
  SHALL be **OS-separable** from the deployment-owner protected-admin authority —
  a distinct OS account whose write authority to `<HPAC_PROTECTED_ROOT>` the
  configured agent principal provably lacks (HBDC-REQ-001/002).
- **HPAC-PAWA-REQ-130.** If the configured agent principal and the deployment
  owner share identical effective protected-root write authority (a
  single-account host, or a misconfigured two-account host where the agent has
  ACL / group write), **REAL `PRODUCTION` writer issuance is INELIGIBLE** —
  `_validate_production_boundary` raises, recognition fails closed
  (`agent_has_protected_write_authority` / `protected_root_untrusted`), and **no
  `PRODUCTION` writer is minted**. Fail closed — never a downgrade to a weaker
  check (PAWA-INV-7).
- **HPAC-PAWA-REQ-205.** **(v1.1)** The v1.1 resolution does **not** weaken this:
  where the `HPAC-PAWA-AGENT-EXCLUSION/1.0`-resolved configured-agent
  `(uid, gids)` and the deployment owner's effective protected-root write
  authority coincide (a single-account host, or the agent gaining write via
  group drift), `_effective_write_access(root, agent_uid, agent_gids)` returns
  `True` ⇒ `agent_has_protected_write_authority` ⇒ **fail closed**, no writer.
  The existence of a concrete resolution source is **not** a reason to relax
  the two-OS-principal requirement.

## 62. Local / offline

- **HPAC-PAWA-REQ-131.** HPAC-PAWA-001 v1.0 is fully local and offline: **no
  network service, no cloud token, no external identity provider, no online key
  verification, no remote attestation**. Provisioning, descriptor read, the
  write probe, and generation-record I/O are local filesystem operations.

## 63. macOS / Linux abstraction

- **HPAC-PAWA-REQ-132.** HPAC-PAWA-001 freezes **normative security properties**,
  not implementation-specific commands. On both macOS and Linux: (a) a
  protected-root admin authority (a deployment owner) exists and owns
  `<HPAC_PROTECTED_ROOT>`; (b) the configured agent principal provably lacks
  write authority to it and its safe-ancestor chain; (c) ownership / mode / ACL
  state is verifiable; (d) a positive `O_EXCL|O_NOFOLLOW` write probe is
  available; (e) no repo / caller / env / cwd influence on any of the above.
  Implementation adapters MAY differ per OS under `.1R.30R.3`;
  `_effective_write_access` / `_ancestor_chain_safe` already span both.
- **HPAC-PAWA-REQ-206.** **(v1.1)** The `HPAC-PAWA-AGENT-EXCLUSION/1.0`
  resolution freezes these cross-platform normative properties, not one OS API:
  (a) a stable **symbolic account lookup** exists; (b) a stable **numeric uid
  continuity check** (`live uid == provisioned_uid`) exists; (c) **live primary
  + supplementary group enumeration** for a named account exists; (d)
  protected-root write-authority evaluation for the resolved `(uid, gids)`
  exists. The Linux `pwd` / `grp` / `os.getgrouplist` idiom and the macOS
  equivalent are **adapter details**; no Linux-specific `/etc/passwd` syntax is
  required normatively.

## 64. No keychain / pinned-key requirement

- **HPAC-PAWA-REQ-133.** Because the adjudication rejected Candidate C
  (admin-signed record + pinned key) and Candidate D (OS keychain / keyring) for
  v1.0, HPAC-PAWA-001 v1.0 does **not** require: an administrator signing key; a
  pinned public verification key; an OS keychain secret; a keyring secret; a
  password / passphrase store. The implementation SHALL NOT reintroduce any of
  these as an authority input. A future **MAJOR** MAY add a signing model if a
  remote / multi-host topology is authorised (§80).

## 65. HBDC relationship

- **HPAC-PAWA-REQ-134.** HBDC-001 v1.2 is **precedent, not a shared authority
  root**. HPAC-PAWA-001 has its **own** protected root and namespace
  (`<HPAC_PROTECTED_ROOT>/.authority/`, distinct from the HATP trust store), its
  **own** descriptor (`HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0`), its **own** writer
  capability (`PRODUCTION` `HPACWriterCapability`), its **own** consumer
  inventory, and its **own** audit lifecycle. There is **no cross-subsystem
  bearer authority**: an HPAC `PRODUCTION` writer capability never authorizes a
  HATP write and vice versa (HPAC-REQ-018/084 discipline).

## 66. HBDC direct-reference boundary

- **HPAC-PAWA-REQ-135.** HPAC-PAWA-001 MAY normatively reference HBDC-001 as
  precedent or source model, but HPAC correctness SHALL NOT depend on mutable
  HBDC runtime state, an HBDC `DeploymentBinding`, an HBDC certification, or the
  HATP trust store. Every load-bearing PAWA requirement is stated explicitly in
  this document; an HBDC citation is evidence of precedent, not a live
  dependency. (The one genuinely shared *code* primitive —
  `hatp_class_b_topology_verifier._effective_write_access` /
  `_ancestor_chain_safe`, already imported by `hpac_foundation.py` — is a shared
  library, HPAC-REQ-019, not a shared trust root.)

## 67. No runtime human approval

- **HPAC-PAWA-REQ-136.** Hard invariant:

  ```
  PRODUCTION HPACWriterCapability  !=  AuthenticatedHumanPrincipal
                                   !=  approval proof
                                   !=  informed intent
                                   !=  runtime approval
  ```

  The deployment-owner protected administration may **enroll / revoke
  credentials and principals**; it does **not** approve runtime operations
  (PAWA-INV-2).

## 68. No PB / RE override

- **HPAC-PAWA-REQ-137.** A `PRODUCTION` writer capability: does not satisfy
  Permission Broker; does not satisfy Runtime Enforcement; does not override a
  no-go; does not create a `DispatchEnvelope`; does not enable the runtime; does
  not transition the runtime out of `Observed` / `observe` / `unavailable`. Even
  a fully successful anchor recognition + registry write leaves every runtime
  gate exactly where it was (PAWA-INV-8; RHAMP-REQ-159/160).

## 69. No FIDO2 requirement for first bootstrap

- **HPAC-PAWA-REQ-138.** Bootstrap non-circularity: the initial protected-admin
  anchor installation (§23) **precedes** FIDO2 credential enrollment and does
  **not** require an existing RHAMP credential, an `AuthenticatedHumanPrincipal`,
  or any prior PCAE principal. Requiring FIDO2 for the *deployment owner* would
  recreate the exact circular dependency the adjudication rejects (FIDO2
  enrollment needs the writer; the writer would need FIDO2). Later routine admin
  actions MAY, in a future version, require a stronger human ceremony — v1.0's
  bootstrap does not depend on one unless parent source says otherwise
  (PAWA-INV-4).

## 70. Future implementation flow

- **HPAC-PAWA-REQ-139.** The conceptual flow `.1R.30R.3` SHALL realise:

  ```
  out-of-band PAWA provision (deployment owner)
    -> canonical <HPAC_PROTECTED_ROOT> + .authority/manifest + descriptor@gen1
       + current-generation.json@1 + provisioning provenance
  admin operation begins (authorized consumer, run as the deployment owner)
    -> production_writer(operation, principal_id=/credential_id=/transaction)
       -> §33 sequence 1..9 (all pass)
       -> mint process-local, operation-scoped PRODUCTION HPACWriterCapability
       -> record HPAC-PAWA-ISSUANCE-EVIDENCE/1.0
    -> HumanPrincipalRegistryStore.<enroll_*|revoke_*>(capability, ...)
       -> require_writer(role, subject) + writer_transaction
          (expected_current compare-and-write, read-back verified)
       -> exactly one bounded mutation
    -> RHAMP-REQ-051 enrollment evidence where the op is an enrollment
    -> capability is spent / discarded; the tool process exits
  ```

## 71. Future FIDO2 enrollment flow

- **HPAC-PAWA-REQ-140.** The RHAMP-001 first-credential enrollment consumes
  **this same** bounded writer capability boundary and embeds **no** second
  admin-authority model:

  ```
  production_writer('enroll_credential', principal_id=P, transaction=T)
    -> PRODUCTION HPACWriterCapability (bound to P + T)
    -> RHAMP-001 §13 registration ceremony (protected presentation, UP+UV
       makeCredential, verify)
    -> enroll_credential(capability, ...) writes CredentialRecord (fresh
       hpc-<hex>) + RHAMP-FIDO2-CREDENTIAL/1.0 sidecar + RHAMP-COUNTER-STATE/1.0
       (atomic, read-back verified)
    -> RHAMP-REQ-051 enrollment evidence
    -> NO runtime approval authority is created
  ```

## 72. Future recovery flow

- **HPAC-PAWA-REQ-141.** HPAC-PAWA-001 MAY authorize, as **administrative**
  operations only: credential revocation; credential replacement (revoke + fresh
  enroll under the same principal); credential re-enrollment; and
  total-credential-loss recovery (repeat the RHAMP-001 bootstrap ceremony under a
  fresh `PRODUCTION` writer). It SHALL NOT provide a **fallback from a failed
  runtime approval to a PAWA writer** — a failed approval is a runtime outcome;
  PAWA never stands in for it (RHAMP-REQ-050 discipline).

## 73. Contract-production traceability

- **HPAC-PAWA-REQ-142.** `.1R.30R.3` (implementation) and `.1R.30R.4` (IV) SHALL
  map every load-bearing HPAC-PAWA-001 clause to exact production-source and test
  evidence — no prose-only security guarantee (RHAMP-REQ-164 discipline). At
  minimum: root resolution (§25); configured-agent-principal resolution source
  (§9 / F-1); configured-agent exclusion (§26); descriptor schema + closed-field
  validation (§14); root-identity binding (§16); generation + rollback
  prevention (§20, §21); the `O_EXCL|O_NOFOLLOW` write probe (§28); the
  not-configured-agent current-context check (§31); consumer authorization + the
  consumer-inventory guard (§32, §39); capability minting + seal discipline
  (§36); operation / principal / credential scope (§42–§44); process-local /
  non-bearer / non-serializable (§45–§47); restart invalidation (§48); one-
  operation lifetime (§49); rotation / revocation (§50, §51); bootstrap
  non-circularity (§23, §69); the issuance / provisioning audit records (§54,
  §55); the failure taxonomy and its RHAMP mapping (§56, §57).
- **HPAC-PAWA-REQ-207.** **(v1.1)** `.1R.30R.3.1` and its IV SHALL additionally
  map to exact production-source and test evidence, per v1.1 clause: the
  `HPAC-PAWA-AGENT-EXCLUSION/1.0` closed schema + validation (§32A.1) →
  `hpac_pawa_agent_exclusion.py` schema symbol + test; the named resolution
  source (§9.1 / HPAC-PAWA-REQ-164) → `resolve_configured_agent_identity()` +
  test that it reads the record, not `os.geteuid()`; `symbolic_account` live
  resolution + `live uid == provisioned_uid` (§32A.4 / C-1) →
  `resolve_configured_agent_identity()` + `test_recreated_account_new_uid_mismatch_fails_closed`;
  live group enumeration + group drift (§32A.6) → the group-resolution symbol +
  `test_group_drift_detected`; `agent_exclusion_digest` binding into
  `HPAC-PAWA-CURRENT-GENERATION/1.0` (§20A / C-2) → the current-generation schema
  helper + `test_restored_stale_exclusion_record_rejected`; §33 steps 2 / 3 / 7
  substeps (§32A / §33) → the `hpac_protected_admin_writer.py` recognition
  sequence + a step-ordering / atomicity test; provisioning + `set-agent-exclusion`
  (§32B) → `scripts/hpac_protected_root_admin.py` symbols + a provisioning test;
  the no-caller / no-env / no-euid rules (§32A.8) →
  `test_no_caller_uid_injection_on_production_api` + `test_fixture_seam_is_test_only`;
  the exclusion-record-writer and non-agent-importable guards (§75) → the guard
  test symbols.

## 74. Future implementation source boundary

- **HPAC-PAWA-REQ-143.** The expected `.1R.30R.3` production surface,
  conceptually (this phase implements none of it): the new admin writer module +
  `production_writer` factory; the new `provision` / rotation / revoke script;
  the `HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0` +
  `HPAC-PAWA-CURRENT-GENERATION/1.0` + `HPAC-PAWA-ISSUANCE-EVIDENCE/1.0` schema
  helpers; `HumanPrincipalRegistryStore` production writer path (schema
  byte-unchanged); the RHAMP-001 sidecar / counter-state stores; the
  protected-admin enrollment + first-credential bootstrap tool; `FIDO2HumanAuthenticator`
  and the `hpac_verifier` real-assertion path (RHAMP-001 territory, same phase).
  **This phase implements none of it.**
- **HPAC-PAWA-REQ-208.** **(v1.1)** The expected `.1R.30R.3.1` (Slice 1) surface
  additionally includes a **new** production module
  `src/pcae/core/hpac_pawa_agent_exclusion.py` — the `HPAC-PAWA-AGENT-EXCLUSION/1.0`
  closed schema helper, trusted load / validate, `symbolic_account` resolution,
  `provisioned_uid` equality, live group enumeration, digest / currentness
  validation, and `resolve_configured_agent_identity()` (protected record →
  symbolic name → live `pwd` / `grp` → `(uid, gids)`; fail-closed on every
  ambiguity) — placed **inside** the non-agent-importable consumer-inventory
  fence with `hpac_protected_admin_writer.py`. `scripts/hpac_protected_root_admin.py`
  gains `set-agent-exclusion --agent-account <name>` and writes the record as
  part of `provision`. The `.1R.30R.3.1` A1 atomic unit SHALL land the exclusion
  resolver **together with** the writer factory — no `production_writer` factory
  is shipped without the resolver. **This phase implements none of it.**

## 75. Future consumer guards

- **HPAC-PAWA-REQ-144.** `.1R.30R.3` SHALL add guard tests for: importers of the
  PAWA writer factory module; production consumers of `production_writer`;
  writers of the authority descriptor / generation record;
  provisioning / recovery / rotation entrypoints. **No wildcard allowlists**
  (PAWA-INV-9).
- **HPAC-PAWA-REQ-209.** **(v1.1)** `.1R.30R.3.1` SHALL additionally add exact
  guard tests that: only the out-of-band admin provisioning / rotation script
  writes `<HPAC_PROTECTED_ROOT>/.authority/agent-exclusion.json`; only the PAWA
  §33 recognition path reads it; **no** agent / runtime / Gate / plugin /
  `pcae` CLI module writes or imports `hpac_pawa_agent_exclusion` (text-scan of
  `cli.py`, `commands/**`, `core/agent.py`, and any agent-reachable entry); and
  no production API accepts a caller-supplied `symbolic_account` / uid / gids.
  **No wildcard / prefix / `fnmatch` / glob** in any of these inventories
  (PAWA-INV-9, PAWA-INV-12).

## 76. Future IV requirements

- **HPAC-PAWA-REQ-145.** `.1R.30R.4` (IV of `.1R.30R.3`) SHALL, at minimum,
  independently verify: descriptor canonicality + closed schema; the
  configured-agent (not `geteuid()`) exclusion (F-1); the two-principal
  requirement (§61); write-probe semantics (`O_EXCL|O_NOFOLLOW` create-and-unlink,
  not `os.access`); path / symlink attacks on the root, `.authority/`, the
  descriptor, and the probe target; rollback of an old descriptor (F-3);
  generation rotation and monotonicity; a wrong-`installation_id` descriptor; a
  cloned descriptor / cloned whole root; a direct factory call from an
  unauthorized consumer; same-UID / agent-has-write denial; direct
  `HumanPrincipalRegistryStore` bypass without a valid capability; capability
  copy / deepcopy / pickle / `object.__new__` reconstruction; restart
  invalidation; wrong principal scope; wrong credential scope; wrong mutation
  class; a revoked anchor; a partial / interrupted bootstrap; a machine
  migration; audit-record non-authority; that RHAMP-001 first-credential
  enrollment consumes a PAWA capability correctly; that PAWA cannot create a
  runtime approval; that the runtime posture and first-effect-absent guards are
  unchanged.
- **HPAC-PAWA-REQ-210.** **(v1.1)** A **dedicated contract IV of HPAC-PAWA-001
  v1.1**, `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A.3` (finding **C-3**), SHALL run
  **before** `.1R.30R.3.1` implementation. It is the safer default because
  `HPAC-PAWA-AGENT-EXCLUSION/1.0` is a **new protected authority-input artifact**,
  not a prose restatement; folding it into `.1R.30R.3.2` (the Slice-1 IV) is
  permitted **only at the authorizing operator's explicit discretion**. `.2A.3`,
  at minimum, SHALL independently verify: the closed `HPAC-PAWA-AGENT-EXCLUSION/1.0`
  schema and the `agent_exclusion_digest` current-generation delta; the
  R1-HYBRID identity model (symbolic name + `provisioned_uid` pin + live groups);
  that account deletion / recreation-under-a-new-uid / UID reuse / rename each
  fail closed to `agent_principal_unknown`; that group drift is detected and
  group removal recovers without reprovision; that the three F-1 predicates stay
  distinct; that no new `pawa_failure_code` and no RHAMP edit is required; that
  the descriptor schema is byte-unchanged; that HPAC-001 v2.1 / RHAMP-001 v1.0 /
  HBDC-001 v1.2 are byte-unchanged; that the v1.1 delta is MINOR under §80; and
  that `git diff <2A.2-entry> HEAD -- src/pcae` is empty.

## 77. Implementation successor (finding F-2)

- **HPAC-PAWA-REQ-146.** **`.1R.30R.3`, NOT `.1R.30R.2`, is the fresh
  implementation successor.** `.1R.30R.2` (this phase) is the **contract-freeze**
  phase. Implementation needs the frozen contract first (`.1R.30R` §21.1
  precondition 1). The `.1R.30R` doc's §21.4 heading and §24 summary line, which
  said `.1R.30R.2` = implementation, are erroneous; the dominant statement
  (`.1R.30R` §21.5 table, §24 downstream-sequence line, PROJECT_STATUS,
  completion metadata) and the `.1R.30R.1` IV (§21, §27.4) are correct. This
  contract records the correction; **no `.1R.30R` doc edit is required or made by
  this phase.**
- **HPAC-PAWA-REQ-147.** Recommended `.1R.30R.3` title:
  `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3 — N-16-5 Production Protected-Admin Writer
  Anchor + Real FIDO2 Credential Registry and Authentication Mechanism
  Implementation` (or a repository-derived exact title). It realises the
  originally intended historical `.1R.30` scope from the adjudicated + frozen
  baseline; it is **NOT** a resumed `.1R.30`. Historical `.1R.30` remains
  immutable **BLOCKED**, never reused, never resumed (CPIPC-001 §4;
  PAWA-INV-11).

## 78. Downstream sequence

- **HPAC-PAWA-REQ-148.** The frozen downstream sequence (phase IDs
  **recommended, NOT reserved**; each its own explicitly human-authorized phase
  with its own IV pair):

  | ID | Scope |
  |---|---|
  | `.1R.30R.2` | HPAC-PAWA-001 v1.0 contract freeze |
  | `.1R.30R.2A` | configured-agent-principal resolution source adjudication (verdict B — v1.1 MINOR) |
  | `.1R.30R.2A.1` | independent verification of `.1R.30R.2A` (VERIFIED WITH CORRECTIONS — C-1 / C-2 / C-3 / S-1) |
  | `.1R.30R.2A.2` | **this phase** — HPAC-PAWA-001 **v1.1** contract freeze (`HPAC-PAWA-AGENT-EXCLUSION/1.0`, C-1 / C-2 / S-1) |
  | `.1R.30R.2A.3` | dedicated independent verification of the HPAC-PAWA-001 v1.1 contract freeze (finding **C-3**; MAY fold into `.1R.30R.3.2` only at explicit operator discretion) |
  | `.1R.30R.3.1` | Slice 1 — PAWA production writer anchor + `hpac_pawa_agent_exclusion.py` + `resolve_configured_agent_identity()` (consumes v1.1; atomic unit A1) |
  | `.1R.30R.3.2` | IV of `.1R.30R.3.1` |
  | `.1R.30R.3.3` / `.3.4` | Slice 2 — RHAMP credential registry + `RHAMP-FIDO2-CREDENTIAL/1.0` sidecar + `RHAMP-COUNTER-STATE/1.0` + enrollment / bootstrap tool / its IV |
  | `.1R.30R.3.5` / `.3.6` | Slice 3 — `FIDO2HumanAuthenticator` + native CTAP2 verify + `_ELIGIBLE_MECHANISM_IDS` widening + 41-code terminal-reason wiring / its IV |
  | `.1R.30R.4` | composite IV of `.1R.30R.3.*` (broad fixed-SHA A/B, HPAC-PAWA-REQ-145) |
  | `.1R.30R.5` | protected human-approval presentation + real approval-proof integration + `require_real_assurance = True` wiring through Gate 5 / Gate 9 (the old `.1R.32` scope) |
  | `.1R.30R.6` | IV of `.1R.30R.5` + mandatory real-CTAP2-hardware verification (RHAMP-REQ-152) + **N-16-5 closure** |

- **HPAC-PAWA-REQ-149.** **No phase in this sequence is automatically
  authorized.** Each requires its own separate explicit human authorization.
  **(v1.1)** Listing an ID here does **not** reserve or authorize it (CPIPC-001
  §4; PAWA-INV-11). `.1R.30R.2A` / `.2A.1` / `.2A.2` are grammar-valid
  `numeric-segment` (`2` + `A`) with dotted children; historical `.1R.30`
  remains immutable **BLOCKED**, never reused, never resumed.

## 79. N-16-6 / N-16-7 order

- **HPAC-PAWA-REQ-150.** After N-16-5 closes: **N-16-6** (RPAC-REQ-095 fixed-argv
  external-executable adapter + supply-chain admission), **then N-16-7**
  (runtime capability enablement `Observed → Approved/Executable`) **strictly
  last**. **No Slice C** until N-16-3..7 all close. HPAC-PAWA-001 does not begin,
  reference, or unblock N-16-6 or N-16-7 (RHAMP-REQ-157 discipline).

## 80. Contract versioning

- **HPAC-PAWA-REQ-151.** HPAC-PAWA-001 uses contract `MAJOR.MINOR`. **v1.0 is
  the initial freeze; v1.1 and v1.2 are MINOR evolutions**. v1.1 adds the
  `HPAC-PAWA-AGENT-EXCLUSION/1.0` configured-agent-principal resolution source,
  §32A, plus the `agent_exclusion_digest` current-generation field, §20A.
  v1.2 adds only the closed `configure_presentation_mechanism` metadata
  mutation family and exact protected-presentation admin consumer, §80.2.
  Unknown versions fail closed. A recognition running under HPAC-PAWA-001 v1.1
  SHALL require the v1.1 artifacts (§20A, §32A); it SHALL NOT silently accept a
  v1.0-era installation missing them (fail closed, `agent_principal_unknown`).
- **HPAC-PAWA-REQ-152.** A change that does any of the following requires a new
  **MAJOR** plus explicit human authorization and independent verification:
  making `sudo` / `euid` / any environment variable sufficient authority;
  collapsing or removing the configured-agent exclusion; permitting a
  same-principal agent / deployment-owner topology; introducing a remote /
  network / cloud authority service or transport; making the writer capability
  bearer, durable, serialisable, or reusable across operations; broadening the
  capability into runtime approval / PB permission / RE result / runtime
  capability / execution; changing the bootstrap trust root away from OS
  filesystem write authority on the out-of-band-provisioned protected root;
  removing the `generation` / rollback-prevention protection; adding a signing
  key / pinned key / keychain requirement as an authority input; widening the
  authorized-consumer inventory by wildcard / prefix / glob.
- **HPAC-PAWA-REQ-153.** A **MINOR** may: re-state verified behaviour; add a
  `pawa_failure_code` for a genuinely new terminal path **without** removing or
  re-meaning an existing one, provided the RHAMP-001 §49 mapping (§57) still
  resolves; add an authorized-consumer **category** by explicit enumeration
  (never wildcard); tighten (never loosen) a bound; clarify a
  platform-adapter detail; or add an additional macOS / Linux adapter within the
  frozen normative properties (§63) — provided no meaning above changes.
  It may also add one explicitly enumerated protected-admin **metadata mutation
  family** whose target is inside the same protected root, provided executable
  bytes and runtime evidence remain outside PAWA, the capability remains
  process-local/non-bearer/one-operation, and no MAJOR trigger in §152 fires.
- **HPAC-PAWA-REQ-154.** No future HPAC-PAWA-001 version may retrospectively
  widen an already-minted capability's granted scope or an already-provisioned
  anchor's authority.

### 80.1 v1.1 versioning rule (finding S-1)

- **HPAC-PAWA-REQ-211.** **Explicit MINOR rule (S-1):** *adding a closed,
  generation-bound, deployment-owner-provisioned, agent-unwritable protected
  **recognition-input artifact** that concretely **resolves** — but does not
  widen, weaken, or redefine — an authority predicate the frozen contract
  **already requires** is a **MINOR** evolution.* This is consistent with
  HPAC-PAWA-REQ-153's existing permits (it *tightens* the §26 predicate from
  "unresolvable — no source exists" to "resolved against a protected,
  generation-bound record"; the `pwd` / `grp` resolution is a
  platform-adapter detail within §63's frozen properties) and with the direct
  precedent of **HPAC-001 v2.1**, itself a MINOR that "adds one closed binding
  object … widens no authority … possession or reconstruction grants nothing."
  Future readers SHALL apply this rule directly rather than re-deriving the
  classification from the absence of a MAJOR trigger.
- **HPAC-PAWA-REQ-212.** **v1.1 MAJOR-trigger review — none fires
  (HPAC-PAWA-REQ-152):** the v1.1 evolution does **not** make `sudo` / `euid` /
  an environment variable sufficient authority (authority basis stays live
  effective filesystem write access); does **not** collapse or remove the
  configured-agent exclusion (it *implements* it); does **not** permit a
  same-principal topology (§61 / HPAC-PAWA-REQ-205 — still fail closed); does
  **not** introduce a remote / network / cloud authority service (fully local;
  `pwd` / `grp` are local NSS reads); does **not** make the capability bearer /
  durable / serialisable / reusable; does **not** broaden the capability into
  runtime approval / PB / RE / runtime capability / execution; does **not**
  change the bootstrap trust root away from OS filesystem write authority on the
  out-of-band-provisioned protected root; does **not** remove the `generation` /
  rollback-prevention protection (C-2 *binds into* it); does **not** add a
  signing key / pinned key / keychain requirement as an authority input (a
  symbolic name in a protected file + `pwd` / `grp`; no key, no signature, no
  secret); does **not** widen the authorized-consumer inventory by wildcard /
  prefix / glob. **⇒ HPAC-PAWA-001 v1.1 — MINOR.**
- **HPAC-PAWA-REQ-213.** **MAJOR triggers preserved (unchanged for v1.1):**
  weakening the configured-agent exclusion; permitting a same-agent topology;
  changing the bootstrap trust root; making the capability bearer / durable;
  adding remote authority; widening mutation scope; replacing the OS
  protected-root TCB; adding runtime approval semantics — any of these remains a
  **MAJOR** plus its own adjudication and independent verification.

### 80.2 v1.2 protected-presentation configuration authority

- **HPAC-PAWA-REQ-219.** HPAC-PAWA-001 v1.2 selects the least-powerful
  executable-installation model: the deployment owner installs immutable helper
  bytes out of band; PAWA authorizes only registration, rotation, or revocation
  of the exact metadata that pins those bytes. A PAWA capability SHALL NOT
  install executable bytes or authorize a generic filesystem/process mutation.
- **HPAC-PAWA-REQ-220.** The one new operation is exactly
  `configure_presentation_mechanism`, role
  `presentation_mechanism_installer`, subject equal to the exact
  `mechanism_id`, and one nonempty
  `presentation_configuration_transaction_id`. Its closed lifecycle action is
  exactly one of `{install, rotate, revoke}`. The lifecycle action is issuance
  evidence and transaction input, not a reusable capability field.
- **HPAC-PAWA-REQ-221.** The operation may mutate only the HPAC-PPA-001 v1.0
  installation-generation record, current-generation anchor, HPAC-REQ-090
  descriptor, and the existing HPAC provenance sidecars for those records,
  all beneath the exact mechanism directory. Every other path, including the
  helper executable path itself, is outside its authority.
- **HPAC-PAWA-REQ-222.** An install/rotate/revoke that changes more than one
  authorized metadata artifact is one bounded multi-write administrative
  transaction under HPAC-PAWA-REQ-106/107 and the independently verified
  `complete_multi_write` ACTIVE→CONSUMED lifecycle. It is not multiple
  operations and creates no new lifecycle primitive.
- **HPAC-PAWA-REQ-223.** The exact future production factory consumer added by
  v1.2 is `pcae.core.hpac_protected_presentation_admin`. The only entry point
  allowed to reach it is the standalone
  `scripts/hpac_protected_presentation_admin.py`. Neither name is a prefix,
  glob, or category wildcard. The launcher, helper, presentation store,
  verifier, Gates, runtime, agent, CLI, and plugins remain unauthorized.
- **HPAC-PAWA-REQ-224.** The protected-presentation administration module and
  script are non-agent-importable, local, out-of-band deployment-owner tools
  under §§37–39. They SHALL NOT be registered as a `pcae` CLI command, plugin,
  runtime provider, Gate consumer, repository hook, or task callback.
- **HPAC-PAWA-REQ-225.** The capability issuance scope adds no slot or durable
  authority field. The existing process-local issuance registry binds the
  canonical capability identity to role, mechanism subject, operation,
  transaction, authority class, and ACTIVE lifecycle. Object fields alone are
  never sufficient authority.
- **HPAC-PAWA-REQ-226.** Initial install requires no pre-existing protected
  presentation approval. The already-recognized deployment-owner PAWA anchor
  authorizes the metadata transaction after the helper bytes have been
  installed out of band. This is the non-circular bootstrap; first-caller-wins,
  self-install, repository install, environment install, and deterministic
  fixture promotion are prohibited.
- **HPAC-PAWA-REQ-227.** Rotation and revocation are explicit new invocations,
  each with a new PAWA capability and configuration transaction. No live
  capability survives the one-operation transition; no presentation runtime
  component may rotate or revoke its own installation.
- **HPAC-PAWA-REQ-228.** The existing 21-code `pawa_failure_code` vocabulary is
  sufficient and unchanged. Unrecognized/malformed configuration issuance
  input maps to `operation_scope_invalid`; wrong mechanism/transaction use maps
  to `target_scope_invalid`; a reused or generation-stale capability maps to
  `capability_stale`; protected-root/descriptor/consumer failures keep their
  existing exact codes; an otherwise unclassified fail-closed administration
  error maps to `internal_fail_closed`. Runtime helper/evidence failures are
  RHAMP/HPAC failures, not PAWA failures.
- **HPAC-PAWA-REQ-229.** Runtime role `protected_presentation_mechanism` and all
  writes of `HPAC-PRESENTATION-EVIDENCE/2.0` remain explicitly outside PAWA.
  Possessing or consuming a PAWA installation capability SHALL NOT authorize a
  presentation, election, proof, approval, PB decision, runtime capability,
  dispatch, or effect.
- **HPAC-PAWA-REQ-230.** No §152 MAJOR trigger fires: v1.2 keeps the OS
  protected-root trust anchor, R1-HYBRID exclusion, two-principal topology,
  exact enumerated consumer discipline, non-bearer/process-local/restart-dead
  capability, one-operation bound, generation rollback checks, and closed
  failure semantics. It adds no remote service, signing-key authority,
  environment authority, runtime approval, PB/RE authority, runtime capability,
  execution, or wildcard. Therefore v1.2 is a **MINOR**.
- **HPAC-PAWA-REQ-231.** HPAC-PPA-001 v1.0 owns the installation-record,
  current-generation, fixed-helper launch, and runtime evidence-writer
  semantics. This contract owns only recognition and issuance of the bounded
  protected-admin metadata mutation. The two contracts SHALL NOT be read as a
  shared runtime authority.
- **HPAC-PAWA-REQ-232.** RHAMP-001 v1.0, HPAC-001 v2.1, RIHAC-001 v2.0,
  RIASC-001 v3.0, RDGO-001 v3.1, and the HPAC writer-provenance schema remain
  byte-unchanged by v1.2. Their existing descriptor/evidence/consumer extension
  points are specialized, not redefined, by HPAC-PPA-001 v1.0.
- **HPAC-PAWA-REQ-233.** This v1.2 freeze changes no production source, creates
  no helper or installation, writes no descriptor/evidence, modifies no Gate,
  and enables no runtime capability or external effect. Historical v1.0/v1.1
  freeze artifacts remain immutable.

## 81. Existing-contract byte identity

- **HPAC-PAWA-REQ-155.** At finalization, `.1R.30R.2` SHALL independently prove
  **byte-unchanged**: HPAC-001 v2.1; RHAMP-001 v1.0; RIHAC-001 v2.0; RIASC-001
  v3.0; HPSE-001 v1.1; HHCE-001; `HPAC-AUTHORITY-CONSUMPTION` (`/2.1`); HBDC-001
  v1.2; REPRC-001 v1.0; PBNDE-001 v1.0; RDGO-001 v3.1; RPAC-001 v1.0; the RE
  No-Go Registry; and every other unrelated contract. The **only** new normative
  file is `docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`
  (HPAC-PAWA-001 v1.0).
- **HPAC-PAWA-REQ-214.** **(v1.1)** At `.1R.30R.2A.2` finalization the phase
  SHALL independently prove **byte-unchanged**: HPAC-001 v2.1; RHAMP-001 v1.0;
  RIHAC-001 v2.0; RIASC-001 v3.0; HPSE-001 v1.1; HHCE-001;
  `HPAC-AUTHORITY-CONSUMPTION` (`/2.1`); HBDC-001 v1.2; REPRC-001 v1.0;
  PBNDE-001 v1.0; RDGO-001 v3.1; RPAC-001 v1.0; the RE No-Go Registry; and every
  other unrelated contract. `git diff --name-only <2A.2-entry> HEAD --
  docs/contracts` SHALL name **exactly** this one file
  (`HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`, now
  HPAC-PAWA-001 v1.1) and **no** other contract.

## 82. No production source change

- **HPAC-PAWA-REQ-156.** Hard requirement: `git diff <phase-entry> HEAD --
  src/pcae` is **empty** for `.1R.30R.2`. No production implementation, no
  non-production source file.
- **HPAC-PAWA-REQ-215.** **(v1.1)** Hard requirement: `git diff <2A.2-entry>
  HEAD -- src/pcae` is **empty** for `.1R.30R.2A.2`. The v1.1 evolution adds
  normative contract text only — no `hpac_pawa_agent_exclusion.py`, no
  `resolve_configured_agent_identity()`, no schema helper, no `pwd` / `grp`
  call, no provisioning-script change.

## 83. Normative contract scope

- **HPAC-PAWA-REQ-157.** Hard requirement (v1.0): `git diff --name-only
  <phase-entry> HEAD -- docs/contracts` contains **exactly one new file** (this
  contract) and **no existing contract edit**.
- **HPAC-PAWA-REQ-216.** Hard requirement (v1.1): `git diff --name-only
  <2A.2-entry> HEAD -- docs/contracts` names **exactly one** file — this
  contract, evolved in place to HPAC-PAWA-001 v1.1 — and **no other contract
  edit and no second new contract**.

## 84. No test implementation

- **HPAC-PAWA-REQ-158.** This contract-freeze phase adds no functional
  implementation test and manufactures no functional success evidence. Any
  contract-traceability test, if the repository's convention wants one, stays
  contract-only and non-production. The ≥ 24-case IV matrix (§76) and the
  contract-production traceability obligation (§73) are **specifications for
  `.1R.30R.3` / `.1R.30R.4`**, not tests authored now.
- **HPAC-PAWA-REQ-217.** **(v1.1)** `.1R.30R.2A.2` likewise authors no
  functional implementation test and manufactures no functional success
  evidence. It MAY reconcile a **point-in-time** assertion in a prior IV suite
  that pinned a v1.0 count (e.g. the requirement inventory total) to the v1.1
  inventory — a mechanical maintenance edit, no `def test_` renamed, removed,
  skipped, or xfailed. The `HPAC-PAWA-AGENT-EXCLUSION/1.0` schema, resolver, and
  guard tests are **specifications for `.1R.30R.3.1` / `.1R.30R.3.2`** and the
  dedicated `.1R.30R.2A.3` contract IV — not tests authored now.

## 85. Runtime

- **HPAC-PAWA-REQ-159.** Runtime SHALL remain: State `Observed`; Maximum
  Capability `observe`; Execution Availability `unavailable`; Plugins `0`;
  Capabilities `0`. This contract changes none of it.

## 86. First external effect

- **HPAC-PAWA-REQ-160.** The first external effect SHALL remain **ABSENT**. No
  `adapter.dispatch()` production path, no Slice C, no runtime effect adapter, no
  shell execution authority. The `PRODUCTION` writer capability writes only the
  protected registry / sidecar / counter-state stores — a **protected local
  filesystem write**, never an external effect.

## 87. N-16-5 status

- **HPAC-PAWA-REQ-161.** On a clean `.1R.30R.2`: **N-16-5 —
  WRITER-ANCHOR CONTRACT FROZEN — IMPLEMENTATION PENDING — NOT CLOSED.**
  Adjudication VERIFIED (`.1R.30R.1`); companion contract FROZEN (this phase);
  implementation not begun.
- **HPAC-PAWA-REQ-218.** On a clean `.1R.30R.2A.2`: **N-16-5 — PAWA v1.1
  CONFIGURED-AGENT RESOLUTION CONTRACT FROZEN — DEDICATED CONTRACT IV
  (`.1R.30R.2A.3`) PENDING — IMPLEMENTATION NOT BEGUN — NOT CLOSED.** The
  configured-agent-principal resolution-source gap (finding F-1 of `.1R.30R.1`)
  is closed **at the contract level** by `HPAC-PAWA-AGENT-EXCLUSION/1.0` (§32A);
  N-16-5 closure still requires `.1R.30R.3.*` implementation, `.1R.30R.4`
  composite IV, `.1R.30R.5` presentation + `require_real_assurance` wiring, and
  `.1R.30R.6` (IV + mandatory real-CTAP2-hardware verification).

## 88. N-16-6 / N-16-7

- **HPAC-PAWA-REQ-162.** N-16-6 and N-16-7 remain **OPEN and untouched**;
  N-16-7 strictly last. **(v1.1)** HPAC-PAWA-001 v1.1 does not begin, reference,
  or unblock N-16-6 or N-16-7, and no Slice C.

## 89. N-23-1 / N-23-2

- **HPAC-PAWA-REQ-163.** N-23-1 (INFO) and N-23-2 (INFO / DEFERRED NORMALIZATION
  DEBT) are carried **unchanged** by v1.0 and by v1.1. HPAC-PAWA-001 does not
  normalize PBRD / PBNDE semantics.

## 90. Contract-freeze verdict

```
HPAC PRODUCTION PROTECTED ADMINISTRATION WRITER ANCHOR CONTRACT:

HPAC-PAWA-001 v1.0 — FROZEN
HPAC-001 v2.1 — UNCHANGED (no bump)
RHAMP-001 v1.0 — UNCHANGED (byte-identical)
HBDC-001 v1.2 — UNCHANGED (precedent only; not a shared authority root)

PRODUCTION PROTECTED-ADMIN WRITER ANCHOR: CONTRACT FROZEN — NOT IMPLEMENTED

  TRUST ROOT        = OS filesystem write authority on the out-of-band-
                      provisioned <HPAC_PROTECTED_ROOT>, the CONFIGURED agent
                      principal provably excluded (finding F-1)
  POSITIVE RECOG.   = fixed-root + not-(configured-)agent-writable + safe
                      ancestors  +  root-identity-bound .authority/
                      deployment-owner descriptor (closed schema, explicit
                      monotonic generation + rollback prevention — finding F-3)
                      +  O_EXCL|O_NOFOLLOW positive write probe  +
                      not-(configured-)agent current-context  +
                      authorized-factory-consumer   [all six required, §33]
  CAPABILITY ISSUER = new PRODUCTION writer factory in a non-agent-importable
                      module, exact consumer-inventory guarded (no wildcard)
  CAPABILITY SCOPE  = one operation, one principal/credential, process-local,
                      non-serializable, non-bearer, restart-invalid,
                      one-operation lifetime
  BOOTSTRAP         = one-time out-of-band deployment-owner provision;
                      create-only; non-recurring; not agent-reachable;
                      NON-CIRCULAR (no existing HPACWriterCapability, no FIDO2)
  ROTATION          = explicit; generation += 1; monotonic current-generation
                      anchor record; old generation cannot mint
  REVOCATION        = deployment-owner filesystem replace/remove/mark;
                      state {ACTIVE, SUPERSEDED, REVOKED}; revoked -> fail closed
  MIGRATION         = new installation_id + fresh root identity + generation 1;
                      copying files alone is never sufficient
  FAILURE TAXONOMY  = 21 closed pawa_failure_code values; deterministic map onto
                      RHAMP-001 v1.0 §49 codes #1 / #2 / #40 / #41 — NO new
                      terminal_reason_code
  SAME-UID EXCLUSN  = no write access + no importability + seal identity +
                      __reduce__ raising + live re-probe; single-account host ->
                      no PRODUCTION root -> writer unavailable (fail closed)

FINDINGS INCORPORATED:
  F-1  per-predicate identity matrix (§10); every predicate names the exact
       identity it evaluates; the negative boundary keys off the CONFIGURED
       agent principal, not os.geteuid(), on the writer path (§9, §26, §62)
  F-2  .1R.30R.3 (not .1R.30R.2) is the implementation successor (§77);
       .1R.30R.2 = contract freeze; historical .1R.30 immutable BLOCKED
  F-3  explicit monotonic descriptor generation + current-generation anchor
       record + rollback-prevention rule (§20, §21)

Runtime: not_implemented / Observed / observe / unavailable; 0 plugins /
0 capabilities. First external effect: ABSENT. N-16-5: NOT CLOSED.
N-16-6 / N-16-7: OPEN, untouched, N-16-7 last. N-23-1 / N-23-2: carried.

RECOMMENDED NEXT PHASE (as of v1.0): 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3 —
N-16-5 Production Protected-Admin Writer Anchor + Real FIDO2 Credential Registry
and Authentication Mechanism Implementation. Own explicit human authorization
required. Do not begin it.

DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED — preserved.
```

### 90.1 v1.1 contract-freeze verdict

```
HPAC-PAWA-001 v1.1 — FROZEN (MINOR; sole normative delta)
HPAC-001 v2.1        — UNCHANGED (no bump; byte-identical)
RHAMP-001 v1.0       — UNCHANGED (byte-identical; no new terminal_reason_code)
HBDC-001 v1.2        — UNCHANGED (precedent only; NOT amended — this is why R2
                       was rejected)
HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0 — SCHEMA BYTE-UNCHANGED
every other contract — byte-unchanged

CONFIGURED-AGENT-PRINCIPAL RESOLUTION SOURCE: CONTRACT FROZEN — NOT IMPLEMENTED

  RESOLUTION SOURCE  = HPAC-PAWA-AGENT-EXCLUSION/1.0 at
                       <HPAC_PROTECTED_ROOT>/.authority/agent-exclusion.json
                       (§32A) — protected, deployment-owner-provisioned,
                       agent-unwritable, installation- and generation-bound
  IDENTITY MODEL     = R1-HYBRID (C-1): symbolic_account (OS account NAME)
                       + provisioned_uid (integrity pin); at every §33
                       recognition require live getpwnam(name).pw_uid ==
                       provisioned_uid, then enumerate the account's CURRENT
                       primary + supplementary groups LIVE; authority basis =
                       live effective filesystem write access, never the uid
  DELETE            -> symbolic_account absent -> agent_principal_unknown -> deny
  RECREATE (new uid)-> live uid != provisioned_uid -> agent_principal_unknown
                       -> deliberate reprovision (no silent rebind — C-1)
  UID REUSE         -> name lookup mandatory; no reverse-uid fallback -> deny
  RENAME           -> old name unresolvable -> agent_principal_unknown -> deny
  GROUP DRIFT      -> live groups seen -> agent_has_protected_write_authority
                       -> fail closed
  GROUP REMOVAL    -> reflected live; may recover with no reprovision
  OS ACCOUNT DB    = inside PAWA's OS TCB (no hostile-root claim)
  ROLLBACK (C-2)   = agent_exclusion_digest bound into
                       HPAC-PAWA-CURRENT-GENERATION/1.0 (§20A); a restored
                       superseded record whose digest != the anchor -> fail
                       closed; independent rollback IMPOSSIBLE without forging
                       the monotonic anchor (deployment-owner/root write)
  FULL-SET ROLLBACK = bounded by the single monotonic anchor + {device,inode}
                       root identity, exactly as v1.0 (§21); not overclaimed
  BOOTSTRAP        = the exclusion record is created create-only alongside
                       deployment-owner.json at provisioning; NON-CIRCULAR
                       (no HPACWriterCapability, no FIDO2, no prior principal;
                       a filesystem write + an OS-account-DB read)
  PROVISIONING     = scripts/hpac_protected_root_admin.py provision /
                       set-agent-exclusion --agent-account <name>; explicit
                       protected-admin input; never implicit euid/username/env
  DUPLICATE BOOT   = fail closed (duplicate_bootstrap) or explicit rotation;
                       never a silent authority reset
  ROTATION         = explicit; generation += 1; new record + new
                       agent_exclusion_digest via atomic anchor replace; old
                       record SUPERSEDED and no longer satisfies §33
  MIGRATION        = fresh installation_id + {device,inode}; copy alone never
                       validates
  NO ENV AUTHORITY = PCAE_AGENT_PRINCIPAL / USER / LOGNAME / SUDO_USER never
                       the trust source and never an override
  NO CALLER INPUT  = production_writer(...) carries no uid/gids/account param;
                       one leading-underscore documented fixture-only seam,
                       guard-checked
  NO CURRENT-EUID  = os.geteuid() is the §28 probe subject and one operand of
                       the §31 comparison — never the operand of
                       agent_has_protected_write_authority
  THREE F-1 PREDS  = agent_has_protected_write_authority (configured identity),
                       current_context_is_agent (live vs configured), positive
                       write probe (live operation) — DISTINCT, none substitutes
  §33 SEQUENCE     = 11 steps unchanged; the configured-agent resolution is now
                       explicit atomic substeps of steps 2/3/7 (§33)
  FAILURE TAXONOMY = 21 closed pawa_failure_code values UNCHANGED; every v1.1
                       rejection maps onto #3 / #4 / #14 / #19 / #21 (§42A);
                       RHAMP §49 map (#1/#2/#40/#41) UNCHANGED — NO new code
  CURRENT-GEN SCHEMA= HPAC-PAWA-CURRENT-GENERATION/1.0 gains exactly one field,
                       agent_exclusion_digest; schema id NOT bumped (internal
                       monotonic anchor; contract version governs its shape —
                       §20A / §29 adjudication)

CORRECTIONS INCORPORATED:
  C-1  R1-PURE -> R1-HYBRID: add provisioned_uid; live getpwnam equality pin;
       groups stay live. Closes the recreate-under-new-uid silent rebind;
       resolves the adjudication's §6-vs-§12.2 internal inconsistency. (§32A.3,
       §32A.4, §32A.5)
  C-2  bind agent_exclusion_digest into HPAC-PAWA-CURRENT-GENERATION/1.0;
       resolve the adjudication's "extend the anchor OR require generation ==="
       to the anchor-digest option. (§20A, §32C)
  S-1  explicit MINOR versioning rule for a closed generation-bound protected
       recognition-input artifact that resolves an already-required predicate.
       (§80.1 / HPAC-PAWA-REQ-211)
  C-3  a DEDICATED v1.1 contract IV, .1R.30R.2A.3, is the recommended default
       (fold into .1R.30R.3.2 only at explicit operator discretion). (§76
       HPAC-PAWA-REQ-210, §96A)

DESCRIPTOR SCHEMA: BYTE-UNCHANGED. HPAC-001 / RHAMP-001 / HBDC-001: byte-
unchanged. src/pcae: unchanged. Runtime: not_implemented / Observed / observe /
unavailable; 0 plugins / 0 capabilities. First external effect: ABSENT AND
UNREACHABLE. N-16-5: NOT CLOSED (contract-level gap closed; implementation +
dedicated contract IV pending). N-16-6 / N-16-7: OPEN, untouched, N-16-7 last.
N-23-1 / N-23-2: carried.

RECOMMENDED NEXT PHASE: 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A.3 — Independent
Verification of the HPAC-PAWA-001 v1.1 Configured-Agent-Principal Resolution
Source Contract Freeze (finding C-3; MAY fold into .1R.30R.3.2 only at explicit
operator discretion). Own explicit human authorization required. Do not begin it.

DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED — preserved.
```

### 90.2 v1.2 contract-freeze verdict

```
HPAC-PAWA-001 v1.2 — FROZEN (MINOR; metadata authority only)
HPAC-PPA-001 v1.0 — FROZEN companion (installation/evidence specialization)
HPAC-001 v2.1 / RHAMP-001 v1.0 / RIHAC-001 v2.0 / RIASC-001 v3.0 /
RDGO-001 v3.1 / HBDC-001 v1.2 — UNCHANGED

INSTALLATION AUTHORITY = existing deployment-owner PAWA anchor
EXECUTABLE INSTALL MODEL = out-of-band immutable helper bytes + PAWA metadata pin
PAWA MUTATION = configure_presentation_mechanism
PAWA ROLE = presentation_mechanism_installer
PAWA CONSUMER = pcae.core.hpac_protected_presentation_admin only
ENTRY POINT = scripts/hpac_protected_presentation_admin.py only
RUNTIME EVIDENCE ROLE = protected_presentation_mechanism (outside PAWA)
GENERIC EXECUTABLE / RUNTIME / EFFECT AUTHORITY = NONE

Runtime remains Observed / observe / unavailable; first external effect absent.
N-16-5 remains NOT CLOSED. N-16-6 / N-16-7 remain OPEN and untouched.
DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED — preserved.
```

## 91. Requirement inventory

**Requirement count (v1.0):** HPAC-PAWA-001 v1.0 defined **163** requirements,
`HPAC-PAWA-REQ-001` through `HPAC-PAWA-REQ-163` inclusive.

**Requirement count (v1.1):** HPAC-PAWA-001 v1.1 defines **218** requirements,
`HPAC-PAWA-REQ-001` through `HPAC-PAWA-REQ-218` inclusive, sequential, no gaps,
no duplicates. The v1.1 additions are `HPAC-PAWA-REQ-164` through
`HPAC-PAWA-REQ-218` (§9.1, §20A, §31, §32A, §32B, §32C, §33, §42A, §57, §61,
§63, §73–§76, §80.1, §81–§84, §87–§89).

**Requirement count (v1.2):** HPAC-PAWA-001 v1.2 defines **233** requirements,
`HPAC-PAWA-REQ-001` through `HPAC-PAWA-REQ-233` inclusive, sequential, no gaps,
no duplicates. The v1.2 additions are `HPAC-PAWA-REQ-219` through
`HPAC-PAWA-REQ-233` (§80.2).

**Invariant count:** 12 — `PAWA-INV-1` through `PAWA-INV-12` (§92, below).

## 92. Security invariants (PAWA-INV-1 .. PAWA-INV-12)

- **PAWA-INV-1.** `euid == 0`, a `sudo` invocation, and any `SUDO_*` /
  environment variable are **never**, in whole or in part, the positive
  deployment-owner recognition predicate; `euid == 0` alone mints nothing
  (§34, §35).
- **PAWA-INV-2.** A `PRODUCTION` `HPACWriterCapability` is **not** an
  `AuthenticatedHumanPrincipal`, an approval proof, informed intent, or runtime
  approval; the deployment owner enrolls/revokes credentials, never approves
  runtime operations (§67).
- **PAWA-INV-3.** Correct path + valid closed structure is **never** a trusted
  descriptor: ownership/mode + root-identity binding + current generation +
  provisioning provenance + `state == ACTIVE` + (for minting) configured-agent
  exclusion + positive write probe + not-configured-agent context are all
  additionally required (§18, §33).
- **PAWA-INV-4.** The one-time out-of-band bootstrap requires **no** existing
  `HPACWriterCapability` and **no** FIDO2 credential — it is a filesystem
  provisioning act by the OS deployment owner, outside PCAE's authority model
  (non-circular; §23, §69).
- **PAWA-INV-5.** A descriptor or whole protected root copied to another
  installation does **not** automatically validate — the `{device, inode}`
  root-identity binding and `installation_id` catch it (§16, §22, §53).
- **PAWA-INV-6.** HPAC-PAWA-001 protects against the configured agent principal,
  the same normal-user domain on a two-principal deployment, and
  repository/caller/environment/cwd/task/Git/session influence; it does **not**
  defend against a fully compromised OS root/admin account (§8, §60).
- **PAWA-INV-7.** Where the two-OS-principal topology is absent (or the agent
  holds protected-root write authority), REAL `PRODUCTION` writer issuance is
  **ineligible** and no capability is minted — fail closed, never a downgrade
  (§25, §61).
- **PAWA-INV-8.** A PAWA failure is an administrative writer failure; it is
  **never** a PB decision, a Runtime Enforcement reason id, a runtime-capability
  reason, a `Gate7Result` field, or a `DispatchEnvelope` rejection; the PAWA and
  runtime vocabularies stay separate (§58, §68).
- **PAWA-INV-9.** The authorized-consumer inventory is an **exact** enumerated
  list; no wildcard, prefix, `fnmatch`, or glob broadening is ever valid; a new
  consumer fails the guard until explicitly enumerated **and** the contract is
  amended (§38, §39, §75).
- **PAWA-INV-10.** Audit evidence (provisioning provenance, issuance evidence,
  enrollment evidence) proves a write happened; it is **never** capability and
  never bearer authority (§54).
- **PAWA-INV-11.** Historical `.1R.30` is immutable **BLOCKED** — never reused,
  never resumed, never relabelled; the fresh implementation successor is
  `.1R.30R.3` (§77, CPIPC-001 §4).
- **PAWA-INV-12.** **(v1.1)** The configured-agent-principal resolution source
  is the `HPAC-PAWA-AGENT-EXCLUSION/1.0` protected record (§32A) and nothing
  else: it stores a **symbolic OS account name** + a **`provisioned_uid`**
  integrity pin, is agent-unwritable, is bound to the installation and to the
  `HPAC-PAWA-CURRENT-GENERATION/1.0` `agent_exclusion_digest` (so independent
  rollback is impossible), and its `(uid, gids)` is resolved **live** at every
  §33 recognition — group membership is **never** persisted as authority, the
  uid is **never** the authority basis, and `os.geteuid()` / an environment
  variable / a caller parameter is **never** the source. Any record fault, an
  unresolvable account, or a `live uid != provisioned_uid` mismatch fails closed
  (`agent_principal_unknown`); no new `pawa_failure_code` (§32A, §42A).

## 93. Contract self-consistency statement

This contract, at v1.2: (a) introduces no implementation dependency, in either direction, on
`src/pcae/**` or `scripts/**` — it references existing and planned modules /
functions / symbols by name in normative text only, and imports / executes
nothing; (b) does not amend HPAC-001, RHAMP-001, HBDC-001, or any other
pre-existing contract's byte content; it adds the HPAC-PPA-001 v1.0 companion
and does not touch the
`HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0` schema; (c) creates no protected state, OS
principals, filesystem permissions, descriptors, exclusion records, account
resolutions, or writer capabilities; (d) is internally traceable — every
`HPAC-PAWA-REQ-###` ID is sequential from 001 through 233 with no gaps and no
duplicates, and every `PAWA-INV-#` (1..12) referenced elsewhere appears in §92
exactly once; (e) leaves runtime `not_implemented` / `Observed` / `observe` /
`unavailable` and the first external effect ABSENT.

## 94. Contract versioning history

HPAC-PAWA-001 was frozen as **v1.0** by Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2
— the positive production protected-admin writer anchor for HPAC-REQ-022/023,
adjudicated by `.1R.30R` and independently verified by `.1R.30R.1`, made into a
precise normative companion contract before any writer-anchor implementation
attempt. v1.0 requires its own independent verification — folded into
`.1R.30R.4` or run as a dedicated phase — before its own text is relied upon as
settled.

**v1.1** was frozen by Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A.2 — a
**MINOR** evolution, the sole normative delta, that closes the
configured-agent-principal resolution-source gap (finding **F-1** of
`.1R.30R.1`; discovered during `.1R.30R.3` primary-source decomposition;
adjudicated by `.1R.30R.2A` — verdict **B**, resolution **R1**; independently
**VERIFIED WITH CORRECTIONS** by `.1R.30R.2A.1`). It adds the
`HPAC-PAWA-AGENT-EXCLUSION/1.0` protected recognition-input artifact (§32A), the
`agent_exclusion_digest` field on `HPAC-PAWA-CURRENT-GENERATION/1.0` (§20A), the
S-1 versioning rule (§80.1), and names the resolution source in §2 / §9 / §10 /
§33. It incorporates **C-1** (R1-PURE → R1-HYBRID: `symbolic_account` +
`provisioned_uid` + live groups), **C-2** (anchor-digest rollback binding), and
**S-1** (explicit MINOR rule). It **does not** rewrite the v1.0 freeze record;
v1.1 is append-only. HPAC-001 v2.1, RHAMP-001 v1.0, HBDC-001 v1.2, and the
`HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0` schema are byte-unchanged; no new
`pawa_failure_code`; no `src/pcae` change. v1.1 requires its own **dedicated**
independent verification — `.1R.30R.2A.3` (finding **C-3**), foldable into
`.1R.30R.3.2` only at explicit operator discretion — **before** `.1R.30R.3.1`
implementation relies on its text.

**v1.2** was frozen by Phase
149O.20L.7O.3W.1R.2B.1R.1.1R.30R.4R — a **MINOR** evolution resolving the
historical `.30R.4` implementation blocker. It adds the single metadata-only
`configure_presentation_mechanism` family, exact role
`presentation_mechanism_installer`, and exact admin consumer
`pcae.core.hpac_protected_presentation_admin`; executable helper bytes remain
out-of-band deployment-owner installed. HPAC-PPA-001 v1.0 is frozen alongside
it as the narrow companion owning installation/currentness and runtime
evidence-writer semantics. Runtime role `protected_presentation_mechanism`
remains outside PAWA. No existing failure code, PAWA recognition predicate,
capability field, one-operation lifecycle, or security invariant is weakened.
HPAC-001 v2.1 and RHAMP-001 v1.0 remain byte-unchanged. Historical v1.1 and its
IV remain immutable.

## 95A. R1 / R2 / R3 / R4 design disposition (append-only, v1.1)

| Option | Disposition |
|---|---|
| **R1-PURE** (adjudication `.1R.30R.2A` §7.1) — protected `agent-exclusion.json`, symbolic account name, no uid integer, live `(uid, gids)` | **superseded** by the independently-verified **R1-HYBRID** correction (C-1): the pure-symbolic form silently rebinds when the account is deleted and recreated under a new uid, and is internally inconsistent with the adjudication's own §6 "bound expectation" language. |
| **R1-HYBRID** (this IV `.1R.30R.2A.1` §7.7 / §15.2) — symbolic account name **+** `provisioned_uid`, live `getpwnam(name).pw_uid == provisioned_uid`, live groups, digest bound into the current-generation anchor | **FROZEN in v1.1** (§32A, §20A). |
| **R2** — bind the account name into an HBDC-001 environment-lock config | **REJECTED** — requires an HBDC-001 amendment (a second frozen contract evolving, and HBDC's own v1.1 / v1.2 are pending IV); violates HPAC-PAWA-REQ-134 (PAWA's exclusion source belongs in PAWA's own `.authority/` namespace — no cross-subsystem coupling). |
| **R3** — ship with no production mapping, fixture seam only | **REJECTED as the resolution** — fail-closed safe but permanently production-unsatisfiable; `.1R.30R.3.1` could then never establish the production writer anchor N-16-5 requires, and the blocker would resurface at `.1R.30R.6`. **Retained only as the test-seam strategy** (needed under R1-HYBRID too — §32A / HPAC-PAWA-REQ-166 / §75). |
| **R4** — some other existing source | **REJECTED** — no superior source-supported option exists: `DeploymentBinding` / the store manifest name no OS principal; folding the name into `deployment-owner.json` is contra §14 / HPAC-PAWA-REQ-037; a systemd `User=` / launchd `UserName` / `run_as` fact is exactly the caller/environment-controlled input HPAC-PAWA-REQ-021 forbids as the resolution source. |

The historical `.1R.30R.2A` verdict prose is **not** rewritten by v1.1; this
table records the append-only refinement (R1-PURE → R1-HYBRID) the IV
established.

## 95. Expected contract verdict

```
HPAC PRODUCTION PROTECTED ADMINISTRATION WRITER ANCHOR CONTRACT:
HPAC-PAWA-001 v1.0 — FROZEN
— PRODUCTION WRITER ANCHOR CONTRACT FROZEN — NOT IMPLEMENTED
— NO PRODUCTION SOURCE CHANGE
— NO HPAC-001 BUMP — NO RHAMP-001 CHANGE — NO EXISTING-CONTRACT CHANGE
— F-1 / F-2 / F-3 INCORPORATED
— RUNTIME Observed / observe / unavailable
— FIRST EXTERNAL EFFECT ABSENT
— N-16-5 NOT CLOSED
```

### 95.1 Expected contract verdict (v1.1)

```
HPAC-PAWA-001 v1.1 — FROZEN
— CONFIGURED-AGENT-PRINCIPAL RESOLUTION SOURCE CONTRACT FROZEN — NOT IMPLEMENTED
— R1-HYBRID FROZEN — HPAC-PAWA-AGENT-EXCLUSION/1.0 (symbolic_account +
  provisioned_uid + live groups + agent_exclusion_digest current-generation
  binding) FROZEN
— DELETE / RECREATE-UNDER-NEW-UID / UID-REUSE / RENAME FAIL CLOSED
— GROUP DRIFT DETECTED (live groups)
— THREE F-1 PREDICATES REMAIN DISTINCT
— NO ENVIRONMENT / CALLER / CURRENT-EUID SHORTCUT
— NO NEW pawa_failure_code — NO RHAMP-001 CHANGE — DESCRIPTOR SCHEMA UNCHANGED
— HPAC-001 v2.1 / RHAMP-001 v1.0 / HBDC-001 v1.2 BYTE-UNCHANGED
— MINOR (S-1) — NO MAJOR TRIGGER
— C-1 / C-2 / S-1 INCORPORATED — C-3 (.1R.30R.2A.3 dedicated contract IV)
  RECOMMENDED, NOT AUTHORIZED
— NO PRODUCTION SOURCE CHANGE
— RUNTIME Observed / observe / unavailable — FIRST EXTERNAL EFFECT ABSENT
— N-16-5 NOT CLOSED (contract-level gap closed; implementation + dedicated
  contract IV pending)
```

## 96. Recommended next phase (v1.0 baseline)

**149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3 — N-16-5 Production Protected-Admin Writer
Anchor + Real FIDO2 Credential Registry and Authentication Mechanism
Implementation.** It requires its own separate explicit human authorization
(ID recommended, NOT reserved). It SHALL implement: the `PRODUCTION` writer
factory in a non-agent-importable module + the exact consumer-inventory guard;
the `HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0` + `HPAC-PAWA-CURRENT-GENERATION/1.0` +
`HPAC-PAWA-ISSUANCE-EVIDENCE/1.0` schema helpers and validation; the out-of-band
`provision` / rotation / revoke script; the §33 positive validation sequence
(F-1 per-predicate identity); `HumanPrincipalRegistryStore` production writer
path (`CredentialRecord` byte-unchanged); the RHAMP-001 `RHAMP-FIDO2-CREDENTIAL/1.0`
sidecar and `RHAMP-COUNTER-STATE/1.0` stores; the protected-admin enrollment +
first-credential bootstrap tool; `FIDO2HumanAuthenticator` for
`hpac.fido2.uv_presence.v2`; real CTAP2 assertion verification in `hpac_verifier`
incl. the `FLAG.UV` check; `_ELIGIBLE_MECHANISM_IDS += {hpac.fido2.uv_presence.v2}`;
`terminal_reason_code` wiring (41-code vocabulary). **No protected approval UI.
No real approval-authority production path. No N-16-6 / N-16-7. No Slice C. No
first external effect. No execution enablement.** Then `.1R.30R.4` (IV) →
`.1R.30R.5` (protected presentation + real-assurance wiring) → `.1R.30R.6`
(IV + mandatory real-CTAP2-hardware verification + N-16-5 closure) → N-16-6 →
N-16-7 (strictly last). **Do not begin `.1R.30R.3`.**

## 96A. Recommended next phase (as of v1.1)

**`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A.3` — Independent Verification of the
HPAC-PAWA-001 v1.1 Configured-Agent-Principal Resolution Source Contract
Freeze** (finding **C-3**; ID recommended, **NOT reserved**; requires its own
separate explicit human authorization; a fold into `.1R.30R.3.2` is permitted
**only at the authorizing operator's explicit discretion**). Its minimum scope
is HPAC-PAWA-REQ-210. Then `.1R.30R.3.1` (Slice 1 — PAWA production writer
anchor + `hpac_pawa_agent_exclusion.py` + `resolve_configured_agent_identity()`;
atomic unit A1) → `.1R.30R.3.2` (IV) → `.1R.30R.3.3` / `.3.4` (Slice 2 — RHAMP
credential registry + sidecar / counter-state + enrollment tool / IV) →
`.1R.30R.3.5` / `.3.6` (Slice 3 — `FIDO2HumanAuthenticator` + native CTAP2
verify + `_ELIGIBLE_MECHANISM_IDS` widening + 41-code terminal-reason wiring /
IV) → `.1R.30R.4` (composite IV) → `.1R.30R.5` (protected presentation +
`require_real_assurance` wiring through Gate 5 / Gate 9) → `.1R.30R.6` (IV +
mandatory real-CTAP2-hardware verification + **N-16-5 closure**) → N-16-6 →
N-16-7 (strictly last). **Do not begin `.1R.30R.2A.3`. Do not begin
`.1R.30R.3.1`. Do not begin N-16-6 / N-16-7 / Slice C. Do not implement or call
the first external effect. Do not enable execution.**
