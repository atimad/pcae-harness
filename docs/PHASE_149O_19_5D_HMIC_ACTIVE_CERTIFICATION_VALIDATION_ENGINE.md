# Phase 149O.19.5D — HMIC Active Certification Validation Engine

**Status:** IMPLEMENTED — READY FOR NEXT BOUNDED HMIC IMPLEMENTATION WAVE
**Wave:** D of 5 (149O.19.5A–E) under HMIC-001 v1.0
**Selected source of ownership:** `docs/PHASE_149O_19_4_HATP_MANDATORY_
INDEPENDENT_VERIFICATION_CERTIFICATION_IMPLEMENTATION_PLAN.md` §9.3

---

## 1. Baseline

- Latest completed phase: 149O.19.5C (HMIC Protected Certification State
  Store), commits `ef451f4c`/`37d6bd00`/`e5da16ed`, pushed,
  `origin/main..HEAD` = 0.
- HMIC-001 v1.0: FROZEN — REPAIRED (149O.19.3R), status text unchanged by
  this phase (this phase does not amend or re-verify the contract text
  itself).
- Wave A/B/C production result: one module,
  `src/pcae/core/hatp_mandatory_certification.py` — data models, strict
  parsing, canonical serialization, closed status vocabulary,
  implementation/contract identity derivation, `certification_id`
  derivation, protected storage/locking, explicit-ID readers, and
  internal admin-only write primitives. No validation algorithm, no
  admin ceremony, no readiness wiring existed before this phase.
- `mandatory_consumption_implementation_independently_verified = False`
  (`hatp_mandatory_cutover.py`): unchanged by this phase.
- Initial inspection confirmed: repo clean, `origin/main..HEAD = 0`,
  `pcae health` healthy, `pcae check` passed, `pcae status coherence`
  coherent, `pcae doctor task-memory` pre-existing warnings only (stale
  `tasks/active/`/`tasks/done/` entries predating this phase, outside
  its allowed-file scope, not remediated here), `pcae push check`
  clean, `pcae runtime inspect` Observed/observe/unavailable, `pcae
  notify status` Telegram configured/enabled/ready, `pcae phase-report
  show --latest` and `pcae phase-report reconcile --phase-id 149O.19.5C`
  both confirmed 149O.19.5C completed/complete with no mutation.

## 2. Stop Condition W-1 (Restated, Not Crossed)

149O.19.4 §10.3 froze a hard sequencing gate: the future HMIC validator
module must eventually join HMIC-001's frozen 22-file implementation-
identity set via a dedicated v1.1 contract amendment (independently
verified) before Wave F may wire it into the readiness ceiling. This
phase (Wave D) implements the validation algorithm itself, but never
connects it to real readiness: `hatp_mandatory_cutover.py` is
byte-unchanged and never imports the new module; `hatp_mandatory_
certification.py` remains outside the v1.0 22-file frozen subject; the
validator has **zero production callers** at phase exit
(`TestZeroProductionCallers`). W-1 remains mandatory and unresolved by
design — see §11 (No-Go Confirmations).

## 3. Scope Wall Preserved

This wave answers only: "is the currently active-bound certification
`VALID` against the current environment?" It never answers: may
activation proceed? does PB `ALLOW`? does HATP/RAE rollback approval
exist? is any runtime execution capability granted? Those remain outside
HMIC-001's scope entirely (§5's semantic walls) or, for activation
wiring specifically, Wave F — gated by W-1, not implemented here.

## 4. Wave-D Requirement/CIVC/Attack Traceability (Restated From 149O.19.4 §6/§7/§8)

27 HMIC-REQ IDs carry `VALID`/Wave-D ownership (wholly or shared with
another wave's primary owner): 008, 019, 023, 030, 040, 045, 048, 049,
059, 069, 072, 074, 085, 089, 090, 094, 101, 103, 104, 105, 107, 109,
110, 111, 112, 113, 144.

| HMIC-REQ | Subject | Implemented by |
|---|---|---|
| 008, 074 | "Certified" never means phase-report/test-pass/commit/status-file; closed prohibition list never consulted | `_validate_at_root` never opens `PROJECT_STATUS.md`/`tasks/**`/`CHANGELOG.md`/any phase report/`.pcae/phase-*`/test results/env vars (only exception: `PCAE_HMIC_ROOT` is read by a *test* to prove it has no effect, `test_no_root_override_env_or_flag_accepted`) |
| 019 | Read access ≠ write authority | `_validate_at_root`/`validate_active_...` call only `_load_active_binding`/`_load_certification_record` (Wave C readers); never a Wave C writer |
| 023, 111 | No env var/CLI flag/config resolves an alternate root; production root resolution closed | `validate_active_hatp_mandatory_independent_verification_certification` always resolves `HATPTrustStore.production().root` internally; `_validate_at_root`'s `protected_root` parameter exists only as the internal test seam (HMIC-REQ-112) |
| 030 | No hardware/FIDO2 touch required | Structural — no HATP proof/hardware-provider call anywhere in Wave D |
| 040 | Self-consistency: validation re-derives `certification_id`, `MALFORMED` on mismatch | Step 11, `_recompute_certification_id(record) != record.certification_id` |
| 045, 110, 112 | Both identifiers, and every authority value, derived fresh internally; no caller-suppliable authority input on any path, including the test seam | `_validate_at_root` accepts only `protected_root`/`repository_root`; `repository_instance_id`/`canonical_deployment_root`/`implementation_commit`/`implementation_scope_digest`/`contract_versions` are all freshly derived inside the function body, never a parameter |
| 048, 049 | Commit-changed-bytes-same and bytes-changed-commit-same both `IMPLEMENTATION_MISMATCH` | Step 9's `current_commit != record.implementation_commit or current_scope_digest != record.implementation_scope_digest` — either mismatch alone triggers the same status |
| 059 | Missing frozen file at validation time ⇒ `IMPLEMENTATION_MISMATCH` | Step 9's `except HMICIdentityDerivationError` (covers `FrozenFileDerivationError`) |
| 069 | Contract drift — any `contract_versions` difference ⇒ `CONTRACT_MISMATCH`, no compatibility table | Step 10 |
| 072 | `verification_record_digest`/phase ID never sufficient/fallback for `VALID` | Structural — no step of the algorithm ever reads `record.verification_record_digest` as a validity input |
| 085, 089, 090 | Active-Certification Pointer is the only active signal; no implicit-latest; old-implementation/contract replay rejected by comparison alone; only the pointed record is ever consulted | Step 4 (`_load_active_binding`, never scans/sorts `certifications.json`); step 5 loads only the one named `certification_id` |
| 094 | Revoked active-pointed certification ⇒ `REVOKED`; non-active-pointed revocation has no effect on this evaluation | Step 8 |
| 101 | Validator never acquires `.certification-transition.lock` | `_validate_at_root`/`validate_active_...` never call `_certification_transition_lock` (`TestReadOnlyStructural`, AST-verified) |
| 103, 104, 105 | 12-step algorithm, exact order, first-failing-step-determines-status; root/file access failure ⇒ `MISSING`/`ACCESS_ERROR` | `_validate_at_root`'s full body; steps 1 (Protected Root absence) and 4/5 (file absence) naturally fall through Wave C's own tri-state readers to `MISSING`; steps 2-3 (repository/deployment identity derivation failure) and the production wrapper's own root-resolution failure map to `ACCESS_ERROR` — see §9 below for this phase's documented interpretation |
| 107 | Readiness mapping — exactly `VALID` maps `True` | Wave A's `certification_status_satisfies_readiness`, reused unmodified; `TestReadinessMappingExhaustive` re-confirms all 9 members at Wave D's own boundary |
| 109 | Conceptual production entrypoint `(repository_root: Path) -> <typed result>` | `validate_active_hatp_mandatory_independent_verification_certification` |
| 113 | No validity cache | No memoization decorator anywhere in the module (`test_no_lru_cache_or_memoization_decorator_used`); every call re-runs all 12 steps |
| 144 | No self-certification path (CIVC-12 restated) | Validator never trusts a stored field at face value — every authority-sensitive field is freshly re-derived and *compared*, never read-and-returned |

CIVC coverage this wave: CIVC-1, CIVC-3 (validation half), CIVC-4
(validation half), CIVC-5 (validation half), CIVC-6 (validation half),
CIVC-7, CIVC-8, CIVC-10 (validation half), CIVC-12 (validation half).
Attack coverage this wave: 8, 9, 10, 11, 12, 13, 14, 15, 16 (partial —
document-level malformed only; record-level malformed is Wave A's own
model-layer concern), 17, 18, 20, 21, 22, 23, 24, 25, 26 (confirmatory),
28, 30, 119-class (explicit-A), 120-class (bound-revoked-A/valid-B).

## 5. Production Module

`src/pcae/core/hatp_mandatory_certification.py` (extended; sole
production file touched this phase — same module Waves A/B/C created,
per 149O.19.4 §9.3's `VALID` ownership legend). New Wave-D surface:

- **Typed result:** `HMICValidationResult` (frozen dataclass: `status:
  CertificationStatus`, `reason: str` — no `approved`/`permitted`/
  `executed`/`capable`/`ready`/`readiness`/`activation` field).
- **Internal, non-production-reachable test seam (HMIC-REQ-112):**
  `_validate_at_root(*, protected_root: Path, repository_root: Path) ->
  HMICValidationResult`.
- **Production entrypoint (HMIC-REQ-109):**
  `validate_active_hatp_mandatory_independent_verification_certification
  (repository_root: Path) -> HMICValidationResult`.

New Wave-D-authorized imports: `pcae.core.hatp_bootstrap.
HATPTrustStoreError` and `pcae.core.repository_identity.
RepositoryIdentityError` (both exception base classes, used only to map
steps 1-3's genuine derivation/access failures to `ACCESS_ERROR` — no
new I/O primitive, no new identity/storage scheme). No new third-party
or stdlib import. Still never imports `hatp_mandatory_cutover.py`, the
provider/hardware modules, the Permission Broker, `rollback_approval_
evidence.py`, `agent.py`, `commands/agent.py`, or `cli.py`
(`TestReadOnlyStructural::test_module_imports_no_permission_broker_
rae_or_agent_execution_path`).

## 6. The 12-Step Algorithm (HMIC-REQ-103, Exact Order)

```
 1. resolve Protected Root                -> (naturally falls through to
                                              MISSING at step 4 if absent;
                                              ACCESS_ERROR if the
                                              production root-resolution
                                              call itself raises)
 2. resolve repository_instance_id        -> ACCESS_ERROR on derivation
                                              failure (see §9)
 3. resolve canonical_deployment_root     -> ACCESS_ERROR on derivation
                                              failure (see §9)
 4. load certification-bindings.json      -> MISSING if no binding /
                                              no active_certification_id
 5. load certifications.json              -> MISSING if the bound ID has
                                              no stored record
 6. strict-parse both documents           -> MALFORMED on any deviation
                                              (folded into steps 4-5 via
                                              Wave C's own readers)
 7. repository_instance_id +
    canonical_deployment_root match       -> WRONG_REPOSITORY /
                                              WRONG_DEPLOYMENT
 8. status == "active"                    -> REVOKED
 9. fresh implementation_commit +
    implementation_scope_digest,
    compare against the record            -> IMPLEMENTATION_MISMATCH
10. fresh contract_versions vs. the four
    frozen contracts' live headers        -> CONTRACT_MISMATCH
11. certification_id self-consistency      -> MALFORMED
12. every step above passed                -> VALID
```

Steps are evaluated in exactly this order inside `_validate_at_root`;
the first failing step returns immediately (`TestStatusPrecedence`
confirms this for four multi-defect combinations: revoked +
implementation-mismatch → `REVOKED`; wrong-repository + revoked →
`WRONG_REPOSITORY`; implementation-mismatch + contract-mismatch →
`IMPLEMENTATION_MISMATCH`; malformed-cert + revocation is structurally
`MALFORMED` since a malformed document can never reach step 7 at all).

## 7. Validator API and Freshness

`validate_active_hatp_mandatory_independent_verification_certification`
resolves `HATPTrustStore.production().root` internally and delegates to
`_validate_at_root`. Neither function accepts `implementation_digest=`,
a precomputed `implementation_commit=`/`contract_versions=`,
`repository_instance_id=`, `canonical_deployment_root=`, `revoked=`,
`status=`, `root=`, or `store_root=` — confirmed by direct
`inspect.signature` checks (`TestNoCallerSuppliableAuthorityInput`), not
merely by docstring claim. No cache of any kind exists: every call
re-derives repository/deployment identity, re-reads both certification
files, and re-recomputes implementation/contract identity from scratch
(`TestFreshnessNoCache`, six tests plus a static "no `lru_cache`" grep).

## 8. Deliberate Divergence From the Plan's Illustrative `_validate_at_root` Signature

149O.19.4 §9.3 sketches `_validate_at_root(protected_root: Path,
repository_instance_id: str, canonical_deployment_root: str)` as an
illustrative ("conceptually") shorthand for the internal test seam. This
phase implements `_validate_at_root(*, protected_root: Path,
repository_root: Path)` instead — deriving `repository_instance_id`/
`canonical_deployment_root` freshly *inside* the function from
`repository_root`, never accepting either as a parameter, even on the
test-only path. This is required, not optional: HMIC-REQ-045 ("Both
identifiers SHALL be derived read-only ... never accepted as caller
input on either path") and HMIC-REQ-110 ("No caller-suppliable authority
input") apply without a stated test-seam exception, and this phase's own
governing prompt (§6) repeats the prohibition explicitly for
`repository_instance_id`/`deployment_id`. Accepting the plan's literal
shorthand signature would have created exactly the caller-suppliable
authority input both requirements forbid. The test seam still satisfies
HMIC-REQ-112 exactly: it accepts an explicit `protected_root`, used only
by tests constructing isolated fixture roots.

## 9. Documented Interpretation — Steps 2-3 Failure Mapping (`ACCESS_ERROR`)

HMIC-REQ-105 explicitly pairs "root/file access failure" (steps 1, 4, 5)
with either `MISSING` (ordinary absence) or `ACCESS_ERROR` (a genuine
I/O error). It does not explicitly name a status for a step-2/3
identity-*derivation* failure (e.g. no `repository_instance_id` has ever
been established for this repository at all, or the deployment root
cannot be resolved). This phase maps any such failure to `ACCESS_ERROR`,
by documented analogy rather than improvisation: the failure occurs
before any certification file is even consulted, so it is not "ordinary
absence of certification state" (`MISSING`'s own domain per steps 4-5),
and it is a genuine environment/derivation error in the same general
class HMIC-REQ-105 already assigns to `ACCESS_ERROR`. This is not a
contract gap requiring a new status value (§41 of the governing prompt's
STOP condition is not triggered): `ACCESS_ERROR` already exists in the
closed 9-value vocabulary and is general-purpose enough to cover this
case without inventing a tenth status. The production root-resolution
call (`HATPTrustStore.production().root`, which can raise
`HATPBootstrapUnsupportedPlatformError`) is mapped identically, in the
public wrapper. Both are fail-closed (`ACCESS_ERROR` maps to readiness
`False` identically to every other non-`VALID` status) and are covered
by `TestAccessError`.

## 10. No-Go Confirmations

- Only Wave-D-authorized production file was modified: `git diff
  --name-only` against the phase-entry commit for `src/pcae/` shows
  exactly `src/pcae/core/hatp_mandatory_certification.py` (modification,
  not addition — the same file Waves A/B/C created).
- HMIC-001, HMRC-001, HATP-001, HSCE-001, RAE-001, RWMPC-001, PBPA-001,
  and PBPC-001 all remain byte-unchanged.
- The exact 22-file certified subject remained byte-unchanged this phase
  (Wave D never reads or writes any of the 22 files as a side effect;
  the validator *reads* frozen-file bytes only via Wave B's existing
  `derive_implementation_scope_digest`/`derive_contract_versions`,
  neither of which is new to this wave).
- `hatp_mandatory_cutover.py` remains byte-unchanged; the hard-coded
  `mandatory_consumption_implementation_independently_verified = False`
  ceiling is untouched (`test_hardcoded_false_readiness_ceiling_still_
  present`). The new validator function is never imported by
  `hatp_mandatory_cutover.py` or any other existing production file
  (`TestZeroProductionCallers`, both a source-text grep across every
  `src/pcae/**/*.py` file and an explicit `hatp_mandatory_cutover.py`
  text-scan for the module name).
- No admin ceremony, no `create_certification`/`activate_certification`/
  `revoke_certification` function exists; the validator never calls
  `_append_certification_record`/`_write_active_binding`/`_write_
  revocation`/`_certification_transition_lock`/`_atomic_write_
  protected_json` (`TestReadOnlyStructural`, AST-verified against both
  the production entrypoint and the internal seam's own function
  bodies).
- No ordinary `pcae` CLI change; no `commands/agent.py`/`agent.py`
  change; no admin writer script exists anywhere in the repository yet
  (Wave E, not this phase).
- No real certification artifact, active-certification binding, or
  revocation record was created anywhere on this host — every test uses
  an isolated `tmp_path` protected root and an isolated, git-initialized
  `tmp_path` fixture repository (never this repository's own real
  frozen files for mismatch-inducing mutation); `HATPTrustStore.
  production().root` is never constructed for a write in this test
  suite, and the one test that does call the real production entrypoint
  (`test_no_root_override_env_or_flag_accepted`) only confirms it
  resolves the *real* production root (i.e. does NOT find the isolated
  fixture's `VALID` state), never that it writes anywhere.
- No Cutover Record or activation marker was created or modified. No
  real `HATP_MANDATORY` activation occurred. No Class-B provisioning
  occurred. No Permission Broker behavior changed. `POL-005` remained
  unchanged. No `COMP-002` capability was implemented.
- Runtime/executed-source-binding remains deferred per HMIC-REQ-063
  (`attack_29`-class residual limitation, unchanged and unrevisited this
  phase — the validator's `implementation_scope_digest` comparison still
  binds only on-disk bytes, not the executing interpreter's actual
  module resolution).
- W-1 remains mandatory before any future readiness integration (Wave
  F); this phase does not begin, and could not begin, that gate.
  `hatp_mandatory_certification.py` remains outside the v1.0 22-file
  frozen subject. The validator now exists — this phase's own §82/83
  obligation (governing prompt) — making W-1 concrete rather than
  hypothetical: `_validate_at_root` and `validate_active_hatp_mandatory_
  independent_verification_certification` (both in `src/pcae/core/
  hatp_mandatory_certification.py`) are the exact source paths that must
  join HMIC-REQ-050's frozen enumeration in a future v1.1 amendment
  before Wave F may wire this validator into real readiness.

## 11. Tests

- `tests/test_phase_149o_19_5d_hmic_active_certification_validation_
  engine.py` — 51 tests: VALID control-flow proof (including immutable-
  result and no-forbidden-field checks); all 9 status outcomes reachable
  and individually tested (`MISSING` ×4, `MALFORMED` ×3,
  `WRONG_REPOSITORY`/`WRONG_DEPLOYMENT`/cross-protected-root-copy,
  `REVOKED` ×3 including no-failover-to-a-valid-unbound-certification and
  explicit-binding-ignores-newer-certification, `IMPLEMENTATION_
  MISMATCH` ×4, `CONTRACT_MISMATCH`, `ACCESS_ERROR`); 3 multi-defect
  status-precedence tests; 6 freshness/no-cache tests plus a static
  no-`lru_cache` source check; 1 real-thread concurrency confirmatory
  test (concurrent revocation never observed as a torn/ambiguous
  status); signature-level no-caller-suppliable-authority-input checks
  (`inspect.signature`) for both the production entrypoint and the
  internal seam, plus a no-root-override-via-environment-variable test
  against the real production entrypoint; AST-based structural checks
  confirming neither validation function ever calls a Wave C write
  primitive, and the whole module imports no PB/RAE/cutover/agent/CLI
  module; a repository-wide grep confirming zero other `src/pcae/**`
  file references the validator function name; an exhaustive readiness-
  mapping re-confirmation over all 9 `CertificationStatus` members.
- All fixtures use an isolated, git-initialized `tmp_path` repository
  with `monkeypatch`-substituted `_FROZEN_AUTHORITY_BEARING_FILES`/
  `_FROZEN_SRC_PCAE_RELATIVE_COUNT`/`_CONTRACT_IDENTITY_FILES` (the
  identical seam pattern the 149O.19.5B suite's own `fixture_repo`
  established) — never this repository's own real frozen files are
  mutated to induce a mismatch.
- Widened one 149O.19.5C-era stale scope-boundary assertion (the same
  established pattern as every prior wave's widening, recorded in each
  wave's own phase doc): `tests/test_phase_149o_19_5c_hmic_protected_
  certification_state_store.py::test_no_validation_function_exists_in_
  module` now allowlists `validate_active_hatp_mandatory_independent_
  verification_certification` and `_validate_at_root` by name (Wave D's
  own, later, separately-authorized addition to this same module) — the
  test's actual purpose, "Wave C's storage layer never itself answers
  'is X VALID?'", is unchanged and still enforced by every other
  assertion in that suite.
- New test module self-declares `pytestmark = pytest.mark.fast_green`
  (the same convention `test_phase_149o_19_5c_...` etc. use), so it is
  automatically included under `-m fast_green` without any `tests/
  conftest.py` change; deterministic — all fixtures live entirely under
  pytest's `tmp_path`, no shared/network state, no real `HATPTrustStore.
  production()` write; the one concurrency test uses only in-process
  `threading`, no external process/service.

## 12. Regression

- Wave A/B/C/D local run (`tests/test_hatp_mandatory_certification_
  models.py`, `tests/test_phase_149o_19_5a_hmic_certification_models_
  canonical_parsing.py`, `tests/test_phase_149o_19_5b_hmic_identity_
  derivation.py`, `tests/test_phase_149o_19_5c_hmic_protected_
  certification_state_store.py`, `tests/test_phase_149o_19_5d_hmic_
  active_certification_validation_engine.py`): 419 tests, all passing.
- Broad `-k "hmic or hatp or 149o"` sweep: A/B-confirmed via `git stash
  -u` against unmodified `main` — before: 155 failed / 3660 passed;
  after (this phase's uncommitted diff): 165 failed / 3701 passed. All
  10 net-new failures are the same, already-recorded class of
  pre-existing test-design limitation this repository's own history
  documents repeatedly (149O.19.5A/B/C phase docs): an older phase's own
  "`git diff` against my fixed historical entry commit touches no
  `src/pcae/` file" / "task governance allowed-file pattern already
  matches" assertion, which this phase's own legitimate, allowlisted
  touch to `src/pcae/core/hatp_mandatory_certification.py` necessarily
  trips for those older phases' fixed baselines — not a functional
  regression. `diff` of the sorted `FAILED` line lists confirms all 155
  baseline failures are byte-identical between runs.
- Fast Green (`-m fast_green`): see §13 for exact numbers.

## 13. Fast Green (`-m fast_green`)

True A/B baseline via `git stash -u` (not just an uncommitted-diff
comparison): baseline **33 failed / 5975 passed / 1 skipped / 25639
deselected**; post-implementation **35 failed / 6024 passed / 1 skipped
/ 25639 deselected**. `diff` of the sorted `FAILED` line lists confirms
all 33 baseline failures are byte-identical between runs (unrelated
pre-existing issues), and exactly 2 net-new failures, both the identical
benign "no production-source-change-since-my-fixed-baseline" class
described in §12:
`test_phase_149o_14_..._test_git_diff_against_pre_phase_head_touches_
no_src_pcae_or_contract_file` and
`test_phase_149o_1g_..._test_only_expected_production_files_changed`.
Clean, deselected run (all 35 pre-existing/newly-tripped nodeids
explicitly `--deselect`ed): **0 failed, 6024 passed, 1 skipped, 25674
deselected**.

## 14. Implementation Verdict

```
HMIC ACTIVE CERTIFICATION VALIDATION ENGINE: IMPLEMENTED
— READY FOR NEXT BOUNDED HMIC IMPLEMENTATION WAVE
```

## 15. Recommended Next Phase

149O.19.5E — HMIC Protected Admin Certification / Revocation Surface:
protected-admin certification creation, explicit supersession, protected
revocation, canonical authority-input derivation, reusing the A-D layers
unmodified, on a separate non-agent-writable admin surface
(`scripts/hatp_certification_admin.py`, never imported by `cli.py`/
`commands/agent.py`). Still no readiness integration, no hardcoded-
`False` replacement, no activation. After Wave E: STOP for the W-1 HMIC
v1.1 contract-evolution + independent-verification gate before any Wave
F readiness integration — do not skip directly to Wave F.

## 16. Status Restatement (Unchanged By This Phase)

B-149O.19.3-1: INDEPENDENTLY CONFIRMED CLOSED (unchanged). B-149O-1..4:
INDEPENDENTLY CONFIRMED CLOSED AT SYSTEM IMPLEMENTATION/ENFORCEMENT
BOUNDARY — DEPLOYMENT/OPERATIONAL ACTIVATION DEFERRED (unchanged). HATP
production: **NOT READY**. Runtime: **Observed / observe / unavailable**.
