# Phase 149O.1D — Human Approval Trusted Provenance Implementation Plan

## 0. Baseline

- **Repository:** `~/repos/pcae-harness`, branch `main`, working tree clean
  at phase start, `origin/main..HEAD` = 0.
- **Latest completed phase:** 149O.1C — Human Approval Trusted Provenance
  Contract Independent Verification (commit `15cb7543`, pushed).
  Verdict: `VERIFIED WITH NON-BLOCKING FINDINGS — HATP-001 v1.0 CONFORMS`.
  Contract readiness: `READY FOR IMPLEMENTATION PLANNING`. Deployment
  readiness: `NOT READY` (expected, fail-closed).
- **Frozen contract:** `docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md`,
  identity `HATP-001 v1.0`, status `FROZEN`. Normative span
  `HATP-REQ-001`..`HATP-REQ-117`, 117 unique sequential requirements,
  independently re-verified this phase (fresh `grep -oE 'HATP-REQ-[0-9]+'`
  sweep: 117 unique IDs, no gap, no duplicate).
- **This phase's type:** implementation planning only. `src/pcae/**` and
  `docs/contracts/**` are untouched by this phase (verified below, §176).
- **Open rollback-evidence findings, reconfirmed OPEN, unaffected by this
  phase:** B-149O-1, B-149O-2, B-149O-3, B-149O-4.
- **Runtime state, unaffected by this phase:** `Observed` / `observe` /
  `unavailable` (confirmed via `pcae runtime inspect`, §181 below).
- **Fast Green entering baseline:** `4391 passed` (per 149O.1C's own
  report); this phase's own Fast Green run is recorded at §180.

## 1. HATP Contract Identity

`HATP-001 v1.0`, `FROZEN` by Phase 149O.1B.3, independently verified by
149O.1C. Depends on RAE-001 v1.0, CHGR-001 v1.3, IWC-001 v1.2, RWMPC-001
v1.0, PBPA-001 v1.0, PBPC-001 v1.2 — all unamended. Structural (never
composed) precedent: TAMC-001 v1.0 / TAMPC-001 v1.1 `human_authorization`
shape. This plan treats HATP-001 as **frozen normative input** throughout;
it does not redesign the trust architecture (Root 1, Root 2A, Root 2B, CRI
Model A) established by 149O.1A/149O.1B/149O.1B.1/149O.1B.2 and frozen by
149O.1B.3.

## 2. 117-Requirement Traceability — Method and Result

Every `HATP-REQ-001`..`HATP-REQ-117` is assigned exactly one **primary**
implementation-subsystem owner (§4 letters A-N below); several
requirements are additionally cross-cutting and are noted as such where
relevant, but no requirement carries two primary owners and none is left
`UNMAPPED`. The full range-collapsed table is reproduced at §4.2. A
companion machine-checkable form of this same mapping is embedded in
`tests/test_phase_149o_1d_human_approval_trusted_provenance_implementation_plan.py`,
which independently re-derives the 117 requirement IDs from the contract
text (mirroring 149O.1C's own methodology of never trusting a prior
phase's count) and asserts every one of them appears in this plan
document's traceability table exactly once.

**Result: 117 / 117 HATP requirements have a concrete implementation
disposition. Zero requirements are UNMAPPED. This is a Blocking-avoidance
condition per the governing prompt's own list (§164 of the governing
prompt) — satisfied.**

## 3. Findings Disposition (Carry-Forward)

### 3.1 F-149O.1C-1 (proof payload closed-schema gap)

**Disposition: CLOSED BY IMPLEMENTATION PLAN DECISION.**

Production HATP proof parsing SHALL reject unknown/unrecognized proof
fields unless explicitly versioned and supported (§21 below, "F1
Closed-Schema Hardening"). This is an **implementation-hardening
decision**, not a contract amendment: HATP-001's own text is not modified;
`additionalProperties: false` (or a model-equivalent strict-parsing rule)
is a future-implementation choice within the space HATP-REQ-075/HATP-REQ-069
already leaves open (canonical serialization and payload field-set are
frozen at the field-name/semantics level; schema strictness was not
specified either way). No HATP-001 semantic meaning changes.

### 3.2 F-149O.1C-2 (HATP-REQ-116 self-count editorial gap)

**Disposition: RETAINED EDITORIAL OBSERVATION.** Implementation
traceability in this plan uses the independently re-verified count of
**117** requirements (HATP-REQ-001..HATP-REQ-117), not the 116 stated in
HATP-REQ-116's own prose. HATP-001 is not edited by this phase — byte-
unchanged, confirmed at §176. Per §167 of the governing prompt, this plan
does **not** insert a contract erratum into any implementation critical
path, because no tooling in this plan's design depends on HATP-REQ-116's
prose count; the plan's own validation test (§2 above) uses the
independently re-derived count, exactly as 149O.1C's own suite did.

## 4. Requirement Grouping and Full Traceability Matrix

### 4.1 Fourteen Implementation Subsystems

| Letter | Subsystem | Purpose |
|---|---|---|
| A | Repository Identity | CRI Layer 1 — repository-local, random, persistent `repository_id`; generation, persistence, init/migration integration |
| B | Bootstrap Environment / Security Boundary | Class-B OS principal separation, no-sudo-escape, agent-capability boundary |
| C | Protected Trust Store | CRI Layer 2 deployment binding + admin-owned registry (enrollment, revocation, rebind) storage/ownership model |
| D | Principal / Authority Registry | `principal_id`, key/credential identity, rollback-authority mapping, enrollment/rotation/revocation operations |
| E | Provider / Attestation Abstraction | `HATP_HARDWARE_PROVIDER_V1` profile, provider interface, device attestation, first real-provider strategy |
| F | Human-Presence Signing Interface | Fresh-presence enforcement, 1:1 presence:proof, signing-request path |
| G | HATP Proof Schema / Models | `HumanApprovalProvenanceProof` fields, `proof_version`, discriminated AG3/AG5 payload |
| H | Canonical Serialization | Deterministic signed-payload bytes |
| I | Proof Verification Engine | `verify_hatp_proof`, closed vocabulary, conjunctive `VALID` rule, validation order |
| J | Readiness / Fail-Closed Environment Gate | Activation conjunction, `UNSAFE_CONFIGURATION`/unavailable states, no partial trust |
| K | Test Provider | Deterministic test-only signer, production-unselectable |
| L | RAE Consumption Boundary | RAE-001/CHGR-001/IWC-001/AESIC-001/TAMC-001/RWMPC-001/PBPA-001/PBPC-001 non-amendment boundaries |
| M | Migration / Initialization | `pcae init` integration, idempotent identity creation, `.gitignore` wiring |
| N | Adversarial Verification | Attack-matrix mapping, B-149O closure mapping, independent-verification criteria |

### 4.2 Full Range-Collapsed Traceability Table

| Requirement(s) | Subsystem | Disposition summary |
|---|---|---|
| HATP-REQ-001..002 | J | Purpose answered by the fail-closed activation gate (§9) and verification engine (§16); no standalone module — enforced end-to-end by J+I. |
| HATP-REQ-003 | J | Activation-gate scope frozen at §9; Wave 4/6 tests assert scope boundary. |
| HATP-REQ-004..005 | L | RAE/PB/RWMPC/CHGR non-governance boundary; enforced by keeping HATP core free of RAE/PB imports (§25 dependency-direction rule). |
| HATP-REQ-006 | C | Term freeze anchored in `hatp_bootstrap.py`'s module docstring; each term's concrete owner is cross-referenced (repository_id -> A, provider -> E, proof -> G, trust store -> C). |
| HATP-REQ-007..008 | B | Threat A capability boundary encoded as the mandatory adversarial test matrix (§23, attacks #6-#9) plus the "no privilege escalation" architecture constraint from 149O.1B.1 §9 (deployment-verification, Wave 5/7). |
| HATP-REQ-009 | J | Threat B/non-goals recorded as explicit stop conditions (§22) — no implementation claims coverage of Threat B. |
| HATP-REQ-010..011 | I | Verification-order (§16.2) and semantic-distinction assertions built into `verify_hatp_proof`'s return-type discipline (never reuses RAE/PB vocabulary, §16.1). |
| HATP-REQ-012 | B | Three-root summary reflected directly in the module split (E=Root1 production, E=Root2A, B=Root2B) — no single module conflates the three roots. |
| HATP-REQ-013 | A | CRI Model A high-level freeze reflected in `repository_identity.py` module docstring; Layer 1/Layer 2 split mirrored in A/C module boundary. |
| HATP-REQ-014..015 | D | `PrincipalRecord.principal_id` stable across rotation (Wave 2 model); authority looked up separately, never derived from `principal_id` alone. |
| HATP-REQ-016..018 | F | `HumanPresenceSigner` interface requires a fresh presence token per signing call; 1:1 presence:proof enforced by the provider interface never accepting a cached/session assertion (Wave 5). |
| HATP-REQ-019..022 | E | `HATP_HARDWARE_PROVIDER_V1` profile encoded as a `Protocol`/ABC with explicit capability-claim fields; test-provider containment enforced structurally (§20, K). |
| HATP-REQ-023..025 | E | Attestation verification is a distinct step from signature verification (§16.2 order); trusted attestation roots sourced from protected config (C), never proof-embedded. |
| HATP-REQ-026..027 | B | Class-B OS boundary and no-sudo-escape are **deployment-verification** obligations, not source-code obligations this phase; Wave 7/deployment-phase readiness check (`hatp readiness`, J) reports on them without claiming full mechanical proof (§35 stop condition). |
| HATP-REQ-028..029 | B | Two-principal v1 topology; `hatp readiness` reports `SAME_USER_UNSAFE` when Agent/Admin share an OS principal (Wave 4 readiness gate, J). |
| HATP-REQ-030..035 | C | `HATPTrustStore` interface (read-only to agent runtime, §14); anti-redirection enforced by no env-var/CLI override in the production API (§25 of governing prompt; Wave 2/3). |
| HATP-REQ-036..042 | D | Enrollment/self-enrollment/replacement/deletion prohibitions enforced structurally: no production API accepts caller-supplied principal/key/authority; admin-surface-only mutation (§28-30, Wave 2/7 adversarial tests). |
| HATP-REQ-043..045 | D | Authority is a registry-exclusive read (`HATPTrustStore.lookup_authority`), never derived from proof content or attestation alone. |
| HATP-REQ-046..051 | A | `repository_id` generation/persistence/properties; owned by a general PCAE core facility (§12 below), not HATP-specific; Wave 1. |
| HATP-REQ-052..066 | C | Full CRI Layer 2 binding + scenario/attack matrix (move/rename/copy/clone/fork/worktree/backup/reidentity) — `DeploymentBinding` model + canonical-root comparison (Wave 2/3, adversarial tests in Wave 4/7). |
| HATP-REQ-067..068 | G | `HumanApprovalProvenanceProof.proof_version = 1` frozen field (Wave 3). |
| HATP-REQ-069..074 | G | Canonical payload field set, discriminated AG3/AG5 shape, mutation-invalidation via digests (Wave 3). |
| HATP-REQ-075 | H | Canonical serialization function, deterministic sorted-key/fixed-encoding JSON (Wave 3, reusing `cltr/canonicalization.py` pattern). |
| HATP-REQ-076 | E | Provider/signature semantics defined per selected first-provider strategy (§19); no algorithm frozen prematurely (Wave 5). |
| HATP-REQ-077 | I | Signer trust always resolves through `HATPTrustStore`, never proof self-assertion (Wave 4). |
| HATP-REQ-078..083 | I | Closed 13-state verification vocabulary; conjunctive `VALID` rule; all replay-rejection scenarios (Wave 4, adversarial tests Wave 4/7). |
| HATP-REQ-084..085 | I | Freshness/future-dated-proof handling inside the verifier; TTL itself remains RAE-owned (cross-reference L). |
| HATP-REQ-086 | D | Deterministic key-rotation procedure, admin-surface-only (Wave 2/7, deferred to admin-CLI scope decision §29). |
| HATP-REQ-087 | D | Key revocation, admin-surface-only, consumption-time lookup. |
| HATP-REQ-088 | D | Authority revocation; consumption-time precedence enforced inside the verifier (I) reading from D's registry. |
| HATP-REQ-089 | C | Deployment-root change requires admin rebind; no agent-driven rebind path exists anywhere in the design. |
| HATP-REQ-090..093 | J | Fail-closed failure semantics; same-user/headless states both resolve to unavailable, never a soft-allow. |
| HATP-REQ-094 | I | Verifier code path has no write capability into the trust store (enforced by dependency direction: verifier imports read-only `HATPTrustStore` methods only). |
| HATP-REQ-095..096 | L | RAE-001 compatible-as-is; AND-conjunction integration rule (`approval_present` requires both valid HATP proof and independent RAE pass) — Wave 6, not implemented until then. |
| HATP-REQ-097 | L | CHGR-001 relationship unchanged; HATP proves independent provenance for the operation CHGR's Decision records. |
| HATP-REQ-098 | L | IWC-001 boundary; IWC confirmation never treated as approval evidence anywhere in the design. |
| HATP-REQ-099 | L | AESIC-001/AEM-001 disclosure-only boundary preserved; no HATP module reads AESIC/AEM as an authority input. |
| HATP-REQ-100 | L | TAMC-001/TAMPC-001 structural-precedent-only; HATP's own dataclasses are independent types, never subclasses/wrappers. |
| HATP-REQ-101..104 | L | RWMPC-001/PBPA-001/PBPC-001 no-amendment boundary; Permission Broker receives only the truthful `approval_present` fact (§24-27 below). |
| HATP-REQ-105..106 | N | B-149O-1..4 closure mapped explicitly to implementation waves (§24 below); none closed by this phase. |
| HATP-REQ-107 | A | Repository-identity contract-ownership statement; `repository_id` implemented as a general PCAE core facility usable (not required) by other subsystems, per explicit-dependency-declaration discipline. |
| HATP-REQ-108 | J | Current deployment readiness block reproduced verbatim at §0 and §183; unaffected by this phase. |
| HATP-REQ-109..110 | N | Threat-capability matrix reproduced as the basis for Wave 4/7 adversarial test design. |
| HATP-REQ-111 | N | All 20 mandatory acceptance attacks individually mapped to implementation waves and tests (§23 below). |
| HATP-REQ-112 | L | Cross-contract compatibility reconfirmed; this plan introduces no new dependency edge contradicting §112's reconfirmed list. |
| HATP-REQ-113 | N | Full requirement-to-property cross-check performed by this plan's own traceability table (§4.2) plus the validation test (§2). |
| HATP-REQ-114 | N | Blocking-condition table reconfirmed unresolved-condition-free at contract-freeze time; this plan introduces no new blocking condition (§26 below re-runs the check against the *implementation* plan itself). |
| HATP-REQ-115 | J | Class-B provisioning explicitly non-blocking for contract text; this plan's Wave 7 (deployment provisioning) is scheduled after software waves, consistent with this. |
| HATP-REQ-116 | N | Subject of F-149O.1C-2 (§3.2); requirement itself is mapped (to N) independent of its own prose miscount. |
| HATP-REQ-117 | G | Versioning discipline; any future concrete algorithm/serialization choice proceeds through a governed contract-amendment phase, never silent reinterpretation. |

## 5. Existing Source Architecture Survey

Full inventory performed this phase (research-only; no files modified).
Summary of reusable precedent, by category:

1. **Canonical JSON / deterministic serialization.** No single shared
   top-level helper exists; the strongest, most direct precedent is
   `src/pcae/cltr/canonicalization.py::canonicalize_dict(value: dict) -> bytes`
   (sha256-over-sorted-JSON pattern), paired with
   `src/pcae/core/rollback_approval_evidence.py:530` `_canonical_bytes(binding)`
   / `:535` `_compute_content_digest(binding)` as RAE's own analogous
   pair. HATP's canonical-payload serializer (H) SHALL mirror this
   pattern rather than invent a new one.
2. **Atomic file write / safe persistence.** No shared top-level helper;
   best structural pair: `src/pcae/cltr/persistence.py:104` `_write_atomic(path, data)`
   and `src/pcae/governance/publication/storage.py:42` `_write_atomic_json(path, payload)`
   plus `:116` `commit_publication()`'s `O_CREAT|O_EXCL` exclusive-create
   idiom — the direct precedent for a race-safe HATP enrollment-marker
   write (C).
3. **Root-containment / symlink-safety.** Two mature implementations:
   `src/pcae/schema_runtime/loader.py::_resolve_root`/`_normalize_lexical`/`load_schema_resource`
   (normalize -> containment-check -> reject-symlink -> `resolve(strict=True)`
   -> re-check containment) and `src/pcae/cltr/persistence.py::_is_safe_segment`/`_resolved_root`/`_safe_generation_dir`
   (TOCTOU-aware, raises `PathContainmentError`). The CRI canonical-root
   resolver (A/C, HATP-REQ-053) SHALL reuse this pattern; it is **not**
   implemented anywhere in RAE's own I/O today (RAE reuses only the plain
   atomic-write idiom, not path-containment hardening) — this is new
   composition, not new invention.
4. **File permission / ACL / ownership checks.** No existing precedent.
   `src/pcae/core/writer.py:110` `make_executable_when_needed` only *sets*
   an executable bit; it does not check or reject unsafe permissions. The
   protected trust-store permission/ownership verification (C,
   HATP-REQ-031) is a **genuine gap** — no reusable helper exists; it must
   be built new in Wave 2, using the `stat` module per `writer.py`'s only
   stylistic precedent for touching file modes.
5. **Repository identity precedent.** No `repository_id`/`repository_instance_id`
   concept exists anywhere in `src/pcae`. A different, unrelated concept,
   `repository_identity` (a plain caller-declared string used by CLTR
   migration derivation, `src/pcae/cltr_prototype/identity.py`,
   `src/pcae/cltr/models.py`), already exists but is explicitly
   disqualified as HATP's identity primitive by 149O.1B.1 §14 (caller-
   selectable, not protected, not hardware/OS-anchored) — this plan does
   **not** reuse or rename that field; HATP's `repository_id` (A) is a
   new, independent concept and MUST NOT be confused with CLTR's
   `repository_identity` string field in code, tests, or documentation.
6. **Trust-store / registry precedent.** Best combination:
   `src/pcae/governance/publication/storage.py::PublicationRecordStore`
   (durable, race-safe, exclusive-create commit pattern) +
   `src/pcae/core/runtime_registry.py::RuntimeRegistry`/`PluginDescriptor`/`validate_descriptor`
   (frozen-vocabulary, frozen-descriptor, fail-closed validation, pure
   in-memory interface style) + `src/pcae/core/rollback_approval_evidence.py`'s
   explicit `revoke_rollback_approval_binding()`/`RevocationMetadata`
   idiom (the only end-to-end revocation implementation in the codebase
   today). `HATPTrustStore` (C) SHALL combine these three patterns.
7. **Schema validation.** `src/pcae/schema_resources/` uses a
   `*.schema.json` + Draft-2020-12 `$id`/`$schema` convention, loaded via
   `src/pcae/schema_runtime/loader.py::load_schema_resource`/`load_schema_package`
   (containment check, no-symlink, strict JSON, digest). A new
   `schema_resources/human_approval_trusted_provenance/records/` directory
   (G) reuses this existing loader unchanged — no new loader is needed.
8. **RAE-001 implementation module.** `src/pcae/core/rollback_approval_evidence.py`.
   Sole authority for `approval_present` (module docstring line 16-17);
   integration point is `derive_rollback_approval_present()` (line 1381,
   thin wrapper over `resolve_rollback_approval_evidence(...).approval_present`,
   line 1399, exported in `__all__`). Future RAE/HATP integration (Wave 6,
   L) SHALL extend this module's inputs or call this function — it SHALL
   NOT re-derive `approval_present` in a second location.
9. **Permission Broker boundary.** `src/pcae/core/permission_broker_foundation.py`
   and `src/pcae/core/permission_broker.py` — confirmed via grep, **zero**
   provider/hardware/signing/fido/hsm references in either file today.
   This plan's dependency-direction rule (§25) preserves that: no HATP
   module is imported by either Permission Broker file.
10. **`pcae init` implementation.** `src/pcae/commands/init.py::run_init`
    (CLI handler) delegates to `src/pcae/core/writer.py::write_missing_files`/`plan_missing_files`
    (idempotent, only-create-if-missing, dry-run-capable) driven by
    `INIT_TEMPLATES` (`src/pcae/core/templates.py`). Repository-identity
    init integration (M) SHALL add entries to this existing templates
    mechanism rather than writing new file-creation logic.
11. **Provider/adapter abstraction precedent.** `src/pcae/core/runtime_registry.py`
    (Phase 110E) — frozen-vocabulary tuples, immutable `PluginDescriptor`
    (`MappingProxyType`-wrapped manifest), pure side-effect-free
    `validate_descriptor()`, explicit "registry never executes lifecycle"
    isolation discipline. HATP's hardware-provider abstraction (E) SHALL
    follow this same structural pattern (interface + registry + selection
    metadata, execution kept separate).
12. **Python version / dependencies.** `pyproject.toml`: `requires-python = ">=3.9"`;
    only production dependency is `jsonschema>=4.18,<5`. **No cryptography,
    fido2, or other security/crypto library exists today.** Any real
    hardware-provider implementation (E, Wave 5) requires a new dependency
    — explicitly out of scope for this phase (§14 below, dependency plan;
    no dependency added this phase).
13. **Timestamp parsing.** `src/pcae/core/rollback_approval_evidence.py::_parse_iso_timestamp`
    (line 778) is the only rigorous, fail-closed, Z-suffix-safe, naive-
    datetime-rejecting parser in the codebase; most other modules use a
    raw `datetime.fromisoformat` with no Z-handling. HATP's `issued_at`
    parsing (I, HATP-REQ-085) SHALL reuse or mirror
    `_parse_iso_timestamp` exactly, never a raw `fromisoformat` call, to
    avoid reintroducing the Python-3.9 portability defect this project
    already hit once in the 149O area.

## 6. Implementation Dependency Graph

```
Repository Identity (A)
        |
Protected Deployment Binding (part of C, admin-owned)
        |
Protected Trust Store / Authority Registry (C, D)
        |
Bootstrap Readiness Check (J: "hatp readiness")
        |
Provider + Attestation (E)
        |
Human-Presence Signer (F)
        |
Proof Schema + Canonical Serialization (G, H)
        |
Verifier (I)
        |
HATP Evidence Resolution (I, exposed to L)
        |
RAE Integration (L)
```

Derivation rationale (from source architecture, not assumed): A must
exist before C's Layer-2 binding can name a `repository_id` to bind. C
(trust store + registry) must exist before D's enrollment operations have
anywhere durable to write. J's readiness gate depends on both B
(deployment-level OS-boundary fact) and C (trust-store existence/
ownership fact) — it is placed after C not before, because a readiness
check that reports on a not-yet-modeled trust store is vacuous. E depends
on nothing upstream except the interface contract (G's canonical payload
shape informs what E must be able to sign over) — E CAN be developed in
parallel with C/D against a stub, but a *real* provider integration
cannot be independently verified until G/H exist to define the exact
payload E signs. F is provider-specific presence enforcement, layered on
top of E. G/H (schema + serialization) can be developed early against a
test provider (K) without waiting for a real E, **provided** production
trust activation remains gated by J regardless (this is the fail-closed
invariant, §9). I (verifier) needs G/H to exist (something to verify) and
C/D to exist (something to verify against). L (RAE integration) is
strictly last — it is the only wave that changes `approval_present`
derivation, and per HATP-REQ-096 both HATP validity and RAE-001's own
independent conditions are required, so RAE integration cannot precede a
working verifier.

## 7. Module Ownership Proposal

Selected module names, informed by §5's survey (no name is finalized as
"the" answer until the implementing phase inspects the tree fresh — but
this proposal follows existing PCAE `src/pcae/core/*.py` conventions,
mirroring `rollback_approval_evidence.py`'s single-large-module style
rather than inventing a new package layout):

```
src/pcae/core/repository_identity.py          (A — general PCAE facility, not HATP-specific)
src/pcae/core/hatp_bootstrap.py                (C, D — trust store, registry, enrollment/rotation/revocation ops)
src/pcae/core/hatp_providers.py                (E, F, K — provider interface, presence, test provider)
src/pcae/core/human_approval_trusted_provenance.py  (G, H, I, J — proof model, serialization, verifier, readiness gate)
```

`rollback_approval_evidence.py` (L's consumption side) is **extended**,
not replaced, in Wave 6 — no HATP logic is planned to live inside it
(§11 below, "avoid monolithic implementation").

## 8. Repository Identity Ownership (A)

`repository_id` is owned by a **general PCAE core facility**
(`repository_identity.py`), not by HATP specifically — per HATP-REQ-107
and 149O.1B.2 §9's explicit design intent ("Layer 1 stays general-purpose
and HATP-independent so other PCAE subsystems... can use it without any
HATP coupling"). HATP consumes it through an explicit dependency, exactly
as HATP-REQ-107 requires of any other subsystem wishing to depend on it.

## 9-10. Repository Identity Generation and Persistence

- **Generation:** a cryptographically strong random UUID (`uuid.uuid4()`,
  stdlib, no new dependency), generated once at a defined initialization
  event (`pcae init`, or a first-use lazy-init guarded the same way).
  Confers no authority by itself (HATP-REQ-051).
- **Persistence:** repository-local, e.g. `.pcae/repository-identity.json`
  (final filename TBD by the implementing phase, following the
  `_XXX_RELATIVE_PATH = Path(".pcae") / "..."` convention already used
  throughout `src/pcae/core/*.py`, §5.5 above). **Not normally committed**:
  149O.1B.2 §12 independently verified `.pcae/` is not globally
  gitignored in this repository (several `.pcae/**` artifacts are tracked
  as part of the governed phase-completion lifecycle) — a future
  repository-identity file MUST be added to `.pcae/.gitignore` as part of
  its own implementation scope (Wave 1 change classification: `M`).

## 11. Existing Repository Initialization / 16. Idempotent Init / 17. Migration

`pcae init` (`src/pcae/commands/init.py::run_init`) delegates to
`src/pcae/core/writer.py::write_missing_files`, which is already
idempotent (only creates missing files; existing files are untouched
without `--force`). Repository-identity integration point: add a
generation step alongside (not inside) the existing `INIT_TEMPLATES`
write, guarded by "if the identity file does not already exist, generate
and write it; otherwise, preserve it unchanged" — this is a natural fit
for `write_missing_files`'s existing semantics and requires no new
idempotency machinery. Migration for repositories lacking an ID: the same
guarded generation step, invoked either by a repeat `pcae init` or a
future identity-aware `pcae init --ensure-identity`-style command; no
HATP authority is created by this step (identity creation alone grants
no authority, HATP-REQ-048).

## 12. Identity Validation / 19. Reidentity / 21. Worktree / 22. Clone Semantics

- **Validation:** format = valid UUID4 string, present schema-version tag
  (e.g. `{"schema_version": 1, "repository_id": "<uuid>"}`), all fields
  present; malformed/missing -> HATP unavailable (never treated as "no
  constraint").
- **Mutation:** unexpected change fails closed — the existing Layer-2
  binding (C) no longer matches; no automatic trust-store re-enrollment.
- **Reidentity:** deferred beyond v1 (per HATP-REQ-065, "No such operation
  is implemented by this phase" — same posture retained here; a future
  explicit reidentity operation MAY exist later, out of this plan's wave
  scope).
- **Worktree:** per 149O.1B.2 §13, each `git worktree add` receives a
  **distinct** repository-instance identity and requires separate
  enrollment — no shared-lineage shortcut. This is a real implementation-
  complexity item: `repository_identity.py`'s initialization path must key
  off the actual working-tree root (not `.git`'s shared object database
  path), which the implementing phase must verify concretely against how
  `.pcae/` is placed relative to worktrees today (149O.1B.2 flagged this
  as a real complexity source, not resolved by architecture alone).
- **Clone:** per 149O.1B.2 §12's verified (not assumed) finding, `.pcae/`
  is not globally gitignored today; the repository-identity file MUST be
  its own explicit gitignore addition (§10 above) so a normal `git clone`
  does not inherit an active local identity through committed state.

## 13. Protected Bootstrap Store Ownership / 24. Location / 25-26. Caller-Selection / 27-28. Interface

- **Ownership:** a distinct production storage abstraction (C,
  `hatp_bootstrap.py`) representing Human/Admin-owned trust state. It
  MUST NOT default to `repo/.pcae/**` (per 149O.1B.1 §12's explicit
  prohibition — repository-local storage is agent-writable and cannot be
  the trust anchor).
- **Location strategy:** platform-neutral abstraction, per 149O.1B.1 §12's
  two illustrative (non-frozen) candidates: a system-level trust directory
  (root-equivalent-owned, world-readable, e.g. `/etc`-analogous) or a
  user-level protected directory under the admin principal's own home
  directory (mode `0750`, group-readable by the agent's group). Selection
  is deployment policy, decided in Wave 2 against the concrete target
  platform(s) — this plan does not hardcode one without justification
  (per governing-prompt item 24).
- **No caller-selection:** the normal `validate_hatp(...)`-equivalent
  production API does NOT accept `trust_store_path`, `trusted_public_key`,
  or `registry` from ordinary callers (mirrors HATP-REQ-035's CLI-flag
  prohibition). Testability requires **internal/test-only dependency
  injection** — a constructor parameter on `HATPTrustStore` usable only
  by test code (never exposed through `pcae`'s normal CLI/config surface,
  §58/§107 below, K).
- **Interface (conceptual, exact API finalized in Wave 2):**

```python
class HATPTrustStore:
    def load_repository_enrollment(self, repository_id: str) -> DeploymentBinding | None: ...
    def lookup_principal(self, principal_id: str) -> PrincipalRecord | None: ...
    def lookup_signer(self, signer_key_id: str) -> SignerRecord | None: ...
    def lookup_authority(self, principal_id: str, repository_id: str) -> AuthorityRecord | None: ...
    def signer_revoked(self, signer_key_id: str) -> bool: ...
```

## 14. Trust Store Is Read-Only to Agent Runtime / 29-30. Administrative Mutation

Production verifier interface exposes only the five read methods above.
No `enroll()`, `grant()`, `revoke()`, or `rotate()` method is reachable
through the ordinary agent-execution code path. Enrollment/revocation/
rotation live in a **separate future Human/Admin administrative surface**
— this plan defers the decision between "administrative library API only"
vs. "dedicated admin CLI" to Wave 2/7 (whichever wave actually implements
the admin surface), because the decision depends on concrete deployment
constraints not yet fixed. Any future admin command MUST verify or assume
execution only under the Human/Admin principal — never a `--i-am-admin`
flag (explicit prohibition carried forward).

## 15. OS Principal Verification / 16. POSIX Reference / 17. Windows / 18. Current Platform

- **Cross-platform check strategy:** effective UID, file UID/GID, mode/
  ACL bits, parent-directory ownership, write-access probing — planned at
  the architecture level; exact implementation deferred to Wave 2/7
  against the concrete target platform.
- **POSIX:** `os.stat().st_uid`/`st_gid`, mode bits (`stat.S_IWGRP`,
  `S_IWOTH`), parent-directory write-check.
- **Windows:** capability abstraction, not silent exclusion. If the first
  implementation targets POSIX/macOS only (§18's likely choice, given
  current development platform is macOS), the Windows provider MUST fail
  closed as explicitly unsupported, never silently "readiness = true" by
  omission.
- **Current platform:** macOS/POSIX reference bootstrap provider is a
  reasonable first target, with explicit unsupported-fail-closed behavior
  elsewhere — decided deliberately in Wave 5/7, not assumed here.

## 16. No Sudo Escape / 36-37. Trust-Store Permission Verification / TOCTOU

- Per 149O.1B.1 §9, "no sudo escape" is a **prerequisite property**, not
  purely mechanically verifiable from software alone — this plan is
  explicit and honest per governing-prompt item 35: absence of
  unrestricted sudo may not be fully inferable from within the agent
  process. The plan distinguishes three tiers: **machine-verifiable
  readiness** (trust-store file ownership/permissions, checkable now),
  **deployment prerequisite** (sudo/ACL configuration, verified by a
  separate deployment-readiness procedure, not by application code alone),
  and **operator assertion** (a documented, human-attested claim that is
  never silently treated as a machine-verified fact). No implementation
  wave claims mechanical proof it cannot actually produce.
- **Permission verification (Wave 2):** agent write-access probe, parent-
  directory write-access probe, unsafe-ownership detection, symlink-
  substitution detection (reusing §5.3's `schema_runtime/loader.py`
  containment pattern). Fail closed on any uncertainty.
- **TOCTOU:** the implementing phase SHALL reuse the check-then-resolve-
  then-recheck pattern already present in `schema_runtime/loader.py` and
  `cltr/persistence.py` (§5.3) and SHALL NOT overclaim race-freedom beyond
  what that pattern actually provides (per governing-prompt item 37's
  explicit caution).

## 17. Canonical Path Resolution

Reuse `schema_runtime/loader.py`'s `_resolve_root`/`_normalize_lexical`
pattern (lexical normalize -> containment check -> reject-symlink ->
`resolve(strict=True)` -> re-check containment) for both the CRI canonical
deployment root (A/C) and the trust-store path resolution (C). No new
path-resolution primitive is invented; this is composition of two
existing, independently-tested patterns (`schema_runtime` +
`cltr/persistence`), applied to a new (HATP) context.

## 18. Bootstrap Enrollment Record / 39. Deployment Binding / 40-44. Path/Copy/Collision/Principal/Key Semantics

**Enrollment record model** (conceptual, Wave 2):

```
registry_version
repository_id
canonical_deployment_root      (resolved, symlink-free)
principal_id
signer_key_id / credential_id
provider_profile
authority_scope
valid_from
revoked_at / status
```

All copy/clone/rename/move/restore/reidentity/worktree scenarios follow
the scenario matrix already frozen at 149O.1B.2 §11 (reproduced
verbatim, not re-derived, since it is architecture already established
and this phase does not reopen it):

| Scenario | `repository_id` (Layer 1) | HATP authority (Layer 2) |
|---|---|---|
| Path rename / move | preserved | requires admin re-bind |
| Full directory copy | copied verbatim | fails closed — canonical root mismatch |
| `git clone` | new ID at that clone's own future init | none until independently enrolled |
| Fork | independent future identity | none inherited |
| `git worktree add` | distinct per worktree | distinct, enrolled separately |
| Backup restore, same root | preserved | may remain valid |
| Backup restore, different root | preserved (ID) | requires admin re-bind |
| Explicit re-identify (deferred) | new ID | must be re-enrolled from scratch |

**Enrollment collision:** if the same `repository_id` is already
registered at another deployment, the second deployment is **not**
silently authorized — an explicit Human/Admin decision is required
(Wave 2 registry design must reject/flag duplicate-ID registration
attempts rather than silently overwrite).

## 20. Principal Model / 44. Key Identifier

Stable `principal_id`, never a display name (HATP-REQ-014). Key/credential
identifier chosen after the Wave 5 provider survey: a deterministic
fingerprint (certificate fingerprint or public-key fingerprint), bound to
the trusted registry — exact representation deferred to Wave 5, since it
is provider-dependent (per governing-prompt item 44).

## 21-22. Provider Abstraction

```python
class HATPHardwareProvider(Protocol):
    def request_signature(self, payload: bytes, *, presence_timeout_s: float) -> ProviderAssertion: ...
    def verify_output(self, assertion: ProviderAssertion) -> bool: ...
    def credential_identity(self) -> str: ...
    def attestation_evidence(self) -> AttestationEvidence | None: ...
    def capabilities(self) -> ProviderCapabilities: ...
```

A provider output is never trusted merely because it implements this
interface (HATP-REQ-023/024) — the verifier (I) independently re-checks
accepted profile, attestation, registry authorization, deployment, and
operation binding regardless of what the provider itself asserts.

## 23. Real Hardware Provider Selection (mandatory concrete choice)

The governing prompt (§47) mandates a concrete first-provider strategy,
not a "TBD." Given this repository's declared dependency baseline
(`jsonschema` only, Python `>=3.9`, no crypto/FIDO library today):

**Selected strategy: FIDO2/WebAuthn as the primary candidate, contingent
on a Wave 5 verification spike confirming it can bind HATP's exact
canonical payload (§26 below); PIV as the documented fallback if that
spike fails.**

Rationale:
- FIDO2 hardware security keys (e.g. common USB/NFC security keys)
  provide a non-exportable private key, fresh user-presence enforcement
  per assertion (the "touch" requirement), and a stable credential
  identity — directly matching `HATP_HARDWARE_PROVIDER_V1`'s (a)/(b)/(d)
  properties (HATP-REQ-019).
- The open question, per HATP-REQ-020 (generic FIDO2/PIV are **not**
  declared interchangeable, and no protocol may be assumed to support
  arbitrary-payload signing without independent demonstration): FIDO2's
  WebAuthn assertion signs a challenge tied to an RP ID/origin model, not
  an arbitrary caller-supplied byte string, in most common
  implementations. Wave 5 MUST independently verify whether the selected
  library/device combination can bind HATP's canonical payload digest
  as the signed challenge before FIDO2 is accepted as compliant
  (HATP-REQ-020's exact requirement). If it cannot, **PIV** (smart-card/
  PKCS#11-based signing, which more directly supports signing an
  arbitrary caller-supplied digest under a touch policy) becomes the
  fallback strategy, with its own key-slot/touch-policy/algorithm
  architecture deferred to that fallback's own Wave 5 sub-plan.
- This is an explicit **provider-core-precedes-hardware-adapter** split
  (§96 of the governing prompt): Waves 1-4 develop proof schema,
  serialization, and verification logic against the test provider (K),
  independent of which real provider wins the Wave 5 spike, while
  production trust remains disabled/unready throughout (§9 below) — the
  spike's outcome affects only Wave 5's concrete adapter, not Waves 1-4's
  design.

## 24. Provider Selection Rationale (semantics check)

Neither FIDO2 nor PIV is selected merely because a device supports it
(§48 prohibition). Both were evaluated against HATP's actual required
properties: fresh physical presence (yes, both via touch/PIN+touch
policies), operation-bound signing (FIDO2: conditional on the Wave 5
spike; PIV: yes, directly), non-exportable key (yes, both, when backed by
genuine hardware), stable credential identity (yes, both), verifiability
(yes, both), and attestation or accepted provenance (yes, both — FIDO2
attestation certificates; PIV attestation via vendor-specific extensions
or accepted issuance chain).

## 25. Dependency Plan

**No dependency is added this phase.** If Wave 5 selects FIDO2, the
anticipated dependency class is a Python FIDO2/WebAuthn client library
(e.g. the `fido2` PyPI package or equivalent) plus possibly `cryptography`
for signature/attestation verification; if PIV, `cryptography` plus a
PKCS#11 binding (e.g. `python-pkcs11`) or platform middleware bridge.
Justification and supply-chain/portability classification are deferred to
Wave 5's own dependency-addition governance step — this plan only
identifies the dependency **class**, per governing-prompt item 51's
explicit "do not add dependency this phase" instruction.

## 26. External CLI Dependency (alternative provider path)

An alternative provider strategy calling system tools (`ykman`,
`ssh-keygen`, platform `security`/`openssl` equivalents) was considered
and is **not** selected as the primary strategy: parsing reliability and
cross-platform behavior are weaker than a library/API boundary, and
human-presence guarantees are harder to verify mechanically through a
subprocess boundary. It remains a documented fallback option only if the
Wave 5 spike finds no suitable library binding for the selected hardware
class on the target platform.

## 27. Provider Availability / 53. Missing Hardware

Missing hardware/provider produces `UNAVAILABLE`, never a software
fallback (HATP-REQ-021/093). Proof creation fails with a clear, non-
authoritative error in that case.

## 28. Human-Presence Enforcement / 54-55. Attestation / 56-57. Attestation Roots and Failure

- Presence is proven by the provider's own hardware enforcement (touch/
  biometric/PIN+touch), never by a caller-supplied boolean
  (`human_present=True` is explicitly rejected as an API shape,
  HATP-REQ-016 mirrored directly in the interface design, §21).
- Attestation verification is a distinct step from signature verification
  (§16.2 order) — a provider output's attestation chain is checked
  against protected, non-agent-authoritative roots (owned by C, either
  built-in pinned roots or admin-configured trust, decided in Wave 5).
- Attestation failure fails closed, same as any other non-`VALID` term
  (HATP-REQ-090).

## 29-32. Human-Side Approval Component, Blind-Touch Defense, Request Artifact, Replay

A dedicated future Human/Admin-side approval component (separate from the
autonomous agent's command path) is required: it independently
reconstructs the canonical operation payload (repository context,
Decision, operation family, AG3/AG5 identifiers) from durable state and
displays it **before** requesting the hardware touch — it does not sign an
opaque agent-provided digest (the "blind-touch defense," §69 of the
governing prompt). Ownership: a dedicated HATP admin/approval CLI
namespace, exact surface deferred to Wave 5/7 (§29 below of this plan
mirrors item 68-71 of the governing prompt exactly). A distinct,
untrusted **approval-request artifact** MAY exist as an agent-writable,
non-authoritative convenience object (never confused with the signed
proof); whether it additionally needs its own ID/freshness is deferred to
Wave 5 — no unnecessary authority semantics are added to it by default.

## 33-34. Proof Persistence / Proof Storage Is Not Trust Root

Proof storage location (co-located with RAE evidence, or a separate
canonical HATP store) is deferred to Wave 3/6 — because the proof is
cryptographically self-protecting (signature + protected-registry
resolution), agent read/copy access to a persisted proof MAY be
acceptable, but **proof validity never derives from file location**
(mandatory implementation principle, restated verbatim as a Wave 4 test
assertion: relocating/copying a valid proof file changes nothing about
its `WRONG_REPOSITORY`/`WRONG_OPERATION` verification outcome).

## 35. Verification Engine / 36. Verification Order / 37. Verification Result / 38. Error vs. Invalid

**Conceptual interface:**

```python
def verify_hatp_proof(proof: HumanApprovalProvenanceProof, *, live_operation_context: OperationContext) -> HATPVerificationResult: ...
```

**Verification order (fail-efficient, fail-closed), derived from the
contract's own conjunctive rule (HATP-REQ-079) and this plan's Wave
sequencing, not assumed independently of it:**

1. Environment readiness (J: is HATP even operationally available?)
2. Schema/structural validity (G/H)
3. Repository identity match (A)
4. Protected deployment enrollment match (C)
5. Signer lookup (D)
6. Authority lookup, consumption-time (D)
7. Provider profile accepted (E)
8. Signature/assertion valid (H/E)
9. Human-presence evidence valid (F)
10. Attestation valid (E)
11. Decision/Binding/operation binding match (G, cross-referencing L's
    RAE fields)
12. Time/revocation check (I, D)

**Result type:** the closed 13-state vocabulary frozen at HATP-REQ-078,
implemented as a closed enum — never the Permission Broker's
`ALLOW`/`DENY`/`HUMAN_REVIEW` vocabulary, never RAE-001's own 8-state
vocabulary (HATP-REQ-078's explicit non-conflation rule).

**Error vs. Invalid:** a structural/config `ERROR`/`UNAVAILABLE` state
(e.g. trust store unreachable, provider crashed) is distinguished from a
semantic `INVALID`-family state (e.g. `WRONG_OPERATION`,
`UNAUTHORIZED_SIGNER`) — both fail closed identically at the
`approval_present` consumption layer (L), but the distinction matters for
operator diagnostics (an `ERROR` suggests a misconfigured deployment; an
`INVALID`-family result suggests a genuine attack or genuine mistake).

## 39. Current Deployment Behavior / 40. Repository Identity Absent / 41. Hardware Absent / 42. Provider Offline Verification / 43. Signer Revocation / 44. Authority Revocation / 45. Rotation / 46-47. Time Handling / 48. Python Compatibility

- Until Class-B OS separation is provisioned, the production verifier
  returns `UNSAFE_CONFIGURATION` (or the closest contract-equivalent
  state, likely folded into `MISSING`/environment-unavailable handling) —
  it MUST NOT mark any proof `VALID` (HATP-REQ-091/092, restated as a
  Wave 4 mandatory test).
- Repository identity absent -> no valid proof (fails at verification
  step 3).
- Hardware absent -> proof **production** unavailable; proof
  **verification** of an already-produced proof preferably does not
  require the physical device to be present again (§80-81 of the
  governing prompt) — this is achievable if the selected provider (§23)
  allows public-key/attestation-only verification, which both FIDO2 and
  PIV candidates support; confirmed feasible in Wave 5's own spike, not
  assumed here.
- Signer/authority revocation: consumption-time lookup against the
  protected registry (HATP-REQ-088), never proof-creation-time-only.
- Rotation: deterministic old-key/new-key transition, admin-only,
  no ambiguous "latest key" filesystem selection (explicit prohibition
  carried forward, HATP-REQ-086).
- **Time handling:** timezone-aware UTC throughout; `issued_at` parsing
  reuses `rollback_approval_evidence.py::_parse_iso_timestamp` exactly
  (§5.13 above) to avoid reintroducing the Python 3.9 `fromisoformat`
  Z-suffix defect this project already hit once. `requires-python = ">=3.9"`
  is reconfirmed from `pyproject.toml` this phase — any new
  implementation MUST remain compatible with 3.9, not silently rely on
  3.11+ `fromisoformat` improvements.

## 40. RAE Integration Boundary (planned only, not implemented)

Future integration point, exact location:
`src/pcae/core/rollback_approval_evidence.py`'s
`resolve_rollback_approval_evidence()` (or a thin new wrapper it calls)
gains an **additional required input** — a resolved `HATPVerificationResult`
— and `derive_rollback_approval_present()`'s return value becomes
conditioned on `HATPVerificationResult == VALID` **in addition to** every
existing RAE-001 condition (RAE-REQ-038 (a)-(i), unchanged). No RAE-001
field, requirement, or enum is modified. This is a **new required AND
term**, not a replacement of any existing RAE-001 logic.

## 41-42. Permission Broker Boundary Preservation

Permission Broker (`permission_broker.py`, `permission_broker_foundation.py`)
remains unaware of signing/provider/attestation details — confirmed via
this phase's grep (§5.9) that neither file imports any such module today,
and no wave in this plan introduces such an import. Permission Broker
continues to receive only the truthful `approval_present` boolean through
existing RAE/mutation permission layering (POL-004's existing
interpretation, HATP-REQ-102, unchanged).

## 43. B-149O-1..4 Closure Mapping

| Finding | Closure requires | Mapped wave |
|---|---|---|
| B-149O-1 (fake CHGR + fake receipt) | No valid hardware-backed HATP proof can be forged | Wave 4 (verifier) + Wave 6 (RAE integration makes this load-bearing in production) |
| B-149O-2 (real Decision + fake Binding + fake registration) | Binding digest covered by a valid HATP proof | Wave 3 (`binding_digest` in canonical payload) + Wave 6 |
| B-149O-3 (fully handcrafted artifact chain) | Same mechanism as B-149O-1 | Wave 4 + Wave 6 |
| B-149O-4 (fresh attacker key) | Attacker key mechanically absent from protected registry; verifier enforces `UNAUTHORIZED_SIGNER` | Wave 2 (registry) + Wave 4 (verifier) + Wave 7 (independent adversarial re-verification) |

None of B-149O-1..4 is closed by this phase. All four remain **OPEN**.
Closure requires implementation through at least Wave 6, plus Wave 7's
independent verification — this plan only maps the path, per HATP-REQ-106.

## 44. Twenty-Attack Implementation Mapping

| # | Attack | Expected outcome | Implementation wave | Verification wave |
|---|---|---|---|---|
| 1 | Handcrafted RAE chain, no HATP proof | invalid | Wave 6 (gate exists) | Wave 7 |
| 2 | Fake HATP signature/proof | invalid | Wave 4 | Wave 4/7 |
| 3 | Attacker-selected public key as signer | `UNKNOWN_SIGNER` | Wave 4 (registry lookup) | Wave 4/7 |
| 4 | Unenrolled genuine hardware key | `UNAUTHORIZED_SIGNER` | Wave 2 + Wave 4 | Wave 4/7 |
| 5 | Valid attestation, unauthorized principal | invalid | Wave 4 | Wave 4/7 |
| 6 | Genuine signer invoked without touch | `USER_PRESENCE_NOT_PROVEN` | Wave 5 (provider enforcement) | Wave 5/7 (may require hardware-in-loop test) |
| 7 | Agent self-enrollment attempt | denied by OS boundary | Wave 2 (no agent-writable enroll path) | Wave 7 (deployment-level) |
| 8 | Agent verifier-key-replacement attempt | denied by OS boundary | Wave 2 | Wave 7 |
| 9 | Trust-store deletion/replacement attempt | denied by OS boundary | Wave 2 | Wave 7 |
| 10 | Env/CLI trust-root redirection attempt | rejected | Wave 2 (no override flag/env var honored) | Wave 4 |
| 11 | Valid proof copied to another operation | `WRONG_OPERATION` | Wave 3/4 | Wave 4/7 |
| 12 | Valid proof copied to another repository | `WRONG_REPOSITORY` | Wave 3/4 | Wave 4/7 |
| 13 | Repository ID copied to unauthorized deployment | `WRONG_DEPLOYMENT` | Wave 1/2/4 | Wave 4/7 |
| 14 | Entire repository copied to another deployment | HATP unavailable for the copy | Wave 1/2/4 | Wave 4/7 |
| 15 | Decision modified after proof creation | invalid | Wave 3/4 (digest check) | Wave 4/7 |
| 16 | Binding modified after proof creation | invalid | Wave 3/4 (digest check) | Wave 4/7 |
| 17 | Signer revoked | `REVOKED_SIGNER` | Wave 2/4 | Wave 4/7 |
| 18 | Authority revoked | invalid | Wave 2/4 | Wave 4/7 |
| 19 | Future-dated proof | `EXPIRED` | Wave 4 | Wave 4/7 |
| 20 | Valid authorized human touch, enrolled repo/operation | `VALID` | Wave 4/5 | Wave 5/7 (positive canonical control, §33 below) |

## 45. Implementation Wave Design

Explicit waves, refined from dependency-graph analysis (§6), not forced
into a single monolithic phase:

### Wave 1 — Repository Identity + Readiness Primitives

- **Files/modules:** `src/pcae/core/repository_identity.py` (new),
  `pcae init` integration (`src/pcae/commands/init.py`,
  `src/pcae/core/templates.py`), `.pcae/.gitignore` addition.
- **Requirements implemented:** HATP-REQ-046..051, HATP-REQ-107 (A);
  contributes scaffolding for HATP-REQ-013.
- **Tests:** repository-identity test matrix (§46 below): create/
  idempotency/malformed/missing/mutation/clone/copy/worktree/move/
  unknown-ID/same-ID-wrong-deployment.
- **Activation state:** no HATP trust activation; `repository_id` confers
  no authority by construction — nothing to gate yet.
- **Rollback/recovery:** deleting the identity file is a safe, fully
  recoverable operation (re-generates on next init); no data-loss risk
  since the field is non-authoritative.
- **Stop conditions:** if worktree-relative `.pcae` placement cannot
  cleanly support per-worktree distinct identity without deeper
  refactoring, STOP and resolve before proceeding to Wave 2.

### Wave 2 — Protected Trust-Store / Authority Registry (Read-Only Verification Substrate)

- **Files/modules:** `src/pcae/core/hatp_bootstrap.py` (new) —
  `HATPTrustStore`, `DeploymentBinding`, `PrincipalRecord`, `SignerRecord`,
  `AuthorityRecord`, permission/ownership verification helpers, canonical-
  root resolution (reusing `schema_runtime/loader.py` pattern, §17).
- **Requirements implemented:** HATP-REQ-006 (registry-side terms),
  HATP-REQ-030..035, HATP-REQ-036..042, HATP-REQ-043..045,
  HATP-REQ-052..066, HATP-REQ-086..089.
- **Tests:** trust-store test matrix (§47 below).
- **Activation state:** still no production trust activation — this wave
  only builds the read-only registry interface and its adversarial-
  resistant storage properties; there is no verifier yet to consume it in
  production.
- **Rollback/recovery:** admin-surface mutation is atomic (temp-file +
  `os.replace`, §5.2); a corrupt/missing store fails closed (verification
  unavailable), never crashes ordinary agent operation.
- **Stop conditions:** if OS-permission verification cannot be
  implemented without requiring actual OS user/group provisioning in the
  test suite itself, STOP and use simulated/temp-filesystem fixtures
  instead (per governing-prompt item 104/119) rather than silently
  weakening the check.

### Wave 3 — Proof Model / Schema / Canonical Serialization / Test Provider

- **Files/modules:** `src/pcae/core/human_approval_trusted_provenance.py`
  (new, proof dataclasses + `proof_version=1`), new
  `schema_resources/human_approval_trusted_provenance/records/human_approval_provenance_proof.schema.json`
  (loaded via existing `schema_runtime.loader`), canonical serializer
  (mirroring `cltr/canonicalization.py`), `src/pcae/core/hatp_providers.py`
  (new, includes the deterministic test provider `K`).
- **Requirements implemented:** HATP-REQ-067..077, HATP-REQ-117 (G/H);
  HATP-REQ-022 (K, test-provider containment).
- **Tests:** proof-schema test matrix (§48), canonical-serialization test
  matrix (§49), F1 closed-schema hardening test (rejects unknown field).
- **Activation state:** still no production trust activation — proof
  objects can be constructed and serialized, but no verifier exists to
  make them meaningful yet; test provider explicitly cannot satisfy a
  production provider profile (HATP-REQ-022, enforced structurally: no
  code path lets `hatp_providers.TestProvider` register as
  `HATP_HARDWARE_PROVIDER_V1`-accepted in production configuration).
- **Rollback/recovery:** schema/model changes at this stage are pre-
  production; no live data depends on them yet.
- **Stop conditions:** if the closed-schema (`additionalProperties: false`)
  decision (F1) cannot be expressed cleanly against the chosen schema/
  model validation library without contradicting `jsonschema`'s existing
  usage conventions in this repo, STOP and resolve the schema-strictness
  mechanism before Wave 4.

### Wave 4 — Verification Engine + Adversarial Tests

- **Files/modules:** `verify_hatp_proof()` in
  `human_approval_trusted_provenance.py`; consumes `HATPTrustStore`
  (read-only) and the Wave 3 proof model.
- **Requirements implemented:** HATP-REQ-010..011, HATP-REQ-077..085,
  HATP-REQ-094; closes most of the 20-attack matrix's non-hardware-
  dependent rows (§44).
- **Tests:** full verification-order test matrix, replay-prevention test
  matrix (§50), attack-matrix reproduction (attacks #1-5, 7-19 from §44 —
  everything except the hardware-presence-dependent #6/#20).
- **Activation state:** verifier exists and is independently testable
  against the test provider (K) and simulated trust-store fixtures — but
  **production activation remains gated** (§9 below); this wave does not
  wire the verifier into RAE/PB.
- **Rollback/recovery:** pure function (`verify_hatp_proof`) — no
  persistent state mutation, trivially "rolled back" by not calling it.
- **Stop conditions:** per governing-prompt item 172, before this wave is
  considered complete, independently verify: partial substrate cannot
  validate a production proof; unsafe same-user deployment cannot
  validate a proof; test provider cannot activate production trust;
  unprotected registry cannot activate trust. Any failure here is
  Blocking for proceeding to Wave 5/6.

### Wave 5 — Real Hardware Provider / Human Approval Surface

- **Files/modules:** `hatp_providers.py` gains a real provider adapter
  (FIDO2 primary, PIV fallback per §23); a human-side approval CLI
  surface (namespace TBD, §29-32).
- **Requirements implemented:** HATP-REQ-016..025 (F, E) at the concrete-
  implementation level; HATP-REQ-076.
- **Tests:** provider-abstraction test matrix (§51), human-presence test
  matrix (§53), attestation test matrix (§54); attack #6/#20 (hardware-
  dependent) — explicitly classified as integration/hardware-required,
  not Fast Green (§57 below).
- **Activation state:** a real provider now exists and can be
  independently verified, but production RAE/PB integration (Wave 6) has
  not yet occurred — HATP validity is meaningful in isolation but not yet
  consumed anywhere that changes `approval_present`.
- **Rollback/recovery:** provider adapter failures fail closed
  (`UNAVAILABLE`); no mutation risk.
- **Stop conditions:** if the FIDO2 spike (§23) cannot bind HATP's exact
  canonical payload as the signed challenge, switch to the PIV fallback
  strategy before continuing; if **neither** can satisfy
  `HATP_HARDWARE_PROVIDER_V1`'s exact signing requirement (HATP-REQ-020),
  STOP entirely and recommend a dedicated provider-selection-repair phase
  rather than forcing an implementation that overclaims compliance.

### Wave 6 — RAE Integration

- **Files/modules:** `src/pcae/core/rollback_approval_evidence.py`
  (extended, not replaced, per §40 above).
- **Requirements implemented:** HATP-REQ-095..096, HATP-REQ-101..104.
- **Tests:** RAE/HATP AND-conjunction test matrix; B-149O-1/2/3
  reproduction against the now-integrated pipeline.
- **Activation state:** `approval_present` derivation now conditions on
  both RAE-001's own pass **and** a `VALID` HATP result — but this remains
  gated by Wave 4's activation-conjunction discipline (§9): if Wave 7's
  Class-B deployment isn't provisioned, HATP still returns
  `UNSAFE_CONFIGURATION`/unavailable, so `approval_present` still cannot
  become `True` in this repository's current deployment even after this
  wave lands.
- **Rollback/recovery:** this is the first wave touching a currently-
  production-consumed function (`derive_rollback_approval_present`) —
  requires its own dedicated regression suite proving no existing RAE-only
  behavior changes when HATP is unavailable (the common case today).
- **Stop conditions:** if any transitional state during this wave could
  cause `approval_present=True` without a genuinely `VALID` HATP proof,
  STOP — this is the single most safety-critical wave in the entire plan.

### Wave 7 — Independent Verification + Class-B Deployment Provisioning

- **Scope:** dedicated deployment-provisioning phase (OS principal
  creation, ACL/permission configuration) — explicitly **not** ordinary
  repository source-code work (§39 of the governing prompt); independent
  adversarial re-verification of every wave above, full B-149O reopening
  and re-attempt, hardware-in-the-loop tests for attacks #6/#20.
- **Requirements implemented:** closes the remaining OS-boundary-
  dependent requirements (HATP-REQ-026..029) at the *deployment* level
  (they were already satisfied at the *design* level by Wave 2).
- **Tests:** full mandatory-attack-matrix re-run (all 20), B-149O-1..4
  closure attempt, self-enrollment/verifier-replacement deployment-level
  tests (governing-prompt items 113-114).
- **Activation state:** this is the **only** wave after which
  `HATP_TRUSTED_OPERATIONAL` (§9 below) can become achievable in a real
  deployment.
- **Stop conditions:** if Class-B provisioning cannot be mechanically
  distinguished from an unsafe same-user deployment by the readiness
  check, this is a **Blocking planning defect** per the governing prompt's
  own stop-condition list (§160 item) — must be resolved before any
  production activation claim.

## 46-57. Test Matrices (Summary Index)

Full matrices are enumerated per the governing prompt's own item list
(§103-119); this plan reproduces them as **planned test suites**, one per
wave, without pre-writing test code (that is implementation work, out of
scope for a planning phase):

- §46 Repository Identity: create, init-idempotency, malformed, missing,
  mutation, clone, copy, worktree, move, unknown-ID, same-ID-wrong-
  deployment. (Wave 1)
- §47 Bootstrap Store: agent-readable, agent-unwritable, unsafe
  permissions, parent-writable, symlink-replacement, wrong-owner, missing
  store, corrupt store, unknown signer, revoked signer, wrong repo, wrong
  deployment. (Wave 2, simulated/temp-fixture-based per item 104/119 —
  no real OS-account provisioning inside the test suite.)
- §48 Proof Schema: all required fields, unknown-field rejection, missing
  field, wrong version, wrong operation discriminator, wrong timestamp,
  malformed signature, attacker-selected public key, field mutation after
  signing. (Wave 3)
- §49 Canonical Serialization: semantic-equivalent-serialization attacks
  (key reordering, whitespace variants, numeric representation variants).
  (Wave 3)
- §50 Replay: same operation, different AG3 job, different commit,
  different AG5 PER, different ECP, different family, different repo ID,
  same ID wrong deployment. (Wave 4)
- §51 Human Presence: presence-satisfied, presence-absent, without making
  production caller-controlled. (Wave 5, test-provider-based for the
  non-hardware part.)
- §52 Attestation: accepted provider, unknown provider, invalid
  attestation, attacker-selected attestation root. (Wave 5)
- §53 Authorization: known-authorized, known-unauthorized, unknown
  signer, revoked signer, principal-scope mismatch, repository-scope
  mismatch, deployment mismatch. (Wave 4)
- §54 B-149O Reproduction: the original 149O exploit suite rerun
  unchanged wherever feasible, never "fixed" to fit the implementation.
  (Wave 6/7)
- §55 Legitimate Interface Abuse: agent supplies exact payload, calls
  legitimate production signer interface, no physical presence -> cannot
  obtain valid proof. May require provider-level integration/manual
  hardware test. (Wave 5/7)
- §56 Self Enrollment / Verifier Replacement (deployment-level): agent OS
  principal cannot mutate protected HATP registry; cannot replace
  verifier. (Wave 7)
- §57 Positive Canonical Control: a real enrolled authorized human
  reviews the exact operation, touches hardware, proof valid — MUST
  eventually succeed; this plan explicitly does not build a system that
  only rejects (governing-prompt item 115).

## 58. Fast Green Policy / Hardware Test Classification

HATP unit tests join Fast Green only if deterministic, hardware-
independent, and environment-independent (Waves 1-4, most of Wave 6).
Hardware-required tests (parts of Wave 5, attacks #6/#20, §57's positive
control) receive a separate marker/classification and are explicitly
**not** required for Fast Green — mirroring this repository's existing
`fast_green` marker discipline (`pyproject.toml` line 60). Deployment-
required tests (Wave 7's OS-provisioning verification) are their own
separate classification again, never silently folded into unit tests
that would otherwise require real OS-account provisioning inside the
ordinary test run (per governing-prompt item 119).

## 59. Dependency / Packaging Tests

If Wave 5 adds a provider dependency, that wave's own scope MUST include
a package-build/import test (import succeeds, no version-pin conflict
with the existing `jsonschema>=4.18,<5` constraint) — remembering this
project's own prior CHGR/TAM environment-failure incidents as the reason
this check is explicitly required, not assumed safe by default.

## 60. Security Boundary Tests Should Not Depend on Root Privileges

All Wave 2/Wave 7 permission/ownership tests use simulation, mocking, or
temp-filesystem fixtures for logic verification (per §47 above); actual
OS-account/ACL separation is verified only in Wave 7's dedicated
deployment-verification procedure, never inside the ordinary `pytest`
run.

## 61. Implementation Diff Budget (per wave)

| Wave | MUST_CHANGE | MAY_CHANGE | MUST_NOT_CHANGE |
|---|---|---|---|
| 1 | `repository_identity.py`, `init.py`/`templates.py`, `.pcae/.gitignore` | — | `docs/contracts/**`, `rollback_approval_evidence.py`, `permission_broker*.py` |
| 2 | `hatp_bootstrap.py` | `writer.py` (only if a shared atomic-write helper is extracted) | `docs/contracts/**`, RAE, PB |
| 3 | `human_approval_trusted_provenance.py`, `hatp_providers.py` (test provider only), `schema_resources/human_approval_trusted_provenance/**` | `schema_runtime/*` (only if a genuine, narrowly-scoped loader gap is found) | `docs/contracts/**`, RAE, PB, CHGR schemas |
| 4 | `human_approval_trusted_provenance.py` (verifier) | — | `docs/contracts/**`, RAE, PB |
| 5 | `hatp_providers.py` (real adapter), new admin/approval CLI module, `pyproject.toml` (new dependency) | — | `docs/contracts/**`, RAE, PB, existing CLI commands |
| 6 | `rollback_approval_evidence.py` (extended) | — | `docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md`, `docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md`, PB |
| 7 | deployment configuration (outside repo source), test suites | — | any contract text |

**No unrelated hunks** in any wave — this table is the enforcement
mechanism for that rule in future implementation phases.

## 62-70. Boundary Rules (Contract, RAE, Permission Broker, Dependency Direction, Sub-boundaries)

- **HATP contract boundary:** `docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md`
  MUST NOT change during implementation unless a true contract defect is
  demonstrated (none is, this phase).
- **RAE contract boundary:** `docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md`
  MUST NOT change.
- **Permission Broker boundary:** no provider/hardware/signing imports in
  `permission_broker_foundation.py`/`permission_broker.py`, ever.
- **Dependency direction:** RAE -> HATP verification API is allowed;
  HATP -> RAE authority internals is forbidden, unless a future contract
  architecture explicitly requires a shared model (none is planned).
- **HATP/Permission Broker boundary:** HATP must not import or invoke
  Permission Broker.
- **HATP/Agent boundary:** core verifier does not import agent-mutation-
  execution modules (`shell_gate`, `backend_invocations`, etc.).
- **HATP/TAM boundary:** no illegal `human_authorization` composition
  (HATP's dataclasses are independent types, structurally inspired only).
- **HATP/IWC boundary:** no confirmation-as-approval conversion anywhere
  in the design.
- **HATP/AESIC boundary:** no disclosure-as-authority conversion anywhere
  in the design.

## 71-72. Administrative Surface / Human Approval Surface Naming

Deferred: whether admin commands live under a `pcae hatp ...` namespace
or another governance namespace, and whether the human-approval action is
`pcae approval review <request>` or a different name, are **not** decided
by this plan — both require concrete interaction-design work best done
alongside Wave 5/7's actual CLI implementation, not guessed at now. This
plan only fixes that such surfaces are architecturally separate from the
autonomous agent's normal command path (§14, §29-32 above).

## 73. Autonomous Agent Surface (recap)

The agent may only: request approval (submit a request artifact),
inspect status (read-only trust-store queries), and retry an operation
later. It has no enrollment or approval-generation authority anywhere in
this design — enforced structurally (no such method is exposed on any
production-reachable interface in §13's `HATPTrustStore` or §21's
provider interface).

## 74. Request/Proof Discovery

Deterministic file/store discovery only (no scanning of arbitrary
directories where an attacker could plant a poisoning file) — reusing the
directory-injection lessons already applied in RAE's own storage design
(`rollback_approval_evidence.py`'s fixed, non-globbing storage layout).

## 75-76. Atomic Persistence / Crash Consistency

All new persistent writes (repository identity, approval request if any,
HATP proof, protected admin enrollment) use the atomic temp-file +
`os.replace` pattern already standard in this codebase (§5.2). Crash-
consistency reasoning: a crash between proof creation and proof
persistence leaves no proof on disk (safe — treated as if creation never
happened, `MISSING`); a crash between proof persistence and RAE
consumption leaves a valid, at-rest proof that a retry can still consume
correctly (idempotent read, no partial-trust state possible because
`approval_present` is derived fresh on each RAE resolution call, never
cached across a crash boundary).

## 77. Protected Registry Atomicity

Admin mutation of the protected trust registry uses the same atomic-
replacement pattern under the protected parent directory — never a
partial in-place edit.

## 78. Audit Trail

Optional audit records for enrollment/revocation/approval MAY be added in
Wave 2/5/7; audit is explicitly **not** a root of trust — implementation
MUST NOT make proof/authority validity depend on the audit trail's own
presence or completeness.

## 79-80. Secret Material / Sensitive Logging

Private hardware key material never enters PCAE process/file state, per
the selected provider's own non-exportable-key property (§23). PINs,
hardware secrets, private key material, and authentication secrets are
never logged; the public proof/public key MAY be logged per the existing
project logging policy (no change to that policy is proposed).

## 81-84. PIN / Human Presence vs. PIN / Provider UX / Hardware Absence

A PIN alone (if the selected provider requires one in addition to touch)
is not sufficient authorization by itself — fresh hardware user presence
remains separately required; PIN entry, if any, is handled by the
provider's own secure input path, never as a CLI argument or environment
variable reachable by the agent (this may itself influence the final
Wave 5 provider choice, per governing-prompt item 140). Provider UX
(clear touch-request messaging) and hardware-absence error clarity are
Wave 5 UX-design details, not architecture-blocking.

## 85. Provider Replacement Prevention

The agent cannot switch to a weaker provider profile — the trusted
provider profile is sourced from protected configuration (C), never from
an agent-suppliable runtime parameter.

## 86-87. Algorithm Selection / Crypto Library

No concrete signature algorithm is selected by this plan; it is deferred
to Wave 5, contingent on the real-provider spike (§23). Any crypto
library requirement is justified at that point against "why standard
library insufficient," exact API surface needed, and licensing/supply-
chain impact — none of that analysis is performed prematurely here
because it depends on the Wave 5 spike's actual outcome.

## 88. Canonical Digest Algorithm / 89. Proof ID

SHA-256 is used for canonical digests, matching existing project
convention (`cltr/canonicalization.py`, `rollback_approval_evidence.py`'s
own `_compute_content_digest`) — no new hashing convention is introduced.
No explicit standalone `proof_id` field is added beyond the signed
content itself unless a concrete implementation-time need is
demonstrated (avoiding an unnecessary field per governing-prompt item
148); `evidence_id`-style identity is already carried by the RAE Binding
reference the proof itself points to.

## 90. Approval Decision Semantics / 91. `approval_present` Final Derivation / 92-93. RAE Sidecars / Redundant Checks

HATP proves provenance for both `approve_rollback` and `deny_rollback`
Decisions (never bakes `approved=True` into itself, HATP-REQ-149 concept
mirrored from RAE's own Decision-semantics ownership). Final
`approval_present=True` derivation (Wave 6) requires: Decision =
`approve_rollback`, HATP proof `VALID`, RAE Binding valid, RAE TTL valid,
RAE revocation/supersession valid, and every other existing RAE
condition — an AND-conjunction, never a substitution. Existing RAE
sidecars (publication receipt, Binding creation registration) are **not**
removed during HATP implementation; some current RAE canonicality checks
MAY become partially redundant after HATP lands, but this plan explicitly
keeps defense-in-depth for the first implementation (simplification is
deferred to a later, separate hardening phase, per governing-prompt item
153).

## 94. Migration of Existing RAE Evidence / 95. Deployment Migration / 96. Sequence / 97-99. Deployment Provisioning

Existing pre-HATP RAE evidence does **not** become retroactively trusted
— no HATP proof synthesis is back-filled for old evidence. The current
same-user development environment cannot enable HATP; a separate
governed deployment-provisioning phase (Wave 7) precedes any production
activation claim. Likely sequence (software substrate -> independent
software verification -> Class-B deployment provisioning -> hardware
provider integration -> hardware/deployment verification -> RAE
integration) is refined here into the concrete Wave 1-7 sequence above,
placing RAE integration (Wave 6) **before** full Class-B provisioning
(Wave 7) is completed, because Wave 6's own activation-gate discipline
(§9) already prevents `approval_present=True` in an unprovisioned
deployment — this ordering was chosen deliberately so RAE integration
can be independently verified against a controlled test-provider harness
before the higher-cost, harder-to-repeat OS-provisioning work, rather
than blocking all software integration work on deployment logistics.
Deployment provisioning (OS user/ACL creation) is explicitly not ordinary
repository source-code mutation and is scoped to its own future governed
phase, never hidden inside a source-implementation phase's diff.

## 9. Activation Dependency (top-level gate)

```
HATP_TRUSTED_OPERATIONAL := 
    repository_identity_valid
    AND protected_deployment_enrollment_valid
    AND class_b_bootstrap_environment_safe
    AND trusted_approver_mapping_valid
    AND provider_profile_available
    AND provider_attestation_trusted
    AND proof_verifier_available
```

(Exact naming/constant location decided in Wave 4's implementation; this
is the conceptual conjunction, per governing-prompt item 6.) No individual
substrate (repository identity alone, trust-store alone, provider alone)
may cause production HATP evidence to become trusted before this full
conjunction succeeds — this is the single load-bearing invariant of the
entire plan (governing-prompt item 7), re-verified at the end of every
wave in §45 above and again independently at Wave 7.

## Readiness vs. Proof Validity (environment states)

Three environment states: `READY`, `UNAVAILABLE`, `UNSAFE_CONFIGURATION`
(or contract-equivalent naming, finalized in Wave 4). Proof verification
never masks an unsafe environment — an otherwise-`VALID`-looking proof
evaluated in an `UNSAFE_CONFIGURATION`/`UNAVAILABLE` environment still
yields a non-`VALID` overall result (§39 above).

## Stop Conditions (consolidated)

A future implementation wave must STOP if: a contract requirement cannot
be implemented without semantic change; the real provider cannot enforce
fresh human presence; the chosen provider cannot bind the exact
operation; bootstrap state cannot be protected from the agent; repository
identity/worktree semantics cannot be implemented safely; production
trust would require a caller-controlled boolean/path/key; the test
provider could leak into production selection; OS readiness cannot fail
closed; a new dependency materially changes architecture beyond this
plan; or if Class-B readiness cannot be mechanically distinguished from
an unsafe same-user deployment (Blocking planning defect). If production
could ever trust the test provider, if repository ID alone could confer
authority, or if a partial implementation wave could cause production
`approval_present=True` — each is Blocking and halts the affected wave
immediately. If HATP-001 semantic change is required, STOP and recommend
contract repair, never code around it.

## Implementation Readiness Verdict

```
HATP-001 IMPLEMENTATION PLAN COMPLETE
— READY FOR BOUNDED IMPLEMENTATION
```

All 117 requirements map cleanly (§2, §4.2); a safe seven-wave
implementation sequence exists, derived from the actual dependency graph
(§6) and source-architecture survey (§5), not assumed; the one materially
unresolved design choice (real hardware provider protocol, §23) is
resolved to a concrete primary strategy (FIDO2) with an explicit,
concretely-triggered fallback (PIV) and an explicit Wave-5 verification
spike rather than being left as "TBD, decide later"; the current Python
support range (`>=3.9`) is compatible with the planned timestamp-handling
approach (reusing the existing fail-closed `_parse_iso_timestamp`, §5.13)
and imposes no known conflict with either candidate crypto/FIDO library
at the architecture level (concrete dependency compatibility is a Wave-5
verification step, not assumed here); Class-B readiness is mechanically
distinguishable from an unsafe same-user deployment by design (the
readiness gate explicitly checks OS-principal-separation facts, not
merely "a config flag says so"); no partial implementation wave can cause
production `approval_present=True` (§9's activation conjunction plus
Wave 6's explicit stop condition); the test provider structurally cannot
activate production trust (§20, K); repository ID alone cannot confer
authority (§18, Layer 1/Layer 2 separation, reused unmodified from
149O.1B.2).

## Recommended Next Phase

```
149O.1E — HATP Repository Identity + Trust-Store Foundation Implementation
(Wave 1 + Wave 2 of this plan)
```

Rationale for selecting this as the first bounded implementation phase,
not "implement HATP" and not a giant single wave: Wave 1 (repository
identity) and Wave 2 (protected trust store / registry) are the two
waves with (a) no dependency on an unresolved external choice (unlike
Wave 5's provider spike), (b) no risk of touching a currently-production-
consumed code path (unlike Wave 6), and (c) the deepest existing source-
architecture reuse available (§5) — meaning they can be implemented and
independently verified with the least new, untested machinery, while
producing the durable substrate every later wave depends on (§6's
dependency graph places both at the base of the chain). Following §95 of
the governing prompt, this is the safest first wave the dependency
analysis actually supports, not a default "start at the top" choice.
Waves 3 (proof/schema/test-provider) and 4 (verifier) remain safe
candidates for a **subsequent** implementation phase once 149O.1E's
independent verification confirms the foundation holds; Wave 5 (real
provider) is explicitly not attempted until the provider-agnostic core
(Waves 1-4) is independently verified against the test provider, per
§96-97 of the governing prompt.

## Governance Finalization

Prepared as part of this phase's own governed close-out (not embedded
further in this document): `.pcae/phase-completion-report.md` and
`.pcae/phase-completion-metadata.json`, bound to `149O.1D`, canonical
title "Human Approval Trusted Provenance Implementation Plan."
