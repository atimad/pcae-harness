# Phase 149O.1E — HATP Repository Identity + Trust-Store Foundation Implementation

## 0. Baseline

- **Repository:** `~/repos/pcae-harness`, branch `main`, working tree clean at
  phase start, `origin/main..HEAD` = 0.
- **Latest completed phase:** 149O.1D — Human Approval Trusted Provenance
  Implementation Plan (commit `d4bb5f40`, pushed). Verdict: `HATP-001
  IMPLEMENTATION PLAN COMPLETE — READY FOR BOUNDED IMPLEMENTATION`.
- **Frozen contract:** `docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md`,
  `HATP-001 v1.0`, `FROZEN`. `HATP-REQ-001`..`HATP-REQ-117`, 117 unique
  requirements. **Byte-unchanged by this phase** (verified: `git diff
  --name-only HEAD -- docs/contracts/` is empty).
- **This phase's scope:** Wave 1 (Repository Identity) + Wave 2 (Protected
  Trust Store / Authority Registry, read-only substrate) of the 149O.1D
  implementation plan, exactly. Waves 3-7 are not implemented.
- **Open rollback-evidence findings, reconfirmed OPEN, unaffected by this
  phase:** B-149O-1, B-149O-2, B-149O-3, B-149O-4.
- **Runtime state, unaffected by this phase:** `Observed` / `observe` /
  `unavailable` (confirmed via `pcae runtime inspect`).

## 1. Wave 1 Requirement Coverage (Repository Identity, subsystem A)

Implemented, per 149O.1D plan §4.2 Wave-1 assignment:

`HATP-REQ-046`..`HATP-REQ-051`, `HATP-REQ-107` (owner A); scaffolding
contribution to `HATP-REQ-013`.

- **Module:** `src/pcae/core/repository_identity.py` — a general PCAE core
  facility (HATP-REQ-107), independent of HATP/RAE/Permission-Broker
  (no such import anywhere in the module).
- **Model:** `RepositoryIdentity(schema_version=1, repository_instance_id:
  <UUID4 str>, created_at: <ISO-8601 UTC>)`. Closed field set — unrecognized
  fields rejected (`RepositoryIdentityMalformedError`).
- **Generation:** `uuid.uuid4()` (stdlib, no new dependency), generated once
  at first `ensure_repository_identity()` call (invoked from `pcae init`).
  Not derived from path, remote URL, or HEAD (HATP-REQ-047).
- **Persistence:** `.pcae/repository-identity.json`, atomic temp-file +
  `os.replace` write (mirrors `cltr/persistence.py::_write_atomic`), with an
  explicit symlink-position rejection before every read and write
  (`RepositoryIdentitySymlinkError`).
- **Validation:** strict — schema version, UUID4 format, timezone-aware
  ISO-8601 timestamp (via a `_parse_iso_timestamp` deliberately duplicated
  from `rollback_approval_evidence.py`'s own fail-closed parser, per
  149O.1D plan §5.13/§39, rather than imported — this module has zero
  upstream imports from RAE). Unknown/extra fields rejected.
- **Missing vs. malformed:** `read_repository_identity()` returns `None`
  only when the file is genuinely absent; a present-but-invalid file raises
  `RepositoryIdentityMalformedError` and is never auto-regenerated
  (`ensure_repository_identity()` propagates the same error rather than
  overwriting it).
- **Init integration:** `pcae init` (`commands/init.py::run_init`) calls
  `ensure_repository_identity(root)` after the existing `INIT_TEMPLATES`
  write (added alongside, not inside, matching 149O.1D plan §11's guidance);
  idempotent on repeat `pcae init` calls; a malformed identity causes `pcae
  init` to print an explicit error and return exit code 1 rather than
  silently continuing.
- **`.pcae/.gitignore`:** added a `repository-identity.json` line to both
  the real repository file and the `INIT_TEMPLATES` copy used by fresh
  `pcae init` runs elsewhere — narrow addition only, no broad/destructive
  pattern.
- **Worktree behavior:** verified with a real `git worktree add` in
  `tests/test_repository_identity.py::test_worktree_receives_distinct_repository_identity`
  — each worktree has its own physical `.pcae/` directory (worktrees share
  only Git's internal object database, not ordinary working-tree files), so
  a repository-local, cwd-relative identity file is naturally per-worktree
  distinct without any special-case code.
- **Path move:** verified (`test_path_move_preserves_identity`) — renaming
  the containing directory preserves the identity file and its content
  unchanged.
- **Copy/clone:** verified (`test_full_directory_copy_confers_no_authority_by_itself`)
  — this module has no authority concept to leak; a copied identity file
  is just a second copy of a non-authoritative identifier.
- **Manual mutation:** verified (`test_manual_mutation_is_syntactically_validated_only`)
  — a hand-edited, syntactically valid new UUID4 is accepted as the local
  identity (format validation only); this module makes no authority claim
  either way (Layer 2 in `hatp_bootstrap.py` is what would then fail to
  match).
- **No caller trust override:** verified — neither `read_repository_identity`
  nor `ensure_repository_identity` accepts a `trusted_id`-shaped parameter.

## 2. Wave 2 Requirement Coverage (Protected Trust Store, subsystems C/D read-only)

Implemented, per 149O.1D plan §4.2 Wave-2 assignment:

`HATP-REQ-006` (registry-side terms), `HATP-REQ-030`..`HATP-REQ-035`,
`HATP-REQ-036`..`HATP-REQ-042`, `HATP-REQ-043`..`HATP-REQ-045`,
`HATP-REQ-052`..`HATP-REQ-066`, `HATP-REQ-086`..`HATP-REQ-089`.

- **Module:** `src/pcae/core/hatp_bootstrap.py`. Imports only
  `repository_identity.py` (A → C dependency direction, 149O.1D plan §6);
  zero imports of `rollback_approval_evidence.py`, `permission_broker*.py`,
  `agent.py`, or `commands/agent.py` (asserted by
  `tests/test_hatp_bootstrap_foundation.py::test_no_hatp_rae_permission_broker_or_agent_imports`).
- **Models:** `PrincipalRecord`, `SignerRecord`, `AuthorityRecord`,
  `DeploymentBinding` — closed field sets, `status ∈ {active, revoked}`,
  `revoked_at` required iff `status == "revoked"` and forbidden otherwise,
  timestamps parsed via the same fail-closed parser convention as Wave 1.
- **Registry format:** single JSON document, `registry_version` (unknown
  version rejected, no best-effort parse), `principals`/`signers`/
  `deployment_bindings`/`authorities` arrays. Unknown top-level or per-record
  fields rejected. Duplicate keys within any array (same `principal_id`,
  `signer_key_id`, `repository_id`, or `(principal_id, repository_id)` pair)
  raise `HATPTrustStoreMalformedError` — never resolved by file order or
  mtime (HATP-REQ item covering duplicate enrollment ambiguity).
- **Trust-store location (HATP-REQ-030-032):** `HATPTrustStore.production()`
  resolves to `~/.pcae-hatp/trust-store/registry.json` — outside
  `repo/.pcae/**`, per 149O.1B.1 §12's explicit prohibition. `production()`
  takes **no** path argument. Test code instantiates `HATPTrustStore(
  _test_only_root=...)` directly — a constructor parameter never reachable
  through `.production()`, the CLI, or any config file.
- **No caller/env/CLI override (HATP-REQ-034/035):** no environment variable
  is read anywhere in this module; verified by
  `test_production_ignores_environment_overrides`, which sets four
  plausible override variable names and confirms no effect. No `pcae`
  command in this phase exposes a trust-store path flag — there is no
  admin CLI at all yet (deferred to a later wave, per 149O.1D plan §14/§71-72).
- **No mutation surface (HATP-REQ-036-042):** `HATPTrustStore` exposes only
  five read methods (`load_repository_enrollment`, `lookup_principal`,
  `lookup_signer`, `lookup_authority`, `signer_revoked`) plus
  `resolve_deployment_authorization`/`environment_status`. No `enroll`,
  `grant`, `revoke`, `rotate`, `mutate`, `write`, or `save` method exists
  (asserted by `test_no_agent_facing_mutation_methods_exist`).
- **Canonical deployment root (HATP-REQ-053):** `resolve_canonical_deployment_root()`
  — absolute path, `os.path.normpath`, then `Path.resolve(strict=True)`.
  Verified to collapse a symlinked alias to the same canonical string as
  its target.
- **Copy/clone/theft defense (HATP-REQ-057-063):**
  `resolve_deployment_authorization(repository_id, canonical_deployment_root)`
  requires an exact match on **both** Layer 1 and Layer 2, plus
  `status == "active"`. Verified: same-ID-wrong-root → `None`
  (`test_same_id_wrong_root_is_unauthorized`); full-copy attack → `None`
  (`test_full_copy_attack_no_matching_deployment`); revoked binding never
  matches even at the correct root (`test_revoked_binding_never_matches`).
- **Bootstrap environment readiness (HATP-REQ-026-029, HATP-REQ-090-093):**
  `inspect_bootstrap_environment()` — POSIX-only in this phase (non-POSIX
  fails closed as `UNAVAILABLE`, never silently `READY`); checks symlink
  substitution of the store root, group/other-writable mode bits,
  world-writable or owner-mismatched parent directory, and — unconditionally
  — whether the store-owning UID equals the current process's UID. The last
  check cannot be defeated by any file permission this process itself
  controls (verified across four permission modes in
  `test_same_user_environment_can_never_report_ready`), which is exactly
  this repository's actual, current, confirmed-NOT-READY deployment shape
  (`test_current_repository_deployment_is_not_ready`).
- **Signer/authority revocation (HATP-REQ-086-089):** consumption-time
  lookup only — `signer_revoked()` and `lookup_authority()` read current
  registry state on every call; no proof-creation-time caching exists
  because no proof concept exists yet in this phase.

## 3. Explicitly Not Implemented (Waves 3-7)

- HATP proof schema/models, canonical serialization (Wave 3) — not present;
  no `HumanApprovalProvenanceProof` type exists anywhere in this diff.
- Proof verification engine, `verify_hatp_proof` (Wave 4) — not present.
- Real hardware provider (FIDO2/PIV), human-presence signer, admin/approval
  CLI (Wave 5) — not present; no new dependency added (`pyproject.toml`
  unchanged).
- RAE integration, `approval_present` derivation change (Wave 6) — not
  present; `rollback_approval_evidence.py` has zero diff.
- Class-B OS deployment provisioning, AG3/AG5 Permission Broker wiring
  (Wave 7) — not present; no OS user/group/ACL/sudoers change of any kind.

## 4. F1 / F2 Disposition (carried forward unchanged)

- **F-149O.1C-1** (proof payload closed-schema gap): still assigned to the
  future proof-schema wave (Wave 3). This phase implements no proof schema
  at all, so there is nothing to (mis)apply the closed-schema decision to
  yet; disposition unchanged from 149O.1D.
- **F-149O.1C-2** (`HATP-REQ-116` self-count editorial gap): retained
  editorial observation; this phase's own code and tests use the
  independently re-verified `117`-requirement span, never `116`. HATP-001
  is not edited.

## 5. B-149O Status

`B-149O-1`, `B-149O-2`, `B-149O-3`, `B-149O-4` remain **OPEN**. Reconfirmed
by rerunning
`tests/test_phase_149o_rollback_approval_evidence_canonical_provenance_hardening_independent_verification.py`
unmodified: the same 4 tests that failed (documenting the open findings)
before this phase still fail identically after it — this phase's diff does
not touch `rollback_approval_evidence.py` at all, so no behavior in that
module could have changed.

## 6. Production Diff Classification

| File | Class | Purpose |
|---|---|---|
| `src/pcae/core/repository_identity.py` (new) | CRI | Wave 1: identity model, generation, persistence, validation |
| `src/pcae/core/hatp_bootstrap.py` (new) | TRUST_STORE / DEPLOYMENT_BINDING / OS_SECURITY_CHECK | Wave 2: registry models, lookups, canonical-root resolution, environment readiness |
| `src/pcae/commands/init.py` | CRI_INIT | wire `ensure_repository_identity()` into `pcae init` |
| `src/pcae/core/templates.py` | CRI_GITIGNORE | add `repository-identity.json` to the fresh-init `.pcae/.gitignore` template |
| `.pcae/.gitignore` | CRI_GITIGNORE | same addition to this repository's own real file |
| `tests/conftest.py` | TEST_SUPPORT | register the two new deterministic test modules in `FAST_GREEN_MODULES` |

No unrelated hunks. `docs/contracts/**`, `rollback_approval_evidence.py`,
`permission_broker.py`, `permission_broker_foundation.py`,
`mutation_permission.py`, `agent.py`, and `commands/agent.py` all have zero
diff (mechanically verified by
`tests/test_phase_149o_1e_hatp_repository_identity_trust_store_foundation.py`).

## 7. Tests

- `tests/test_repository_identity.py` — 14 tests, Wave 1 matrix (create,
  idempotent ensure, malformed/missing/unknown-version/unrecognized-field/
  non-UUID4/naive-timestamp rejection, symlink defense, path-move, full-copy
  no-authority, manual mutation, no-trust-override signature, worktree
  distinct identity via a real `git worktree add`).
- `tests/test_hatp_bootstrap_foundation.py` — 26 tests, Wave 2 matrix
  (missing/malformed/unknown-version/unrecognized-field/duplicate-record
  rejection, unknown repository/signer/principal, revoked signer, principal-
  and repository-scope mismatch, same-ID-wrong-root and full-copy attacks,
  revoked binding never matches, canonical-root symlink collapse, same-user/
  group-writable/world-writable-parent/symlinked-root/missing-store
  environment classification, registry-file symlink substitution, no-path-
  argument production constructor, no environment-variable override, no
  mutation methods, no forbidden imports).
- `tests/test_phase_149o_1e_hatp_repository_identity_trust_store_foundation.py`
  — 11 tests, cross-cutting adversarial/governance checks (no activation-
  gate or `approval_present` symbol exists yet; identity alone grants
  nothing; trust store alone without a matching ID grants nothing; this
  repository's live deployment is NOT READY; no permission mode this
  process controls can force READY; contract/RAE/Permission-Broker/agent
  byte-diff checks; only-expected-files diff check; runtime state
  unaffected).
- Both new unit-test modules added to `tests/conftest.py`'s
  `FAST_GREEN_MODULES` (deterministic, hardware- and environment-
  independent, per 149O.1D plan §58).

All new/changed tests pass. Pre-existing suites rerun unmodified and
unaffected:

- `tests/test_phase_149o_1c_human_approval_trusted_provenance_contract_independent_verification.py`
  — passes (contract byte-unchanged).
- `tests/test_phase_149o_1d_human_approval_trusted_provenance_implementation_plan.py`
  — passes once this phase's own changes are committed (its
  `test_no_src_pcae_files_modified_this_phase` diffs `git diff HEAD`, which
  is empty only against a clean working tree — it is a mid-phase working-
  tree artifact, not a regression; verified clean post-commit).
- `tests/test_phase_149o_rollback_approval_evidence_canonical_provenance_hardening_independent_verification.py`
  — 4 pre-existing failures (B-149O-1..4) reproduced identically before and
  after this phase's changes (`git stash` A/B comparison); 13 passes
  unaffected.
- Permission Broker suites (`test_permission_broker*.py`,
  `test_phase_148*permission_broker*.py`) and RAE suites
  (`test_rollback_approval_evidence_*.py`, `test_phase_149j/149m/149n*.py`)
  — 632 passed, 0 failed.
- `python -m pytest -m fast_green -n auto -q`: **4431 passed** (entering
  baseline `4391` + 40 new Wave-1/2 tests newly registered in
  `FAST_GREEN_MODULES`; a pre-registration run reproduced the unmodified
  `4391`-test baseline exactly, with no flake, confirming this phase
  introduces no regression in any pre-existing fast-green test).

## 8. Implementation Verdict

```
HATP WAVE 1 + WAVE 2 IMPLEMENTED
— FOUNDATION READY FOR INDEPENDENT VERIFICATION
```

## 9. Foundation Readiness (explicit, not to be conflated with production readiness)

```
HATP CONTRACT:                     FROZEN + VERIFIED (unchanged, byte-identical)
HATP-001 requirement count:        117 (independently re-verified, unchanged)
Wave 1 repository identity:        IMPLEMENTED
Wave 2 bootstrap/trust-store:       IMPLEMENTED (read-only substrate)
Proof schema/models:                NOT IMPLEMENTED
Canonical proof serialization:      NOT IMPLEMENTED
Proof verifier:                     NOT IMPLEMENTED
Real hardware provider:             NOT IMPLEMENTED
Class-B OS deployment:              NOT PROVISIONED
RAE / HATP integration:             NOT IMPLEMENTED
AG3 / AG5:                          UNWIRED
HATP production activation:        NOT READY
```

No production HATP proof can become trusted from this phase's state alone.
No new code causes `approval_present=True` anywhere; the symbol does not
exist in either new module. No RAE production integration was implemented.
`B-149O-1` through `B-149O-4` remain OPEN. No AG3 or AG5 Permission Broker
integration was implemented. No rollback execution behavior changed.
RAE-001 v1.0, RWMPC-001 v1.0, PBPC-001 v1.2, PBPA-001 v1.0, CHGR-001 remain
unchanged. IWC confirmation remains distinct from approval. AESIC/AEM
remain disclosure-only. No illegal CHGR/TAM composition was introduced. No
POL-001..012 meaning was changed; no POL-013+ was added. TK1/TK2/TK3 remain
deferred. No Runtime Enforcement behavior changed. No Prompt Generation,
Prompt Dispatch, or agent-invocation capability was implemented. Runtime
remains `Observed`, maximum capability remains `observe`, execution
availability remains `unavailable`. No real FIDO2 or PIV provider was
implemented. No hardware dependency was added. No human-presence signer was
implemented. No Class-B OS user/security boundary was provisioned.

## 10. Recommended Next Phase

```
149O.1F — HATP Repository Identity + Trust-Store Foundation Independent Verification
```

The independent verifier should attack, at minimum: repository identity
creation/idempotency/malformed handling; worktree identity isolation under
additional worktree topologies; same-ID-wrong-root and full-copy rejection
under adversarial registry construction; trust-store path authority
(attempt to find any caller-reachable override this phase's own tests did
not enumerate); agent-writable-parent and symlink-substitution edge cases
beyond this phase's fixtures; duplicate/ambiguous-enrollment handling; and
a fresh, independent re-derivation of the Wave-1/2 requirement coverage
claimed at §1-§2 above, per 149O.1D plan §142's own recommendation not to
proceed directly to Wave 3 before this foundation is independently
attacked.
