# Phase 149O.20G — HMIC v1.2 HBDC 25-File / 5-Contract Production Identity Alignment Independent Verification

**Phase type:** Independent implementation verification only. No `src/pcae/**`, `scripts/**`, or contract file modified.
**Verifies:** Phase 149O.20F's claim that production (`src/pcae/core/hatp_mandatory_certification.py`) now exactly implements HMIC-001 v1.2's verified 25-file / 5-contract HBDC identity model.
**Adjudicates:** B-149O.20D-1, HBDC-BINDING-GATE, at the implementation-verification boundary.

---

## 1. Baseline

- Phase-entry commit (149O.20E's own exit commit): `43ecacb9`.
- Repo clean at initial inspection; `origin/main..HEAD` = 0; `pcae health` healthy; `pcae check` passed; `pcae status coherence` coherent; `pcae push check` clean; `pcae runtime inspect` Observed/observe/unavailable; `pcae notify status` telegram configured/enabled/ready.
- 149O.20F confirmed completed/pushed via `pcae phase-report show --latest` and `pcae phase-report reconcile --phase-id 149O.20F` (status: reconciled, mutation: none).

## 2. 20F Diff Reconstruction

`git diff --name-only 43ecacb9 HEAD -- src/pcae/ scripts/` → exactly one file: `src/pcae/core/hatp_mandatory_certification.py`. Full diff inspected directly (not summarized from 20F's own report): every changed line is either a docstring/comment, the `_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES`/`_CONTRACT_IDENTITY_FILES` tuple literal (new entries appended), or the `assert len(...) == 25`/`24` count. AST comparison (`ast.dump` over every `FunctionDef`/`AsyncFunctionDef`/`ClassDef`) confirms **zero function/class body changes** — identical node sets, identical dumps, before and after.

## 3. Live Contract Target Extraction (Independent)

Fresh regex extraction directly from `docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`, never importing production's constants as an oracle:

- HMIC-REQ-050's fenced enumeration block: **exactly 25 lines**, in this literal order (`core/hatp_mandatory_cutover.py` … `core/hatp_mandatory_certification.py`, then the five `docs/contracts/*.md` entries, then `scripts/hatp_certification_admin.py`).
- HMIC-REQ-067's prose: **exactly 5** contract IDs, in order `HMRC-001, HATP-001, HSCE-001, RAE-001, HBDC-001`.

## 4. Live Production Extraction (Independent)

Regex extraction over `hatp_mandatory_certification.py`'s own source text (not the imported object) of `_FROZEN_SRC_PCAE_RELATIVE_FILES` (19 entries) + `_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES` (6 entries) = **25**, and `_CONTRACT_IDENTITY_FILES` = **5** pairs. Cross-checked against the actually-imported tuples (`hmic._frozen_canonical_paths()`, `hmic._CONTRACT_IDENTITY_FILES`) — identical, ruling out a stale-bytecode/import mismatch.

## 5. Exact Dual Equality

Programmatic set-and-order comparison (contract canonical paths built by existence-testing each literal entry against `src/pcae/`, independent of the contract's own bucket prose):

- 25-file set: **equal**, both as sets and in literal presentation order.
- 5-member contract-identity set: **equal**, both as sets and in order.
- No extras, no omissions, no alias paths, no replacement members.

## 6. Historical 24/4 Baseline Reconstruction and Exact Delta

`git show 43ecacb9:src/pcae/core/hatp_mandatory_certification.py`, same independent regex extraction: **24 files**, **4 contract members** (`HMRC-001, HATP-001, HSCE-001, RAE-001`). Delta: `current − pre = {docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md}` (files) and `{HBDC-001}` (contract IDs); `pre − current = {}` in both dimensions. Matches 149O.20D.1/149O.20E's named expected delta exactly. All 24 pre-20F entries confirmed a subset of the current 25; all 4 pre-20F contract members confirmed a subset of the current 5.

## 7. Digest Reimplementation, Golden Cross-Check, Mutation Sensitivity

A from-scratch Python reimplementation of HMIC-REQ-054/056-058 (SHA-256 per file, lexicographic order, `<path>\0<hex>\n` records, SHA-256 of the concatenation) was written independently of production's `derive_implementation_scope_digest`.

- **Golden digest cross-check:** independent digest == `hmic.derive_implementation_scope_digest(HarnessPath(repo_root))` == `7b9cbe2f108627a666948380f9514bf25681866ff7adcc52fb59d39f2aed41b0`. Exact match.
- **25/25 mutation sensitivity:** each of the 25 frozen files, one-byte-mutated in isolation (independent digest recomputed with that file's substituted bytes), changes the digest. 25/25, zero insensitive.
- **Historical delta digest:** the independently-reconstructed pre-20F 24-file digest differs from the current 25-file digest for the identical present-day snapshot — a pre-20F-scope identity cannot replay against the current one.

## 8. HBDC Dual Binding (Isolated Fixture, Production's Own Functions)

All three probes ran inside a disposable `git archive`-derived fixture copy — the real working tree was never mutated. Production's own `derive_implementation_scope_digest`/`derive_contract_versions` were called via subprocess against the fixture.

- **Same-version content mutation:** HBDC document body appended with a comment, version/Contract-ID headers untouched → `implementation_scope_digest` **changed**; `derive_contract_versions()["HBDC-001"]` **unchanged** ("1.0"). Confirms the digest binding, not the version-header binding, is what catches same-version drift — closing B-149O.20D-1's originally disclosed gap.
- **Version bump:** `**Version:** 1.0` → `9.9` → `derive_contract_versions()["HBDC-001"]` becomes `"9.9"`; digest also changes (content bytes changed).
- **Malformed Contract-ID:** `**Contract:** HBDC-001` → `WRONG-ID-999` → `derive_contract_versions` raises `ContractIdentityDerivationError` (fail-closed), exact production exception, no silent acceptance.
- **Dual-binding verdict:** HBDC-001 is proven present in **both** identity dimensions — content-digest and contract-version — independently and explicitly, not by mere tuple-membership inspection.
- **Other four bound contracts:** each individually mutated in the same fixture; each still changes the digest. No weakening of pre-existing dual binding.

## 9. Fail-Closed Safety (Isolated Fixture)

- HBDC file deleted → `FrozenFileDerivationError: frozen file does not exist` (HMIC-REQ-059).
- HBDC path replaced with a symlink to another frozen file → `FrozenFileDerivationError: ... is a symlink, refusing ...` (HMIC-REQ-061).
- HBDC path replaced with a directory → `FrozenFileDerivationError: ... is not a regular file` (HMIC-REQ-062).

All three fail closed via production's actual `_resolve_and_reject_unsafe_frozen_file`, not a simulated/mocked path.

## 10. Core Self-Binding

In the isolated fixture: baseline digest computed; `hatp_mandatory_certification.py` itself appended with a trailing comment → digest **changed**; bytes restored → digest **returned exactly to baseline**. Confirms current, post-20F-edit source bytes — not stale pre-edit bytes — participate in the digest the module itself computes.

## 11. No Legacy Path, No Cache, No Import-Time Freeze, No Duplicates

- Regex search for `legacy_scope|file_count\s*=\s*24|ignore_hbdc|hmic_v1_1|legacy_24|legacy_compat` across `hatp_mandatory_certification.py` and `scripts/hatp_certification_admin.py`: **zero matches**.
- `lru_cache`/`@cache` search: **zero matches** in the module (the only hits anywhere in the file are prose *stating* no cache exists).
- AST sweep of module-level statements: **zero** top-level `Expr(Call(...))` nodes — no derivation runs at import time.
- `_frozen_canonical_paths()` and `_CONTRACT_IDENTITY_FILES` checked for duplicates: none.
- `derive_implementation_scope_digest`/`derive_contract_versions` signatures inspected via `inspect.signature`: both take exactly `(root)` — no caller-suppliable contract map, digest, version, or count parameter exists.

## 12. Algorithm/Semantic Stability

AST-body comparison (pre-20F vs. current) for `derive_implementation_scope_digest`, `derive_contract_versions`, `derive_implementation_commit`, `_validate_at_root`, and `validate_active_hatp_mandatory_independent_verification_certification`: **byte-identical AST dumps**, all five. `scripts/hatp_certification_admin.py` and `src/pcae/core/hatp_mandatory_cutover.py`: **byte-identical** text since phase entry (`git show` vs. working tree, direct string comparison). The readiness-fact check name (`mandatory_consumption_implementation_independently_verified`) and its dynamic-derivation call (`validate_active_hatp_mandatory_independent_verification_certification(...)`) are both still present in the byte-unchanged cutover module — the dynamic wiring 20F itself found (correcting a stale "hard-coded False" characterization) is confirmed still in place, not redesigned.

## 13. Historical Repin Review (9 Modules 20F Touched)

Independently reproduced 20F's own claimed before/after failure sets via a disposable `git worktree` at `43ecacb9` (not `git stash`, to avoid disturbing the working tree during this read-mostly phase):

- Broad HMIC/HBDC sweep (`-k "hmic or hbdc or 149o_20 or 149o_19_5"`, excluding the known fido2 collection error): **37 failed / 818 passed** at `43ecacb9`; **33 failed / 869 passed** at HEAD (pre-20G-test-module). Diffing the two failing-node-ID sets: **zero new failures** at HEAD not present at `43ecacb9`; **15 failures fixed** by 20F's repair. No evidence laundering — every fixed node ID is a genuine repair of a live-reference antipattern (e.g. asserting the *current* live contract still says "24 entries"/"v1.1"), not a weakened or rewritten historical claim.
- One residual pre-existing failure not among 20F's repaired 9 modules: `test_phase_149o_20c_...::test_hmic_v1_1_current_version_unchanged` (asserts live text still contains `**Version:** 1.1`) — reproduces identically at `43ecacb9`, i.e. it already existed before 20F and 20F did not introduce it. Recorded as a residual, non-blocking, pre-existing gap outside this phase's or 20F's scope (20C's own test file, not one of 20F's 9 repaired modules).

## 14. HMIC-REQ-145 / HMIC-REQ-063 / Option-C

- HMIC-REQ-145 (live contract text): explicitly states the "Repair (this section, as of 149O.20D.1 …)" — HBDC-001's document is now the 25th `implementation_scope_digest` entry, receiving the identical dual binding as the other four bound contracts. **Closed**, confirmed by direct empirical demonstration (§8 above), not merely by reading the contract's own claim.
- HMIC-REQ-063: still present verbatim, still names import-shadowing/executed-code binding as an explicit, unresolved v1.0 limitation. **Retained**, unresolved, as required — this phase introduced no runtime/executed-source cryptographic attestation.
- Option C: contract text unchanged (byte-identical); no production behavior claims Option C unconditionally. **Retained conditional.**

## 15. Current Real Readiness

`assess_hatp_mandatory_activation_readiness(HarnessPath(repo_root))` called read-only against the real host: `ready = False`. The `mandatory_consumption_implementation_independently_verified` check itself: `satisfied = False`, reason `ACCESS_ERROR — could not derive current repository/deployment identity (repository-identity.json is absent)`. No state was created by this read.

## 16. Fast Green / Broad Sweep

- Broad HMIC/HBDC sweep including the new 149O.20G test module: **33 failed / 909 passed / 4 skipped / 31041 deselected**. Zero new failures relative to §13's baseline (40 new passing tests added, same 33 pre-existing failures).
- Repository-standard Fast Green (`pytest -m fast_green -n auto`): **59 failed, 6549 passed, 4 skipped, 1 collection error** (raw). Attribution:
  - 1 collection error: `tests/test_phase_149o_7_...py` — pre-existing `ModuleNotFoundError: No module named 'fido2'` (optional dependency, matches 20F's own citation).
  - 1 failure: `test_backend_cli.py` (a different node ID than 20F's own citation, consistent with xdist-order-dependent concurrent-task-state flake) — confirmed spurious: `pytest tests/test_backend_cli.py` in isolation, single-process: **307/307 passed**.
  - 58 remaining failures: independently reproduced identically at phase-entry commit `43ecacb9` via a disposable worktree (§13, plus a second worktree covering `test_hatp_mandatory_certification_models.py` and six additional modules not in the `-k` sweep) — **all 58 pre-existing, none attributable to 149O.20F or 149O.20G**.
  - **Zero new regressions.**

## 17. Findings

**Blocking:** none.
**Non-Blocking:** none newly introduced. Retained from prior phases (not repaired here, per phase-type restriction): 20C's own residual `test_hmic_v1_1_current_version_unchanged` repin debt (§13); 20C's non-blocking Class-B verifier implementation-coverage gaps (effective ACL/group verification, full ancestor-chain verification, hard-link verification — retained, not repaired, prerequisites for a future deployment-verifier phase).
**Observations:** the `test_backend_cli.py` concurrent-task-state flake pattern (documented in prior-phase memory) reproduced again under a different node ID this run — consistent with the known xdist/shared-state class of noise, not a new defect class.
**Deferred:** Class-B deployment verifier / Model-A environment-lock implementation (per phase-type restriction, explicitly out of scope for 149O.20G).

## 18. Verification Verdict

**HMIC v1.2 HBDC 25-FILE / 5-CONTRACT PRODUCTION IDENTITY ALIGNMENT: INDEPENDENTLY VERIFIED — PRODUCTION EXACTLY MATCHES VERIFIED HMIC v1.2 IDENTITY — HBDC DUAL BINDING COMPLETE.**

- **B-149O.20D-1:** INDEPENDENTLY CONFIRMED CLOSED AT CONTRACT + PRODUCTION IDENTITY BOUNDARY. Class-B deployment/provisioning remains deferred.
- **HBDC-BINDING-GATE:** INDEPENDENTLY CONFIRMED CLOSED AT CONTRACT + PRODUCTION IDENTITY BOUNDARY — CLASS-B DEPLOYMENT VERIFIER / ENVIRONMENT-LOCK IMPLEMENTATION PENDING. This is explicitly NOT equivalent to Class-B deployment verified.
- **W-1:** remains independently closed (no source-scope incompleteness found).
- **B-149O.19.3-1:** remains independently closed; its four provider/hardware files (`hatp_providers.py`, `hatp_fido2_provider.py`, `hatp_piv_provider.py`, `hatp_hardware_credentials.py`) confirmed still present within the current 25-file target (§4-5).
- **B-149O-1..4:** unchanged — INDEPENDENTLY CONFIRMED CLOSED AT SYSTEM IMPLEMENTATION/ENFORCEMENT BOUNDARY, DEPLOYMENT/OPERATIONAL ACTIVATION DEFERRED. No upgrade.
- **Class-B:** CONTRACT VERIFIED — NOT PROVISIONED.
- **HATP production readiness:** NOT READY (§15).

## 19. Next-Phase Reassessment

20G passing does not authorize real provisioning. The next work should address the still-unimplemented Class-B deployment-conformance mechanism named at 20C and retained here (§17): effective ACL/group verification, full authority-bearing ancestor-chain verification, hard-link verification, Python environment-lock conformance (interpreter/venv ownership, `PYTHONPATH`/user-site/`.pth`/import-hook/CWD shadowing), launcher/service environment, trusted Git executable resolution, deployment identity conformance. Recommended direction: a **Class-B Deployment Verifier / Model-A Environment-Lock Implementation Architecture or Plan** phase — architecture/implementation-plan first, then implementation in isolated/non-real mode, then independent verification, before any real OS-principal/protected-root provisioning phase. No real certification or activation is pre-authorized by this phase.
