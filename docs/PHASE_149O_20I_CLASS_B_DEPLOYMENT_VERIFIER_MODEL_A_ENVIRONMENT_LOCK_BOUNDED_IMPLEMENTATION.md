# Phase 149O.20I — Class-B Deployment Verifier / Model-A Environment-Lock Bounded Implementation

## 0. Phase Identity and Type

**Phase:** 149O.20I
**Type:** BOUNDED NON-AUTHORITATIVE IMPLEMENTATION — exactly three new `src/pcae/core/` modules plus their test suites. No existing HMIC-25-bound source file modified. No contract change. No real provisioning, certification, or activation. No PB/POL-005/COMP-002 change. No runtime state change.
**Basis:** HBDC-001 v1.0 (`docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`), HMIC-001 v1.2 (`docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`), and `docs/PHASE_149O_20H_CLASS_B_DEPLOYMENT_VERIFIER_MODEL_A_ENVIRONMENT_LOCK_IMPLEMENTATION_PLAN.md` (149O.20H) §6–§28, which this phase implements exactly, without deviation, per §58's non-authoritative-mode circularity breaker.
**Pre-phase HEAD:** `744f9c8e` (Phase 149O.20H: sync canonical report staging header and phase-completion metadata).

## 1. Baseline (Confirmed at Phase Entry)

- Repo clean, `origin/main..HEAD` = 0, `pcae health` healthy, `pcae check` passed, `pcae status coherence` coherent, `pcae push check` clean (nothing_to_push), `pcae runtime inspect` Observed/observe/unavailable, `pcae notify status` telegram configured/enabled/ready.
- 149O.20H COMPLETE and reconciled (`pcae phase-report reconcile --phase-id 149O.20H` → reconciled, 2 promoted generations, marker `already_dispatched`).
- 149O.20H's plan: 55/55 HBDC-REQ mapped, 8/8 CBD invariants mapped, 21/21 frozen attacks mapped; three planned modules NOT_YET_HMIC_BOUND; CBV-S1 and CBV-S10 triggered-but-sequenced, not closed; recommended next phase exactly this one (149O.20I).
- Class-B: CONTRACT VERIFIED — NOT PROVISIONED. HMIC-001 v1.2, 25/25 file + 5/5 contract identity independently verified through 149O.20G. HATP production NOT READY. Runtime Observed/observe/unavailable.

## 2. Plan Traceability

This phase implements 149O.20H §6–§21 exactly:

- **Result model / status vocabulary (§6)** → `ClassBConformanceStatus`, `ClassBCheckResult`, `ClassBDeploymentVerificationResult` in `hatp_class_b_topology_verifier.py`, imported (not duplicated) by the other two modules.
- **Public API, no caller-supplied authority (§7)** → `verify_class_b_topology_conformance()` and `verify_environment_lock_conformance()` accept zero parameters; `verify_class_b_deployment_conformance(root: Optional[HarnessPath] = None)` accepts only a neutral root locator.
- **Protected Root resolution, no new override (§8)** → topology verifier imports `hatp_bootstrap._default_production_trust_root()` directly; no override parameter exists anywhere in the call chain.
- **Principal verification (§9)** → live `os.geteuid()`/`os.getgroups()` only; HBDC-REQ-009 recorded as satisfied-by-construction (plan's selected disposition (b), not independently re-derived).
- **Effective ACL/group-access verification (§10)** → `_effective_write_access` (mode → group-membership → platform-gated ACL, fail-closed to `INDETERMINATE` on unavailable tooling).
- **Full ancestor-chain verification (§11)** → `_ancestor_chain_safe`, a single shared helper reused by both topology and environment-lock checks (venv path), matching §11's explicit "implemented once" instruction.
- **Symlink safety (§12)** → topology verifier reuses `hatp_bootstrap._reject_symlink` for Protected-Root-domain paths; a local helper is used only for paths with no existing owner (venv, interpreter, Git executable), matching exact reject-on-symlink semantics.
- **Hard-link verification (§13)** → `_hard_link_safe`: frozen `st_nlink != 1` rule, `st_nlink == 0` distinguished as malformed state.
- **Trusted Git executable verification (§14)** → `_resolve_trusted_executable`, PATH-precedence walk + realpath ownership check; `hatp_mandatory_certification._run_git` itself is untouched, matching §14's explicit disposition.
- **Repository/deployment identity (§15)** → `hatp_class_b_conformance._check_deployment_identity` is a thin wrapper over the unmodified `resolve_canonical_deployment_root` / `read_repository_identity` / `deployment_binding_matches`; no reimplementation.
- **Model-A / module-origin verification (§16)** → `_check_module_origin_containment` walks the 19-file `src/pcae/`-relative authority-module set (reproduced as a literal, not imported from the certification module, per §23's rejected-alternative reasoning) and confirms origin containment via `importlib.util.find_spec`.
- **Launcher / service environment (§17)** → best-effort `shutil.which("pcae")` check; absent launcher yields `NON_COMPLIANT`, not a silent skip.
- **Read-only guarantee (§18)** → no `mkdir`/`chmod`/`chown`/ACL-mutation/write call anywhere in the three modules; verified by AST self-check (`_check_read_only_guarantee`) and by dedicated read-only-mutation-guard tests (fixture stat-snapshot equality before/after).
- **Verifier ≠ provisioner ≠ admin ≠ activator (§19)** → none of the three modules imports `hatp_mandatory_certification`'s write surface, `scripts/hatp_certification_admin.py`'s ceremony entry points, or `hatp_mandatory_cutover.py`'s Cutover Record mutation surface.
- **Future readiness consumption (§20)** → explicitly not performed this phase; no eighth readiness check added, no HMRC term invented.
- **COMPLIANT ≠ full readiness (§21)** → result type carries no field interpretable as HMIC `VALID`, HATP readiness, activation, PB `ALLOW`, or rollback readiness.

## 3. File Allowlist (Exact, No Additions)

| File | Status |
|---|---|
| `src/pcae/core/hatp_class_b_topology_verifier.py` | NEW |
| `src/pcae/core/hatp_environment_lock_verifier.py` | NEW |
| `src/pcae/core/hatp_class_b_conformance.py` | NEW |
| `tests/test_phase_149o_20i_hatp_class_b_topology_verifier.py` | NEW (test) |
| `tests/test_phase_149o_20i_hatp_environment_lock_verifier.py` | NEW (test) |
| `tests/test_phase_149o_20i_hatp_class_b_conformance.py` | NEW (test) |
| `docs/PHASE_149O_20I_CLASS_B_DEPLOYMENT_VERIFIER_MODEL_A_ENVIRONMENT_LOCK_BOUNDED_IMPLEMENTATION.md` | NEW (doc, this file) |

No existing production, script, or contract file is present in this list. `git status --porcelain` at phase exit shows exactly these seven new, untracked paths and nothing else, confirmed mechanically (see §12).

## 4. Non-Authoritative Wall (CBV-S1)

The three new modules are, by construction, outside HMIC-001's current 19-file `src/pcae/`-relative frozen scope (25 total including contracts and the admin script) — mechanically confirmed: `"core/hatp_class_b_topology_verifier.py"`, `"core/hatp_environment_lock_verifier.py"`, and `"core/hatp_class_b_conformance.py"` do not appear in `hatp_mandatory_certification._FROZEN_SRC_PCAE_RELATIVE_FILES` (still exactly 19 entries, unchanged this phase).

A repository-wide search (`tests/test_phase_149o_20i_hatp_class_b_conformance.py::test_zero_authority_callers_across_src_pcae`, plus an ad hoc `grep -rln` sweep run manually during this phase) confirms **zero** files under `src/pcae/**` outside the three-module island import or reference any of the three new module names. `hatp_mandatory_cutover.py`, `hatp_mandatory_certification.py`, `hatp_bootstrap.py`, `repository_identity.py`, and `scripts/hatp_certification_admin.py` are confirmed byte-unchanged (`git status --porcelain -- <path>` empty for each, asserted by `test_hmic_bound_files_are_byte_unchanged_this_phase`).

`COMPLIANT` from any of the three modules' public API is diagnostic only, reachable solely by direct test invocation. No CLI subcommand was added (149O.20H §58 offered one as optional; this phase does not add it, to keep the change surface to exactly the three modules the governing prompt authorizes and to avoid any new `commands/`/`cli.py` diff that would itself require HMIC-scope discussion).

## 5. Result/Status Model

```
ClassBConformanceStatus(str, Enum):
    COMPLIANT, NON_COMPLIANT, INDETERMINATE, ACCESS_ERROR, MALFORMED_STATE, UNSUPPORTED_DEPLOYMENT_MODEL

ClassBCheckResult(frozen dataclass):
    check_id: str, satisfied: bool, status: str, evidence: tuple[str, ...]

ClassBDeploymentVerificationResult(frozen dataclass):
    status: ClassBConformanceStatus, checks: tuple[ClassBCheckResult, ...],
    reasons: tuple[str, ...], evidence: tuple[str, ...]
```

Aggregation rule (`_aggregate_status`): only `all(check.satisfied for check in checks)` yields `COMPLIANT`; any single failure, missing evidence, or indeterminate check prevents it. No majority/partial-credit semantics exist anywhere in the implementation (verified: `test_no_majority_partial_success_semantics`, 9-satisfied/1-failed still not `COMPLIANT`).

## 6. Topology Verifier (`hatp_class_b_topology_verifier.py`)

Implements HBDC-REQ-001..021. Principal checks derive UID/GID live, never from a username string (HBDC-REQ-004/005 enforced by an AST self-check scanning for suspicious `os.environ`-key literals and `getuser`/`getlogin`/`setuid`-family calls in this module's own source — deliberately narrower than "any `os.environ` reference," since `_resolve_trusted_executable`'s legitimate `PATH` read would otherwise false-positive). Effective-access, ancestor-chain, symlink, and hard-link checks are described in §2 above.

## 7. Principal / ACL / Group Checks

`_effective_write_access` composes: owner-mode-bit → group-membership-mode-bit → world-mode-bit → platform-gated ACL (Linux: `getfacl -p`, resolved via the same trusted-executable PATH-precedence primitive as Git; macOS: `ls -lde`, ACL-marker-gated, both fail closed to `INDETERMINATE` on tool-resolution failure — never a silent `COMPLIANT`-by-default). `_mode_and_group_write_access` is a deliberately narrower, non-recursive primitive used only inside `_resolve_trusted_executable`'s own PATH-directory scan, to avoid the ACL check (which itself resolves a trusted tool) recursing into itself.

## 8. Ancestor Chain

`_ancestor_chain_safe` walks `path.parent` repeatedly, terminating at the first proven-non-writable ancestor (safe boundary), the first proven-writable ancestor (`NON_COMPLIANT`, does not need to prove every ancestor to `/`), or the filesystem root without ever proving a boundary (`INDETERMINATE`). Shared between the topology verifier (Protected Root) and the environment-lock verifier (venv root), per plan §11's explicit "implemented once" instruction.

## 9. Symlink and Hard-Link Safety

Symlink: Protected-Root-domain paths reuse `hatp_bootstrap._reject_symlink` via import; venv/interpreter/Git paths use a local, byte-for-byte-equivalent `is_symlink()` check (no existing owner for those domains). Hard-link: frozen `st_nlink != 1` → `NON_COMPLIANT`; `st_nlink == 0` distinguished as a malformed-filesystem-state signal, not folded into the ordinary non-compliant path.

## 10. Environment-Lock Verifier (`hatp_environment_lock_verifier.py`)

Implements HBDC-REQ-023, HBDC-REQ-025..039: interpreter (`sys.executable` realpath + ancestor chain), venv (`sys.prefix` vs `sys.base_prefix` detection + effective-access), `PYTHONPATH` (per-entry effective-access scan), user-site (`site.ENABLE_USER_SITE` + `site.getusersitepackages()` effective-access), `sitecustomize`/`usercustomize` (enumerated across effective `sys.path`), `.pth` files (ownership + `import`-prefixed-line scan), `sys.meta_path` hooks (allow-list of expected stdlib finder types — handles both class-as-entry and instance-as-entry registration styles, a defect found and fixed during this phase's own test-writing, §14 below), CWD/`sys.path`-order shadowing (canonical-package-index vs. writable-CWD-index comparison), module-origin containment (19-file authority-module set, `importlib.util.find_spec` + realpath containment against this module's own resolved repository root), editable-install metadata (`importlib.metadata.distribution("pcae")`'s dist-info directory + `direct_url.json`/`RECORD`/finder-file ownership), launcher (`shutil.which("pcae")`), trusted Git (`_resolve_trusted_executable("git")`), and the two jointly-satisfied rows (HBDC-REQ-037 shell-injection via 028+033, HBDC-REQ-039 third-party dependency boundary via the venv lock), exactly as 149O.20H §16–§17 designed.

## 11. Aggregator (`hatp_class_b_conformance.py`)

`verify_class_b_deployment_conformance(root=None)` calls both verifiers, adds a Model-A-detection check (HBDC-REQ-022/024, via the `pcae` distribution's `direct_url.json` `editable` flag — not assumed) and the deployment-identity wrapper (HBDC-REQ-042..046, §2 above), and aggregates via the shared `_aggregate_status`/`_build_result` helpers. No mutation; no self-certification (confirmed: neither `_FROZEN_AUTHORITY_BEARING_FILES` nor `_FROZEN_SRC_PCAE_RELATIVE_FILES` nor the literal string `hatp_mandatory_certification` appears anywhere in this module's own source).

## 12. Read-Only Guarantee — Verified

- AST self-check in each module scans its own source for `mkdir`/`makedirs`/`chmod`/`chown`/`unlink`/`rmdir`/`rename`/`replace`/`symlink`/`link`/`write_text`/`write_bytes` attribute references; none found.
- Fixture-level tests snapshot `(mode, mtime_ns, size)` across a fixture tree before/after running verifier primitives; equality asserted.
- `git status --porcelain` before and after every test run in this phase showed no change to any file outside the seven new paths in §3.

## 13. Zero Authority Callers — Verified

`grep -rln` (manual, this phase) and an automated repository-wide scan (`test_zero_authority_callers_across_src_pcae`) both confirm zero `src/pcae/**` files outside the three-module island reference any of the three new module names. HMIC-25-bound files (`hatp_mandatory_cutover.py`, `hatp_mandatory_certification.py`, `hatp_bootstrap.py`, `repository_identity.py`, `scripts/hatp_certification_admin.py`) confirmed byte-unchanged via `git status --porcelain`.

## 14. Findings

1. **`sys.meta_path` class-vs-instance defect (self-caught, fixed).** The standard library's own `BuiltinImporter`/`FrozenImporter`/`PathFinder` are registered on `sys.meta_path` as classes used directly, not instances; an initial implementation of `_check_meta_path_hooks` computed `type(finder).__name__`, which returns `"type"` (the metaclass) for a class-as-entry, not the finder's own name — causing a false `NON_COMPLIANT` against the real, safe stdlib baseline. Fixed to resolve the entry's own identity (`finder if isinstance(finder, type) else type(finder)`) before checking the allow-list. Caught by this phase's own test-writing (`test_only_expected_meta_path_hooks_present`), not by a downstream reviewer — recorded here for 149O.20J's independent verification to specifically re-check.
2. **HBDC-REQ-004 self-check needed narrowing (self-caught, fixed).** An initial `os.environ`-reference AST scan flagged this module's own legitimate `PATH`-read inside `_resolve_trusted_executable` (needed for Git-trust resolution, HBDC-REQ-038) as an "admin-inference" violation. Narrowed to flag only `os.environ`/`os.getenv` calls keyed by a suspicious admin/user/identity-shaped literal, plus `getuser`/`getlogin` calls — not every `os.environ` reference.
3. **Expected pre-existing-test supersession (disclosed, not a defect in this phase's code):** `tests/test_phase_149o_20c_hatp_class_b_deployment_contract_independent_verification.py::TestEnvironmentLockHasNoLiveImplementationYet::test_no_environment_lock_enforcement_in_core_modules` (5 parametrized cases: `PYTHONPATH`, `sys.meta_path`, `sitecustomize`, `usercustomize`, `ENABLE_USER_SITE`) was written in 149O.20C to affirmatively confirm the gap this very phase is authorized to close. It now fails, correctly — its premise ("no environment-lock enforcement exists in `src/pcae/core/*.py`") is superseded by this phase's legitimate, authorized implementation. This is the intended, disclosed outcome, not a regression.
4. **Expected pre-existing-test false positive (disclosed, unavoidable given HBDC-REQ-034):** `tests/test_phase_149o_19_5e_2_*.py`/`149o_19_5e_3_*.py::test_zero_readiness_or_cutover_callers_of_validator` greps `src/pcae/**` for the literal substring `"hatp_mandatory_certification"` and asserts only three specific files may contain it. `hatp_environment_lock_verifier.py`'s HBDC-REQ-034 module-origin list legitimately includes `"core/hatp_mandatory_certification.py"` as one of the 19 authority-module path *strings* it must check origin-containment for (per plan §16) — this is data, not an import, but the check is a blunt substring scan that cannot distinguish the two. Removing the entry would silently drop HBDC-REQ-034 coverage for that file, which is not an acceptable trade. Recorded as a known, disclosed limitation of a pre-149O.20I test's threat model, not fixed by weakening HBDC-REQ-034 coverage. A companion docstring reference to the same substring in both new modules was removed where it was not load-bearing data (§14 finding was reduced from 2 files to 1 by that cleanup).
5. **Expected pre-existing-test false positives (disclosed, resolve on commit):** 9 distinct pre-149O.20I "no `src/pcae` file dirty in the working tree" self-checks (from 149O.14, 149O.1G, 149O.20A, 149O.20B, 149O.20C, 149O.20D, 149O.20D.1, 149O.20E, 149O.20H) fail while this phase's three new files sit as untracked working-tree entries. Each of these tests' own docstring/comment discloses it is a "best-effort self-check... the phase report's own `git diff --stat` against the pre-phase commit SHA is authoritative" — none is the authoritative evidence source. These will pass again once this phase's changes are committed (confirmed: `git status --porcelain -- src/pcae scripts docs/contracts` is empty except for the three new files, which is exactly what this phase is authorized to add).
6. **No unexplained regression found.** A clean pre-phase baseline (`git status --short` verified empty; the six new phase files temporarily moved out of the working tree to `/tmp` and back) reproduced 149O.20H's own documented Fast Green baseline exactly: 59 failed, 6570 passed, 4 skipped, 1 pre-existing fido2 collection error. Diffing the with-changes failed-test-ID set against this freshly-reproduced baseline (not against the historical count alone) isolated exactly 26 candidate new failures, and all 26 are accounted for by findings 3–5 above (5 + 2 + 9 git-status/env-lock/self-trust false positives = 16) plus 10 `test_backend_cli.py` failures independently reproduced as pre-existing parallel-execution flakiness unrelated to this phase (that file passes 307/307 clean when run in isolation, serially, with these three new modules present).

## 15. Tests

- `tests/test_phase_149o_20i_hatp_class_b_topology_verifier.py`: 37 tests — result model, status vocabulary, public API/no-authority-boolean, effective-access primitive (owner/group/world/missing/symlink), ancestor-chain (safe boundary, writable-parent, symlinked ancestor), hard-link (single/multiple/missing), Protected-Root scenario checks (missing root, same-uid, group-writable mode, symlink root, hard-linked registry), read-only-mutation guard, fail-closed-on-exception, static self-checks (no admin-inference, no self-elevation, no mutation call, no self-trust claim, not yet in HMIC scope), aggregation-rule unit tests.
- `tests/test_phase_149o_20i_hatp_environment_lock_verifier.py`: 31 tests — public API, real-host non-compliant result, all HBDC-REQ rows present, interpreter/venv fixtures, `PYTHONPATH` (unset/agent-writable/agent-unwritable), user-site, sitecustomize/usercustomize, `.pth` (absent/agent-writable/import-line), meta_path (baseline-clean and injected-hook), CWD-shadow (real environment and hostile-fixture), module-origin (real environment and forced-shadow), editable-install/launcher/Git-trust smoke tests, fake-Git-on-PATH attack test, fail-closed-on-exception, not-yet-in-HMIC-scope, and a subprocess-fixture end-to-end hostile-`PYTHONPATH` test.
- `tests/test_phase_149o_20i_hatp_class_b_conformance.py`: 30 tests — public API/no-authority-boolean, real-host result, aggregation rule (all-satisfied, single-failure parametrized across 5 positions, missing-evidence, no-majority-semantics, empty-checks), status-vocabulary closure, deployment-identity wrapper (no-binding non-compliant, reuse-not-reimplementation AST check), Model-A detection (real environment, distribution-missing fail-closed), read-only/non-mutation guarantee, result-type-has-no-activation-field, no-attestation-language, no-self-trust-claim, zero-authority-callers repository sweep, three-modules-not-in-HMIC-scope, HMIC-bound-files-byte-unchanged, no-self-certification, fail-closed-on-exception.

**Total: 98 new tests, 98/98 passing.**

## 16. Implementation Verdict

```
CLASS-B DEPLOYMENT VERIFIER / MODEL-A ENVIRONMENT-LOCK:
IMPLEMENTED IN NON-AUTHORITATIVE MODE
— READ-ONLY
— FAIL-CLOSED
— ZERO PRODUCTION AUTHORITY CONSUMERS
— SOURCE NOT YET HMIC-BOUND
— POSITIVE CONSUMPTION FORBIDDEN
```

Class-B: CONTRACT VERIFIED — VERIFIER IMPLEMENTED NON-AUTHORITATIVELY — NOT PROVISIONED.
CBV-S1: NON-AUTHORITATIVE IMPLEMENTATION COMPLETE — HMIC SOURCE-SCOPE BINDING PENDING — NOT CLOSED.
CBV-S10: READINESS INTEGRATION CONTRACT GAP REMAINS — NOT CLOSED.
HATP: NOT READY.

## 17. Recommended Next Phase

**149O.20J — Class-B Deployment Verifier / Model-A Environment-Lock Independent Implementation Verification.** Must independently re-derive every check in the three modules from primary source (mirroring 149O.20C/20E/20G's methodology), confirm zero authority-consuming callers, confirm the read-only guarantee, independently re-verify effective ACL/group handling, full ancestor-chain handling, hard-link handling, environment-lock attacks, fail-closed aggregation, no-caller-authority, no-runtime-attestation-overclaim, current HMIC non-binding, and CBV-S1 sequencing safety. Not started, not authorized by this phase. No provisioning, HMIC scope evolution, or readiness integration is authorized until 149O.20J passes.
