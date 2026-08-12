# Phase 149O.20F — HMIC v1.2 HBDC 25-File / 5-Contract Production Identity Alignment

**Status:** IMPLEMENTATION COMPLETE — PRODUCTION/CONTRACT 25-FILE / 5-CONTRACT SETS ALIGNED — PENDING INDEPENDENT IMPLEMENTATION VERIFICATION

**Phase type:** NARROW PRODUCTION IDENTITY ALIGNMENT IMPLEMENTATION ONLY.
Implements the production half of finding B-149O.20D-1's contract-level
repair (149O.20D.1, independently verified 149O.20E). Does not amend
HMIC-001, HBDC-001, or any other contract. Does not change the digest
algorithm, path canonicalization, file ordering, Git-identity semantics,
or validator/storage/admin-writer semantics. Does not implement a
Class-B verifier, environment lock, or any real
provisioning/certification/binding/revocation/activation. Does not
close HBDC-BINDING-GATE or B-149O.20D-1 at the implementation-verification
boundary.

---

## 1. Baseline

- Latest completed phase entering this one: **149O.20E** (HMIC v1.2
  HBDC Bound-Contract Identity Independent Verification), exit commit
  `43ecacb9`, pushed, `origin/main..HEAD` = 0 at entry, repo clean.
- `pcae health`: healthy; required files present; policy valid; git clean.
- `pcae check`: passed.
- `pcae status coherence`: coherent.
- `pcae doctor task-memory`: warnings — pre-existing `tasks/done/`
  entries missing from `tasks/DONE.md`, unrelated to HMIC-001, not
  remediated here (outside this phase's allowed-file scope).
- `pcae push check`: clean, `nothing_to_push`.
- `pcae runtime inspect`: Runtime state Observed; execution capability
  unavailable; Permission Broker status execution_unavailable.
- `pcae notify status`: Telegram configured/enabled/ready.
- `pcae phase-report show --latest` / `phase-report reconcile
  --phase-id 149O.20E`: 149O.20E recommends exactly 149O.20F — bounded
  production alignment (24→25 files, 4→5 contract_versions members),
  no validator/admin/readiness semantic changes, not the independent
  verification of that alignment (149O.20G, this phase's own recommended
  next step).

## 2. Verified Target Identity (Independently Extracted, §77-78)

- HMIC-REQ-050 live enumeration: **25** files, fresh-extracted from
  `docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`'s
  fenced code block. 25th entry:
  `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` (HBDC-001).
- HMIC-REQ-067 (v1.2) live `contract_versions` set: **5** members —
  `HMRC-001`, `HATP-001`, `HSCE-001`, `RAE-001`, `HBDC-001`.

## 3. Entering Divergence (Reconstructed Before Editing)

- Contract (`HMIC-REQ-050`/`HMIC-REQ-067`, live text): 25 files / 5
  contract_versions members.
- Production (`_FROZEN_AUTHORITY_BEARING_FILES`/`_CONTRACT_IDENTITY_FILES`,
  pre-edit): 24 files (`assert len(_FROZEN_AUTHORITY_BEARING_FILES) ==
  24`) / 4 contract_versions members.
- Exact delta: contract − production =
  `{docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md}` (files) /
  `{HBDC-001}` (contract members); production − contract = empty in
  both dimensions. Matches the expected delta named by 149O.20D.1/149O.20E.

## 4. Production Allowlist and Implementation

Only `src/pcae/core/hatp_mandatory_certification.py` was modified in
`src/pcae/**`. No `scripts/**` file was touched.

Change, in full:

1. `_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES` (5 → 6 entries): inserted
   `"docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"` as the 5th
   entry, immediately before `"scripts/hatp_certification_admin.py"` —
   matching HMIC-REQ-050's own literal presentation order exactly.
2. `assert len(_FROZEN_AUTHORITY_BEARING_FILES) == 24` →
   `assert len(_FROZEN_AUTHORITY_BEARING_FILES) == 25`. No permissive
   `>= 25` was used.
3. `_CONTRACT_IDENTITY_FILES` (4 → 5 entries): appended
   `("HBDC-001", "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md")`
   as the 5th, final entry — identical representation to the other four,
   no HBDC-specific parsing branch.
4. Module-level comment blocks in the same neighborhood (module
   docstring lines ~21/~117, and the block comments directly above the
   two frozen-set tuples and `_CONTRACT_IDENTITY_FILES`) were corrected
   from "24"/"four" to "25"/"five" — these described the *current*
   state of the very constants being changed, not historical narrative,
   so leaving them unedited would have made the file self-contradictory.

No other hunk exists. Hunk classification: `HBDC_FROZEN_SCOPE_ADDITION`
(the frozen-set tuple entry), `FROZEN_COUNT_ALIGNMENT` (the assert),
`HBDC_CONTRACT_IDENTITY_ADDITION` (the `_CONTRACT_IDENTITY_FILES`
entry), `DIRECT_COMMENT_ALIGNMENT` (the surrounding module-level
comments) — `CONTRACT_COUNT_ALIGNMENT`/`UNRELATED` are both **0**.

**Disclosed, deliberate documentation staleness (non-blocking):** three
function/class docstrings still say "four"/"the four contract files"
(`FrozenFileDerivationError`, `ContractIdentityDerivationError`,
`derive_contract_versions`'s own docstring) — left byte-unchanged so
that `test_every_function_and_class_body_is_ast_source_identical_to_
phase_entry` (§7 below) proves, with zero exceptions, that no
function/class body changed this phase. This is a minor, disclosed
documentation-accuracy gap, not a semantic defect; a future phase may
freshen these three docstrings' prose without touching behavior.

## 5. Self-Module Hashing Analysis (No Circularity)

Unchanged from 149O.19.5E.3's own precedent analysis:
`derive_implementation_scope_digest` hashes the *source bytes* of every
frozen file, including — still — `hatp_mandatory_certification.py`'s
own current on-disk bytes (this phase's own edits included). Because
the module's own bytes (including the very tuple/assert edits made in
§4) are what get hashed, self-binding is real and was verified directly
against the live repository (not a synthetic fixture) in
`test_live_digest_uses_post_edit_core_module_bytes_not_stale_cache`.

## 6. HBDC-001 Dual-Binding Analysis

Verified directly against production's own live functions (not a
scratch reimplementation only) in the new test module:

- **Content-digest binding** (`implementation_scope_digest`,
  HMIC-REQ-050/053-058): `test_hbdc_same_version_content_mutation_
  changes_implementation_scope_digest` — a same-version, content-only
  mutation of `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`
  changes the digest. This is the production closure of
  B-149O.20D-1's repaired property.
- **Version-header binding** (`contract_versions`, HMIC-REQ-067/069):
  `test_hbdc_version_drift_changes_contract_versions` — bumping
  HBDC-001's `**Version:**` header changes the derived
  `contract_versions["HBDC-001"]` value.
- **Contract-ID fail-closed**: `test_hbdc_wrong_contract_id_fails_
  closed` — a malformed/renamed Contract-ID header raises
  `ContractIdentityDerivationError`, no silent substitution.
- **Dual-binding mechanical check**:
  `test_hbdc_participates_in_both_scope_digest_and_contract_versions`
  — HBDC-001 is a member of both `_frozen_canonical_paths()` and
  `_CONTRACT_IDENTITY_FILES`.
- **Other-four regression**: `test_other_four_bound_contracts_dual_
  binding_regression` — the four pre-existing bound contracts'
  own dual binding is unweakened by this phase's addition of a fifth.

## 7. Algorithm, Git-Identity, Validator/Storage/Admin-Writer Stability

Verified two ways in the new test module:

1. **Whole-module AST sweep**
   (`test_every_function_and_class_body_is_ast_source_identical_to_
   phase_entry`): every top-level function/class body in
   `hatp_mandatory_certification.py` is byte-identical, via
   `ast.get_source_segment`, to this phase's own entry commit
   (`43ecacb9`) — **zero exceptions**, including the three docstrings
   disclosed in §4 as deliberately left stale. Only module-level
   statements (the two frozen-set tuples, `_CONTRACT_IDENTITY_FILES`,
   the count assert, and their comments) changed.
2. **Named spot-checks** on `derive_implementation_scope_digest`,
   `_frozen_canonical_paths`, `_canonical_frozen_path`,
   `derive_contract_versions`, `derive_implementation_commit`,
   `_run_git`, `_validate_at_root`,
   `validate_active_hatp_mandatory_independent_verification_certification`,
   the three Wave C writers, and the Wave A parsers/serializer.

`scripts/hatp_certification_admin.py`, `src/pcae/core/hatp_mandatory_
cutover.py`, and all nine frozen-corpus contracts (HMIC-001, HBDC-001,
and the seven other bound/upstream contracts) were confirmed
byte-unchanged since phase entry via direct `git show`/byte comparison.

## 8. Readiness/Cutover Semantics — Correction of a Stale Governing-Prompt Assumption

The governing phase instruction (§38-39) characterized production
readiness as gated by a "hard-coded `False`" ceiling with "zero
readiness/cutover callers of the validator" — accurate as of
149O.19.5E.3's own time, but **stale relative to the current repository**:
a later phase (Wave F, 149O.19.5F, independently confirmed closed at
149O.19.5E.4) already wired
`validate_active_hatp_mandatory_independent_verification_certification`
into `assess_hatp_mandatory_activation_readiness` — readiness is now
computed dynamically, not hard-coded. Per the governing instruction's
own item 3 ("Do not derive target lists only from this prompt"), this
was independently confirmed by reading `hatp_mandatory_cutover.py`
directly, not assumed from the prompt text.

`hatp_mandatory_cutover.py` remains byte-unchanged by this phase
(§7, `test_cutover_module_byte_unchanged_since_phase_entry`), and live
readiness was empirically re-confirmed `ready=False`
(`test_readiness_still_not_ready_against_real_production_state`) — no
real Protected Root, repository-identity file, or certification state
exists on this host, so the pre-existing readiness wiring correctly
reports NOT READY regardless of this phase's identity-alignment change.

## 9. Historical Repin-Debt Repaired This Phase (§100-104)

Widening production's live frozen-set/contract-identity constants from
24/4 to 25/5 caused 36 test failures across 9 pre-existing historical
phase test modules whose own assertions described production's state
*as of their own conclusion* using a **live** read of
`hatp_mandatory_certification.py` (a "moving reference" antipattern
this repository has repeatedly disclosed as repin-debt since
149O.19.5E.3, §10). Following that exact precedent (re-pin to the
phase's own fixed exit commit, never weaken the original claim), the
following modules were repaired:

- `tests/test_phase_149o_19_5b_hmic_identity_derivation.py` — Wave B's
  own **live** regression suite (not historical): count assertions
  24→25 / four→five, evolving current-state expectations exactly as
  149O.19.5E.3 evolved 22→24 for this same file. Added
  `test_hbdc_contract_now_in_v1_2_frozen_set`.
- `tests/test_phase_149o_19_5e_3_hmic_v1_1_24_file_production_identity_
  alignment.py` — 3 assertions ("still 24", "23 unchanged", "22 vs 24
  digest differs") re-pinned to that phase's own exit commit
  (`ca282cce`) via a new `_historical_canonical_paths_at()` helper.
- `tests/test_phase_149o_19_5e_4_hmic_v1_1_24_file_alignment_
  independent_verification.py` — `_production_canonical_paths()` (used
  by genuinely-historical count/delta/AST-diff claims) re-pinned to
  that phase's own exit commit (`dd649271`); a new
  `_live_production_canonical_paths()` helper introduced for the
  distinct "production's live self-consistency" cross-checks
  (contract-vs-production set equality, `_frozen_canonical_paths()`
  vs. independent re-derivation) that legitimately track the *current*
  live state, not a historical snapshot.
- `tests/test_phase_149o_19_5f_hmic_activation_readiness_integration.py`
  — 3 assertions re-pinned to that phase's own exit commit
  (`a786f89f`, newly named `_PHASE_149O_19_5F_EXIT_COMMIT`) via a new
  `_historical_frozen_canonical_paths_at()` helper.
- `tests/test_phase_149o_19_5g_hmic_assembled_attack_matrix_hardening.py`
  — 1 **live** assertion (explicitly documented as "currently-live" in
  its own docstring) evolved 24→25, renamed
  `test_real_25_file_enumeration_includes_self_binding_admin_and_
  cutover_files`.
- `tests/test_phase_149o_20c_hatp_class_b_deployment_contract_
  independent_verification.py` — 3 assertions re-pinned to that phase's
  own exit commit (`4e7d137c`) via a new
  `hatp_mandatory_certification_text_at_phase_exit` fixture, added
  alongside (not replacing) the existing live fixture used by this
  module's many unrelated, unaffected semantic checks.
- `tests/test_phase_149o_20d_hmic_v1_2_hbdc_bound_contract_identity_
  evolution.py` — 1 assertion re-pinned to that phase's own exit commit
  (`86f89841`).
- `tests/test_phase_149o_20d_1_hmic_v1_2_hbdc_content_identity_binding_
  repair.py` — 3 assertions re-pinned to that phase's own exit commit
  (`7c632bdf`).
- `tests/test_phase_149o_20e_hmic_v1_2_hbdc_bound_contract_identity_
  independent_verification.py` — 3 assertions re-pinned to that phase's
  own exit commit (`43ecacb9`, this phase's own entry commit) via a new
  `_HMIC_MODULE_TEXT_AT_PHASE_EXIT` constant, added alongside the
  existing live `_HMIC_MODULE_TEXT` used elsewhere in the module.

No historical claim was rewritten or weakened; every re-pinned
assertion's original numeric claim (24, four, "23 unchanged", etc.) is
preserved exactly, now measured against that phase's own fixed
historical commit instead of live/moving source.

**Not fixed (pre-existing, confirmed via `git stash` baseline re-run,
outside this narrow phase's scope):** contract-side drift from HMIC-001's
own v1.1→v1.2 evolution and the 149O.20D.1 HBDC-001 addition — both
predate and are independent of this phase's production-alignment work
— accounts for the remaining pre-existing failures in
`test_phase_149o_19_5e_2`, `test_phase_149o_19_5e_3`(2 of its own
assertions), `test_phase_149o_19_5e_4`(1), `test_phase_149o_19_5f`(1),
`test_phase_149o_19_5g`(1), `test_phase_149o_20c`(1), plus the
long-standing, previously-disclosed unrelated failure clusters in
`test_phase_149o_13`/`14`/`15`/`16`/`16_2`/`17`/`18c`/`18d`/`19_2`/
`19_3`/`19_3r`/`19_3r_1`/`19_4`/`19_5e_1`, and
`test_hatp_mandatory_certification_models.py`'s pre-existing fraction-
literal test defect. None of these were introduced by this phase, and
none are in this phase's allowed-file scope.

## 10. Tests

New: `tests/test_phase_149o_20f_hmic_v1_2_hbdc_25_file_5_contract_
production_identity_alignment.py` (46 tests — production/contract
exact 25-file and 5-contract-member set equality with literal
presentation-order equality, file safety, 24-unchanged/1-changed byte
diff, AST function/class-identity sweep with zero exceptions, live
self-binding/dual-binding/mutation-sensitivity/replay/golden digest
tests against production's own real functions, HBDC content/version/
Contract-ID drift fail-closed behavior, no-legacy-override, empirical
NOT-READY readiness confirmation, no-real-certification-state).

Updated (repairing repin-debt per §9, evolving live current-state
expectations per §9's first bullet): the 9 modules listed above.

## 11. Regressions

- New module: **46/46 passed**.
- 9 repaired historical modules: all pass except each module's own
  pre-existing, unrelated failures (§9's "Not fixed" paragraph),
  unchanged in count/identity from phase entry (confirmed via `git
  stash` baseline re-run of the exact failing node-ID set before any
  fix).
- Fast Green (`pytest -m fast_green`, deselecting the pre-existing,
  environment-caused `fido2`-import collection error in
  `test_phase_149o_7_...py`, confirmed via `git stash` to predate this
  phase and be unrelated to it): raw run **71 failed / 6497 passed / 4
  skipped / 25375 deselected** at this phase's own final, uncommitted
  working tree. Of the 71: **9 are working-tree-dirty checks**
  (`git status --porcelain`/`git diff HEAD` against `src/pcae`,
  never a historical-commit comparison) that fail only while this
  phase's own edit is uncommitted and resolve once committed — the
  identical, previously-documented artifact 149O.19.5E.3 itself
  disclosed for this exact test class. **4 are a confirmed-spurious
  concurrent-task-state artifact**
  (`tests/test_backend_cli.py`, 4 sub-tests) — reproduced as failing
  only when run inside the same full-suite pass as this session's
  `pcae task new`/`task update`/`task close` calls, and confirmed
  passing 307/307 in isolation; matches this repository's own
  previously-documented gotcha ("running the full suite concurrently
  with task-lifecycle mutations produces spurious extra failures in
  tests reading live `tasks/active/` state"). The remaining **58** are
  reproduced **identically** against this phase's own entry commit
  (`43ecacb9`) via `git stash push -u` (removed after use): pre-existing,
  unrelated to this phase, not introduced by it, and confirmed via the
  exact same failing-node-ID set before any of this phase's edits.
  Deselected/attributable-to-this-phase new failure count: **0**.
- Broad `-k "hmic or hbdc or 149o_20 or 149o_19_5"` sweep: consistent
  with the Fast Green attribution above; no additional HMIC-specific
  regression found beyond the 9 dirty-tree/repin items already
  addressed.

## 12. Findings

**No blocking findings.** Production and contract 25-file /
5-contract-member sets are exactly equal, including literal
presentation order. HBDC-001 participates in both
`implementation_scope_digest` (content bytes) and `contract_versions`
(version header) — the dual binding is mechanically proven, not
merely asserted. Same-version content drift, version drift, and
Contract-ID drift on HBDC-001 are all now digest-/mapping-sensitive
and fail-closed, proven against production's own live functions. The
digest algorithm, path canonicalization, Git identity, and
validator/storage/admin-writer semantics are AST-proven unchanged with
zero exceptions. The original 24 frozen-set entries and 4
contract-identity members remain present. `scripts/hatp_certification_
admin.py`, `hatp_mandatory_cutover.py`, HMIC-001, HBDC-001, and all
seven other bound/upstream contracts remain byte-unchanged. No real
Class-B provisioning, certification, active binding, revocation, or
Cutover Record/activation exists on this host, before or after.

**Non-blocking, disclosed.** (1) Three function/class docstrings still
say "four"/"the four contract files" (§4) — deliberately left
byte-unchanged to preserve a zero-exception AST function/class-identity
proof; cosmetic, not a semantic defect. (2) The governing phase
instruction's characterization of readiness as "hard-coded `False`"
with "zero validator callers" was stale relative to the current
repository (§8) — corrected here via direct source inspection, not
propagated. (3) 9 pre-existing repin-debt failures were repaired this
phase (§9); a further, smaller set of pre-existing contract-side-drift
and long-standing unrelated failures remain, out of this narrow phase's
scope, unchanged in count from phase entry.

## 13. Verdict

**HMIC v1.2 HBDC PRODUCTION IDENTITY ALIGNMENT: IMPLEMENTED —
PRODUCTION NOW MATCHES VERIFIED 25-FILE / 5-CONTRACT CONTRACT —
HBDC DUAL BINDING PRESENT IN PRODUCTION — INDEPENDENT IMPLEMENTATION
VERIFICATION PENDING.**

- Contract source/content count: **25**. Production source/content
  count before: **24**. After: **25**. Exact 25th addition:
  `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`. Source/content
  exact equality: **YES**.
- Contract `contract_versions` count: **5**. Production contract
  identity count before: **4**. After: **5**. Exact fifth addition:
  `HBDC-001`. Contract identity exact equality: **YES**.
- HBDC-001 participates in `implementation_scope_digest`: **YES**.
  Participates in `contract_versions`: **YES**. Dual binding complete
  in production: **YES**.
- Same-version HBDC-001 content drift visible: **YES**. Version drift
  visible: **YES**. Contract-ID drift visible (fail-closed): **YES**.
  25/25 mutation sensitivity: **YES** (all 25 live files individually
  digest-sensitive).
- Original 24 preserved: **YES**. Original 4 contract members
  preserved: **YES**.
- Digest algorithm changed: **NO**. Contract identity algorithm
  changed: **NO**. Git identity changed: **NO**. `CertificationStatus`
  vocabulary changed: **NO**. Artifact schema changed: **NO**.
  Validator semantics changed: **NO**. Store semantics changed: **NO**.
  Parser/model semantics changed: **NO**. Admin script changed: **NO**.
  Cutover/readiness semantics changed: **NO**. Core HMIC module
  post-edit bytes participate in digest: **YES**. Legacy 24-file/
  4-contract selector: **NO** (neither exists).
- Pre-20F replay result: rejected (24/4-scope digest ≠ live 25/5-scope
  digest for an identical snapshot). Pre-repair-v1.2 and v1.1 replay
  results: unaffected, still rejected (unchanged mechanism).
  HMIC-REQ-063/Option-C retained: **YES**. Class-B environment lock
  implemented: **NO**. Real Class-B provisioned: **NO**. Real
  Protected Root/certification/active binding/activation: **NO**.
- Production files modified: **1** (expected 1).
  Frozen subject files changed: **1** (expected 1, itself frozen).
  Other 24 target frozen files unchanged: **YES** (24, expected 24).
  Contracts changed: **NO**. PB changed: **NO**. POL-005 changed:
  **NO**. COMP-002 implemented: **NO**. Runtime changed: **NO**.

**B-149O.20D-1 exit status:** CONTRACT DEFECT CLOSED — PRODUCTION
REPAIR IMPLEMENTED — **INDEPENDENT IMPLEMENTATION VERIFICATION
PENDING.**

**HBDC-BINDING-GATE exit status:** PRODUCTION 25-FILE / 5-CONTRACT
ALIGNMENT IMPLEMENTED — INDEPENDENT IMPLEMENTATION VERIFICATION
PENDING — **NOT CLOSED.**

**W-1, B-149O.19.3-1, B-149O-1..4:** unaffected, remain independently
closed at their own respective boundaries.

**Class-B status:** CONTRACT VERIFIED — NOT PROVISIONED, unchanged.

**HATP production readiness:** NOT READY (empirically re-confirmed,
§8). **Runtime:** Observed / observe / unavailable — unchanged by this
phase.

**Recommended next phase:** **149O.20G — HMIC v1.2 HBDC 25-File /
5-Contract Production Identity Alignment Independent Verification**
(independently re-derive and confirm every claim in §2-§9 above from
primary sources, not this document's prose; adjudicate B-149O.20D-1
and HBDC-BINDING-GATE at the implementation-verification boundary).
NOT a Class-B deployment-verifier/environment-lock/provisioning
planning phase.
