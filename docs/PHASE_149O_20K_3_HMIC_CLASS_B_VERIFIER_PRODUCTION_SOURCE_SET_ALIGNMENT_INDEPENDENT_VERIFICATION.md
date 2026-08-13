# Phase 149O.20K.3 — HMIC Class-B Verifier Production Source-Set Alignment Independent Verification

**Purpose.** Independently verify Phase 149O.20K.2's production
alignment of live HMIC (`src/pcae/core/hatp_mandatory_certification.py`)
to the independently verified HMIC-001 v1.3 Class-B verifier
source-scope target (28 authority-bearing files). Verification-only:
no production source or contract modification. Does not perform
readiness integration, does not provision Class-B, does not certify or
activate HATP.

Trusted nothing from K.2's report or test module. Every claim below is
re-derived from primary sources (git history, live contract text, live
production source, and fresh calls into the real, unmodified
`derive_implementation_scope_digest`/`derive_contract_versions`/
`verify_class_b_deployment_conformance` functions against isolated
fixtures or, for the real-host check only, the live repository
read-only).

## 1. True K.2 parent

`git rev-parse 05e3861b^` independently resolves to
`17a797af58a8f82605ed2d69f30a9959c27dac1d`, "Phase 149O.20K.1: task
lifecycle transitions (close to idle)" — K.1's own exit commit,
matching K.2's own §1 claim, confirmed independently rather than
trusted.

## 2. Exact K.2 production diff

`git diff --name-only 17a797af 05e3861b` → exactly one `src/pcae/`
file touched: `src/pcae/core/hatp_mandatory_certification.py` (36
lines changed: two docstring/comment updates, the `+3` tuple entries,
and the `25`→`28` assert-count literal). All other seven files in
K.2's commit are docs/report/task-lifecycle scaffolding
(`CHANGELOG.md`, `PROJECT_STATUS.md`,
`docs/PHASE_149O_20K_2_...md`, `tasks/DONE.md`,
`tasks/active/...20k-2....md`, `tasks/done/...post-149o-20k-1.md`,
`tests/test_phase_149o_20k_2_...py`).

## 3. Pre-K.2 production reconstruction (25/5)

Read `hatp_mandatory_certification.py` at `17a797af` directly (`git
show`), not from K.2's report: `_FROZEN_SRC_PCAE_RELATIVE_FILES` = 19
entries, `_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES` = 6 entries, total
25. None of the three Class-B verifier modules present.
`_CONTRACT_IDENTITY_FILES` = 5 members (`HMRC-001`, `HATP-001`,
`HSCE-001`, `RAE-001`, `HBDC-001`).

## 4. Current production reconstruction (28/5)

Read the live file directly: `_FROZEN_SRC_PCAE_RELATIVE_FILES` = 22
entries, `_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES` = 6 entries, total
28, all unique. `_CONTRACT_IDENTITY_FILES` unchanged at 5 members.

## 5. Independent contract extraction

Parsed HMIC-REQ-050's fenced enumeration directly out of
`docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`
with a fresh regex/parse (own extraction method, not K.2's copied
list): 28 entries, in the contract's own presentation order.

## 6. Exact contract/production equality

Independently-extracted contract path list == live production path
list (`_FROZEN_SRC_PCAE_RELATIVE_FILES + _FROZEN_REPOSITORY_ROOT_RELATIVE_FILES`),
both as sets and in exact presentation order. No mismatch.

## 7. Exact +3 delta / 25-preservation

`current_set - pre_set == {core/hatp_class_b_topology_verifier.py,
core/hatp_environment_lock_verifier.py, core/hatp_class_b_conformance.py}`,
`pre_set - current_set == {}` (empty — no removal), `pre_set ⊂
current_set`. All 28 canonical paths unique (no duplicate entry
inflating the apparent count).

## 8. Byte-identity since K.2 entry (`17a797af` → current)

All byte-identical (SHA-256 compared): the three Class-B verifier
modules, `HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`
(HMIC-001 itself), `HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` (HBDC-001),
and the four other bound contracts (`HMRC-001`, `HATP-001`, `HSCE-001`,
`RAE-001`) plus `scripts/hatp_certification_admin.py`. K.2 aligned
production to the contract; it did not mutate the contract or the
already-verified verifier code.

## 9. Digest derivation code review

Read `_validate_frozen_path_literal`, `_canonical_frozen_path`,
`_frozen_canonical_paths`, `_resolve_and_reject_unsafe_frozen_file`,
`_read_frozen_file_bytes`, and `derive_implementation_scope_digest`
directly. Mechanism: two-level SHA-256 (per-file digest, then a
lexicographically-ordered `path\0digest\n` record hash), symlink
rejection walking every path component up to `repository_root`,
`O_NOFOLLOW` TOCTOU-resistant read, `FrozenFileDerivationError` fail-
closed on missing/symlinked/non-regular/unreadable files — no partial
digest ever returned.

## 10. Digest sensitivity (isolated fixture, real production function)

Built an isolated 28-file fixture (copied from live canonical paths)
and called the real, unmodified `derive_implementation_scope_digest`
against it (not a reimplementation). Results, independently obtained:

- All three new files: digest changes on both a semantically
  meaningful appended-comment mutation **and** a single-flipped-byte
  mutation (byte-level sensitivity, not just semantic-region
  sensitivity).
- Representative existing files (`hatp_mandatory_certification.py`,
  `hatp_providers.py`, `hatp_fido2_provider.py`, `hatp_piv_provider.py`,
  `hatp_hardware_credentials.py`) and `HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`:
  still digest-sensitive — the 28-file alignment is additive, not
  displacing.
- `derive_contract_versions` on the same fixture: `HBDC-001` present —
  HBDC dual-binding (content digest + version mechanism) reconfirmed.

## 11. Missing-file / unreadable-file fail-closed

Independently simulated, on the isolated fixture, each of the three
new files missing (renamed out) and one made unreadable (`chmod
0o000`): every case raised `FrozenFileDerivationError`; no partial
digest returned in any case. Fixture was not copied from K.2's test
module.

## 12. Alias / normalization / duplicate-entry attack

Swapped one new file for a symlink to a decoy file on the isolated
fixture: `derive_implementation_scope_digest` raised
`FrozenFileDerivationError` (symlink rejected before read, per
HMIC-REQ-061) rather than silently digesting the decoy.
`_validate_frozen_path_literal` independently confirmed to reject a
`..`-segment path and an absolute path. `_frozen_canonical_paths()`
independently confirmed to return exactly 28 unique canonical entries
— no duplicate inflating the count.

## 13. HMIC v1.3 identity representation

There is no separate "current HMIC version" runtime field in
production; per HMIC-REQ-051 the enumeration is embedded directly in
the frozen contract, not delegated to an external manifest — the
identity mechanism *is* the structural equality between the contract's
28-path enumeration and production's `_FROZEN_*` constants (§6, above),
plus the unrelated 5-member `contract_versions` mechanism for the five
bound *contracts other than HMIC-001 itself*. Grepped every `v1.1` /
`v1.2` / `v1.3` occurrence in `hatp_mandatory_certification.py`: all
docstring/comment/assert-message references to the 28-file enumeration
correctly say v1.3; the one remaining `v1.2` reference
(`HMIC-REQ-067 (v1.2)`) correctly describes that specific requirement's
own last-amended version (HMIC-REQ-067 was not touched by the v1.3
amendment), not a stale overall-contract-version claim. No location
found claiming v1.2 while using the 28-file set — no contradiction
across dimensions (contract text, production constant, docstrings,
version-mechanism membership all agree).

## 14. Contract identity member count

`_CONTRACT_IDENTITY_FILES` independently confirmed still exactly 5
members (`HMRC-001`, `HATP-001`, `HSCE-001`, `RAE-001`, `HBDC-001`).
Reasoning independently re-derived from the contract text itself
(§17/HMIC-REQ-050's own narrative): the 149O.20K amendment widened
HMIC's *source scope* (the file-byte enumeration feeding
`implementation_scope_digest`) by three entries; it did not introduce
a new bound *contract family* requiring a sixth
`_CONTRACT_IDENTITY_FILES` member, because the three new files are
production source modules, not separately-versioned contract
documents — HBDC-001 (the only Class-B-related contract) was already a
member since 149O.20D.1.

## 15. Cycle / self-binding

Fresh `ast`-based import walk (this phase's own module, not K.2's):
none of the three Class-B verifier modules import
`hatp_mandatory_certification`; `hatp_mandatory_certification` does
not import any of the three verifier modules (its only references to
their names are the three string-literal tuple entries, confirmed via
AST import-node inspection — no import statement contains any of the
three verifier module names as a substring). No cycle. No semantic
self-reference either: `derive_implementation_scope_digest` only opens
and reads file bytes — it does not import or execute verifier code.

## 16. Zero production consumers

Fresh repo-wide `grep -rl` for the three verifier module names and for
`verify_class_b_deployment_conformance`/`ClassBConformanceStatus`
across `src/` and `scripts/`: the only hits are the three verifier
modules themselves (mutual/self references) and
`hatp_mandatory_certification.py`'s path-literal bindings. No
readiness, certification, activation, Permission Broker, rollback, or
cutover module references the verifier functions or the
`COMPLIANT`/`NON_COMPLIANT`/`INDETERMINATE` verdict. Binding source
bytes (HMIC scope) ≠ consuming verifier results (readiness) — confirmed
still separate.

## 17. Real host result

Called `verify_class_b_deployment_conformance(HarnessPath(repo_root))`
read-only against the live repository. Result: `NON_COMPLIANT` (host
deliberately unprovisioned — protected root absent, no venv lock,
agent-owner-writable interpreter/site-packages, etc.). `git
rev-parse HEAD` and `git status --short` identical before and after
the call; only artifact present throughout was this phase's own new,
not-yet-committed task file. No chmod/chown/ACL/provisioning/
Protected-Root/environment-lock/certification/activation action was
taken.

## 18. CBV-S10 regression

`CBV-S10` searched in `PROJECT_STATUS.md`: still present, still
described as `OPEN`/`NOT CLOSED` (readiness contract/integration gap).
This phase performed no readiness-surface search hit beyond what §16
already covers, and made no edit to any readiness/certification/
activation file. CBV-S10 untouched.

## 19. Fixed-baseline Fast Green / broad-sweep attribution

Created a detached worktree at the true K.2 parent (`17a797af`) via
`git worktree add --detach`, confirmed `PYTHONPATH`-isolated
`pcae.__file__` resolves inside the worktree (not the primary
checkout), and ran the identical Fast Green (`pytest -m fast_green -n
auto`) and broad-sweep (`pytest -k "hmic or hbdc or class_b or
149o_20" -n auto`) commands on both the baseline and current `HEAD`.

**Fast Green:** baseline 105 failed / 6804 passed / 10 errors;
`HEAD` 123 failed / 6841 passed / 10 errors. Exact node-ID diff: 10
node IDs fail at `HEAD` but not baseline, 0 fixed. All 10 re-run
serially (not under `-n auto`) reproduce deterministically — not an
xdist/order flake. Root cause independently traced: these ten tests
(`test_phase_149o_15_...`, `test_phase_149o_16_...`,
`test_phase_149o_18c_...`, `test_phase_149o_18d_...`) each compute
`git diff <their-own-old-fixed-phase-entry-commit> -- src/pcae/`
against the *current working tree* and assert disjointness from a
`_FORBIDDEN_MODIFIED_FILES`/allowlist set; because production has
advanced 20+ phases past their fixed pin (independent of K.2/K.3),
`git diff` against the live tree now includes files unrelated to those
old phases' own scope — a pre-existing fixed-commit self-check
staleness pattern (repin-debt), not a regression introduced by K.2 or
K.3. Confirmed by direct evidence: run in the baseline worktree
(checked out at `17a797af`, whose *working tree* is the old commit
itself), the same `git diff` naturally shows no drift, so the tests
pass there — proving the failure is a property of tree-age drift, not
of K.2's/K.3's own content.

**Broad sweep:** baseline 81 failed / 1555 passed / 10 errors; `HEAD`
114 failed / 1577 passed / 10 errors. Exact node-ID diff: 43 new
failures at `HEAD`, 8 fixed. All 43 new failures classified: every one
is a historical fixed-count/fixed-scope assertion from a superseded
phase (e.g. `test_production_frozen_file_count_still_25`,
`test_zero_production_consumers_of_class_b_verifier_island`,
`test_new_modules_absent_from_current_hmic_frozen_source_set`,
`test_hmic_frozen_authority_bearing_files_still_25_none_are_class_b`)
— tests from phases 149O.19.5B through 149O.20K.1 that intentionally
pinned the *pre-K.2* 25-file/verifier-excluded/zero-binding state.
These are expected, legitimate production-alignment supersession: K.2
was designed to move production past exactly the state these tests
pin, and they were already known (per the K.2 phase report) to be
expected to flip. The 8 "fixed" node IDs are historical
mismatch-detection assertions (e.g.
`test_contract_and_production_literal_order_is_identical`,
`test_golden_digest_independent_matches_production`) whose own
pass/fail polarity is sensitive to which specific historical state
production is compared against — reconfirmed as pre-existing drift
churn, not a K.3-introduced defect, since K.3 made zero production
changes. No new failure among the 43+10 traces to any change other
than the true K.2 diff already fully accounted for in §2.

## 20. Historical-test disposition

Not modified. Every failing historical test inspected in §19 was left
as-is: K.3 is verification-only and does not opportunistically patch
tests or production. If historical re-pinning is warranted, that is a
separate, later governance decision, not taken here.

## 21. New independent K.3 tests

`tests/test_phase_149o_20k_3_hmic_class_b_verifier_production_source_set_alignment_independent_verification.py`
— 50 tests, does not import K.2's or K.1's test modules, covers: true
K.2 parent reconstruction, exact production diff/pre-K.2 25-file
reconstruction, live 28-file extraction, independent HMIC-REQ-050
extraction, exact contract/production equality (set + order), exact
+3 delta, original-25 preservation, 28 unique canonical paths,
byte-identity (verifier modules, HMIC-001, HBDC-001, four other bound
contracts, `hatp_certification_admin.py`), topology/environment-lock/
conformance-aggregator digest sensitivity (semantic + byte-level),
representative existing-file sensitivity, HBDC dual-binding, missing-
file fail-closed for all three new files, unreadable-file fail-closed,
symlink-alias rejection, path-literal `..`/absolute rejection, HMIC
v1.3 identity representation, five-member contract-identity count, no
cycle (both import-graph and string-literal-only binding), zero
consumers repo-wide, real-host `NON_COMPLIANT`, and CBV-S10 still
open. All 50 pass (`pytest
tests/test_phase_149o_20k_3_hmic_class_b_verifier_production_source_set_alignment_independent_verification.py
-q` → `50 passed`).

## 22. Production/contract modification check

`git status --short` / `git diff` confirm zero modification to
`hatp_mandatory_certification.py`, the three Class-B verifier modules,
`HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`,
`HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`, readiness/certification/
activation surfaces, Permission Broker, or runtime enforcement code
throughout this phase.

## 23. CBV-S1 adjudication

All fourteen closure criteria (§37 of this phase's brief) independently
verified: exact 28-file equality (§6-7), exact +3 delta (§7), original
25 retained (§7), all three new files individually digest-sensitive at
byte level (§10), missing files fail closed (§11), no alias/
normalization gap (§12), HMIC v1.3 identity correctly represented with
no contradiction (§13), HBDC binding preserved (§10), provider binding
preserved (§10), no cycle (§15), no consumer introduced (§16), verifier
bytes unchanged (§8), contract bytes unchanged (§8), no relevant
regression (§19 — all deltas traced to pre-existing repin-debt/
supersession, none to K.2's or K.3's own content).

**CBV-S1: INDEPENDENTLY CONFIRMED CLOSED AT HMIC CONTRACT + PRODUCTION
SOURCE-IDENTITY BOUNDARY.** This closure is scoped exclusively to the
HMIC contract/production source-identity boundary. It does **not**
imply Class-B deployment conformance, provisioning, HATP readiness, or
activation/execution authority — all of which remain unresolved,
unrelated gates.

## 24. CBV-S10 status

**OPEN — READINESS CONTRACT/INTEGRATION GAP.** Unchanged, not touched
by this phase (§18).

## 25. Class-B / HATP / runtime status

- **Class-B:** CONTRACT VERIFIED — VERIFIER REPAIR LINE INDEPENDENTLY
  VERIFIED — HMIC SOURCE BINDING INDEPENDENTLY VERIFIED — NOT
  PROVISIONED.
- **HATP:** NOT READY.
- **Runtime:** Observed / observe / unavailable (unchanged, confirmed
  via `pcae runtime inspect` at phase entry).

## 26. Exact tests run

- `pytest tests/test_phase_149o_20k_3_hmic_class_b_verifier_production_source_set_alignment_independent_verification.py -q` → 50 passed.
- `pytest -m fast_green -n auto` on fixed baseline `17a797af`: 105 failed / 6804 passed / 5 skipped / 10 errors.
- `pytest -m fast_green -n auto` on current `HEAD`: 123 failed / 6841 passed / 5 skipped / 10 errors (10 new, all pre-existing repin-debt, §19).
- `pytest -k "hmic or hbdc or class_b or 149o_20" -n auto` on baseline: 81 failed / 1555 passed / 10 errors.
- `pytest -k "hmic or hbdc or class_b or 149o_20" -n auto` on `HEAD`: 114 failed / 1577 passed / 10 errors (43 new / 8 fixed, all historical supersession churn, §19).

## 27. Next phase recommendation

Do not provision Class-B. Do not begin readiness integration. The next
unresolved architectural stop is CBV-S10.

**Recommended: Phase 149O.20L — Class-B Full-HBDC Readiness
Contract / Integration Analysis.** Scope: determine how full Class-B
deployment conformance enters HATP readiness; whether an existing
readiness term can represent it; whether contract evolution is
required; whether a new readiness Boolean is actually necessary (not
assumed); non-bypassability; interaction with current readiness/
certification semantics. Not begun by this phase.
