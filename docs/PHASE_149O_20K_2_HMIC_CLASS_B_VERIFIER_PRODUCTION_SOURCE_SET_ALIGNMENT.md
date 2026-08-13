# Phase 149O.20K.2 — HMIC Class-B Verifier Production Source-Set Alignment

**Purpose.** Align live production HMIC (`src/pcae/core/
hatp_mandatory_certification.py`) with the independently verified
(149O.20K.1) HMIC-001 v1.3 Class-B verifier source-scope contract. This
is the production implementation/alignment phase. Does not redesign
HMIC-001, does not expand the target beyond the independently verified
28-file set, does not perform readiness integration, does not
provision Class-B, does not certify or activate HATP, and does not
close CBV-S1.

## 1. True phase-entry commit

`17a797af58a8f82605ed2d69f30a9959c27dac1d` — "Phase 149O.20K.1: task
lifecycle transitions (close to idle)" — 149O.20K.1's own exit commit,
confirmed via `git log -1 HEAD` at this phase's own initial
inspection, before any change was made.

## 2. Pre-alignment live 25/5 reconstruction

Read directly from `src/pcae/core/hatp_mandatory_certification.py` at
phase entry: `_FROZEN_SRC_PCAE_RELATIVE_FILES` (19 entries) +
`_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES` (6 entries) =
`_FROZEN_AUTHORITY_BEARING_FILES`, `assert len(...) == 25`.
`_CONTRACT_IDENTITY_FILES`: exactly 5 `(contract_id, path)` pairs
(`HMRC-001`, `HATP-001`, `HSCE-001`, `RAE-001`, `HBDC-001`), unchanged
since 149O.20F. None of the three Class-B verifier modules present in
either constant. Confirmed via `git show 17a797af:...` matching the
live pre-edit source exactly.

## 3. Reconfirmation of the independently verified target (sanity check, not re-design)

Read the live contract directly (not from any prior phase's summary):
HMIC-REQ-050's fenced enumeration, extracted via a fresh regex parse,
is exactly 28 entries, unchanged since 149O.20K. HMIC-REQ-052 still
carries limb (c), unchanged. The three newly required entries are,
verbatim, `core/hatp_class_b_topology_verifier.py`,
`core/hatp_environment_lock_verifier.py`,
`core/hatp_class_b_conformance.py` — identical to K.1's independently
verified target. No inconsistency found; this phase proceeds on the
existing, already-independently-verified contract without amending it.

## 4. Exact production diff

Exactly one production file touched:
`src/pcae/core/hatp_mandatory_certification.py`. Confirmed via
`git diff --name-only 17a797af HEAD -- src/pcae` (see §14) and via
AST function/class-body comparison (see §11) that no function or class
body changed — only module-level constants and their surrounding
comments.

## 5. Exact +3 delta

`_FROZEN_SRC_PCAE_RELATIVE_FILES` gained exactly three entries, appended
in the contract's exact presentation order (after
`core/hatp_mandatory_certification.py`, before the repository-root-
relative bucket):

```
core/hatp_class_b_topology_verifier.py
core/hatp_environment_lock_verifier.py
core/hatp_class_b_conformance.py
```

`_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES` (6 entries) and
`_CONTRACT_IDENTITY_FILES` (5 members) are byte-identical to phase
entry — this amendment widened HMIC-REQ-050 only, not HMIC-REQ-067; no
sixth contract-identity member was added for the Class-B verifier.
`assert len(_FROZEN_AUTHORITY_BEARING_FILES) == 28` (was `== 25`).
Module-level comments naming the file/member counts and version
(`v1.2`/`25-path`) updated to `v1.3`/`28-path`, mirroring 149O.20F's
24→25 precedent exactly — historical "added at v1.2 ..." provenance
comments describing the HBDC-001 addition are preserved unchanged (they
are correct historical references, not current-target claims).

## 6. Exact retained 25

The pre-alignment 25-file set (`_entry_frozen_authority_bearing_files`,
reconstructed via AST parse of the phase-entry commit's source) is a
strict subset of the current 28-file `_FROZEN_AUTHORITY_BEARING_FILES`
— `current - entering == {the three Class-B files}`,
`entering - current == set()`. No existing bound file was removed,
renamed, or reordered.

## 7. Contract identity behavior (§6-7 of the governing instruction)

`_CONTRACT_IDENTITY_FILES` stores `(contract_id, path)` pairs only —
versions are never hardcoded; `derive_contract_versions` reads each
bound contract's own live `**Version:**` header at call time
(drift-detected dynamically, never a stored expected value). HMIC-001
itself has no self-version constant in production (its own version
lives only in its own contract-file header) — there is no live
mechanism that could "report v1.2 while using v1.3 source scope"; the
only production-visible v1.2/v1.3 identity signal is the module-level
comment describing the frozen-set constant's own version and file
count, which this phase updated to v1.3/28-path (§5, §18). No sixth
contract-identity member was added for the Class-B verifier (§7) — the
five-contract model is preserved unweakened.

## 8. HMIC v1.3 production identity representation

The module docstring's Wave B API description
(`_FROZEN_AUTHORITY_BEARING_FILES` (HMIC-REQ-050's literal 28-path
enumeration, v1.3)`) and the frozen-set count-assertion comment
(`# HMIC-REQ-050 (v1.3): exactly 28, no more, no fewer.`) now correctly
state v1.3/28, eliminating any v1.2/v1.3 contradiction between the
module's own comments and its live 28-file source scope.

## 9. Per-new-file digest sensitivity

Exercised individually against the real `derive_implementation_scope_
digest` mechanism, using isolated fixture-tree copies (never mutating
committed production files in place), restored after each test:

- `hatp_class_b_topology_verifier.py`: appended-byte mutation and a
  semantically meaningful mutation (`COMPLIANT = "COMPLIANT"` →
  `COMPLIANT = "COMPLIANT_MUTATED"`) both change the aggregate digest.
- `hatp_environment_lock_verifier.py`: appended-byte mutation and a
  semantically meaningful mutation (a new module-level marker
  assignment) both change the digest.
- `hatp_class_b_conformance.py`: appended-byte mutation and a
  semantically meaningful mutation (a docstring edit to the "Strictly
  read-only" sentence) both change the digest.

Each test mutates a copy under `tmp_path`, computes the digest via an
independently reimplemented two-level SHA-256 construction (mirroring
HMIC-REQ-054/056-058, not calling production's own digest function for
the mutation half), and restores original bytes before the next
assertion — sensitivity is proven, not inferred from list membership.
See `tests/test_phase_149o_20k_2_...py::test_each_new_verifier_file_is_
individually_digest_sensitive` (parametrized ×3) and the three
`test_*_semantic_mutation_changes_digest` tests.

## 10. Missing-new-file fail-closed behavior

For each of the three new files, individually, in an isolated fixture
tree: deleting the file and calling production's own
`derive_implementation_scope_digest` raises `FrozenFileDerivationError`
(HMIC-REQ-059) — no partial digest is ever silently returned. Verified
against the real, unmodified `_resolve_and_reject_unsafe_frozen_file`/
`derive_implementation_scope_digest` functions, not a reimplementation.

## 11. Representative existing-file digest sensitivity

Reconfirmed digest-sensitive after the 25→28 alignment: the HMIC/
certification module itself (`hatp_mandatory_certification.py`), all
four B-149O.19.3-1 provider files (`hatp_providers.py`,
`hatp_fido2_provider.py`, `hatp_piv_provider.py`,
`hatp_hardware_credentials.py`), and HBDC-001's document bytes (a
same-version content-only edit still changes
`implementation_scope_digest`). This proves the new alignment did not
replace or bypass existing identity participation.

## 12. HBDC binding preservation

`docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` continues to
participate in both dimensions: content bytes in
`implementation_scope_digest` (§11) and version header in
`contract_versions` (`derive_contract_versions(...)["HBDC-001"] ==
"1.0"`, unchanged). B-149O.20D-1 stays **INDEPENDENTLY CONFIRMED CLOSED
AT CONTRACT + PRODUCTION IDENTITY BOUNDARY** — not reopened; no
contradictory evidence found.

## 13. B-149O.19.3-1 regression

All four historical provider dependency files (`hatp_providers.py`,
`hatp_fido2_provider.py`, `hatp_piv_provider.py`,
`hatp_hardware_credentials.py`) remain members of
`_frozen_canonical_paths()` and remain individually digest-sensitive
(§11) — the Class-B additions did not displace or omit any existing
source.

## 14. Path uniqueness / normalization / safety

All 28 frozen canonical paths exist, are regular files, and are not
symlinks (`test_all_28_frozen_paths_exist_are_regular_and_not_
symlinked`). No duplicate entries in `_FROZEN_AUTHORITY_BEARING_FILES`
or `_frozen_canonical_paths()`. The three new entries are accepted by
the unmodified `_validate_frozen_path_literal`/`_canonical_frozen_path`
functions with no special-casing. `derive_implementation_scope_digest`
and `derive_contract_versions` accept no caller-suppliable scope-
override parameter (`inspect.signature` shows `{"root"}` only).

## 15. Cycle / self-binding regression (W-1)

A fresh AST walk (independent per-file, not reused from any prior
phase) found zero `Import`/`ImportFrom` node in any of the three new
verifier modules naming `hatp_mandatory_certification` or
`hatp_certification_admin`. A fresh AST walk of
`hatp_mandatory_certification.py` and `scripts/hatp_certification_
admin.py` found zero `Import`/`ImportFrom` node naming any of the
three verifier modules — the frozen-set constants bind by path
*string*, never by import. W-1 not reopened; no new cycle introduced.

## 16. Zero-consumer check

A fresh `grep -rl -E --include=*.py` sweep of `src/pcae/` for the three
module names and the three exported verification functions found
matches only inside the island itself and
`hatp_mandatory_certification.py` (the frozen-set path-literal
binding, confirmed non-import/non-call in §15). No other production
module — not `hatp_mandatory_cutover.py`, not `scripts/hatp_
certification_admin.py`, not any readiness/certification/activation/
Permission-Broker code — references the island. Spot-checked several
of the resulting historical test failures (§20) directly and confirmed
each is the same naive path-substring pattern, not a genuine new
consumer.

## 17. Class-B module byte-identity

All three Class-B verifier modules
(`hatp_class_b_topology_verifier.py`, `hatp_environment_lock_
verifier.py`, `hatp_class_b_conformance.py`) are byte-identical to
their phase-entry (`17a797af`) content, confirmed via `git show
17a797af:<path>` comparison. This phase binds; it does not modify.

## 18. HMIC contract byte-identity

`docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_
CONTRACT.md`, `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`, and
the other three upstream bound contracts are byte-identical to
phase-entry content. `scripts/hatp_certification_admin.py` is
byte-identical to phase-entry content. `git diff --name-only 17a797af
HEAD -- docs/contracts` and `-- scripts` are both empty.

## 19. AST function/class-body identity

Every top-level function and class body in
`hatp_mandatory_certification.py` (`ast.get_source_segment` per node)
is source-identical to the phase-entry commit — the function/class
inventory is unchanged and zero body differs. Specifically reconfirmed
unchanged: `derive_implementation_scope_digest`, `_frozen_canonical_
paths`, `_canonical_frozen_path`, `derive_contract_versions`,
`_validate_at_root`, `validate_active_hatp_mandatory_independent_
verification_certification`, `_append_certification_record`,
`_write_active_binding`, `_write_revocation`,
`parse_certification_record`, `parse_certification_binding`,
`canonical_serialize`. Only module-level constants and their
surrounding comments changed.

## 20. Historical-test disposition

Fixed pre-K.2 baseline: `git worktree add --detach /tmp/pcae_149o_20k2_
baseline 17a797af` (not `git stash`), `PYTHONPATH` forced to the
worktree's own `src/`, verified via `python3 -c "import pcae; print(pcae.
__file__)"` resolving inside the worktree.

**Fast Green baseline:** 106 failed, 6803 passed, 5 skipped, 10 errors
(116 unique failing/error node IDs).
**Fast Green current-HEAD** (raw, with the new 55-test module
included): 137 failed, 6827 passed, 5 skipped, 10 errors (147 unique
nodes).

Exact node-ID `comm` diff: **40 new nodes**, independently classified,
none left unclassified:

- Fixed-commit `git status`/`git diff`/"dirty working tree" self-checks
  in prior historical phases (149O.14, 149O.17, 149O.19.4, 149O.1G,
  149O.20A, 149O.20C, 149O.20D, 149O.20D.1, 149O.20E, 149O.20H) whose
  own entry commit predates this phase's production edit — any future
  production-file edit permanently triggers these (documented
  repin-debt, not this phase's defect).
- Historical fixed-25/24-file-count and fixed-delta assertions
  (149O.19.5B ×3, 149O.19.5G, 149O.20F ×4, 149O.20G ×2) — legitimately
  superseded now that production is 28, not 25/24.
- **The largest category** — 149O.20I (×5), 149O.20J.3 (×3), 149O.20J
  independent-verification (×4), 149O.20K (×3), 149O.20K.1 (×4)'s own
  historical self-checks asserting the Class-B verifier is "not yet in
  HMIC's frozen scope" / "zero production consumers", using a naive
  path-substring search rather than an AST/import distinction — now
  correctly, predictably superseded because
  `hatp_mandatory_certification.py` legitimately names the three
  verifier files as path literals (§15, §16). Spot-checked
  `test_readiness_certification_admin_pb_files_have_zero_references`
  (149O.20J.2) and `test_zero_production_consumers_of_topology_
  verifier` (149O.20J.3) directly — both use `grep -rl <name> src/pcae/`
  with no AST distinction. This is the intended, designed effect of
  HMIC-REQ-052(c) — not a defect.
- One confirmed pytest-xdist ordering flake:
  `test_backend_cli.py::TestBackendReviewCreate::test_create_json_no_
  secrets` — passes 1/1 in isolation.

**9 nodes fixed** (in baseline, absent at HEAD): 8 "contract and
production literal order/set is identical" tests spread across
149O.19.5B (×1), 149O.19.5E.3 (×1), 149O.19.5E.4 (×2), 149O.20F (×1),
and 149O.20G (×3) that dynamically extract the *live* contract
enumeration and compare it to the *live* production constant — these
were failing only during the 149O.20K/149O.20K.1 window (contract at
v1.3/28, production still at 25) and now correctly pass again since
both sides read 28, entry for entry. Plus one confirmed
`test_shell_gate.py::TestAuditPersistence::test_verify_detects_tampered_
record` xdist ordering flake (passes 7/7 in isolation). **Zero
previously-failing node was fixed by weakening, rewriting, or
repointing a test** — every non-flake fixed node is a natural
consequence of production now matching the already-independently-
verified contract.

**Broad sweep** (`pytest -k 'hmic or hbdc or class_b or 149o_20' -n
auto`): baseline 81 failed/1555 passed/5 skipped/10 errors (91 unique
nodes); current-HEAD 125 failed/1566 passed/5 skipped/10 errors (135
unique nodes). New-node set is a superset of the fast_green new-node
set (marker-filtered vs. keyword-filtered), with the additional
109O.20J.2/20J.4/20J.5/20J.6/20J.7/20J.8-family nodes following the
identical naive-substring pattern (§16, spot-checked
`test_readiness_certification_admin_pb_files_have_zero_references`),
plus one meta-test
(`149O.20J.8::test_j6_suite_still_passes_in_full_after_the_pin_update`)
that reruns 149O.20J.6's own suite in a subprocess and transitively
fails for the identical reason. Fixed-node set identical to the
fast_green fixed set. No genuinely new-root-cause failure found in
either sweep.

## 21. Clean-deselected citation

A 148-node `--deselect` argv list (Python subprocess argv, not shell
string interpolation) covering the 147 HEAD-failing nodes plus one
further xdist flake (`test_shell_gate.py::TestAuditPersistence::
test_audit_verify_cli`, identified after the first clean run, confirmed
passing 7/7 in isolation) was run twice:

- Run 1: 0 failed, 6826 passed, 5 skipped, 1 pre-existing collection
  error (`test_phase_149o_7_hatp_class_b_activation_independent_
  verification.py` — missing `fido2` module, pre-existing/unrelated).
- Run 2: identical — 0 failed, 6826 passed, 5 skipped, 1 pre-existing
  collection error.

This is the primary evidence citation. It is not the sole proof of
correctness — the exact node-ID classification in §20 is.

## 22. Real-host result

`verify_class_b_deployment_conformance()` called directly against the
real host (read-only): returns `ClassBConformanceStatus.NON_COMPLIANT`
as expected (host deliberately unprovisioned — no Protected Root, no
admin-provisioned interpreter/venv, several HBDC-REQ checks
unsatisfied). `git status --porcelain` confirmed unchanged immediately
before and after the call.

## 23. CBV-S1 exact status

**OPEN — PRODUCTION HMIC SOURCE-SET ALIGNED TO INDEPENDENTLY VERIFIED
HMIC-001 v1.3 TARGET — INDEPENDENT PRODUCTION ALIGNMENT VERIFICATION
PENDING — NOT CLOSED.** Not closed by this phase.

## 24. CBV-S10 exact status

**OPEN — READINESS CONTRACT/INTEGRATION GAP.** Untouched by this
phase — no readiness requirement, activation-readiness calculation,
certification gate, cutover, or activation code path was modified.
`assess_hatp_mandatory_activation_readiness(...)` still returns
`ready=False` against the real, unprovisioned host.

## 25. Class-B / HATP / runtime state

Class-B: **CONTRACT VERIFIED — VERIFIER REPAIR LINE INDEPENDENTLY
VERIFIED — HMIC v1.3 CONTRACT INDEPENDENTLY VERIFIED — PRODUCTION HMIC
SOURCE SET ALIGNED — INDEPENDENT ALIGNMENT VERIFICATION PENDING — NOT
PROVISIONED.** HATP production: **NOT READY.** Runtime: **Observed /
observe / unavailable** (unchanged — no Permission Broker, POL-005,
COMP-002, or runtime enforcement file touched).

## 26. Tests actually run

- New: `tests/test_phase_149o_20k_2_hmic_class_b_verifier_production_
  source_set_alignment.py` — 55 tests, all passing.
- Full `pytest -m fast_green -n auto` (raw and clean-deselected, twice).
- `pytest -k 'hmic or hbdc or class_b or 149o_20' -n auto` (baseline and
  HEAD).
- Isolated reruns of both identified xdist flakes, confirming pass in
  isolation.

## 27. Governance results

`pcae health`: healthy. `pcae check`: passed. `pcae status coherence`:
coherent. `pcae doctor task-memory`: warnings (pre-existing,
unrelated — historical `tasks/done/`/`DONE.md` gap predating this
phase, outside this phase's allowed-file scope). `pcae push check`:
clean prior to this phase's own commit. `pcae runtime inspect`:
Observed / observe / unavailable (unchanged). `pcae notify status`:
Telegram configured/enabled. `pcae phase-report reconcile --phase-id
149O.20K.1`: reconciled, read-only, no mutation.

## 28. Phase-owned commits, pushed status, origin/main..HEAD

Recorded in `.pcae/phase-completion-metadata.json` at governed
completion time.

## 29. Exact next-phase recommendation

**Phase 149O.20K.3 — HMIC Class-B Verifier Production Source-Set
Alignment Independent Verification.** Not begun by this phase. Must
independently verify: the exact production 28-file set; exact
contract/production equality; HMIC v1.3 identity representation; each
of the three new files individually digest-sensitive; existing 25
preserved; HBDC binding preserved; provider-source binding preserved;
missing-file fail-closed behavior; no source alias/normalization gap;
no consumer introduced; no cycle introduced; the three Class-B modules
byte-unchanged; the HMIC/HBDC contracts byte-unchanged; real host
remains NON_COMPLIANT; CBV-S10 remains OPEN. Only a clean K.3 may
consider CBV-S1 independently closed. This phase does not close CBV-S1,
does not begin K.3, does not begin readiness integration, and does not
provision Class-B.
