# HATP Class-B Deployment Contract

## Contract identity and status

**Contract:** HBDC-001
**Version:** 1.0
**Status:** FROZEN — PENDING INDEPENDENT VERIFICATION
**Frozen by:** Phase 149O.20B — HATP Class-B Deployment Contract Freeze
**Depends on:** HATP-001 v1.0 (unamended), HMIC-001 v1.1 (unamended), HMRC-001 v1.0 (unamended)
**Architecture basis:** `docs/PHASE_149O_20A_HATP_DEPLOYMENT_READINESS_ARCHITECTURE.md` (Decision Records §13, §14, §78, §79, §80; requirement inventory §84 DRA-REQ-001..003; stop conditions §86 DRA-S1..S9); `docs/PHASE_149O_1B_1_HUMAN_APPROVAL_BOOTSTRAP_AUTHORITY_ARCHITECTURE.md` (two-OS-principal topology, unmodified); `docs/PHASE_149O_1B_2_CANONICAL_REPOSITORY_IDENTITY_ARCHITECTURE.md` (CRI Model A, worktree/clone/migration scope).

This is a contract-freeze document. It freezes normative, testable requirements. It is not an implementation, does not create real protected state, and does not authorize real provisioning, certification, or activation.

---

## 0. Normative Language

The key words "SHALL", "SHALL NOT", "MUST", "MUST NOT", "MAY", and "SHOULD" are to be interpreted per RFC 2119 conventions used throughout this repository's other bound contracts. Every normative sentence in this contract carries a unique requirement ID, `HBDC-REQ-###`, sequential from 001, no gaps, no duplicates (verified mechanically — see §21). Security invariants carry a separate `CBD-#` label (§19). Requirement IDs are stable across future amendments; a superseded requirement is marked superseded, not renumbered or deleted.

## 1. Purpose

This contract answers, in testable terms, the question posed by Phase 149O.20B's charter: *when may a deployment legitimately claim that the Class-B trust topology required by HATP has been established?* It makes DRA-REQ-001 (OS-principal separation), DRA-REQ-002 (Protected Root ownership/permissions), and DRA-REQ-003 (agent Python execution-environment lock) — all three named in `docs/PHASE_149O_20A_HATP_DEPLOYMENT_READINESS_ARCHITECTURE.md` §84 — into concrete, filesystem-testable, process-testable normative requirements a future independent verification phase can check against a real, provisioned host.

## 2. Scope and Relationship to Other Contracts

HBDC-001 governs **deployment topology and environment configuration** for a Class-B PCAE deployment under Model A (editable install from the canonical repository working tree, per HMIC-REQ-064). It does not redefine:

- HATP-001's proof-production, human-presence, or hardware-attestation model;
- HMIC-001's certification data model, storage format, or validation algorithm;
- HMRC-001's Cutover Mode state machine;
- HSCE-001's evidence-store write model.

HBDC-001 is a **prerequisite-topology contract**: it defines what "Class-B established" concretely means so that those other contracts' own certification/activation gates can be trusted to mean what they claim. §17 explicitly addresses whether HBDC-001 itself must become one of HMIC-001's bound contracts; as of v1.0 it does not (see HBDC-REQ-047..049).

## 3. Terminology

- **Agent OS principal** — the distinct OS account (`PCAE_AGENT_PRINCIPAL` per 149O.1B.1 §4) under which the autonomous PCAE agent/runtime executes.
- **Admin OS principal** — the distinct OS account (`PCAE_BOOTSTRAP_ADMIN_PRINCIPAL`) combining human-approver and bootstrap-administrator roles for v1, per HATP-001 §13/HATP-REQ-028/029.
- **Protected Root** — `HATPTrustStore.production().root`, resolved by `hatp_bootstrap._default_production_trust_root()` from a fixed, platform-specific path (macOS: `/Library/Application Support/PCAE/HATP/trust-store`; Linux: `/etc/pcae/hatp/trust-store`).
- **Authority-bearing state** — any content whose write access confers or records protected authority: Protected Root content, HMIC `CertificationRecord`/`CertificationBinding`/revocation records, `DeploymentBinding` records, the hardware-credential registry, and the Cutover Record / `CutoverActivationMarker`.
- **Canonical deployment root** — `resolve_canonical_deployment_root()`'s output for the repository working tree bound in an active `DeploymentBinding`.
- **Environment lock** — the set of admin-controlled, agent-unwritable configuration governed by §13 (HBDC-REQ-025..039): interpreter, venv, `PYTHONPATH`, user-site, `.pth` files, `sitecustomize`/`usercustomize`, import hooks, launcher/wrapper configuration.

## 4. Threat Model

Inherited unmodified from `docs/PHASE_149O_20A_HATP_DEPLOYMENT_READINESS_ARCHITECTURE.md` §16's four threat classes: (1) a malicious or compromised agent attempting to write authority state directly; (2) a malicious or compromised agent attempting environment-shadowing (the class HMIC-REQ-063 names); (3) replay/reuse of certification or binding state across repositories, worktrees, clones, or hosts; (4) loss or compromise of a hardware signer. HBDC-001 concretizes the topology-level mitigations for classes 1, 2, and 3. Class 4 remains HATP-001's scope (§10 of this contract references it only for third-party hardware-dependency disposition; HBDC-001 does not redefine hardware-signer recovery).

## 5. Non-Goals

- HBDC-001 does not claim resistance to a fully compromised OS root/admin account (§18 root-compromise limit).
- HBDC-001 does not claim cryptographic executed-source / runtime-module-resolution attestation (§14).
- HBDC-001 does not replace or duplicate HATP-001's hardware-signer assurances (§4 above).
- HBDC-001 does not implement COMP-002, change Permission Broker behavior, or change POL-005.
- HBDC-001 does not authorize real provisioning, certification, or activation (§16).

## 6. DRA-REQ Traceability

| Architecture requirement (149O.20A) | HBDC-001 normative mapping |
|---|---|
| DRA-REQ-001 (agent/admin distinct OS accounts) | HBDC-REQ-001..005 (§7) |
| DRA-REQ-002 (Protected Root created only by admin, out-of-band) | HBDC-REQ-011..021 (§10–§11) |
| DRA-REQ-003 (agent Python import search path admin-provisioned, agent-unwritable) | HBDC-REQ-025..041 (§13–§14) |
| DRA-REQ-004 (agent-writable import search path forfeits READY claim) | HBDC-REQ-040 (§14) |
| DRA-REQ-006 (recertification on copy/clone/migrate/restore) | HBDC-REQ-043..046 (§16) |

No DRA-REQ ID is renumbered or reused as an HBDC-REQ ID (149O.20A §84 namespace discipline preserved).

## 7. Principal Model

- **HBDC-REQ-001.** Exactly two OS principals are required for a v1.0-compliant Model-A Class-B deployment: the agent principal and the admin principal. No third principal is required.
- **HBDC-REQ-002.** The agent principal and the admin principal SHALL be distinct OS accounts (distinct `uid`) on the deployment host. A deployment where both roles run under the same OS account is non-compliant, matching `hatp_bootstrap.inspect_bootstrap_environment`'s existing `"agent_and_admin_share_os_principal"` check.
- **HBDC-REQ-003.** If a future contract revision splits the combined bootstrap-admin/human-approver role (HATP-REQ-028's deferred three-principal split) into separate principals, this contract SHALL be revised accordingly; v1.0 does not anticipate or silently accommodate that split.
- **HBDC-REQ-004.** Admin authority SHALL NOT be inferred from environment variables, Python function or class names, repository file ownership, or Git commit identity/authorship. Admin authority is conferred solely by OS-level identity and Protected Root ownership (§10–§11).
- **HBDC-REQ-005.** The agent principal SHALL NOT possess any application-level, OS-level, or configuration-level mechanism to elevate itself to, or execute as, the admin principal.

## 8. Agent Principal Authority

- **HBDC-REQ-006.** The agent principal MAY read, execute, validate, and inspect Protected Root content and its own repository-local artifacts.
- **HBDC-REQ-007.** The agent principal SHALL NOT hold write permission — directly, via group membership, or via ACL — to: Protected Root or any path beneath it; HMIC `CertificationRecord`/`CertificationBinding` documents; revocation records; `DeploymentBinding` records / protected deployment identity; the Cutover Record or `CutoverActivationMarker`; the hardware-credential/signer-authorization registry; or environment-lock provisioning artifacts (§13).
- **HBDC-REQ-008.** The sole exception to HBDC-REQ-007 is repository-local artifacts that other bound contracts already designate agent-writable and explicitly non-authoritative — e.g. `.pcae/hatp-evidence/` (HSCE-001 §27, "not an authority root") and `.pcae/repository-identity.json` (HATP-001 §17, CRI Layer 1, "confers no authority alone"). HBDC-001 does not change that disposition.

## 9. Admin Principal Authority

- **HBDC-REQ-009.** The admin principal exclusively holds write authority to: Protected Root creation; HMIC certification records, the active-binding pointer, and revocation records; `DeploymentBinding` records; hardware-credential registry entries; Cutover Record transitions; and environment-lock provisioning (interpreter, venv, `PYTHONPATH` policy, site-packages, launcher configuration).
- **HBDC-REQ-010.** Admin write authority does not itself confer ordinary PCAE runtime execution authority. An admin who wishes to run PCAE as the agent does so by operating as the agent principal, not by exercising admin write privileges during ordinary runtime.

## 10. Protected Root — Definition and Resolution

- **HBDC-REQ-011.** Protected Root resolves solely through `HATPTrustStore.production()` → `_default_production_trust_root()`'s fixed, platform-keyed constant paths. No environment variable, CLI flag, constructor parameter, or repository-local file may override it in production code. (`HATPTrustStore.__init__`'s `_test_only_root` parameter exists structurally outside `.production()` and is not a production override path.)
- **HBDC-REQ-012.** No PCAE agent-invoked code path SHALL auto-create Protected Root (`mkdir` or equivalent). Creation is admin-exclusive and occurs out-of-band from any PCAE agent invocation.

## 11. Protected Root — Ownership, Permissions, and Path Safety

- **HBDC-REQ-013.** Protected Root SHALL be owned by the admin OS principal (`st_uid` matches the admin account).
- **HBDC-REQ-014.** Protected Root's mode SHALL NOT set the group-write or other-write bits (`mode & 0o022 == 0`), consistent with the check already implemented in `hatp_mandatory_cutover._assess_hatp_mandatory_activation_readiness_at_root`'s `protected_activation_authority_mechanism_available` step. Recommended concrete modes: `0750` for directories, `0640` for files, admin-owned, with a dedicated admin-controlled group used only for read-only traversal by the agent principal where the agent needs read access (e.g. to consult active certification state).
- **HBDC-REQ-015.** No group of which the agent principal is a member SHALL hold write permission on Protected Root or any path beneath it. Mode-bit inspection alone (HBDC-REQ-014) is insufficient; a future verifier MUST test **effective** group-derived write access, not declared mode bits alone.
- **HBDC-REQ-016.** No POSIX ACL, extended ACL, default ACL, or inherited ACL entry SHALL grant the agent principal write access to Protected Root or any descendant path, even where base mode bits would otherwise deny it.
- **HBDC-REQ-017.** Every ancestor directory of Protected Root, up to the point the agent principal has no write access at all, SHALL be non-agent-writable. Protected-child ownership is insufficient on its own: an agent that can write a writable parent directory can rename or replace the directory entry naming Protected Root even without write access to Protected Root's own bytes. This requirement closes that channel jointly with HBDC-REQ-013..016.
- **HBDC-REQ-018.** Protected Root, and no authority-bearing path beneath it, SHALL be — or be reachable through — an agent-controlled symlink. Any symlink encountered while resolving Protected Root or a protected path SHALL cause validation to fail closed, mirroring the `_reject_symlink` pattern already implemented independently in `hatp_bootstrap.py`, `hatp_mandatory_certification.py`, and `hatp_mandatory_cutover.py`.
- **HBDC-REQ-019.** Hard links to authority-bearing files SHALL NOT be created from any agent-writable directory. Only the admin principal, acting entirely within Protected Root, may hold additional hard-linked references to authority-bearing file content.
- **HBDC-REQ-020.** An implementation SHALL treat "the agent principal can delete or rename the directory entry naming an authority-bearing file, even without write access to that file's own bytes" as a compliance failure equivalent to a direct write. This is satisfied jointly by HBDC-REQ-017 (parent-path protection) and is not separately re-derivable from file-level mode bits alone.
- **HBDC-REQ-021.** Agent-side readiness and validation code SHALL fail closed — not auto-provision, not silently degrade to a partial check — if Protected Root is absent, malformed, or does not satisfy HBDC-REQ-013..018.

## 12. Model-A Deployment and Canonical Repository Root

- **HBDC-REQ-022.** HBDC-001 v1.0 authorizes exactly one deployment model: **Model A** — PCAE authority modules execute from the canonical repository working tree via editable install (`pip install -e .` / an equivalent venv pointed directly at the source tree), or an equivalent `PYTHONPATH`-free editable resolution from that tree, consistent with HMIC-REQ-064.
- **HBDC-REQ-023.** Future conformance evidence for Model-A deployment SHALL include: (a) the resolved `canonical_deployment_root` matches the `DeploymentBinding` record active for the repository (`hatp_bootstrap.deployment_binding_matches`); (b) the executing interpreter's editable-install metadata resolves PCAE package imports into that same working tree; (c) no channel governed by §13 (HBDC-REQ-025..039) redirects resolution elsewhere.
- **HBDC-REQ-024.** Models B (installed wheel / site-packages distribution), C (a dedicated immutable deployment tree), and D (any other model) are NOT authorized under HBDC-001 v1.0. Adopting any of them requires an explicit future contract revision naming that model, not a configuration toggle — mirroring HMIC-REQ-064's own discipline.

## 13. Agent Python Execution-Environment Lock (DRA-REQ-003)

This section is the concrete mitigation permitting a Model-A deployment to claim HMIC-REQ-063's accepted-residual branch. See §14 for the boundary statement.

- **HBDC-REQ-025.** The production agent Python execution environment — interpreter, venv, site-packages, and import configuration — SHALL be admin-provisioned. The agent principal SHALL NOT hold write permission to any component of it.
- **HBDC-REQ-026.** A production venv, if used, SHALL be owned and writable only by the admin principal. A developer/repo-local `.venv` writable by the agent principal is non-compliant for production Class-B deployment regardless of the source tree's own certification status.
- **HBDC-REQ-027.** The production Python executable resolved for PCAE agent invocation SHALL NOT be replaceable by the agent principal — neither the executable path itself nor any directory earlier in its resolution than an admin-controlled one may be agent-writable.
- **HBDC-REQ-028.** `PYTHONPATH` SHALL NOT be settable or influenceable by the agent principal for the process that executes certified, frozen-file authority code. Compliant designs: (a) unset entirely by admin-controlled launch configuration; (b) fixed by admin-controlled launch configuration and not agent-overridable; or (c) validated against an admin-defined allow-list before use, rejecting (not silently dropping) any unrecognized entry.
- **HBDC-REQ-029.** Python user-site (`site.ENABLE_USER_SITE`) SHALL be disabled for the production agent environment (e.g. `-s` / `PYTHONNOUSERSITE=1` in admin-controlled launch configuration), or, if enabled, the admin principal SHALL demonstrate the agent principal cannot write to the resolved user-site directory.
- **HBDC-REQ-030.** `sitecustomize.py` and `usercustomize.py`, wherever present on the resolved production `sys.path`, SHALL be admin-controlled and agent-unwritable, or absent.
- **HBDC-REQ-031.** Any `.pth` file present on the resolved production `sys.path` — including one capable of executing `import`-prefixed lines — SHALL be admin-controlled and agent-unwritable, or absent.
- **HBDC-REQ-032.** The agent principal SHALL NOT be able to install a `sys.meta_path` entry, or any other import-hook mechanism, that executes before or in place of certified PCAE authority modules, via any admin-controlled startup path reachable in production.
- **HBDC-REQ-033.** Changing the agent process's current working directory SHALL NOT cause import shadowing of certified PCAE authority modules. The resolved production `sys.path` SHALL NOT place an agent-writable, agent-selectable directory (including `sys.path[0]`/CWD) ahead of the canonical repository working tree's package location.
- **HBDC-REQ-034.** A fake or shadow `pcae` package or module placed by the agent principal earlier in the resolved import path SHALL NOT execute as authority. Compliance is achieved jointly by HBDC-REQ-028, 029, and 033 under Model A; v1.0 does not require an additional runtime self-check beyond those three (see §14).
- **HBDC-REQ-035.** Editable-install link metadata (`.pth` file, `direct_url.json`, egg-link, or the equivalent artifact used by the actual packaging tool) SHALL be admin-controlled and agent-unwritable in the production environment.
- **HBDC-REQ-036.** If PCAE production execution passes through a launcher, wrapper, or service-manager configuration, that configuration SHALL be admin-controlled and agent-unwritable to the extent it affects module resolution, working directory, or the environment variables governed by HBDC-REQ-028..033.
- **HBDC-REQ-037.** The agent principal's ordinary shell/service-launch environment SHALL NOT be able to inject import- or source-path-authority-changing environment variables into the process executing certified authority modules. This requirement does not ban all environment variables — only ones capable of affecting HBDC-REQ-022..035.
- **HBDC-REQ-038.** If authority derivation invokes a system Git executable (e.g. `derive_implementation_commit`'s `git rev-parse HEAD`), the resolved Git executable path SHALL NOT be replaceable by the agent principal; admin-controlled `PATH` configuration (or an admin-pinned absolute executable path) is required for the subprocess environment used by authority-bearing derivation code.
- **HBDC-REQ-039.** Third-party Python dependencies required by authority-bearing modules — including FIDO2/PIV hardware-provider libraries — are not HMIC-certified source under v1.0, but the agent principal SHALL NOT hold write permission allowing their replacement in the production environment. This is satisfied by HBDC-REQ-025..027's venv/site-packages lock; v1.0 does not require a separate dependency-pinning mechanism beyond that.

## 14. HMIC-REQ-063 Option-C Boundary

- **HBDC-REQ-040.** The environment-lock requirements of §13 (HBDC-REQ-025..039) are the concrete mitigation that permits a Model-A deployment to claim HMIC-REQ-063's accepted-residual-limitation branch (**OPTION C**, per 149O.20A §14/§78). A deployment that does not satisfy HBDC-REQ-025..039 falls into HMIC-REQ-063's BLOCKING branch and MUST NOT proceed to `HATP_MANDATORY` activation without first implementing an executed-source binding check (149O.20A §18's nine compared, unimplemented candidate designs remain the relevant future-work menu; none is selected by this contract).
- **HBDC-REQ-041.** Compliance with HBDC-REQ-025..039 SHALL NOT be represented as executed-code or runtime-module-resolution cryptographic attestation. It establishes admin-controlled, agent-unwritable **configuration** only. No claim beyond that is authorized by this contract, mirroring HMIC-REQ-063's own explicit, named limitation.

## 15. Deployment-Model Eligibility Summary

Per HBDC-REQ-022..024: Model A is the only deployment model HBDC-001 v1.0 authorizes. A deployment under any other model is not implicitly accepted by this contract, regardless of whether it otherwise satisfies §7–§11's principal/root requirements.

## 16. Repository/Deployment Identity, Worktrees, Clones, Host Migration, Backup/Restore

- **HBDC-REQ-042.** `repository_instance_id` (CRI Layer 1, repository-local and agent-writable per HATP-001 §17) confers no authority by itself. The controlling authority artifact is the admin-created `DeploymentBinding` (CRI Layer 2).
- **HBDC-REQ-043.** A distinct Git worktree of the same repository SHALL require its own `DeploymentBinding`/`canonical_deployment_root` and, if HMIC certification is claimed, its own certification. A worktree does not implicitly inherit another worktree's Class-B authority (149O.1B.2 worktree scope preserved unmodified).
- **HBDC-REQ-044.** A clone or copy of the repository SHALL require its own `DeploymentBinding` and certification under the same rule as HBDC-REQ-043. Copying protected-root-adjacent configuration files does not itself transfer Class-B compliance.
- **HBDC-REQ-045.** Migrating a deployment to a new host SHALL require a new `DeploymentBinding` and recertification. A certification issued for one `canonical_deployment_root`/host combination SHALL NOT be treated as valid on another.
- **HBDC-REQ-046.** Restoring a backup of protected state to a `canonical_deployment_root`/host different from the one it was created for SHALL NOT be treated as retaining Class-B authority. Only a byte-identical restore to the original path/host may be treated as still valid, and remains subject to the other bound contracts' own restore rules (this contract adds no exception to them).

## 17. HBDC Trust/Binding Disposition

This section resolves the question 149O.20A §67/§74 leaves open: does HBDC-001's own normative text need protected identity binding before it can gate real deployment claims?

**Selected disposition: Option A.** HBDC-001's normative text governs deployment claims, but as of v1.0 it is **not** one of HMIC-001's bound contracts — it is not present in `contract_versions`, and its bytes do not participate in the 24-file `implementation_scope_digest`.

- **HBDC-REQ-047.** HBDC-001's normative text is deployment-verification-governing but is not, as of v1.0, one of HMIC-001's bound contracts.
- **HBDC-REQ-048.** Before any deployment may be represented as satisfying HMIC-REQ-063's Option-C accepted-residual branch on the strength of this contract in a mechanically-gated way, HBDC-001 SHALL be added to HMIC-001's bound-contract set — at minimum, its version tracked in `contract_versions` — via a future HMIC-001 amendment (target: HMIC-001 v1.2). **This amendment is NOT made by Phase 149O.20B.** It requires its own governed phase and its own independent verification, and MUST NOT be performed silently as a side effect of any other phase.
- **HBDC-REQ-049.** Until HBDC-REQ-048's amendment exists, HBDC-001 conformance is evidentiary/advisory only: it informs a human or a future independent-verification phase whether Class-B topology is legitimately established, but it does not mechanically gate `validate_active_hatp_mandatory_independent_verification_certification`'s result, and no phase report or contract may represent it as doing so.

**Rejected alternatives:**
- *Option B (deployment-verifier contract only, never bound to HMIC)* — rejected because it would leave HMIC certification permanently unable to reflect Class-B topology compliance even after a future amendment closes that gap; freezing "never" forecloses a needed future capability without benefit.
- *Option C (a separate protected deployment manifest binds HBDC-001's version/digest, independent of HMIC-001)* — rejected as an unnecessary second protected-binding mechanism when HMIC-001's existing `contract_versions` field already exists for exactly this purpose (HMIC-REQ-067/068); introducing a parallel manifest would duplicate, not simplify, the trust model.

Consequence: real Class-B provisioning and certification remain blocked, independent of this disposition, by DRA-REQ-008/009 (149O.20A §45–§48) and by HBDC-REQ-050/051 below — HBDC-REQ-048's future amendment is a prerequisite for *mechanically gated* certification validity, not for provisioning authorization, which is separately and independently blocked regardless.

## 18. Threat-Model Limits

- **CBD non-goal.** A fully compromised OS root/admin account can generally alter protected filesystem state and the execution environment this contract locks down. HBDC-001 does not claim resistance beyond the two-principal trust model it defines (§4–§5).
- The hardware HATP signer (HATP-001 §9–§11) remains a separate protection for signing and human-presence; HBDC-001's filesystem/environment contract does not claim to replace hardware assurances.

## 19. Security Invariants (CBD-1 .. CBD-8)

- **CBD-1.** The agent principal cannot write protected authority state (HBDC-REQ-007, HBDC-REQ-013..021).
- **CBD-2.** The admin principal exclusively controls protected authority state (HBDC-REQ-009).
- **CBD-3.** The agent principal cannot redirect Protected Root — no override path exists, and symlink/ACL/group/parent-path channels are closed (HBDC-REQ-011, HBDC-REQ-015..018).
- **CBD-4.** The agent principal cannot redirect Model-A authority-module execution environment (HBDC-REQ-025..039).
- **CBD-5.** Identifier mutation alone (`repository_instance_id`) cannot confer authority (HBDC-REQ-042).
- **CBD-6.** Deployment conformance does not authorize real provisioning, certification, or activation (HBDC-REQ-050..051).
- **CBD-7.** Fail-closed on incomplete evidence: `INDETERMINATE` is never treated as ready (HBDC-REQ-052..053).
- **CBD-8.** HBDC-001 does not mechanically gate HMIC certification validity until formally bound into HMIC's contract set (HBDC-REQ-047..049).

## 20. Conformance Vocabulary

- **HBDC-REQ-052.** Deployment conformance status SHALL be one of a closed vocabulary: `COMPLIANT`, `NON_COMPLIANT`, `INDETERMINATE`. `INDETERMINATE` SHALL be treated as NOT ready for any readiness claim — fail-closed; there is no "unknown but allowed" outcome.
- **HBDC-REQ-053.** A future verifier that cannot obtain sufficient evidence to check every requirement in HBDC-REQ-001..046 SHALL report `INDETERMINATE`, never `COMPLIANT`.

## 21. Requirement Inventory and Attack Matrix

**Requirement count:** HBDC-001 v1.0 defines **55** requirements, `HBDC-REQ-001` through `HBDC-REQ-055` inclusive, sequential, no gaps, no duplicates (see §24 Full Requirement Traceability).

**Invariant count:** 8, `CBD-1` through `CBD-8` (§19).

### Attack Matrix (21 scenarios)

| # | Attack | Disposition |
|---|---|---|
| 1 | Agent writes Protected Root directly | Prevented — no write permission (HBDC-REQ-013..015) |
| 2 | Agent redirects Protected Root via env var / CLI override | Prevented — no override parameter exists on `HATPTrustStore.production()` (HBDC-REQ-011) |
| 3 | Agent uses ACL/group membership to gain effective write access | Prevented — HBDC-REQ-015/016 require effective-access testing, not mode-bits-only |
| 4 | Agent replaces a writable parent directory entry to rename/redirect Protected Root | Prevented — ancestor non-writability required (HBDC-REQ-017) |
| 5 | Agent redirects Protected Root via symlink | Prevented — fail-closed symlink rejection (HBDC-REQ-018) |
| 6 | Agent hard-links an authority-bearing file into an agent-writable location | Prevented — hard-link creation restricted to admin, inside Protected Root (HBDC-REQ-019) |
| 7 | Protected Root missing; agent-side code auto-provisions it | Prevented — fail-closed, no auto-provisioning (HBDC-REQ-012, HBDC-REQ-021) |
| 8 | Agent modifies production venv or site-packages | Prevented — admin-owned, agent-unwritable (HBDC-REQ-025, HBDC-REQ-026) |
| 9 | Agent replaces production Python executable | Prevented — agent-unwritable executable path (HBDC-REQ-027) |
| 10 | Hostile `PYTHONPATH` injected by agent launch environment | Prevented/rejected per admin-controlled policy (HBDC-REQ-028) |
| 11 | Agent shadows import via CWD manipulation | Prevented — `sys.path` ordering requirement (HBDC-REQ-033) |
| 12 | Agent installs hostile `sitecustomize.py`/`usercustomize.py` | Prevented — admin-controlled or absent (HBDC-REQ-030) |
| 13 | Agent installs hostile `.pth` file with import-executing lines | Prevented — admin-controlled or absent (HBDC-REQ-031) |
| 14 | Agent installs a `sys.meta_path` import hook | Prevented — no admin-controlled startup path grants this (HBDC-REQ-032) |
| 15 | Agent creates a fake/shadow `pcae` package earlier on `sys.path` | Prevented jointly by HBDC-REQ-028, 029, 033 (HBDC-REQ-034) |
| 16 | Wrong-repository / wrong-deployment certification reuse | Prevented — `DeploymentBinding` match required (HBDC-REQ-042) |
| 17 | Worktree/clone replay of another deployment's binding | Prevented — independent binding/certification required (HBDC-REQ-043, HBDC-REQ-044) |
| 18 | Host migration certification reuse | Prevented — new binding/recertification required (HBDC-REQ-045) |
| 19 | Backup restored to a different path/host retains authority | Prevented unless byte-identical restore to original path/host (HBDC-REQ-046) |
| 20 | Agent replaces resolved Git executable to falsify `implementation_commit` derivation | Prevented — admin-controlled `PATH`/pinned executable (HBDC-REQ-038) |
| 21 | Contract-freeze-only claim represented as real certification/activation authorization | Prevented — explicit non-authorization (HBDC-REQ-050, HBDC-REQ-051) |

## 22. Stop / Fail Conditions

DRA-S1..S9 (149O.20A §86) are **not retriggered or reopened** by this contract; all remain NOT TRIGGERED as of the architecture phase. HBDC-001 adds the following contract-freeze-specific fail conditions, evaluated in §26:

| Blocking condition | Resolved by this contract? | Where |
|---|---|---|
| Contract does not require distinct OS principals | Yes | §7, HBDC-REQ-001/002 |
| Contract allows agent write authority to Protected Root | Yes | §11, HBDC-REQ-013 |
| Contract checks only mode bits, ignores effective ACL/group access | Yes | HBDC-REQ-015/016 |
| Contract ignores writable-parent replacement | Yes | HBDC-REQ-017 |
| Contract permits agent-controlled authority-root redirect | Yes | HBDC-REQ-011, 018 |
| "Python environment locked" left undefined | Yes | §13, HBDC-REQ-025..039 |
| Contract permits agent-controlled `PYTHONPATH`/module shadowing | Yes | HBDC-REQ-028, 033, 034 |
| Contract permits agent-writable production venv/import metadata | Yes | HBDC-REQ-026, 035 |
| Contract implicitly accepts non-Model-A deployment despite Option C | Yes | HBDC-REQ-022, 024 |
| Contract claims runtime-source cryptographic provenance is solved | Yes (explicitly disclaimed) | HBDC-REQ-041 |
| Contract allows deployment verification to auto-provision authority state | Yes (explicitly disclaimed) | HBDC-REQ-012, 021 |
| Contract allows certification/activation merely because conformance passes | Yes (explicitly disclaimed) | HBDC-REQ-050, 051 |
| HBDC's own trust/binding disposition left unresolved | Yes | §17, HBDC-REQ-047..049 |
| This phase modifies HMIC/HATP/HMRC production contracts | No modification made | §23 |
| Real provisioning/certification/activation occurs | No occurrence | §23 |
| PB/POL-005/COMP-002 changes | No change made | §23 |

## 23. Real-Authorization Gates

- **HBDC-REQ-050.** Successful HBDC-001 conformance (a future `COMPLIANT` verification result) does NOT itself authorize creation of a real Protected Root, real OS principal provisioning, real HMIC certification, real active binding, real Cutover Record transition, or real `HATP_MANDATORY` activation. Each requires its own separately authorized governed phase, mirroring DRA-REQ-008/009.
- **HBDC-REQ-051.** Freezing this contract (Phase 149O.20B itself) does not authorize any of the actions listed in HBDC-REQ-050 either.

## 24. Full Requirement Traceability

| ID | One-line statement | Section |
|---|---|---|
| HBDC-REQ-001 | Exactly two OS principals required, v1.0 | §7 |
| HBDC-REQ-002 | Agent/admin SHALL be distinct OS accounts | §7 |
| HBDC-REQ-003 | Third-principal split requires contract revision | §7 |
| HBDC-REQ-004 | Admin authority not inferred from env/name/ownership/Git identity | §7 |
| HBDC-REQ-005 | Agent has no self-elevation path to admin | §7 |
| HBDC-REQ-006 | Agent MAY read/execute/validate/inspect | §8 |
| HBDC-REQ-007 | Agent MUST NOT write authority-bearing state | §8 |
| HBDC-REQ-008 | Exception: designated agent-writable non-authoritative artifacts | §8 |
| HBDC-REQ-009 | Admin exclusive write authority enumerated | §9 |
| HBDC-REQ-010 | Admin write authority ≠ runtime execution authority | §9 |
| HBDC-REQ-011 | Protected Root resolution has no override path | §10 |
| HBDC-REQ-012 | No agent-invoked auto-creation of Protected Root | §10 |
| HBDC-REQ-013 | Protected Root owned by admin principal | §11 |
| HBDC-REQ-014 | Protected Root mode excludes group/other write | §11 |
| HBDC-REQ-015 | No agent group membership grants effective write | §11 |
| HBDC-REQ-016 | No ACL grants agent write access | §11 |
| HBDC-REQ-017 | Ancestor directories non-agent-writable | §11 |
| HBDC-REQ-018 | Symlink resolution fails closed | §11 |
| HBDC-REQ-019 | Hard links restricted to admin, inside Protected Root | §11 |
| HBDC-REQ-020 | Directory-entry replacement treated as write-equivalent | §11 |
| HBDC-REQ-021 | Agent-side code fails closed on absent/malformed root | §11 |
| HBDC-REQ-022 | Model A is the authorized deployment model | §12 |
| HBDC-REQ-023 | Model-A conformance evidence enumerated | §12 |
| HBDC-REQ-024 | Models B/C/D not authorized under v1.0 | §12 |
| HBDC-REQ-025 | Production Python environment admin-provisioned | §13 |
| HBDC-REQ-026 | Production venv admin-owned only | §13 |
| HBDC-REQ-027 | Production Python executable agent-unwritable | §13 |
| HBDC-REQ-028 | `PYTHONPATH` not agent-settable/influenceable | §13 |
| HBDC-REQ-029 | User-site disabled or proven agent-unwritable | §13 |
| HBDC-REQ-030 | sitecustomize/usercustomize admin-controlled or absent | §13 |
| HBDC-REQ-031 | `.pth` files admin-controlled or absent | §13 |
| HBDC-REQ-032 | No agent-installable `sys.meta_path` hook | §13 |
| HBDC-REQ-033 | CWD change cannot shadow authority imports | §13 |
| HBDC-REQ-034 | Fake `pcae` package cannot execute as authority | §13 |
| HBDC-REQ-035 | Editable-install metadata admin-controlled | §13 |
| HBDC-REQ-036 | Launcher/wrapper configuration admin-controlled | §13 |
| HBDC-REQ-037 | Shell environment cannot inject authority-changing vars | §13 |
| HBDC-REQ-038 | Git executable resolution agent-unwritable | §13 |
| HBDC-REQ-039 | Third-party authority dependencies agent-unreplaceable | §13 |
| HBDC-REQ-040 | Env-lock is the concrete Option-C mitigation | §14 |
| HBDC-REQ-041 | No overclaim of cryptographic executed-source attestation | §14 |
| HBDC-REQ-042 | `repository_instance_id` confers no authority alone | §16 |
| HBDC-REQ-043 | Worktrees require independent binding/certification | §16 |
| HBDC-REQ-044 | Clones/copies require independent binding/certification | §16 |
| HBDC-REQ-045 | Host migration requires new binding/recertification | §16 |
| HBDC-REQ-046 | Cross-host/path backup restore does not retain authority | §16 |
| HBDC-REQ-047 | HBDC-001 not yet an HMIC bound contract | §17 |
| HBDC-REQ-048 | Future HMIC v1.2 amendment required to bind HBDC-001 | §17 |
| HBDC-REQ-049 | Until bound, HBDC-001 conformance is advisory only | §17 |
| HBDC-REQ-050 | Conformance does not authorize real provisioning/certification/activation | §23 |
| HBDC-REQ-051 | Contract freeze itself does not authorize those actions | §23 |
| HBDC-REQ-052 | Closed conformance vocabulary, fail-closed on `INDETERMINATE` | §20 |
| HBDC-REQ-053 | Insufficient evidence SHALL yield `INDETERMINATE`, not `COMPLIANT` | §20 |
| HBDC-REQ-054 | "CLASS-B DEPLOYMENT VERIFIED" reserved for independent verification | §25 |
| HBDC-REQ-055 | Conformance ≠ HATP/production/rollback readiness | §25 |

## 25. Status-Claim Discipline

- **HBDC-REQ-054.** The phrase "CLASS-B DEPLOYMENT VERIFIED" SHALL only be used after an independent verification phase (149O.20C or a successor) has confirmed conformance under an actually-provisioned topology. Contract freeze alone never establishes it.
- **HBDC-REQ-055.** Contract conformance under HBDC-001 does not by itself equal "HATP DEPLOYMENT READY," "HATP PRODUCTION READY," or "ROLLBACK EXECUTION READY" as those broader terms are defined by 149O.20A §63 and other architecture. Those terms retain their own, separately gated definitions; Permission Broker, POL-005, COMP-002, and runtime-capability prerequisites are unaffected by this contract.

## 26. Blocking-Condition Check

All rows in §22's table resolve "Yes" or "No modification/occurrence" as shown — no blocking condition from the 149O.20B phase charter is left open by this contract text.

## 27. Contract Self-Consistency Statement

This contract: (a) introduces no dependency, in either direction, on `src/pcae/**` or `scripts/**`; (b) does not amend HATP-001, HMIC-001, or HMRC-001's byte content; (c) does not create real protected state, OS principals, or filesystem permissions; (d) explicitly defers its own binding into HMIC-001's contract set to a future, separately-governed phase (§17); (e) is internally traceable — every `HBDC-REQ-###` ID referenced elsewhere in this document appears in §24's table exactly once.

## 28. Contract Versioning

HBDC-001 is frozen as v1.0 by Phase 149O.20B. Reason: freeze Class-B deployment topology and the Model-A execution-environment lock as concrete, testable requirements before any real provisioning is attempted. No prior version exists.

## 29. Expected Contract Verdict

```
HATP CLASS-B DEPLOYMENT CONTRACT:
HBDC-001 v1.0 — FROZEN
— PENDING INDEPENDENT VERIFICATION
— REAL PROVISIONING NOT AUTHORIZED
— REAL ACTIVATION NOT AUTHORIZED
```

## 30. Recommended Next Phase

**149O.20C — HATP Class-B Deployment Contract Independent Verification.** That phase must independently: reconstruct 149O.20A's decisions; re-derive the two-principal model; independently attack Protected Root permission semantics; independently attack ACL/group/writable-parent loopholes; independently attack the Model-A Python environment lock; independently test the OPTION-C boundary; independently verify HBDC-001's contract-binding/self-trust disposition (§17); and verify no real provisioning or activation occurred during Phase 149O.20B. It must not recommend provisioning directly. If it confirms HBDC-REQ-048's HMIC v1.2 prerequisite, that conclusion must be independently re-derived, not merely accepted, before any HMIC amendment is authorized.
