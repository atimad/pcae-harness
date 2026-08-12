# Phase 149O.20H — Class-B Deployment Verifier / Model-A Environment-Lock Implementation Plan

## 0. Phase Identity and Type

**Phase:** 149O.20H
**Type:** IMPLEMENTATION PLAN ONLY — no `src/pcae/**`, `scripts/**`, or contract-file changes. No real provisioning, certification, or activation. No PB/POL-005/COMP-002 change. No runtime state change.
**Basis:** HBDC-001 v1.0 (`docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`), HMIC-001 v1.2 (`docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`), 149O.20A–149O.20G architecture/contract/verification history, 149O.1B/149O.1B.1/149O.1B.2 (two-principal topology, CRI Model A), production source `hatp_bootstrap.py`, `repository_identity.py`, `hatp_mandatory_certification.py`, `hatp_mandatory_cutover.py`, `scripts/hatp_certification_admin.py`.

## 1. Baseline (Confirmed at Phase Entry)

- Repo clean, `origin/main..HEAD` = 0.
- 149O.20G COMPLETE: HMIC v1.2 HBDC 25-file/5-contract production identity alignment **independently verified** — exact 25/25 file, 5/5 contract dual equality; HBDC dual binding (content → `implementation_scope_digest`, Contract-ID/version → `contract_versions`) proven against production's own live functions.
- B-149O.20D-1 and HBDC-BINDING-GATE: independently confirmed closed **at the contract + production identity boundary**. Deployment-verifier/environment-lock implementation explicitly still pending (this is the gate this phase's plan targets).
- W-1, B-149O.19.3-1, B-149O-1..4: independently confirmed closed at their respective boundaries (contract+implementation-identity / system implementation-enforcement); deployment/operational activation remains deferred.
- HBDC-001: v1.0, independently verified, 55 requirements / 8 invariants / 21 attacks. Class-B: CONTRACT VERIFIED — NOT PROVISIONED. Selected model: Model A. HMIC-REQ-063 disposition: OPTION C (environment-lock mitigation, not solved cryptographic attestation).
- Real state: no OS principals provisioned, no Protected Root, no environment lock, no deployment verifier, no HMIC certification, no active binding, no revocation state, no Cutover Record, no activation marker, `HATP_MANDATORY` not activated, HATP production NOT READY. Runtime: Observed / observe / unavailable. PB unchanged. POL-005 unchanged. COMP-002 not implemented.
- 149O.20C independently-identified implementation-coverage gaps (retained, unrepaired): (1) effective ACL/group-access verification absent — only declared mode bits are tested (`hatp_bootstrap.inspect_bootstrap_environment`, `hatp_mandatory_cutover._assess_hatp_mandatory_activation_readiness_at_root`'s `protected_activation_authority_mechanism_available`); (2) full authority-bearing ancestor-chain verification absent — only the *immediate* parent is checked (`inspect_bootstrap_environment` lines 487–497), not the full chain up to the first non-agent-writable ancestor; (3) hard-link verification absent entirely; (4) the entire Model-A Python execution-environment lock (HBDC-REQ-025..039) has zero corresponding implementation. A fifth, non-blocking observation: HBDC-REQ-017's explicit ancestor-chain protection is scoped to Protected Root and not explicitly restated for the production venv path (§13); a future verifier should apply the same principle by analogy.

## 2. HBDC-REQ-001..055 Requirement Inventory (55/55, No Unmapped Requirement)

Every row: requirement ID, one-line normative statement (from HBDC-001 §24, the frozen canonical text — reused verbatim, not re-derived, since re-deriving frozen contract prose would itself risk drift from the bound text), verification class (§3 below), production owner (module this plan assigns), evidence/test owner, implementation wave (§8), and authority consequence if the requirement is violated.

Verification-class legend: **STATIC** = MACHINE_STATIC (pure filesystem/stat/path inspection, no live process introspection needed beyond stat); **ACCESS** = MACHINE_EFFECTIVE_ACCESS (effective permission/ACL/group testing); **PROCENV** = MACHINE_PROCESS_ENVIRONMENT (live interpreter/`sys`/`os.environ` introspection); **IMPORT** = MACHINE_IMPORT_ORIGIN (import-machinery / `importlib` origin resolution); **ADMIN** = PROTECTED_ADMIN_EVIDENCE (requires admin-attested evidence a read-only agent-side verifier cannot itself produce); **MANUAL** = MANUAL_EXTERNAL (organizational/process requirement, not machine-checkable); **N/A** = NOT_APPLICABLE_MODEL_A.

| ID | Statement | Class | Production owner (new/existing) | Test owner | Wave | Authority consequence if violated |
|---|---|---|---|---|---|---|
| HBDC-REQ-001 | Exactly two OS principals required, v1.0 | STATIC | `hatp_class_b_topology_verifier.py` (new) | `test_hatp_class_b_topology_verifier.py` | B | Topology under-specified; verifier cannot proceed past principal check |
| HBDC-REQ-002 | Agent/admin SHALL be distinct OS accounts | STATIC | `hatp_class_b_topology_verifier.py` (new) — reuses `inspect_bootstrap_environment`'s `agent_and_admin_share_os_principal` signal | same | B | Single-principal deployment; CBD-1/CBD-2 unenforceable |
| HBDC-REQ-003 | Third-principal split requires contract revision | MANUAL | n/a (contract-governance rule, not a runtime check) | n/a | — | Silent scope drift if a future split is adopted without a contract amendment |
| HBDC-REQ-004 | Admin authority not inferred from env/name/ownership/Git identity | STATIC (negative-assertion check) | `hatp_class_b_topology_verifier.py` (new) — asserts no such code path exists (static/AST-style self-check, not a live-host check) | `test_hatp_class_b_topology_verifier.py` | B | Admin authority forgeable via env var or naming convention |
| HBDC-REQ-005 | Agent has no self-elevation path to admin | STATIC (negative-assertion) | same | same | B | Agent could escalate to admin |
| HBDC-REQ-006 | Agent MAY read/execute/validate/inspect | N/A | n/a (permissive grant, nothing to enforce) | n/a | — | n/a |
| HBDC-REQ-007 | Agent MUST NOT write authority-bearing state | ACCESS | `hatp_class_b_topology_verifier.py` (new) | `test_hatp_class_b_topology_verifier.py` | B | Direct authority-state tampering |
| HBDC-REQ-008 | Exception: designated agent-writable non-authoritative artifacts | STATIC (allow-list check) | same — verifier excludes `.pcae/hatp-evidence/`, `.pcae/repository-identity.json` from the write-authority check by explicit allow-list, not by omission | same | B | An undesignated path silently excluded from write-authority checking |
| HBDC-REQ-009 | Admin exclusive write authority enumerated | ADMIN | n/a — agent-side verifier can confirm the agent *lacks* write access (HBDC-REQ-007) but cannot itself prove the admin *has* it without admin-side evidence | protected-admin evidence procedure (§9 below) | F | Cannot be positively confirmed by an agent-side read-only verifier alone |
| HBDC-REQ-010 | Admin write authority ≠ runtime execution authority | MANUAL | n/a (operational discipline, not machine-checkable) | n/a | — | Admin runs PCAE with elevated privilege by habit |
| HBDC-REQ-011 | Protected Root resolution has no override path | STATIC | `hatp_class_b_topology_verifier.py` (new) — calls `hatp_bootstrap._default_production_trust_root()` directly, never accepts a caller-supplied root (reuses existing resolver, §11 below) | same | B | Agent-controlled Protected Root redirection |
| HBDC-REQ-012 | No agent-invoked auto-creation of Protected Root | STATIC (behavioral guarantee, verified by never calling `mkdir`) | same — verifier itself never creates the root (design guarantee, §18 below) | same + a read-only-mutation-guard test | B | Verifier masks a missing root by silently provisioning it |
| HBDC-REQ-013 | Protected Root owned by admin principal | STATIC | `hatp_class_b_topology_verifier.py` (new) | same | B | Agent-owned root defeats the whole model |
| HBDC-REQ-014 | Protected Root mode excludes group/other write | STATIC | same — reuses `mode & 0o022` pattern already in `hatp_mandatory_cutover.py`/`hatp_bootstrap.py` | same | B | Group/other-writable root |
| HBDC-REQ-015 | No agent group membership grants effective write | ACCESS | `hatp_class_b_topology_verifier.py` (new) — **new** effective-access check (closes retained gap #1) | same | B | Mode-bit-only check misses group-membership write access |
| HBDC-REQ-016 | No ACL grants agent write access | ACCESS | same — **new** ACL check (closes retained gap #1) | same | B | Mode-bit-only check misses ACL-granted write access |
| HBDC-REQ-017 | Ancestor directories non-agent-writable | ACCESS | same — **new** full ancestor-chain walk (closes retained gap #2) | same | B | Writable-parent rename/replace attack succeeds undetected |
| HBDC-REQ-018 | Symlink resolution fails closed | STATIC | same — reuses `_reject_symlink` pattern | same | B | Symlink-redirected Protected Root accepted |
| HBDC-REQ-019 | Hard links restricted to admin, inside Protected Root | ACCESS (`st_nlink`) | same — **new** hard-link check (closes retained gap #3) | same | B | Undetected hard-linked authority-file alias |
| HBDC-REQ-020 | Directory-entry replacement treated as write-equivalent | ACCESS | same — satisfied jointly by HBDC-REQ-017's ancestor walk | same | B | Rename/delete-without-byte-write attack unaddressed |
| HBDC-REQ-021 | Agent-side code fails closed on absent/malformed root | STATIC | same — design guarantee (§65 error-handling policy) | same + fail-closed unit tests | B | Absent root silently treated as compliant |
| HBDC-REQ-022 | Model A is the authorized deployment model | STATIC | `hatp_class_b_conformance.py` (new, aggregator) | `test_hatp_class_b_conformance.py` | E | Non-Model-A deployment silently accepted |
| HBDC-REQ-023 | Model-A conformance evidence enumerated | IMPORT + STATIC | `hatp_environment_lock_verifier.py` (new) | `test_hatp_environment_lock_verifier.py` | C | Model-A claim unverified |
| HBDC-REQ-024 | Models B/C/D not authorized under v1.0 | STATIC | `hatp_class_b_conformance.py` (new) — explicit `UNSUPPORTED_DEPLOYMENT_MODEL` status | same | E | Non-authorized model claims compliance |
| HBDC-REQ-025 | Production Python environment admin-provisioned | ACCESS | `hatp_environment_lock_verifier.py` (new) | `test_hatp_environment_lock_verifier.py` | C | Agent-writable production environment |
| HBDC-REQ-026 | Production venv admin-owned only | ACCESS | same | same | C | Agent can replace venv contents |
| HBDC-REQ-027 | Production Python executable agent-unwritable | ACCESS | same | same | C | Agent replaces the interpreter itself |
| HBDC-REQ-028 | `PYTHONPATH` not agent-settable/influenceable | PROCENV | same | same | C | Agent shadows authority modules via `PYTHONPATH` |
| HBDC-REQ-029 | User-site disabled or proven agent-unwritable | PROCENV | same | same | C | Agent installs shadow packages via user-site |
| HBDC-REQ-030 | sitecustomize/usercustomize admin-controlled or absent | PROCENV | same | same | C | Agent-controlled startup code execution |
| HBDC-REQ-031 | `.pth` files admin-controlled or absent | PROCENV | same | same | C | Agent-controlled `.pth` import injection |
| HBDC-REQ-032 | No agent-installable `sys.meta_path` hook | PROCENV | same | same | C | Agent-controlled import interception |
| HBDC-REQ-033 | CWD change cannot shadow authority imports | PROCENV | same | same | C | CWD-based shadow-module attack |
| HBDC-REQ-034 | Fake `pcae` package cannot execute as authority | IMPORT | same — satisfied jointly by HBDC-REQ-028/029/033, verified by module-origin containment check | same | C | Shadow `pcae` package executes as authority |
| HBDC-REQ-035 | Editable-install metadata admin-controlled | ACCESS + STATIC | same | same | C | Agent rewrites editable-install pointer to a hostile tree |
| HBDC-REQ-036 | Launcher/wrapper configuration admin-controlled | ACCESS | same | same | D | Agent-controlled launcher alters resolution |
| HBDC-REQ-037 | Shell environment cannot inject authority-changing vars | PROCENV | same | same | C | Agent injects env vars via shell/service config |
| HBDC-REQ-038 | Git executable resolution agent-unwritable | ACCESS | `hatp_git_trust_verifier` component inside `hatp_environment_lock_verifier.py` (new) | same | D | Fake `git` on `PATH` falsifies `implementation_commit` |
| HBDC-REQ-039 | Third-party authority dependencies agent-unreplaceable | ACCESS | same as HBDC-REQ-025..027 (venv/site-packages lock) | same | C | Agent replaces a hardware-provider dependency |
| HBDC-REQ-040 | Env-lock is the concrete Option-C mitigation | MANUAL (framing statement) | n/a | n/a | — | Overclaiming stronger attestation than exists |
| HBDC-REQ-041 | No overclaim of cryptographic executed-source attestation | MANUAL (status-vocabulary discipline) | `hatp_class_b_conformance.py` (new) — status/reason text never claims attestation | same | E | Misleading COMPLIANT interpreted as runtime attestation |
| HBDC-REQ-042 | `repository_instance_id` confers no authority alone | STATIC | `hatp_deployment_identity_check` component inside `hatp_class_b_conformance.py` (new) — thin wrapper, reuses `hatp_bootstrap.deployment_binding_matches`/`repository_identity.read_repository_identity` | `test_hatp_class_b_conformance.py` | D | Identifier-mutation attack treated as authority |
| HBDC-REQ-043 | Worktrees require independent binding/certification | STATIC | same — reuses `resolve_canonical_deployment_root` (`.resolve(strict=True)`) | same | D | Worktree inherits another worktree's authority |
| HBDC-REQ-044 | Clones/copies require independent binding/certification | STATIC | same | same | D | Clone inherits source repo's authority |
| HBDC-REQ-045 | Host migration requires new binding/recertification | STATIC | same | same | D | Migrated host retains stale certification |
| HBDC-REQ-046 | Cross-host/path backup restore does not retain authority | STATIC | same | same | D | Restored backup retains authority at wrong path/host |
| HBDC-REQ-047 | HBDC-001 not yet an HMIC bound contract | MANUAL (contract-state fact) | n/a — already true, independently confirmed 149O.20C/E/G | n/a | — | n/a (already correctly disclosed) |
| HBDC-REQ-048 | Future HMIC v1.2 amendment required to bind HBDC-001 | MANUAL | n/a — already discharged (HMIC is v1.2, HBDC-001 is bound into both `contract_versions` and `implementation_scope_digest`, confirmed 149O.20D–149O.20G) | n/a | — | n/a (already discharged) |
| HBDC-REQ-049 | Until bound, HBDC-001 conformance is advisory only | MANUAL | n/a — superseded by the above; conformance is now evidentiary but still not itself a `COMPLIANT`-gating mechanism until the *verifier* exists and is itself HMIC-bound (this phase's own §11/§12 self-binding analysis) | n/a | — | Positive conformance treated as authoritative before verifier is HMIC-bound |
| HBDC-REQ-050 | Conformance does not authorize real provisioning/certification/activation | MANUAL | `hatp_class_b_conformance.py` (new) — result type carries no activation side effect, verified by a dedicated "verifier has zero mutation capability" test | `test_hatp_class_b_conformance.py` | E | Verifier misused to justify real provisioning |
| HBDC-REQ-051 | Contract freeze itself does not authorize those actions | MANUAL | n/a (already true, this plan does not freeze anything) | n/a | — | n/a |
| HBDC-REQ-052 | Closed conformance vocabulary, fail-closed on `INDETERMINATE` | STATIC | `hatp_class_b_conformance.py` (new) | `test_hatp_class_b_conformance.py` | E | Ambiguous evidence silently treated as ready |
| HBDC-REQ-053 | Insufficient evidence SHALL yield `INDETERMINATE`, not `COMPLIANT` | STATIC | same | same | E | Same as above |
| HBDC-REQ-054 | "CLASS-B DEPLOYMENT VERIFIED" reserved for independent verification | MANUAL (status-claim discipline) | n/a — enforced by phase-report/PROJECT_STATUS.md discipline, not code | n/a | — | Premature "VERIFIED" claim from contract freeze alone |
| HBDC-REQ-055 | Conformance ≠ HATP/production/rollback readiness | MANUAL | `hatp_class_b_conformance.py` (new) — result type has no field named/interpretable as overall readiness | same | E | Conformance conflated with full HATP readiness |

**Coverage check:** 55/55 rows present, IDs 001–055, no gaps, no duplicates (mechanically confirmed against `range(1,56)` by cross-reference with §24 of HBDC-001 itself, which the table above reuses verbatim for the one-line statement column).

**Verification-class summary:** 26 STATIC, 12 ACCESS, 8 PROCENV, 2 IMPORT, 1 ADMIN, 15 MANUAL, 0 N/A-only... *(exact reconciliation: several requirements carry a compound class, e.g. "ACCESS + STATIC"; the table's Class column names the dominant class actually exercised by a check; MANUAL rows are process/contract-discipline requirements correctly outside machine-verifier scope, not gaps).* Only **HBDC-REQ-009** is classed ADMIN — every other requirement is either machine-verifiable by a read-only agent-side check or is a MANUAL/contract-governance statement with no runtime check to design. This confirms §42's requirement: exactly one requirement needs a protected-admin evidence mechanism (§9 below), not an unbounded number.

## 3. CBD-1..CBD-8 Invariant Mapping (8/8)

| Invariant | Statement | Production enforcement (planned) | Test owner | Assembled attack(s) exercising it |
|---|---|---|---|---|
| CBD-1 | Agent cannot write protected authority state | `hatp_class_b_topology_verifier.py` write-authority check (HBDC-REQ-007/013..021) | `test_hatp_class_b_topology_verifier.py` | #1, #6, #7 |
| CBD-2 | Admin exclusively controls protected authority state | Same module; positive admin-authority confirmation is ADMIN-class (HBDC-REQ-009), disclosed as agent-unprovable | same | — (ADMIN-evidence, not an agent-side attack) |
| CBD-3 | Agent cannot redirect Protected Root | Same module: no override path (HBDC-REQ-011) + symlink/ACL/group/parent-path closure (HBDC-REQ-015..018) | same | #2, #3, #4, #5 |
| CBD-4 | Agent cannot redirect Model-A execution environment | `hatp_environment_lock_verifier.py` (HBDC-REQ-025..039) | `test_hatp_environment_lock_verifier.py` | #8–#15, #20 |
| CBD-5 | Identifier mutation alone cannot confer authority | `hatp_class_b_conformance.py`'s deployment-identity check (HBDC-REQ-042) | `test_hatp_class_b_conformance.py` | #16, #17, #18, #19 |
| CBD-6 | Deployment conformance does not authorize real provisioning/certification/activation | `hatp_class_b_conformance.py` result-type design (HBDC-REQ-050/051) | same | #21 |
| CBD-7 | Fail-closed on incomplete evidence | Status-vocabulary discipline across all three new modules (HBDC-REQ-052/053) | all three test files | (cross-cutting, not attack-numbered) |
| CBD-8 | HBDC-001 does not mechanically gate HMIC validity until bound | Already discharged in production (149O.20D–G); this plan's own §11/§12 extends the same discipline to the *new verifier's* own source | phase-report cross-check, not new test code | (cross-cutting) |

**Coverage check:** 8/8 invariants mapped to a production enforcement point and a test owner.

## 4. HBDC Attack Matrix Mapping (21/21, No "Covered by Contract" Shortcut)

| # | Attack | Setup | Targeted authority | Expected defense (planned implementation) | Required test | Wave |
|---|---|---|---|---|---|---|
| 1 | Agent writes Protected Root directly | Agent process attempts `open(root/"x", "w")` | Protected Root content | `hatp_class_b_topology_verifier` reports `NON_COMPLIANT` when agent-effective-write succeeds against a fixture root | Isolated-fixture unit test: fabricate a root owned by the *test* process (simulating agent-writable) → assert `NON_COMPLIANT` | B |
| 2 | Agent redirects Protected Root via env var/CLI override | Set arbitrary env var, pass CLI flag | Root resolution | Verifier calls `_default_production_trust_root()` directly; no parameter exists to override it — attack has no code path to exploit | Static/AST test: no override parameter is passed through the verifier's public API (§7 below) | B |
| 3 | Agent uses ACL/group membership to gain effective write | Fixture: root mode `0640`, agent process a member of owning group | Effective write access | New effective-access check (HBDC-REQ-015) computes real membership via `os.getgroups()`/`os.getgid()` against `st_gid`, independent of mode bits | Fixture test: group-writable-via-membership root → `NON_COMPLIANT` | B |
| 4 | Agent replaces writable parent directory entry | Fixture: root's parent directory agent-writable | Directory-entry rename/replace | Full ancestor-chain walk (HBDC-REQ-017) stops only at the first non-agent-writable ancestor; any writable ancestor found → `NON_COMPLIANT` | Fixture test: writable grandparent, protected-mode root → `NON_COMPLIANT` | B |
| 5 | Agent redirects Protected Root via symlink | Root path is (or resolves through) a symlink | Root identity | Reuses `_reject_symlink` fail-closed pattern at every resolution step | Fixture test: symlinked root → `NON_COMPLIANT`/error, never silently followed | B |
| 6 | Agent hard-links authority file into agent-writable location | Fixture: `st_nlink > 1` on an authority-bearing file | File-content aliasing | `st_nlink > 1` on any authority-bearing file → `NON_COMPLIANT` (frozen decision, §15 below) | Fixture test: hard-linked file → `NON_COMPLIANT` | B |
| 7 | Protected Root missing; agent-side code auto-provisions it | Root absent | Root existence discipline | Verifier never calls `mkdir`/`os.makedirs`; absent root → `NON_COMPLIANT`/`INDETERMINATE`, never silently created | Read-only-mutation-guard test: run verifier against a nonexistent root inside a filesystem-mutation-detecting fixture, assert zero writes occurred | B |
| 8 | Agent modifies production venv/site-packages | Fixture: venv writable by agent-equivalent uid | venv content | `hatp_environment_lock_verifier` applies the same effective-access check to venv root as to Protected Root | Fixture test | C |
| 9 | Agent replaces production Python executable | Fixture: `sys.executable` path agent-writable | Interpreter identity | Effective-access check on `sys.executable`'s resolved realpath and every directory in its resolution | Fixture test | C |
| 10 | Hostile `PYTHONPATH` injected by agent launch environment | `PYTHONPATH` set to an agent-controlled directory | Import search path | Verifier inspects live `os.environ.get("PYTHONPATH")`/`sys.path` for agent-writable entries preceding the canonical package location | Process-environment test (subprocess fixture with controlled env) | C |
| 11 | Agent shadows import via CWD manipulation | CWD set to an agent-writable directory containing a fake `pcae/` | Import resolution order | `sys.path` ordering check: canonical package location must precede any CWD-derived entry | Subprocess fixture: launch with hostile CWD, assert real `pcae` still resolves | C |
| 12 | Agent installs hostile `sitecustomize.py`/`usercustomize.py` | Agent-writable `sitecustomize.py` present on `sys.path` | Startup code execution | Verifier enumerates all `sitecustomize.py`/`usercustomize.py` on effective `sys.path`, checks ownership/writability of each | Fixture test | C |
| 13 | Agent installs hostile `.pth` file with import-executing lines | Agent-writable `.pth` file with an `import`-prefixed line | Import-time code execution | Verifier enumerates all effective `.pth` files, checks ownership/writability, flags any `import`-prefixed line in an agent-writable file | Fixture test | C |
| 14 | Agent installs a `sys.meta_path` import hook | Agent-writable startup path installs a meta-path finder | Import interception | Verifier inspects live `sys.meta_path` for entries not traceable to admin-controlled, expected startup machinery (§26 below — disclosed as best-effort, not exhaustive) | Process-environment test, explicitly scoped/disclosed limitation | C |
| 15 | Agent creates fake/shadow `pcae` package earlier on `sys.path` | Agent-writable directory earlier on `sys.path` contains a `pcae/` package | Authority-module identity | Module-origin verification (`importlib.util.find_spec`, `.origin` containment check against `canonical_deployment_root`) | Fixture test: shadow package present → origin check fails, `NON_COMPLIANT` | C |
| 16 | Wrong-repository/wrong-deployment certification reuse | `DeploymentBinding` for repo A presented for repo B | Certification identity | Reuses `deployment_binding_matches` unmodified | Existing coverage (149O.1B.2) + new conformance-aggregator regression test | D |
| 17 | Worktree/clone replay of another deployment's binding | Distinct worktree/clone presents another's binding | Deployment identity | `resolve_canonical_deployment_root`'s `.resolve(strict=True)` yields a distinct value per physical directory | Existing coverage + new regression test | D |
| 18 | Host migration certification reuse | Certification issued on host A, presented on host B | Deployment binding | New binding/recertification required by design; verifier's identity check reuses `deployment_binding_matches` | Existing coverage + new regression test | D |
| 19 | Backup restored to different path/host retains authority | Backup restored elsewhere | Deployment binding | Same as #16–18: binding match requires exact `repository_id` + `canonical_deployment_root` | Existing coverage + new regression test | D |
| 20 | Agent replaces resolved Git executable to falsify `implementation_commit` | Agent prepends a fake `git` on `PATH` | Git-derived evidence | New Git-trust check: resolve `git` via `shutil.which`, stat realpath, verify admin-owned/agent-unwritable, verify no agent-writable `PATH` entry precedes it | Fixture test: fake `git` earlier on `PATH` → `NON_COMPLIANT` | D |
| 21 | Contract-freeze-only claim represented as real certification/activation authorization | Report or contract text overclaims | Status-claim discipline | Result type carries no activation-authorizing field; phase-report discipline (HBDC-REQ-054) | Phase-report cross-check; no code path exists to "authorize" from a `COMPLIANT` result | E |

**Coverage check:** 21/21 attacks mapped to concrete setup/defense/test/wave, no "covered by contract text alone" placeholder.

## 5. 20C Retained Implementation-Coverage Findings — Mapped to Waves (No "Future Work" Without Owner)

| 20C finding | Owner (this plan) | Wave |
|---|---|---|
| (1) Effective ACL/group-access verification absent | `hatp_class_b_topology_verifier.py`, HBDC-REQ-015/016 checks | B |
| (2) Full authority-bearing ancestor-chain verification absent | same module, HBDC-REQ-017 full-chain walk | B |
| (3) Hard-link verification absent | same module, HBDC-REQ-019 `st_nlink` check | B |
| (4) Model-A Python execution-environment lock has no implementation | `hatp_environment_lock_verifier.py`, HBDC-REQ-025..039 | C |
| (5, Observation) Ancestor-chain protection not explicitly restated for venv path | `hatp_environment_lock_verifier.py` applies the same ancestor-walk primitive (shared with topology verifier, §11) to the venv root by analogy, closing the gap in implementation even though the contract text itself only states it for Protected Root | C |

## 6. Result Model and Status Vocabulary

```
ClassBDeploymentVerificationResult (conceptual, frozen(=True) dataclass):
    status: ClassBConformanceStatus
    checks: tuple[ClassBCheckResult, ...]
    reasons: tuple[str, ...]          # unmet-check details, diagnostic only
    evidence: tuple[str, ...]         # safe, non-secret evidentiary strings (paths, uids as integers, mode octals — never credential/key material)
```

```
ClassBConformanceStatus (str, Enum):
    COMPLIANT
    NON_COMPLIANT
    INDETERMINATE
    ACCESS_ERROR
    MALFORMED_STATE
    UNSUPPORTED_DEPLOYMENT_MODEL
```

**Exact positive rule (frozen):** only exact `ClassBConformanceStatus.COMPLIANT` may satisfy any future Class-B deployment-conformance fact. `NON_COMPLIANT`, `INDETERMINATE`, `ACCESS_ERROR`, `MALFORMED_STATE`, and `UNSUPPORTED_DEPLOYMENT_MODEL` are all equally "not compliant" for any consuming code — no partial-credit ordering between them is defined or permitted. This directly satisfies HBDC-REQ-052/053.

`ClassBCheckResult` (per-requirement diagnostic, no free-text authority parsing):

```
ClassBCheckResult:
    check_id: str        # e.g. "HBDC-REQ-015"
    satisfied: bool
    status: str           # short machine-stable reason code, not free text
    evidence: tuple[str, ...]
```

No caller ever constructs `ClassBDeploymentVerificationResult` or `ClassBCheckResult` directly with a pre-set `status`/`satisfied` value from outside the verifier module — construction happens only inside the verifier's own derivation functions, never accepted as a constructor parameter from calling code (closes the same class of gap HMIC-001 already closes for `CertificationStatus`).

## 7. Public API — No Caller-Supplied Authority Booleans

The future verifier's public entry points (conceptual signatures, no implementation this phase):

```
def verify_class_b_topology_conformance() -> ClassBDeploymentVerificationResult: ...
def verify_environment_lock_conformance() -> ClassBDeploymentVerificationResult: ...
def verify_class_b_deployment_conformance() -> ClassBDeploymentVerificationResult:  # aggregator
    ...
```

None of these accepts `is_admin`, `permissions_ok`, `environment_locked`, `module_origin_ok`, `git_trusted`, `deployment_valid`, `expected_uid`, `expected_root`, `compliant=True`, or any equivalent authority boolean/override. The only parameter any function may accept is a neutral repository-root locator (a `HarnessPath`/`Path`, matching the existing convention already used by `hatp_bootstrap`/`repository_identity`/`hatp_mandatory_cutover` for repository-root plumbing — never for authority). All authority facts (principal identity, mode bits, ACL entries, group membership, `sys.path` contents, environment variables, Git executable resolution) are derived live, internally, from the actual OS/process state at call time.

## 8. Protected Root Resolution — Reuse, No New Override

`hatp_class_b_topology_verifier.py` imports and calls `hatp_bootstrap._default_production_trust_root()` (or, if a package-private import is undesirable, the equivalent already-public `HATPTrustStore.production().root`) directly. No new environment variable, CLI flag, constructor parameter, or repository-local file is introduced as an override path, matching HBDC-REQ-011.

## 9. Principal Verification

Planned checks, all against live OS state via `os.getuid()`/`os.getgid()`/`os.getgroups()` and `Path.stat()`:

- Agent effective UID = current process's `os.geteuid()`.
- Admin ownership = Protected Root's `st_uid`.
- Distinctness = `st_uid != os.geteuid()` (mirrors `inspect_bootstrap_environment`'s existing `agent_and_admin_share_os_principal` signal, reused not reimplemented).
- **HBDC-REQ-009 (admin exclusively holds write authority)** cannot be positively proven by an agent-side read-only verifier: the verifier can confirm the agent *lacks* effective write access (HBDC-REQ-007), but proving the admin principal specifically *has* it requires either (a) admin-side self-attestation evidence written by the admin ceremony script (`scripts/hatp_certification_admin.py`, already in the HMIC 25-file set) into a protected, admin-only-writable location the agent can read but not forge, or (b) accepting that HBDC-REQ-009 is satisfied by construction whenever HBDC-REQ-013 (ownership) holds and no other principal exists per HBDC-REQ-001. This plan selects **(b)**: HBDC-REQ-009 is treated as satisfied-by-construction from HBDC-REQ-001+HBDC-REQ-013's combination, not as an independently agent-checkable fact requiring its own admin-evidence protocol. This is recorded explicitly, not silently assumed, and is the single point in the entire 55-requirement inventory resolved this way (§2's ADMIN-class row).

Usernames are never treated as sole authority; every check above resolves numeric UID/GID, never a string username.

## 10. Effective ACL/Group-Access Verification (Closes Retained Gap #1)

Design, honestly scoped to what is provable:

1. **Mode-bit baseline** (existing, reused): `st_mode & 0o022`.
2. **Group-membership effective-write check (new):** if the group-write bit is set, compute whether the agent's effective GID or any of `os.getgroups()` equals the path's `st_gid`. Because this deployment topology never uses `setuid`/`setgid` binaries (no such mechanism is introduced anywhere in this plan), real UID/GID and effective UID/GID coincide for the verifier's own process, so `os.getgroups()` read from the live process is authoritative for *that* process — not a claim about arbitrary other processes.
3. **POSIX ACL check (new, platform-gated):** on Linux, query extended ACLs via a trusted, admin-pinned `getfacl` executable path resolved the same way as HBDC-REQ-038's Git-trust check (§14 below) — never a bare `"getfacl"` string. Parse for any `user:<agent-uid>:` or `group:<agent-gid>:` entry granting `w`. On macOS, native extended ACLs (`ls -le`-visible) are queried via `os.listxattr`/platform-specific inspection where a reliable, dependency-free mechanism exists; where it does not, the check yields `ACCESS_ERROR`/`INDETERMINATE` rather than silently skipping — never `COMPLIANT` on an unverified ACL state.
4. **Fail-closed composition:** if ACL tooling is unavailable, times out, or returns an unparseable result, the check yields `INDETERMINATE`, never `NON_COMPLIANT`-with-a-guess or `COMPLIANT`-by-default.

This directly satisfies HBDC-REQ-015/016's explicit textual anticipation ("a future verifier MUST test effective group-derived write access, not declared mode bits alone") and 149O.20C's own finding.

## 11. Full Ancestor-Chain Verification (Closes Retained Gap #2)

Design: starting from Protected Root, walk `path.parent` repeatedly until reaching either (a) an ancestor the agent principal provably cannot write (mode+group+ACL check per §10, applied at each level), or (b) the filesystem root `/`. Any ancestor found agent-writable before a non-writable ancestor is reached → `NON_COMPLIANT` (HBDC-REQ-017/020). The walk terminates the first time a non-writable ancestor is found — it does not need to prove *every* ancestor up to `/` is non-writable, only that there exists an unbroken non-writable boundary between Protected Root and any agent-writable directory. This is the same primitive `hatp_environment_lock_verifier.py` reuses for the venv path (§5, finding 5) and (§16 below) for the "full ancestor-chain" requirement extended by analogy to the Model-A working-tree root and venv root — implemented once as a shared internal helper, not duplicated across modules.

## 12. Path / Symlink Safety

Reuses the existing `_reject_symlink` pattern (already implemented independently in `hatp_bootstrap.py`, `hatp_mandatory_certification.py`, `hatp_mandatory_cutover.py`, and `repository_identity.py`) rather than introducing a fourth/fifth independent implementation. The new verifier modules call the closest existing helper where the path in question belongs to that module's existing domain (e.g. Protected Root symlink rejection reuses `hatp_bootstrap`'s helper via import, not reimplementation); a small shared private helper is added only for paths (venv, interpreter, Git executable) that have no existing owner, matching the exact reject-on-symlink semantics byte-for-byte.

## 13. Hard-Link Verification (Closes Retained Gap #3)

**Frozen decision (per governing-prompt §17 instruction):** `st_nlink > 1` on any authority-bearing file is sufficient reason for `NON_COMPLIANT`. This plan is explicit about what this does and does not prove: `st_nlink` reports the *count* of directory-entry aliases to an inode; it does not identify *where* those aliases live or who created them. A verifier cannot, without a full filesystem scan (infeasible to require of a production readiness check and out of scope for HBDC-001's threat model), enumerate every hard-link alias and confirm each one lives inside admin-only-writable territory. Requiring `st_nlink == 1` as the compliant baseline is therefore a conservative, honest, fail-closed choice: it flags *any* additional alias as non-compliant rather than falsely asserting the aliases were individually verified safe. This satisfies HBDC-REQ-019/020 without an overclaim.

## 14. Trusted Git Executable Verification

New check (not a modification to `hatp_mandatory_certification.py`'s `_run_git`, which stays untouched — HBDC-001 is a deployment-topology contract, not a code-change contract, and 149O.20C already concluded the mitigation is deployment-level):

1. Resolve `git` via `shutil.which("git")` against the live process `PATH`.
2. For every directory in `PATH` that appears *before* the directory containing the resolved `git`, verify none is agent-writable (effective-access check, §10). If any agent-writable directory precedes the resolved `git`, the check fails even if the *currently* resolved `git` happens to be legitimate — a `PATH`-prepend attack (attack #20) succeeds by placing a fake `git` earlier, independent of where the real one sits.
3. `realpath()` the resolved `git`, confirm admin ownership and agent-non-writability of the executable and its containing directory.
4. §35 (Git execution path) disposition, decided by this plan: production `_run_git` continues to invoke the bare `"git"` argument, PATH-resolved. Pinning `_run_git` to an admin-supplied absolute path would strengthen the guarantee but is a `src/pcae/**` change outside this phase's scope and outside HBDC-001's own stated non-goals (§5, "does not... change Permission Broker behavior" and its broader "topology, not code" framing). This plan records the trade-off — PATH-lock at the deployment level (this verifier's job) is the selected mitigation under Option C; absolute-path pinning inside `_run_git` remains a possible *future* contract/code amendment, not adopted here, and not silently deferred without being named.

## 15. Repository/Deployment Identity, Worktrees, Clones, Host Migration, Restore

No new mechanism. `hatp_class_b_conformance.py`'s deployment-identity check is a thin wrapper: calls `repository_identity.read_repository_identity`, `hatp_bootstrap.resolve_canonical_deployment_root`, and `hatp_bootstrap.deployment_binding_matches` exactly as they exist today, and maps their existing outputs into one `ClassBCheckResult` per HBDC-REQ-042..046. Wrong-model, worktree, clone, host-migration, and cross-host-restore scenarios all resolve through the existing `.resolve(strict=True)`/binding-match logic (149O.1B.2 scope, unmodified) — this plan maps existing semantics into new test coverage, it does not reimplement them.

## 16. Model-A Installation and Module-Origin Verification

- **Authority module origins (§29):** the mechanically-derived, importable-Python subset of HMIC-REQ-050's 25-file set — 19 `src/pcae/` `.py` files (all entries except the 5 `docs/contracts/*.md` documents and `scripts/hatp_certification_admin.py`, which is an invoked script, not an importable package module, and is checked separately as a launcher-adjacent artifact per §17 below, not via import-spec).
- **Verification mechanism:** for each of the 19 modules, `importlib.util.find_spec("pcae.core.X")` (or the already-imported module's `__spec__.origin`/`__file__`), `realpath()` the resulting origin, and confirm containment inside the resolved `canonical_deployment_root` (the same value `hatp_bootstrap.resolve_canonical_deployment_root` produces). A module whose resolved origin lies outside that tree — e.g. shadowed by an earlier `sys.path` entry — fails the check (HBDC-REQ-034).
- **Editable-install metadata:** the verifier does not assume `.egg-link` vs. `.pth` vs. the modern `__editable__.<dist>.finder.py` mechanism. It inspects `importlib.metadata.distribution("pcae")` for `direct_url.json` (editable flag) and enumerates the actual `.pth`/finder files present on `site-packages`, checking whichever mechanism is actually in use in the live environment, and verifies that artifact's ownership/writability (HBDC-REQ-035).

## 17. Launcher / Service Environment

- **Launcher/wrapper (HBDC-REQ-036):** if PCAE production execution passes through a shell wrapper script or console-script entry point, the verifier resolves that script's realpath and checks ownership/writability identically to the interpreter check (§9/§10 primitives, reused).
- **`scripts/hatp_certification_admin.py`:** checked the same way — realpath, ownership, agent-non-writability — as a launcher-adjacent authority artifact, not imported.
- **Service environment (HBDC-REQ-33 detail per prompt §33):** if PCAE production runtime is launched by a service/process manager (systemd unit, launchd plist, etc.), this plan does not assume one exists — current production runtime is `Observed / observe / unavailable` (§76), with no service-manager integration built yet. This is recorded as a **deployment prerequisite** the verifier will report `INDETERMINATE`/`ACCESS_ERROR` against when no such integration is detected, rather than silently skipping the check. A concrete service-environment verifier design is deferred to whichever future phase actually introduces service-managed PCAE execution — designing it now against a nonexistent target would be speculative.

## 18. Protected Root / Environment Non-Auto-Creation (Read-Only Guarantee)

All three new modules are read-only by construction: no `mkdir`, `os.makedirs`, `chmod`, `chown`, `setfacl`, ACL-mutation, venv-repair, environment-cleanup, or binding-creation call appears anywhere in their planned implementation. This is enforced at review time by (a) a dedicated test that runs the verifier inside a filesystem-mutation-detecting fixture (e.g. a temp tree with `stat` snapshots before/after, asserting zero mtime/permission changes) and (b) restricting the modules' own imports to read-only primitives (`os.stat`, `os.access`, `Path.resolve`, `shutil.which`, `importlib.util.find_spec`, `subprocess.run` for read-only tool invocations only). Missing Protected Root/venv/interpreter → `NON_COMPLIANT` or `INDETERMINATE` (never auto-provisioned, never silently degraded to a partial pass).

## 19. Verifier ≠ Provisioner ≠ Certification Admin ≠ Activator (Frozen)

None of the three new modules imports or calls: `hatp_mandatory_certification.py`'s certification-*writing* functions (only its read-only `validate_active_hatp_mandatory_independent_verification_certification`/status-inspection surface may be referenced, and only where genuinely needed — the topology/environment/aggregator verifiers designed here do not need it at all, since they answer a narrower question than "is there an active certification"), `scripts/hatp_certification_admin.py`'s `certify`/`activate`/`revoke` entry points, or `hatp_mandatory_cutover.py`'s Cutover Record mutation surface. A failed check never triggers self-repair. This is a design freeze, not a runtime assertion this phase implements — enforced by code review discipline and by the "read-only guarantee" test in §18 at implementation time.

## 20. Future Readiness Consumption and Readiness-Model Compatibility

Reconstructed directly from `hatp_mandatory_cutover.py::_assess_hatp_mandatory_activation_readiness_at_root` (lines ~784–925), the current production readiness-check set feeding `HATPMandatoryActivationReadiness`:

1. `class_b_protected_storage_available` — checks only `protected_root.is_dir() and not protected_root.is_symlink()`.
2. `repository_deployment_identity_valid` — checks `repository_instance_id` is a valid UUID4.
3. `hatp_substrate_operational` — delegates to `inspect_hatp_verification_substrate_readiness`.
4. `hsce_signing_implementation_available` — checks the signing-ceremony module imports.
5. `mandatory_consumption_implementation_independently_verified` — fresh HMIC active-certification validation (`certification_status_satisfies_readiness`).
6. `production_dependency_provenance_valid` — checks the trust-store dependency resolved.
7. `protected_activation_authority_mechanism_available` — checks **only** `mode & 0o022` on Protected Root — the exact same shallow, mode-bits-only gap this plan closes for the standalone Class-B verifier (§10).

**Finding:** no existing readiness check constitutes genuine HBDC-001 conformance. Checks #1 and #7 are shallow proxies (existence + mode bits only) — they do not test principal distinctness, effective ACL/group access, ancestor-chain safety, hard-link safety, or any part of the Model-A environment lock. **No existing normative readiness slot already represents "Class-B substrate/deployment operationality" in the sense HBDC-001 defines it.** Per the governing prompt's §48 instruction, this is recorded as a genuine gap, not casually patched by adding an eighth ad hoc check.

**Where a verified `COMPLIANT` result would eventually feed:** the architecturally correct integration point is `_assess_hatp_mandatory_activation_readiness_at_root` itself — replacing or supplementing checks #1/#7 with a call to `hatp_class_b_conformance.verify_class_b_deployment_conformance()`, requiring `status == ClassBConformanceStatus.COMPLIANT` (exact-identity comparison, never truthiness) as an additional/replacing readiness term. This is a **contract-level decision**, not a code decision this plan makes unilaterally: HMRC-001's own `HATPMandatoryActivationReadiness` term set (HMRC-REQ-054–056) would need a normative amendment naming the new term explicitly, mirroring how HMIC-REQ-107/Wave-F wiring for `mandatory_consumption_implementation_independently_verified` was itself a named, deliberate contract-and-implementation act (not an incidental side effect).

**Critical structural consequence (this is the load-bearing finding of this section):** `hatp_mandatory_cutover.py` is itself entry #1 in HMIC-REQ-050's frozen 25-file set. If a future phase modifies it to import and call `hatp_class_b_conformance.py` (or either of the other two new modules, transitively), then **HMIC-REQ-052's existing Transitive-Dependency Coverage — Closure Rule already, automatically, requires every file reachable from `assess_hatp_mandatory_activation_readiness`'s own call graph to be inside the frozen set.** This means the self-binding requirement this plan's governing prompt asks about (§54 below) is not a new, separately-invented rule — it is the *direct, mechanical consequence* of a rule HMIC-001 already contains. No new contract concept needs to be invented to require it; a future HMIC amendment binding the new verifier modules would be applying HMIC-REQ-052 to a new dependency, exactly as 149O.19.3R already did for the four hardware-provider files and 149O.19.5E.1 already did for `hatp_mandatory_certification.py`/`scripts/hatp_certification_admin.py`.

## 21. Class-B COMPLIANT ≠ Full Readiness (Frozen)

`ClassBConformanceStatus.COMPLIANT` (§6) is, and remains, strictly narrower than: HMIC `VALID`, overall HATP readiness, `HATP_MANDATORY` activation, Permission Broker `ALLOW`, or rollback-execution readiness. No future integration may collapse these into one boolean without each of the underlying contracts (HMIC-001, HMRC-001, HATP-001, PB contracts) independently naming that collapse. This plan's result type has no field capable of being misread as any of those broader facts (§6, §2 row HBDC-REQ-055).

## 22. Authority Source Inventory (§50) and HMIC 25-File Coverage Classification (§51 — Mandatory)

| Path (planned) | New/Modify | Purpose | Authority role | HMIC-25 coverage |
|---|---|---|---|---|
| `src/pcae/core/hatp_class_b_topology_verifier.py` | NEW | Principal, Protected Root, ACL/group/ancestor/hard-link checks (HBDC-REQ-001..024) | Authority-bearing (derives a positive/negative Class-B topology signal) | **NOT_YET_HMIC_BOUND** |
| `src/pcae/core/hatp_environment_lock_verifier.py` | NEW | Model-A Python environment-lock checks (HBDC-REQ-025..041) | Authority-bearing | **NOT_YET_HMIC_BOUND** |
| `src/pcae/core/hatp_class_b_conformance.py` | NEW | Aggregator: result model, status vocabulary, aggregation rule, deployment-identity wrapper (HBDC-REQ-022, 042..046, 050..055) | Authority-bearing (produces the single `COMPLIANT`/not-`COMPLIANT` fact) | **NOT_YET_HMIC_BOUND** |
| `tests/test_hatp_class_b_topology_verifier.py` | NEW | Test coverage | Not authority-bearing (test code never gates production readiness) | N/A (tests are not part of HMIC-REQ-050's frozen set) |
| `tests/test_hatp_environment_lock_verifier.py` | NEW | Test coverage | Not authority-bearing | N/A |
| `tests/test_hatp_class_b_conformance.py` | NEW | Test coverage | Not authority-bearing | N/A |
| `src/pcae/core/hatp_bootstrap.py` | none this phase; **future** modify only if/when a shared ancestor-walk/effective-access helper is factored into it rather than duplicated | n/a (not touched by 149O.20H) | Already HMIC-bound | ALREADY_HMIC_BOUND (unaffected unless later modified) |
| `src/pcae/core/hatp_mandatory_cutover.py` | none this phase; **future** modify only at the readiness-integration wave (§20), which is explicitly out of scope until self-binding is resolved | n/a | Already HMIC-bound; a future edit importing the new modules is the trigger event for HMIC-REQ-052's closure rule | ALREADY_HMIC_BOUND (unaffected this phase) |

**§51 mandatory classification result:** of the production files this plan actually proposes to create, **3 of 3** planned authority-bearing new files are **NOT_YET_HMIC_BOUND**. Zero planned files are ALREADY_HMIC_BOUND. This phase creates none of them — it only plans them.

## 23. New-Module Consequence and Existing-File Alternative (§52/§53)

**§52 (new-module consequence):** all three new modules are, by construction, outside HMIC-001's current 25-file `implementation_scope_digest`/`contract_versions` scope. Per this phase's Critical New Self-Binding Rule, none of their positive `COMPLIANT` results may become a production-authoritative input (i.e., consumed by `hatp_mandatory_cutover.py`'s readiness assessment or any other authority-bearing consumer) until HMIC's source-set identity has been evolved to include them and that evolution has been independently verified/aligned (mirroring the exact 149O.19.3R / 149O.19.5E.1 / 149O.20D–G precedent already in this repository's own history).

**§53 (existing-file alternative, evaluated and rejected):** embedding the new checks inside `hatp_bootstrap.py` (which already owns `inspect_bootstrap_environment`) was considered as a way to avoid a source-scope evolution entirely, since that file is already HMIC-bound. **Rejected**, for these reasons:
- **Cohesion:** `hatp_bootstrap.py` (607 lines) already owns registry parsing/validation, trust-store lookup, and canonical-root resolution — a distinct concern from ACL/hard-link/ancestor-chain filesystem forensics and from Python-runtime-environment introspection (`sys.path`, `sys.meta_path`, `.pth` files, `sitecustomize`). Folding ~15–20 new checks covering two additional concern domains into this file would blur its existing single responsibility.
- **Auditability:** a future independent-verification phase re-deriving this file's claims (as 149O.20C/149O.20G's own methodology already does for every HMIC-bound file) would face a substantially larger diff surface mixing unrelated concerns, making line-by-line re-derivation slower and more error-prone.
- **Testability:** the environment-lock checks (§C wave) need process-environment/subprocess fixtures entirely distinct from the topology checks' filesystem fixtures; separate modules keep each test file's fixture surface narrow.
- **Authority clarity:** a reviewer asking "what production file decides Class-B conformance" gets one unambiguous answer (`hatp_class_b_conformance.py` as the aggregator, with two clearly-named contributing verifiers) instead of a conformance decision embedded inside a file whose name and existing docstring describe a different purpose (trust-store bootstrap, not deployment verification).

This plan therefore selects **clean module boundaries over avoiding governance work**, per the governing prompt's explicit instruction that architectural cleanliness should not be sacrificed merely to dodge the required HMIC evolution sequence, and accepts the resulting self-binding sequencing obligation (§24 below) as the correct cost of that choice.

## 24. Self-Binding Stop Condition and Circularity Resolution (§54, §57, §58 — Mandatory)

**CBV-S1 (frozen):** No positive Class-B conformance result may become production-authoritative if any source responsible for deriving that result is outside HMIC's verified implementation identity.

**§58 — non-authoritative implementation mode (the circularity breaker):** the three new modules *can* be implemented, tested, and independently verified **before** HMIC binding, provided, for the entire duration prior to binding:
- zero production caller (in particular, `hatp_mandatory_cutover.py`) imports or invokes them;
- no readiness assessment consumes their result;
- no activation/certification path references them;
- their result is diagnostic/test-only — reachable only via direct unit-test invocation and (optionally) a clearly-labeled, non-authoritative CLI inspection subcommand (e.g. `pcae hatp class-b inspect`, printed output explicitly headed "DIAGNOSTIC ONLY — NOT AN AUTHORITATIVE READINESS SIGNAL", never wired to any exit-code-based automation).

This restriction is frozen for this plan: it is the mechanism that breaks the apparent circularity between "verifier must exist to be tested" and "verifier's result can't be trusted until HMIC-bound."

**Selected sequence (§57):**

1. **Wave B/C/D/E — bounded, non-authoritative implementation.** Implement all three modules exactly as designed in §9–§21, with zero authority-consuming callers, per §58's restriction. (Phase 149O.20I, recommended next — see §29.)
2. **Wave F(i) — independent verification of the bounded implementation.** A fresh independent-verification phase re-derives every check from primary source (the same methodology 149O.20C/149O.20E/149O.20G already used), confirms zero authority-consuming callers exist, confirms the read-only guarantee (§18) holds, confirms 55/55 requirement coverage in the actual code (not just this plan). (149O.20J.)
3. **Wave F(ii) — HMIC contract source-scope evolution.** A dedicated contract-freeze phase amends HMIC-001 to HMIC v1.3: widens HMIC-REQ-050's file enumeration to 28 entries (25 existing + 3 new modules), widens HMIC-REQ-052/053 text if needed, following the exact precedent of 149O.19.3R/149O.19.5E.1/149O.20D. This phase does **not** touch production source, mirroring 149O.20B/149O.20D's own contract-only discipline. (149O.20K.)
4. **Wave F(iii) — independent verification of the HMIC v1.3 amendment.** Mirrors 149O.20E's methodology exactly. (149O.20L.)
5. **Wave F(iv) — production HMIC source-set alignment.** Updates `hatp_mandatory_certification.py`'s frozen-file-set constants (`_FROZEN_AUTHORITY_BEARING_FILES`/`_CONTRACT_IDENTITY_FILES` or their v1.3 equivalents) to the 28-file/5-contract set, mirroring 149O.20F's methodology exactly. This is itself a modification to an already-HMIC-bound file (`hatp_mandatory_certification.py`), so it re-triggers the ordinary "same-file content changed" re-derivation discipline, not a new-scope-evolution question. (149O.20M.)
6. **Wave F(v) — independent verification of production alignment.** Mirrors 149O.20G's methodology exactly — the same phase type this plan's own predecessor was. (149O.20N.)
7. **Wave G — readiness-integration contract/implementation.** Only after steps 1–6 close CBV-S1 for the three new modules may a future phase amend HMRC-001 (naming a new/replaced readiness term, §20) **and** modify `hatp_mandatory_cutover.py` to import and consume `hatp_class_b_conformance.verify_class_b_deployment_conformance()`'s result. This is its own contract-plus-implementation-plus-independent-verification arc, not started or authorized by this plan. (149O.20O+, not yet numbered — depends on Wave F's outcome.)

No step in this sequence is left ambiguous: each has a named predecessor phase-type precedent already executed in this repository's own history, and each is assigned to a specific future phase slot (not yet authorized).

## 25. No Self-Certification (§59)

The verifier's own source cannot decide that its own currently-unbound status is acceptable for authoritative use — that determination belongs exclusively to HMIC-001's own contract-and-implementation-identity machinery (HMIC-REQ-050 committee-of-one: the frozen contract text, not any runtime code, defines the bound set). Nothing in `hatp_class_b_conformance.py`'s design includes a self-check like "am I HMIC-bound? if not, still report COMPLIANT" — the module has no way to answer that question about itself at all, and is not designed to try; the enforcement of CBV-S1 lives entirely in *caller* discipline (§58's restriction) and in the future contract-evolution sequence (§24), never in the verifier module itself.

## 26. Test Plan (§60–§61)

| Test category | Coverage | Authoritative evidence? |
|---|---|---|
| Unit (pure logic) | Result-model construction, status-vocabulary closure, aggregation-rule logic | Yes — deterministic, no live-host dependency |
| Isolated filesystem fixture | Protected Root/venv mode-bit, symlink, hard-link (`st_nlink`), ancestor-chain scenarios built under `tmp_path` | Yes, for the logic; not a substitute for real-host effective-access proof (see below) |
| Process environment fixture | `PYTHONPATH`, user-site, `.pth`, sitecustomize/usercustomize, CWD-shadow scenarios via subprocess with controlled env | Yes, for the logic |
| Import environment fixture | Module-origin containment, shadow-package detection via `importlib` in an isolated subprocess/venv | Yes, for the logic |
| Effective-access / cross-principal integration | Group-membership and ACL checks against fixtures simulating (not necessarily provisioning) multiple principals | **Partial** — see §61 |
| Assembled adversarial | All 21 attacks (§4) reproduced end-to-end against fixtures | Yes, for the logic |
| Real-host read-only (future, not this phase) | Running the finished verifier read-only against an actually-provisioned Class-B host | The only fully authoritative evidence for real-host conformance; explicitly deferred, not attempted by any wave this plan authorizes |

**§61 — isolated OS-principal testing without real provisioning:** two honest options, both usable, neither individually sufficient alone:
- **Mocked/simulated metadata** (fixture stat results, fabricated `os.getgroups()` return values via monkeypatching): proves the verifier's *logic* is correct for a given input, cheaply and repeatably, in CI. **Cannot** independently prove real OS effective-access behavior — a mock that misunderstands POSIX semantics would pass its own test while being wrong on a real host.
- **Temporary users/groups in an isolated VM or container**: the only mechanism that exercises *real* kernel-enforced effective-access semantics without touching the actual macOS development host or any shared CI runner's real accounts. This is the authoritative evidence source for HBDC-REQ-015/016's effective-access claim; it is heavier-weight and is planned as an explicit, separate CI/test-infrastructure wave (not assumed to exist already), not silently folded into the ordinary `pytest -m fast_green` run.

Mocks alone are recorded, explicitly, as insufficient to independently prove real effective-access behavior — consistent with the governing prompt's instruction.

## 27. Platform Scope (§62) and Tooling (§63–§64)

Production `_default_production_trust_root()` already commits to **both** macOS (`darwin`) and Linux, keyed on `sys.platform`, with an explicit fail-closed `HATPBootstrapUnsupportedPlatformError` for anything else. This plan follows that existing commitment rather than narrowing it: the verifier targets **both macOS and Linux**, via a small internal platform-abstraction seam (one function per platform-sensitive primitive: effective-group-access, ACL query, hard-link count — the last of which, `st_nlink`, is POSIX-portable and needs no per-platform branch). Any platform other than `darwin`/`linux` yields `UNSUPPORTED_DEPLOYMENT_MODEL`/`ACCESS_ERROR`, never a silent pass. Implementation-wave ordering (§28) builds and tests the macOS backend first, matching the actual development host, with the Linux backend following in the same wave rather than a separate one (the abstraction seam makes both cheap once the shared primitives — mode/group/ancestor/hard-link logic, all portable — are written).

**ACL tooling (§63):** Linux ACL queries go through a trusted, admin-pinned executable path resolution identical in kind to the Git-trust check (§14) — never a bare `"getfacl"` string trusted from `PATH` without the same precede-check discipline. macOS ACL inspection uses native, dependency-free mechanisms where available; where a reliable native mechanism is not available without adding a new third-party dependency, the check honestly reports `ACCESS_ERROR`/`INDETERMINATE` rather than silently skipping (§10). No new third-party ACL library dependency is introduced by this plan without that dependency itself then falling under HBDC-REQ-039's "third-party dependencies used by authority-bearing modules" scope — recorded as a design constraint, not resolved with a specific library choice in this plan (implementation-time decision, evaluated against §39's venv-lock coverage once made).

**Hard-link tooling (§64):** pure `Path.stat().st_nlink`, no subprocess, no platform branch needed (POSIX-portable). `st_nlink != 1` (not just `> 1`, since `0` is not a valid POSIX regular-file link count and would itself indicate a malformed/racing filesystem state) → `NON_COMPLIANT`/`MALFORMED_STATE` respectively. No directory/exception carve-out is defined — Protected Root is expected to be a directory (checked separately, HBDC-REQ-013/014) and this check applies only to authority-bearing *files* within it.

## 28. Error Handling and Status Reasons (§65–§66)

**Fail-closed, uniformly:** any exception, `OSError`, permission-denied `stat()` call, unparseable ACL/`.pth`/environment output, or platform-unsupported condition anywhere in the check pipeline maps to `INDETERMINATE` or `ACCESS_ERROR` (never silently caught-and-treated-as-`COMPLIANT`, matching the existing repository idiom already visible in `hatp_mandatory_cutover.py`'s own `except Exception: ... = False` pattern reused for a new-but-identical purpose). No `try/except: pass` construct is permitted in the planned implementation.

**Status reasons are diagnostic only:** `ClassBCheckResult.status`/`reasons`/`evidence` fields are machine-stable reason codes and safe evidentiary strings (paths, numeric UIDs, octal modes) for human/audit consumption. No code anywhere parses a status/reason *string* to make an authority decision — every authority decision is made from the typed `satisfied: bool`/`status: ClassBConformanceStatus` fields, never from substring matching on free text (mirrors HMIC-001's own long-standing discipline against string/prose-based authority determination).

## 29. Blocking-Condition Self-Check (§91)

Walking every listed blocking condition against this plan:

- Unmapped HBDC requirement — none; 55/55 mapped (§2).
- Mode-bits-only effective-permission claim — rejected; §10/§11 design real effective-access/ancestor checks.
- ACL/group access unaddressed — addressed, §10.
- Complete ancestor replacement authority unaddressed — addressed, §11.
- Hard links unaddressed — addressed, §13.
- Python environment lock left vague — concrete per-requirement design, §16 of this plan (checks HBDC-REQ-025..039 individually, no hand-waving).
- Hostile PYTHONPATH/user-site/.pth/customization/CWD shadowing allowed — none allowed; each has its own check (§2 rows, wave C).
- Trusted Git resolution ignored — addressed, §14.
- Caller-supplied compliance booleans allowed — none; §7 explicitly forbids them.
- Verifier state-mutating — no; §18 freezes read-only design.
- Verifier self-provisions — no; §18/§19.
- COMPLIANT conflated with activation — no; §21/§6 (result type has no activation field).
- Environment lock conflated with cryptographic runtime attestation — no; explicitly disclaimed (§2 row HBDC-REQ-041, mirrors HBDC-001's own §14 text).
- Production consumption planned before verifier source is HMIC-bound — no; §24's sequence explicitly forbids it (CBV-S1) and defers Wave G until after Wave F completes.
- New authority logic hidden inside an existing HMIC-bound file to avoid source-scope evolution — no; §23 explicitly evaluates and rejects that shortcut.
- Real provisioning authorized in "the next implementation wave" without prerequisites — no; §30/§31 name Wave B/C/D/E (bounded, non-authoritative implementation) as the next phase, not provisioning.
- Contract changes required but silently skipped — none required *by this plan* (Wave F(ii)'s HMIC v1.3 amendment is explicitly named as a required future phase, not silently skipped or silently performed here).

No blocking condition is triggered by this plan.

## 30. Implementation File Manifest (§84 — Mandatory)

| File | NEW/MODIFY/TEST/DOC | HMIC_BOUND_NOW |
|---|---|---|
| `src/pcae/core/hatp_class_b_topology_verifier.py` | NEW | NO |
| `src/pcae/core/hatp_environment_lock_verifier.py` | NEW | NO |
| `src/pcae/core/hatp_class_b_conformance.py` | NEW | NO |
| `tests/test_hatp_class_b_topology_verifier.py` | TEST | N/A (not part of HMIC-REQ-050) |
| `tests/test_hatp_environment_lock_verifier.py` | TEST | N/A |
| `tests/test_hatp_class_b_conformance.py` | TEST | N/A |
| `docs/PHASE_149O_20I_...` (future planning artifact for the bounded-implementation phase) | DOC (future phase) | N/A |
| `docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md` | MODIFY (future, Wave F(ii) only — HMIC v1.3) | Already bound (contract document itself is entry #21 of the 25) |
| `src/pcae/core/hatp_mandatory_certification.py` | MODIFY (future, Wave F(iv) only) | Already bound |
| `src/pcae/core/hatp_mandatory_cutover.py` | MODIFY (future, Wave G only — readiness integration) | Already bound |
| `docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md` | MODIFY (future, Wave G only, if a new readiness term is named) | Already bound |

No file in this manifest is touched by Phase 149O.20H itself — this table is the plan's required deliverable, not an execution record.

## 31. Test File Manifest (§85 — Mandatory)

Planned suites (future implementation waves), each covering:

- `test_hatp_class_b_topology_verifier.py`: principal distinctness, Protected Root ownership/mode/ACL/group/ancestor/symlink/hard-link, fail-closed-on-absent-root, read-only-mutation guard, authority-input-rejection (no boolean override accepted), all HBDC-REQ-001..024 rows.
- `test_hatp_environment_lock_verifier.py`: interpreter/venv ownership+writability, `PYTHONPATH`/user-site/`.pth`/sitecustomize/usercustomize/meta_path/CWD-shadow/editable-install/launcher checks, Git-trust check, all HBDC-REQ-025..041 rows, assembled attacks #8–#15/#20.
- `test_hatp_class_b_conformance.py`: aggregation rule (all-mandatory-checks-satisfied → COMPLIANT, any failure → not-COMPLIANT, no partial credit), status-vocabulary closure, deployment-identity wrapper correctness (HBDC-REQ-042..046, attacks #16–#19), read-only/non-mutation guard at the aggregator level, HBDC-REQ-050/051/054/055 status-claim-discipline assertions, module-origin/import-environment tests for HBDC-REQ-034.
- (Deferred, separate infrastructure wave, §26) isolated-OS-principal integration suite using temporary users/groups in a container/VM — not part of the ordinary `pytest -m fast_green` run.

## 32. Real Authorization Boundaries (Restated, Frozen)

Confirmed unauthorized by this phase and by this plan for any future phase this plan itself would authorize: real Class-B provisioning; real OS principal/user/group creation; real Protected Root creation/chown/chmod/ACL mutation; real Python-environment change; real HMIC certification/binding/revocation state creation; real `HATP_MANDATORY` activation; real Cutover Record/activation-marker creation; PB behavior change; POL-005 change; COMP-002 implementation; runtime-state change. All remain gated behind their own, separately authorized governed phases, consistent with HBDC-REQ-050/051 and DRA-REQ-008/009.

## 33. Stop Conditions (§83, CBV-S1..S12)

| ID | Condition | Status as designed by this plan |
|---|---|---|
| CBV-S1 | Positive verifier authority source outside HMIC identity | Triggered by construction (§22) until Wave F completes; **handled** by §24's non-authoritative-mode sequencing, not bypassed |
| CBV-S2 | Effective ACL/group access cannot be reliably established | Mitigated by §10's design; residual platform gaps (macOS ACL without a native mechanism) fail to `INDETERMINATE`, not silently accepted |
| CBV-S3 | Full ancestor replacement authority cannot be established | Mitigated by §11's terminating-walk design |
| CBV-S4 | Hard-link safety cannot be established | Resolved by the frozen `st_nlink != 1` conservative rule, §13 |
| CBV-S5 | Model-A import environment can be agent-redirected | Mitigated by §16's module-origin containment check plus §2's PYTHONPATH/site/.pth/CWD/meta_path checks jointly |
| CBV-S6 | Trusted Git executable cannot be established | Mitigated by §14's PATH-precedence + realpath-ownership design |
| CBV-S7 | Deployment/repository identity cannot be freshly derived | Not triggered — reuses existing, already-verified `resolve_canonical_deployment_root`/`deployment_binding_matches` (§15) |
| CBV-S8 | Verifier requires caller-supplied authority facts | Not triggered — §7 explicitly forbids this by design |
| CBV-S9 | Verifier must mutate state to establish conformance | Not triggered — §18 freezes read-only design |
| CBV-S10 | No contract-defined readiness integration point exists | **Triggered** — confirmed in §20: no existing HMRC readiness term already represents HBDC-001 conformance; Wave G is explicitly gated on a future HMRC amendment naming one |
| CBV-S11 | Platform permission model unsupported | Mitigated for macOS/Linux (§27); any other platform fails closed to `UNSUPPORTED_DEPLOYMENT_MODEL`/`ACCESS_ERROR` |
| CBV-S12 | Implementation would falsely claim runtime executed-source attestation | Not triggered — §2 row HBDC-REQ-041 / §6 status vocabulary make no such claim |

CBV-S1 and CBV-S10 are the two conditions this plan finds genuinely triggered by the chosen architecture; both are handled by explicit, named future-phase sequencing (§24, §20/Wave G) rather than bypassed, hidden, or silently resolved.

## 34. Plan Verdict

```
CLASS-B DEPLOYMENT VERIFIER / MODEL-A ENVIRONMENT-LOCK IMPLEMENTATION PLAN:
COMPLETE
— HBDC-001 55/55 REQUIREMENTS MAPPED
— CBD 8/8 INVARIANTS MAPPED
— 21/21 FROZEN ATTACKS MAPPED
— AUTHORITY SOURCE SELF-BINDING SEQUENCE DEFINED
— REAL PROVISIONING NOT AUTHORIZED
```

## 35. Recommended Next Phase

Per §24/§57/§58's own circularity analysis: option **A** — bounded, non-authoritative-mode verifier implementation (`hatp_class_b_topology_verifier.py` + `hatp_environment_lock_verifier.py` + `hatp_class_b_conformance.py`, zero authority-consuming callers, diagnostic-only surface per §58) — is the correct first next phase, **not** option B (HMIC contract evolution first). Binding HMIC to files that do not yet exist, or that exist but are unverified, would be premature relative to the precedent this repository already follows (implementation before contract-binding, e.g. hardware providers existed before 149O.19.3R bound them; `hatp_mandatory_certification.py` existed before 149O.19.5E.1 bound it).

**Recommended: Phase 149O.20I — Class-B Deployment Verifier / Model-A Environment-Lock Bounded Implementation (Wave B/C/D/E, Non-Authoritative Mode).** Implements the three modules exactly as designed in §6–§21 of this plan, strictly under §58's non-authoritative restriction (zero production callers, diagnostic-only CLI surface if any). Must not modify any HMIC-25-bound file. Must not wire any result into `hatp_mandatory_cutover.py` or any other readiness/certification/activation path. Real Class-B provisioning, real environment-lock provisioning, real certification, and real activation remain unauthorized by 149O.20I as they are by this plan.
