# Phase 150G — N16-5-F-5-TB-HELPER-ADMISSION-RECOGNITION-CORE-IMPLEMENTATION

**Status: COMPLETE — SHARED RECOGNITION CORE IMPLEMENTED**

## Summary

Realizes the Model B architecture Phase 150F selected and froze
(`docs/PHASE_150F_N16_5_F_5_TB_HELPER_ADMISSION_RECOGNITION_SHARED_INFRASTRUCTURE_ARCHITECTURE.md`):
extracts `hpac_protected_admin_writer._run_recognition_sequence`'s §33
steps 1, 4, 5, 6, 2, 3, 7, 8 (in that exact original order) into a new,
neutral, non-agent-importable module,
`src/pcae/core/hpac_pawa_recognition_core.py`, and refactors the legacy
factory to call it. Step 9 (the admin-writer-specific authorized-consumer
check) and step 10/11 (configured-agent binding + capability minting)
remain in the legacy factory unchanged — they were never part of the
extraction.

**Helper admission is still NOT implemented by this phase.** No helper
launcher/OS/store-adapter/writer-authority module was touched or now
imports the new core. Helper step 9-prime is not defined. The separate
foundation blocker (`HPACStoreAuthority._ensure_root` /
`_validate_production_boundary`) is untouched. No contract changed.
**N-16-5 remains NOT CLOSED.**

## 150F predecessor confirmation

- Phase 150F is canonical, complete, and pushed (`81985989`..`ce9b8beb`,
  confirmed on `origin/main` at this phase's own preflight).
- Model B was the architecture it selected.
- No production implementation existed before this phase (confirmed: the
  proposed module did not exist; `_run_recognition_sequence` still ran
  steps 1-8 inline).
- N-16-5 was NOT CLOSED entering this phase; N-16-6/N-16-7 untouched.
- Runtime posture entering this phase: Observed / observe / unavailable.

## Steps 1-8 mapping (old location → new module)

| Step | What it does | Old location | New location |
|---|---|---|---|
| 1 | Root-content checks (symlink rejection, existence, mode, `.authority/` namespace, live root identity + digest). Canonical-root *resolution* itself (`HPACStoreAuthority.production()` / the disclosed test fixture) stays in the legacy factory — only the entitled factory constructs an `HPACStoreAuthority`. | inline in `_run_recognition_sequence` | `recognize_protected_anchor` (root-content checks only; `root: Path` is now a parameter) |
| 4 | `HPAC-STORE-AUTHORITY/1.0` manifest read/validate + `{device,inode}` binding + owner/mode. | inline | `recognize_protected_anchor` |
| 5 | Authority descriptor read/validate + root-identity/state checks. | inline | `recognize_protected_anchor` |
| 6 | Current-generation anchor read/validate + generation/digest checks + provenance verification. | inline | `recognize_protected_anchor` |
| 2 | Configured-agent-principal resolution (`HPAC-PAWA-AGENT-EXCLUSION/1.0`) + provenance verification. | inline | `recognize_protected_anchor` |
| 3 | Configured-agent exclusion + safe-ancestor-chain checks via `TopologyProbe`/live topology. | inline | `recognize_protected_anchor` |
| 7 | Current invocation is not the configured agent (live uid vs. resolved configured-agent uid). | inline | `recognize_protected_anchor` |
| 8 | Positive `O_EXCL\|O_NOFOLLOW` write probe (self-cleaning). | inline (`_positive_write_probe`) | `recognize_protected_anchor` (`_positive_write_probe`, moved) |
| 9 | Authorized-factory-consumer check (`AUTHORIZED_FACTORY_CONSUMERS`/`_TEST_FACTORY_CONSUMERS`). | inline | **unchanged**, still in `_run_recognition_sequence` |
| 10 | Bind configured-agent identity into the authority (`_bind_configured_agent_identity`, requires `_PRODUCTION_WRITER_FACTORY_SEAL`). | `production_writer` | **unchanged**, still in `production_writer` |
| 11 | Mint capability + issuance audit evidence. | `production_writer` | **unchanged**, still in `production_writer` |

Helper functions moved (steps-1-8-only; had zero other call sites in the
legacy module, confirmed by full-file grep before removal):
`_require_owner_and_mode`, `_require_not_configured_agent_writable`,
`_verify_provenance`, `_exclusion_provenance_ref`, `_positive_write_probe`,
`TopologyProbe`, `_real_topology`. `TopologyProbe`/`_real_topology` are
re-imported into `hpac_protected_admin_writer.py` for backward-compatible
attribute access (`hpac_protected_admin_writer.TopologyProbe` unchanged
for ~20 existing test call sites).

Helper functions used by *both* recognition and other (provisioning/
rotation/revocation) operations were left in place, unchanged, in the
legacy module (`_authority_dir`, `_root_identity`, `_reject_component_symlinks`,
`_read_protected_json`, `validate_authority_descriptor`,
`validate_current_generation` — all still have call sites outside the
former recognition sequence).

## New core module / interface

`src/pcae/core/hpac_pawa_recognition_core.py`:

- `recognize_protected_anchor(*, root: Path, configured_agent_identity_source, topology_probe: Optional[TopologyProbe] = None) -> RecognizedAnchorFacts`
- `RecognizedAnchorFacts` (frozen dataclass): `root`, `live_root_identity`,
  `live_root_identity_digest`, `anchor_id`, `installation_id`,
  `generation`, `configured_agent` — **no `authority` field**. This is the
  key design decision resolving the one real tension in Model B: the
  legacy `_RecognizedAnchor.authority: HPACStoreAuthority` field is
  authority-adjacent (used downstream for step 10/11 minting), so it is
  never produced by, or passed through, the shared core. The legacy
  factory still calls its own `_resolve_authority()` to get the
  `HPACStoreAuthority`/`root`, passes only the plain `root: Path` into the
  shared core, and separately keeps its own `authority` reference for
  step 10/11. The shared core never imports, constructs, or references
  `HPACStoreAuthority` at all (confirmed by AST-based test, not
  substring).
- `RecognitionError` (own closed 15-value failure vocabulary, a strict
  subset of the legacy `PAWA_FAILURE_CODES` covering exactly the codes
  steps 1-8 can raise). The legacy factory catches `RecognitionError` and
  re-raises `PawaError(exc.code, exc.detail)` — identical code/detail,
  so the closed vocabulary and every downstream `rhamp_terminal_reason`
  mapping are preserved unchanged. No reverse import (the core never
  imports from `hpac_protected_admin_writer`).
- `TopologyProbe` (moved unchanged) and `_real_topology()` (moved
  unchanged).

## Old vs. new behavior comparison (parity)

Proven by the fresh 37-test suite
(`tests/test_n16_5_f_5_tb_helper_admission_recognition_core_implementation.py`),
calling both `recognize_protected_anchor` directly and the refactored
`_run_recognition_sequence`/`production_writer` against the same fixture
state:

- Valid state: both produce matching facts (root, identity, digest,
  anchor/installation id, generation, configured agent).
- Missing protected root, missing agent-exclusion record, unknown
  configured agent, malformed descriptor, symlinked `.authority/`
  namespace, stale/superseded generation, configured-agent-writable root,
  current-context-is-agent — all fail identically (same `pawa_failure_code`
  / `RecognitionError.code`) old vs. new.
- The full `production_writer` factory path still mints successfully end
  to end through the refactored sequence.
- Unauthorized-consumer rejection (step 9) is unchanged (still covered
  extensively by the pre-existing `.30R.3.1` suite).

## Result type semantics

`recognition result != authority`. `RecognizedAnchorFacts` carries only
ordinary descriptive values (`Path`, `dict`, `str`, `int`, and the
pre-existing `ConfiguredAgentAuthorityIdentity`, itself descriptive). It is
not an instance of, and does not wrap, `HPACWriterCapability` or
`HPACStoreAuthority`. Trust derives from *performing* the checks on each
call against live state — a hand-forged `RecognizedAnchorFacts` conveys no
authority because nothing downstream accepts one in place of a real call
(`production_writer` has no such parameter; confirmed by AST inspection).

## Currentness

No caching, no memoization, no process-lifetime pin: `recognize_protected_anchor`
re-reads live `.authority/` state on every call, identical to the
pre-extraction property (HPAC-PAWA-REQ-075's "runs fresh on every call").
Confirmed by AST scan of module-level assignments (no cache/registry/memo
dict) and by a fixture asserting no cross-call state is retained.

## Security / adversarial test results

37/37 new tests pass, covering: behavior parity (9 scenarios), OS-username/
frame/caller-module non-authority (3), currentness (2), forbidden-import
adversarial checks via AST — not substring, so the module's own docstring
prose cannot false-positive the check — (writer/helper authority families,
`HPACStoreAuthority`, seals, mutation binding methods), no subprocess/shell
dispatch, no frame-inspection/caller-module trust, no mutable module-level
trust registry, non-agent-importability, no duplicate steps-1-8
implementation remaining in the legacy module (AST: the old primitives are
no longer *defined* there; `_run_recognition_sequence` now calls
`recognize_protected_anchor`), Model E non-regression (three authority
classes remain distinct, no shared `HPACStoreAuthority` base, no
`HPACWriterCapability` sink in the core), helper-admission non-wiring
(parametrized check across all six helper admission modules: none imports
or calls the new core), the disclosed pre-existing `configured_agent=None`
gap is untouched, "step 9-prime" is not defined anywhere in the tree, and
no `docs/contracts/**` working-tree change.

## Duplicate-implementation disposition

The five steps-1-8-only helper functions (`_require_owner_and_mode`,
`_require_not_configured_agent_writable`, `_verify_provenance`,
`_exclusion_provenance_ref`, `_positive_write_probe`) and the
`TopologyProbe` class/`_real_topology` function were **removed** from
`hpac_protected_admin_writer.py` (not left as dead code) — confirmed by
full-file grep before removal that they had no other call site, and by a
fresh AST-based test confirming they are no longer defined there.
`_run_recognition_sequence` now calls `recognize_protected_anchor` and no
longer contains an independent steps-1-8 implementation.

## Model E disposition

`HelperAdminMutationAuthority`, `HelperCertificationWriteAuthority`,
`HelperPresentationEvidenceAuthority` (in `hpac_pawa_helper_writer_authority.py`)
are byte-unchanged (confirmed by the pre-existing
`test_n16_5_f_5_tb_helper_admission_provenance_repair.py` byte-identity
check, which still passes for this file). Exact-type recognition, sealing,
and the absence of a shared `HPACWriterCapability` sink are all
reconfirmed by this phase's own suite.

## Helper wiring — explicitly NOT performed

None of `hpac_pawa_helper_launcher.py`, `hpac_pawa_helper_os.py`,
`hpac_pawa_helper_operations.py`, `hpac_pawa_helper_store_adapter.py`,
`hpac_pawa_helper_writer_authority.py`, `hpac_pawa_helper_entrypoint.py`
was modified by this phase, and none imports or calls
`hpac_pawa_recognition_core`/`recognize_protected_anchor` (parametrized
test, all six). The disclosed pre-existing gap
(`hpac_pawa_helper_os.authenticate_peer`'s `configured_agent` defaulting
to `None`, never supplied by its sole caller) is unchanged.

## Step 9-prime — explicitly NOT defined

No helper-side step 9-prime exists anywhere in the tree (tree-wide token
sweep). That adjudication remains a distinct, separately-authorized future
phase, per Phase 150F's own recommendation.

## Foundation blocker disposition

**FOUNDATION BLOCKER UNCHANGED.** `hpac_foundation.py` (home of
`HPACStoreAuthority._ensure_root`/`_validate_production_boundary`) is
byte-unchanged (confirmed by the pre-existing byte-identity test, which
still passes for this file). The new recognition core never imports,
constructs, or references `HPACStoreAuthority`, `_ensure_root`, or
`_validate_production_boundary` (confirmed by AST-based identifier-usage
scan, immune to docstring-prose false positives).

## Contract state — zero delta

`HPAC-PAWA-001 v4.0`, `HPAC-PAWA-HELPER-001 v5.0`, `HPAC-PPA-001 v2.1`
remain the current contracts. `git status --porcelain -- docs/contracts`
is empty in this phase's own working tree (verified by this phase's own
test suite).

## Fast Green

- Baseline: `31ebe985` (this phase's own bare-colon anchor commit's
  parent — `Phase 150G: open task and close stale idle placeholders`,
  itself on top of `ce9b8beb`, 150F's own final pushed commit /
  `origin/main` at this phase's preflight).
- Isolated keyword sweep (`pawa or hpac or helper or admin_writer or
  recognition`, `git stash -u` baseline vs. candidate working tree):
  **78 failed / 1842 passed / 37 skipped** (baseline) vs. **78 failed /
  1879 passed / 37 skipped** (candidate) — identical failure set (`diff`
  of sorted `FAILED` lines is empty), the 37 new tests are exactly this
  phase's own new suite, zero attributable regressions.
- One pre-existing byte-identity test
  (`test_n16_5_f_5_tb_helper_admission_provenance_repair.py::test_deferred_authority_production_files_unchanged[hpac_protected_admin_writer]`)
  legitimately needed a narrow, in-scope repair: it pinned
  `hpac_protected_admin_writer.py` byte-identical to a `fabbfac0` baseline
  forever, which this phase's own explicitly-authorized modification of
  that exact file necessarily breaks (the same stale-moving-assertion
  pattern Phase 150C already repaired in an analogous predecessor suite).
  Repaired by narrowing the parametrized byte-identity list to the two
  files this phase does not touch (`hpac_foundation`,
  `hpac_pawa_helper_writer_authority`, both still byte-identity-checked)
  and adding a substantive replacement assertion for
  `hpac_protected_admin_writer.py` that preserves the original test's
  actual intent (the deferred helper-side authority/registration lineage
  is still absent) without pinning to an unchanging byte snapshot.
- Two other pre-existing stale-baseline test files
  (`tests/test_n16_5_f_5_tb_helper_admission_recognition_shared_infrastructure_architecture.py`
  — 150F's own descriptive suite — and
  `tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_1_pawa_writer_anchor_slice1.py`)
  needed narrow test-location updates (not behavior changes) because they
  literally source-scanned `hpac_protected_admin_writer.py` for code that
  legitimately moved to the new module; both updated to check the union of
  both files (or, for one specific moving-HEAD assertion in 150F's suite,
  re-pinned to 150F's own final commit as a fixed historical boundary,
  matching the same Model FG-E precedent).
- Full `pytest -n auto` run: see governance evidence in
  `.pcae/phase-completion-metadata.json` for this phase (structured
  `fast_green` attribution embedded there per the repository's own
  finalization-gate requirements).

## Runtime posture

Unchanged: **State: Observed. Maximum Capability: observe. Execution
Availability: unavailable.** No first external effect. No runtime
capability advancement. No Gate10 effect reachability.

## N-16 disposition

- Shared recognition core implemented; legacy consumer migrated without
  behavior change. **This is the only claim this phase makes.**
- It does NOT mean: helper admission fixed, step 9-prime resolved,
  foundation fixed, certification ready, or N-16-5 closed.
- **N-16-5 remains NOT CLOSED.** N-16-6 untouched. N-16-7 untouched.

## No-go confirmations

- No helper admission wiring was performed by this phase.
- No helper step 9-prime was defined by this phase.
- No foundation repair was performed by this phase.
- No contract evolution was performed by this phase.
- No Model E production modification was performed by this phase.
- No runtime, PB, or POL change was performed by this phase.
- No caching or memoization was introduced by this phase.
- No first external effect was introduced by this phase.
- No Gate10 effect reachability was introduced by this phase.
- No certification advancement was performed by this phase.
- No N-16-6 artifact was introduced by this phase.
- No N-16-7 artifact was introduced by this phase.

## Recommended successor

Independent verification of this shared recognition-core implementation
(Phase 150G). Do not begin helper wiring in that successor. Do not begin
step 9-prime adjudication in that successor. After IV, the likely next
architecture phase should freeze helper-specific step 9-prime and the
exact admission sequencing before any helper-side implementation.

`recognition result != authority`. **Helper admission is still NOT
implemented by this phase.**

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — this phase's
implementation, tests, and evidence were authored directly by the primary
operator; no delegated fork was used. All lifecycle mutation, finalization,
commit, and push were performed directly by the primary operator.
