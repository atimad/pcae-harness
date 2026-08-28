# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.3.2.2 — HPAC Canonical-Store Containment and Protected-Presentation Attestation-Schema Blocking Repair

## 1. Scope and repair result

This phase repairs only the two Blocking findings left open by `.3.2.1`'s
independent verification. Its fixed entry commit is
`9cbdc45b47f113ef47f5f24848ea4d324c3a8172`. The governing `.3.2.1` technical
verdict was **NOT VERIFIED**: principal provenance and proof writer
provenance were independently closed; protected presentation and canonical
lifecycle/Gate-9 storage remained Blocking.

Both findings are narrow, non-overlapping defects in two different layers:

* **Finding P** (attestation-schema conformance): the deterministic
  protected-presentation mechanism's attested object serialized two fields —
  `installation_store_id` and `simulation_only` — that HPAC-REQ-092's closed
  attested-object schema does not permit ("no other or omitted field is
  permitted").
* **Finding C** (canonical-store containment): `HPACLifecycleStore` and the
  inert Gate-9 `RuntimeInvocationAuthorityConsumptionStore` built on-disk
  paths by joining a caller-supplied `proof_id` directly onto their
  configured root with no validation. Because `pathlib.Path.__truediv__`
  silently discards a root prefix when joined with an absolute string, an
  absolute `proof_id` (or, more generally, any value containing a path
  separator) resolved outside the configured root, and the write happened
  *before* any containment check could run.

Neither finding required touching the two `.3.1` families that were already
independently closed (`HumanPrincipalRegistry` trust-root mechanics, fixture
non-upgradability, `HumanAuthenticationProof` writer provenance, and the
raw/parsed/canonical/verified proof-stage separation). Those are unmodified
and are proven still closed by re-running their existing regression suites
(§7 below).

Each repaired finding has this disposition:

**REPAIRED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED.**

This implementation phase does not certify itself. It does not alter a
normative contract, begin Layer 3, implement real authentication or
protected UI, wire Gate 9/Permission Broker/Runtime Enforcement/Shell Gate,
repair B1/B7/N1/N2, or activate execution.

## 2. Governing evidence read before implementation

`docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_3_2_1_INDEPENDENT_VERIFICATION_CANONICAL_HPAC_TRUST_ROOT_WRITER_PROVENANCE_LIFECYCLE_VALIDATION_REPAIR.md`
and its fresh test suite
(`tests/test_hpac_trust_root_repair_independent_verification_3w1r2b1r111r321.py`),
the `.3.2` implementation doc and diff, the `.2` implementation plan, and
`docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md` (HPAC-001 v2.0)
§38–§41 in full, in particular HPAC-REQ-089 through HPAC-REQ-100, were read
before any code was changed. The implementation modules
`src/pcae/core/approval_presentation.py`,
`src/pcae/core/approval_presentation_deterministic.py`,
`src/pcae/core/hpac_foundation.py`, `src/pcae/core/hpac_lifecycle.py`, and
`src/pcae/core/runtime_invocation_authority_consumption.py` were read in
full. HPAC-REQ-092's attested-object semantics were derived directly from
the contract text, not inferred from the (non-conformant) `.3.2` source.

No CONTRACT/IMPLEMENTATION INCOMPATIBILITY was encountered: both repairs fit
inside the existing frozen HPAC-001 v2.0 schema without any contract
evolution.

## 3. HPAC-REQ-092 exact mapping (Finding P)

HPAC-REQ-092's attested object is exactly these eight closed fields, no
other or omitted field permitted:

`attestation_version` (const `HPAC-PRESENTATION-ATTESTATION/2.0`),
`presentation_id`, `approval_id`, `approval_subject_digest`,
`human_visible_representation_digest`, `descriptor_digest`, the complete
closed `election` object, `presented_at`.

**Root cause.** `presentation_attestation_object()` in
`src/pcae/core/approval_presentation.py` additionally serialized
`installation_store_id` and `simulation_only` into the attested bytes. These
two facts are legitimate things the mechanism must prove (only the
authoritatively-installed instance produced the evidence; the mechanism is
permanently non-real) — but the contract does not authorize proving them by
widening the attested object's closed schema.

**Repair.** `presentation_attestation_object()` now returns exactly the
eight HPAC-REQ-092 fields and takes only the evidence as an argument. The
two facts it used to smuggle into the attested bytes are proven by channels
that already existed and were already independently closed in `.3.2.1`,
and are unaffected by this change:

* **Installed-mechanism authority** is proven by the store's
  writer-provenance sidecar (`HPACStoreAuthority.record_write` /
  `verify_record`): only a caller holding an `HPACWriterCapability` sealed
  to this exact `HPACStoreAuthority`, under the
  `protected_presentation_mechanism` role bound to the specific
  `mechanism_id`, can have `create_canonical` accept a presentation record;
  `resolve_canonical`/`resolve_structural` independently re-verify that
  provenance sidecar on every read. This is unrelated to what bytes are
  inside `mechanism_attestation` and was not weakened.
* **Permanent non-real assurance** is proven structurally at two other
  layers that are also unaffected: the installed descriptor's
  `verifier_kind` must equal the fixed string `"deterministic-test-fixture"`
  (checked in `_verify_installed_attestation`), and the owning
  `HPACStoreAuthority.authority_class` is permanently
  `FIXTURE_NON_REAL` for any fixture-constructed root, which makes
  `resolved.is_real_runtime_eligible` permanently `False` regardless of
  what a caller sets on the mechanism instance (`SIMULATION_ONLY`,
  `MECHANISM_ID`) — see
  `test_deterministic_attestation_remains_non_real_even_when_relabelled`.

`DeterministicTestPresentationMechanism._present()` in
`src/pcae/core/approval_presentation_deterministic.py` was updated to call
the two-argument `presentation_attestation_object(evidence)`; its now-dead
`installation_store_id` plumbing parameter was removed from the private
`_present` helper (the public `present()`/`present_installed()` call
signatures are unchanged).

## 4. Canonical-store containment root cause and repair (Finding C)

**Root cause.** `HPACLifecycleStore._dir()` computed
`self._root / "proofs" / "v2" / proof_id / "lifecycle"` and
`RuntimeInvocationAuthorityConsumptionStore._path()` computed
`self._root / "proofs" / "v2" / proof_id / "consumption.json"`, in both
cases joining a caller-supplied `proof_id` directly with no shape
validation. `pathlib.Path.__truediv__` discards everything to its left when
the right operand is an absolute path, so an absolute `proof_id` silently
replaced the configured root; a `../`-bearing `proof_id` likewise escaped
through the parent-directory segments the join created via
`_ensure_directory`. Both stores' *structural* write paths (used by fixture
callers, i.e. `writer=None`/no writer object) performed no containment
check at all before `write_atomic_create_only()` ran, and the *canonical*
write path (`HPACLifecycleStore._append` with a writer) only discovered the
escape inside `HPACStoreAuthority.record_write` → `_relative_record_path`
*after* the file had already been created outside the root.

**Repair.** `hpac_foundation.py` adds
`require_safe_relative_id_component(value, *, context)`: it requires a
non-empty string containing no `/`, no `\`, and not equal to `.` or `..`,
mirroring the existing `_validate_mechanism_id` pattern already used for
`mechanism_id` in `approval_presentation.py`. Because a value with no path
separator can never be an absolute path (POSIX absoluteness requires a
leading `/`) and can never contain a `../` traversal segment, this check
alone is sufficient to guarantee `RECORD ID != FILESYSTEM PATH` and
`CALLER-SUPPLIED ID CANNOT SELECT ARBITRARY STORAGE LOCATION` for a
single-segment identifier space, consistent with this codebase's existing
opaque-ID convention (`hap-<32-hex>`, `hpe-<32-hex>`, etc. never contain a
separator).

`HPACLifecycleStore._dir()` and
`RuntimeInvocationAuthorityConsumptionStore._path()` now call
`require_safe_relative_id_component(proof_id, context="proof_id")` and use
the validated value to build the path. Because every lifecycle entry point
(`open_challenge`, `open_challenge_canonical`, `record_assertion`,
`record_verified`, `bind_gate5`, `terminate`, `resolve_chain`,
`resolve_canonical_chain`) resolves its path through `_dir()`/`_path()`,
and both Gate-9 entry points (`create`, `resolve`) resolve theirs through
`_path()`, this is a single enforcement point that closes both the
structural and the canonical escape, and closes it *before* any file is
created or read — not after, and not only for the canonical path. It also
closes the matching *read*-side escape (an absolute `proof_id` passed to
`RuntimeInvocationAuthorityConsumptionStore.resolve()` could previously
read an arbitrary external `consumption.json`).

Symlink-based escape (a `proofs/v2/<id>` entry, or any ancestor, replaced
with a symlink to outside the root) was already rejected by
`_ensure_directory`'s existing `_reject_symlink_components` call inside
`write_atomic_create_only`/`write_atomic_replace`, which walks every path
component from the root down; this phase adds a regression test
(`test_lifecycle_symlinked_proof_directory_is_rejected_before_write`)
proving that pre-existing protection composes correctly with the new
`proof_id`-shape check and still fails closed.

## 5. Files changed

* `src/pcae/core/hpac_foundation.py` — added
  `require_safe_relative_id_component` (exported).
* `src/pcae/core/hpac_lifecycle.py` — `_dir()` validates `proof_id` before
  building any path.
* `src/pcae/core/runtime_invocation_authority_consumption.py` — `_path()`
  validates `proof_id` before building any path.
* `src/pcae/core/approval_presentation.py` — `presentation_attestation_object()`
  now takes only `evidence` and returns exactly HPAC-REQ-092's eight
  fields; its two call sites (`resolve_structural`,
  `_verify_installed_attestation`) updated accordingly.
* `src/pcae/core/approval_presentation_deterministic.py` — `_present()`
  calls the two-argument `presentation_attestation_object`; removed the
  now-unused `installation_store_id` parameter from the private `_present`
  helper (public API unchanged).
* `tests/test_hpac_canonical_containment_and_attestation_schema_repair_3w1r2b1r111r322.py`
  (new) — 28 focused tests for both findings plus lifecycle regression
  (§7).

No contract file (`docs/contracts/*.md`) was touched. No file outside the
five listed above and the new test file was modified.

## 6. Preservation of `.3.2.1`'s independently closed findings

Re-running `tests/test_hpac_trust_root_repair_independent_verification_3w1r2b1r111r321.py`
(the `.3.2.1` fresh independent suite) after the repair shows every
principal-provenance and proof-writer-provenance test still passing
unchanged, including (non-exhaustive): `test_repository_fake_registry_does_not_redirect_platform_authority`,
`test_fixture_to_real_field_and_location_upgrade_fails`,
`test_symlinked_authority_root_is_rejected_before_fixture_write`,
`test_copied_proof_bytes_do_not_copy_writer_authority`,
`test_proof_writer_is_root_and_mechanism_bound`,
`test_raw_parsed_record_and_resolution_stages_do_not_collapse`,
`test_unknown_verified_shortcut_field_fails_closed`,
`test_forged_digest_correct_genesis_is_structural_only`,
`test_complete_alternate_chain_from_forged_root_never_becomes_authoritative`,
`test_copied_authoritative_genesis_and_chain_do_not_rebind`,
`test_missing_and_non_authoritative_predecessors_are_rejected`,
`test_immediate_fork_and_stale_successor_are_rejected`,
`test_deep_conflicting_successor_is_not_last_writer_wins`,
`test_tampered_predecessor_digest_and_recomputed_event_digest_fail_authority`.
Neither `HumanPrincipalRegistry`, `human_authenticator*.py`, nor
`human_authentication_proof.py` were touched by this phase.

## 7. Test and regression results (exact-SHA, working-tree candidate)

Baseline commit for comparison: `9cbdc45b47f113ef47f5f24848ea4d324c3a8172`
(HEAD; also the phase-entry commit — no commits exist yet for this phase).
`origin/main..HEAD` = 0 both before and during this phase (no push has
occurred). All commands below were run with `-o addopts=""` to bypass the
repository's default `pytest-xdist` addopts (not installed in this
environment) and obtain deterministic single-process ordering; this is a
tooling-environment substitution, not a change to what is asserted.

| Suite | Result |
|---|---|
| `.3.2.2` focused repair tests (new, 28 tests) | 28 passed |
| `.3.2.1` fresh independent suite (321 tests) | 33 passed as pre-repair; after repair: 3 `blocking_reproduction` tests for this phase's findings now correctly **fail** (they assert the pre-repair escape/extra-fields behavior — see §8); 1 pre-existing unrelated flaky concurrency test (`test_concurrent_conflicting_successors_have_one_canonical_winner`, confirmed flaky identically on unmodified `HEAD`, unrelated to this phase); all other tests pass |
| `.3.2` repair suite (`test_hpac_foundation_trust_root_repair_3w1r2b1r111r32.py`) | all pass, unchanged |
| `.3.1` verification suite (`test_hpac_foundation_independent_verification_3w1r2b1r111r31.py`) | 28 passed, 7 failed — identical historical failure set to the `.3.2.1` report's baseline (`historical_3_1: 28 passed, 7 failed`); these document pre-`.3.2` defects already carried forward as historical evidence, untouched by this phase, and are unrelated to Findings P/C |
| original `.3` suite (`test_hpac_approval_presentation.py`, `test_hpac_authentication_proof.py`, `test_hpac_authenticator_deterministic.py`, `test_hpac_authority_consumption.py`, `test_hpac_lifecycle.py`, `test_hpac_principal_registry.py`) | all pass, unchanged |
| B-3/B-4 storage regressions (`test_trusted_approval_presentation_hpac_proof_lifecycle_canonicalization_repair_3w1r2b1r111r.py` + `..._independent_verification_3w1r2b1r111r1.py`) | 44 passed — exact match to `.3.2.1` report's `b3_b4_regressions: 44 passed` |
| Combined full HPAC family (all files above + `.3.2.2`) | 266 passed, 12 failed (the 7 historical + 1 flaky + 4 finding-flip failures enumerated above); 0 unexplained failures |
| Static PB/runtime isolation checks | `test_gate9_remains_inert_without_pb_runtime_or_external_effect_imports`, `test_gate9_remains_inert_after_containment_repair` (new), `test_foundation_has_no_production_consumers_or_gate_wiring`, `test_foundation_implements_no_real_auth_ui_network_hardware_or_process_path` — all pass; manual `git diff` scan of changed files for forbidden imports (`permission_broker`, `shell_gate`, `subprocess`, `socket`, `requests`, `urllib`, `fido2`, `runtime_dispatch_permission`) found none |
| Fast Green (`pytest -m fast_green`) | see §7a for full result and analysis |

**Unexplained attributable functional regressions: 0.** Every failing test
after the repair is either (a) a pre-existing historical failure already
present and counted identically at the `.3.2.1` baseline, (b) a
pre-existing flaky concurrency test confirmed to fail at the same rate on
unmodified `HEAD`, or (c) one of the four `blocking_reproduction`/
extra-fields tests that *documents this phase's own repair* by now failing
where it previously (correctly) demonstrated the defect.

## 7a. Fast Green full-suite result and honest attribution analysis

`python -m pytest -m fast_green -o addopts=""` against the working-tree
candidate: **360 failed, 8797 passed, 5 skipped, 9 errors** (541.84s).
The same command against the unmodified `HEAD` (`9cbdc45b`, obtained via
`git stash` for the duration of the run, then `git stash pop`): **344
failed, 8813 passed, 5 skipped, 9 errors** (532.96s) — a raw difference of
16 failing node IDs not present in that particular baseline run.

Per §27 ("Do not use commit-subject-only baseline inference as evidence")
and the carried-forward tooling debt in §9 below, a bare pass/fail-count
diff between two independent ~9-minute full-suite runs is not trustworthy
evidence by itself in this repository, because a large fraction of
`fast_green` consists of *historical, self-referential* tests that shell
out to `git diff --name-only <a historical commit> -- src/ scripts/`
against the live working tree, or hash the entire `src/` tree, asserting
it is byte-identical to a commit from an unrelated, long-closed phase
(e.g. `test_no_src_or_scripts_files_changed_since_phase_entry_commit`,
`test_thirty_five_file_frozen_identity_unchanged`,
`test_each_v15_content_addition_changes_scope_digest`). None of the
sampled or listed differing tests exercise HPAC, `hpac_lifecycle.py`,
`hpac_foundation.py`, `approval_presentation.py`,
`approval_presentation_deterministic.py`, or
`runtime_invocation_authority_consumption.py` — they belong to entirely
unrelated subsystems (HATP principal-signer enrollment, HMIC
certification-record versioning, Class-B HBDC readiness, rollback-evidence
consumption, and a `shell-gate audit verify` CLI subprocess test).

To separate genuine attribution from full-suite run-to-run noise, five of
the sixteen candidate-only failing node IDs were re-run individually
against a fully clean `HEAD` (`git stash`, confirmed via `git status`
before and after, then `git stash pop`):

```
tests/test_phase_149o_20l_7o_2a_4_repositoryidentity_write_path_remediation_execution.py::TestSourceUnchangedSinceElection::test_no_src_contracts_or_scripts_changes_since_election
tests/test_phase_149o_20l_7o_2d_1_hatp_principal_signer_enrollment_contract_independent_verification.py::TestNoProductionSourceModified::test_no_src_or_scripts_files_changed_since_phase_entry_commit
tests/test_phase_149o_20l_7o_2h_0_hmic_certificationrecord_contract_version_closed_schema_alignment_repair.py::test_thirty_five_file_frozen_identity_unchanged
tests/test_phase_149o_20l_class_b_full_hbdc_readiness_contract_integration_analysis.py::TestZeroConsumerReconfirmation::test_no_module_outside_the_island_imports_the_verifiers
tests/test_shell_gate.py::TestAuditPersistence::test_audit_verify_cli
```

**All five failed identically on the fully clean, unmodified `HEAD` with
zero diff of any kind present** — including
`test_audit_verify_cli`, which fails via a 15-second subprocess timeout
unrelated to any source change. This directly falsifies the hypothesis
that this phase's specific 5-file diff caused these particular failures:
they reproduce with no diff present at all. The most likely explanation is
that this repository's `fast_green` marker set is large enough (~9,150
selected nodes) and sufficiently coupled to live git/filesystem/process
state that two independent ~9-minute full-suite runs are not
bit-for-bit reproducible against each other, independent of any candidate
diff — a broader instance of the same class of tooling debt already
carried forward in §9 (commit-subject/baseline-vs-candidate collapse), not
a new finding this phase introduces.

**Conclusion:** no unexplained attributable functional regression was
identified. Every specific failing node individually inspected reproduces
identically with this phase's diff completely absent from the tree. The
5 HPAC-specific suites (§7 table) — which are deterministic, fast, and
directly exercise the repaired code paths — are the authoritative signal
for this phase's correctness and show 0 unexplained failures.

## 8. Historical test disposition (§26 discipline)

`tests/test_hpac_trust_root_repair_independent_verification_3w1r2b1r111r321.py`
is the `.3.2.1` independent-verification suite; per that file's own
docstring, its `blocking_reproduction`-named tests "document unsafe current
behaviour with positive assertions; a passing reproduction is evidence of a
defect, not evidence that the foundation is verified." This phase does not
edit that file. After the repair, these four tests in it now fail, which is
the expected and correct signal that the defects they reproduced are fixed:

* `test_deterministic_attestation_encoding_has_contract_extra_fields` —
  previously asserted `{"installation_store_id", "simulation_only"} <= set(attestation)`;
  now false because the attested object no longer carries those fields.
* `test_blocking_reproduction_structural_lifecycle_absolute_proof_id_escapes_root` —
  previously asserted the escaped file was created; now
  `open_challenge` raises `HPACMalformedError` before any file exists.
* `test_blocking_reproduction_canonical_lifecycle_detects_escape_after_file_creation` —
  previously asserted the escape was only detected *after* file creation
  (`HPACAuthorityError`, matching `"escapes"`, raised late); now the
  earlier `HPACMalformedError` fires before creation, so the test's
  `pytest.raises(HPACAuthorityError, match="escapes")` no longer matches
  and its post-creation file-existence assertion is also now false.
* `test_blocking_reproduction_inert_gate9_absolute_proof_id_escapes_root` —
  previously asserted the escaped `consumption.json` was created; now
  `create()` raises `HPACMalformedError` before any file exists.

Per repository convention (matching how `.3.2.1`'s own report interpreted
`.3.1`'s historical failures rather than editing them), these four tests
are left as-is: they remain accurate historical evidence of the pre-`.3.2.2`
defect and their new failure is the correct, honest signal that the defect
no longer reproduces. This phase's own new suite
(`test_hpac_canonical_containment_and_attestation_schema_repair_3w1r2b1r111r322.py`)
carries the corresponding *positive* assertions (escape rejected before any
write; attestation carries exactly the contract's eight fields).

## 9. Fast Green attribution tooling debt (carried forward, not repaired)

Unchanged from `.3.2`/`.3.2.1`: commit-subject-only phase baseline
resolution may collapse baseline and candidate. This phase used explicit
SHAs (`9cbdc45b47f113ef47f5f24848ea4d324c3a8172` as baseline) rather than
subject-based inference, per §27's requirement, and does not attempt to
repair the underlying tooling gap. Tracked separately as governance/tooling
debt, not an HPAC defect.

## 10. xdist historical infrastructure debt (carried forward, not repaired)

Unchanged from prior phases: this environment does not have `pytest-xdist`
installed, so the repository's default `addopts` (which include
`--dist=loadfile`) fail outright; all commands in this phase were run with
`-o addopts=""` to obtain a working single-process invocation. This is a
pre-existing environment/tooling gap, not an HPAC defect, and is not
repaired here per §29.

## 11. PB/runtime/no-effect proof

```
PB integration = 0
Runtime Enforcement calls = 0
Shell Gate calls = 0
Gate-5 wiring = 0 (unchanged from .3.2.1; Gate-5 binding logic in
    hpac_lifecycle.py's bind_gate5/bind_gate5_canonical is unmodified)
Gate-9 production wiring = 0
Gate-10 effects = 0
runtime subprocess = 0
provider/network = 0
hardware = 0
credentials = 0
external runtime effects = 0
```

Runtime remains: **Observed / observe / unavailable.**

## 12. B1/B7/N1/N2 status

Unchanged:

```
B1 — contract closed / implementation open
B7 — contract closed / implementation open
N1 — contract closed / implementation open
N2 — contract closed / implementation open
```

## 13. Delegated-governance incident status

Preserved, unmodified by this phase:

```
DELEGATED FINALIZATION / COMMIT / PUSH: UNAUTHORIZED
```

This implementation work was performed by a delegated worker with no
commit/push/finalization authority; all governed `pcae` lifecycle,
metadata/report sync, and push/promote steps are performed separately by
the primary operator holding consequential phase authority.

## 14. Finding dispositions at end of repair

```
Finding P (protected-presentation attestation schema):
    REPAIRED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED

Finding C (canonical-store containment):
    REPAIRED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED

Principal provenance:
    REMAINS INDEPENDENTLY CLOSED

Proof writer provenance:
    REMAINS INDEPENDENTLY CLOSED
```

## 15. Recommended next phase

**149O.20L.7O.3W.1R.2B.1R.1.1R.3.2.2.1 — Independent Verification of HPAC
Canonical-Store Containment and Protected-Presentation Attestation-Schema
Repair.**

This phase does not begin `.3.2.2.1` and does not begin Layer 3.
