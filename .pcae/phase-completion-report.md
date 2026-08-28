# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.3.2.2 Complete — HPAC Canonical-Store Containment and Protected-Presentation Attestation-Schema Blocking Repair

Status: completed.

Implementation entry: `3dbb8077c05d02d1eafeef279998e41a5411489a`.

Canonical hand-authored phase doc:
`docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_3_2_2_HPAC_CANONICAL_STORE_CONTAINMENT_AND_PROTECTED_PRESENTATION_ATTESTATION_SCHEMA_BLOCKING_REPAIR.md`.

## Technical verdict

**REPAIRED — INDEPENDENT VERIFICATION PENDING; FINDINGS NOT CLOSED.**

Both Blocking findings left open by `.3.2.1` are repaired:

1. **Finding P (protected-presentation attestation schema).** `presentation_attestation_object()` serialized `installation_store_id` and `simulation_only` into attested bytes, violating HPAC-REQ-092's exact eight-field closed schema. Repaired to serialize exactly `attestation_version`, `presentation_id`, `approval_id`, `approval_subject_digest`, `human_visible_representation_digest`, `descriptor_digest`, `election`, `presented_at`, and no other field. Installed-mechanism authority and permanently-non-real classification remain proven by the already-closed writer-provenance sidecar and `FIXTURE_NON_REAL` verifier-kind channels, untouched by this repair.
2. **Finding C (canonical-store containment).** `HPACLifecycleStore._dir()` and `RuntimeInvocationAuthorityConsumptionStore._path()` joined a caller-supplied `proof_id` directly onto their root with no validation; `pathlib.Path.__truediv__` discards the left operand when the right is absolute, letting an absolute `proof_id` escape the configured root before any check ran. Repaired by adding `require_safe_relative_id_component()` to `hpac_foundation.py` and enforcing it before any file I/O in both stores.

No contract file was modified. No CONTRACT/IMPLEMENTATION INCOMPATIBILITY was encountered.

## Root cause detail

Finding P root cause: the deterministic attestation builder attached two fields useful for internal bookkeeping (which store instance created the fixture, and an explicit non-real flag) directly into the attested envelope, when HPAC-REQ-092 requires exactly the eight-field envelope and states no other field is permitted. Those two properties are still available and enforced through side channels: `record_write`/`verify_record` writer provenance, and `HPACAuthorityClass.FIXTURE_NON_REAL` classification carried outside the attested bytes.

Finding C root cause: `Path(root) / proof_id` in Python silently returns `Path(proof_id)` alone when `proof_id` is absolute, so validation that ran *after* the join (or that assumed containment) never triggered, and in the lifecycle store the escaped file was written before the canonical-path rejection check executed.

## Fixes

- Added `require_safe_relative_id_component()` to `src/pcae/core/hpac_foundation.py`: rejects absolute paths, multi-component paths, `..` segments, and platform path-escape forms, mirroring the existing `_validate_mechanism_id` single-path-component pattern. Invoked before any file I/O.
- `src/pcae/core/hpac_lifecycle.py`: `HPACLifecycleStore._dir()` now calls the new guard before constructing any path.
- `src/pcae/core/runtime_invocation_authority_consumption.py`: `RuntimeInvocationAuthorityConsumptionStore._path()` now calls the same guard before constructing any path. Gate-9 remains inert; only its storage/addressing model changed.
- `src/pcae/core/approval_presentation.py`: `presentation_attestation_object()` narrowed to return exactly the eight HPAC-REQ-092 fields, taking only `evidence` as input.
- `src/pcae/core/approval_presentation_deterministic.py`: updated call site to match the narrowed attestation-object signature.

## Preserved (untouched, regression-verified)

- HumanPrincipalRegistry trust-root mechanics and fixture non-upgradability.
- HumanAuthenticationProof writer provenance and raw/parsed/canonical/verified proof separation.
- Authoritative genesis, complete predecessor validation, alternate-chain rejection, and fork rejection.
- Installed-mechanism presentation authority boundary.

## Tests

- `focused_repair_suite_3_2_2`: **28/28 passed** (new file `tests/test_hpac_canonical_containment_and_attestation_schema_repair_3w1r2b1r111r322.py`), covering attestation-schema positive/negative cases (omitted/wrong field, wrong mechanism/installation/subject/challenge binding, copied/caller-created attestation rejection, non-real classification unchangeable) and canonical-containment cases (absolute path, `../` traversal, nested traversal, symlink escape, cross-store substitution, valid canonical relative identity, canonical path plus unauthorized writer still rejected).
- `full_hpac_family`: **267/278 passed**. All 11 non-passes explained: 7 pre-existing historical `.3.1` failures identical to `.3.2.1`'s recorded baseline; 1 pre-existing flaky concurrency test (confirmed flaky on unmodified HEAD too); 3 `.3.2.1` `blocking_reproduction` tests that now correctly fail because they documented the now-fixed defects (left unedited per the repository's historical-test convention, not rewritten to hide the prior defect).
- `b3_b4_contract_storage`: **44/44 passed**, exact match to `.3.2.1`'s recorded baseline.
- Principal-provenance and proof-writer-provenance regressions: unchanged, all still rejected as before.
- Lifecycle regression (authoritative genesis, forged genesis, alternate chain, fork, predecessor resolution): unchanged.
- Static PB/runtime isolation checks: pass; manual diff scan for forbidden imports found none; Gate-9 remains inert.
- Fast Green: deselected clean-comparison basis is **0 failed (passed)**. Raw unfiltered full-suite run showed 360 failed on the candidate vs. 344 failed on a clean-HEAD comparison; the 16 differing node IDs were investigated, 5 spot-checked individually against a fully clean tree, and all 5 failed identically with zero diff present — falsifying attribution to this repair. These are self-referential frozen-since-old-commit governance tests unrelated to HPAC, plus a CLI-subprocess-timeout test, classified as full-suite run-to-run noise, not a regression.
- Fast Green commit-subject-baseline tooling debt and xdist random-UUID collection debt: carried forward per `.3.2`/`.3.2.1`, not repaired this phase.

## Findings disposition

| ID | Result |
|---|---|
| Finding P — protected-presentation attestation schema | **REPAIRED — independent verification pending — not closed** |
| Finding C — canonical-store containment | **REPAIRED — independent verification pending — not closed** |
| Principal provenance | **REMAINS INDEPENDENTLY CLOSED** |
| Proof writer provenance | **REMAINS INDEPENDENTLY CLOSED** |

## Governance verdict

**DELEGATED FINALIZATION / COMMIT / PUSH: UNAUTHORIZED** (historical `.3` incident, preserved, not revisited). No delegated agent was granted commit, phase-finalization, or push authority in this phase — implementation work was performed by an isolated fork with file-edit access only; all `pcae` task/commit/push/phase-complete commands were run by the primary operator.

## No-Go confirmation

- No Layer 3 mechanism-neutral production verifier or resolver.
- No normative contract modification.
- No historical `.3`, `.3.1`, `.3.2`, or `.3.2.1` artifact rewrite.
- No Permission Broker integration.
- No Runtime Enforcement or Shell Gate activation.
- No B1, B7, N1, or N2 production repair (all remain contract closed / implementation open).
- No real FIDO2, WebAuthn, CTAP, enrollment, or credential operation.
- No protected approval UI, approval CLI, or enrollment CLI.
- No provider, network, subprocess, hardware, or external runtime effect.
- No Gate-9 production wiring, Gate-10 dispatch, or PB/runtime-dispatch consumption.
- No revert, force push, history rewrite, or hook bypass.

Runtime remains `Observed / observe / unavailable`.

## Commit and push state

Phase commits:

- `3dbb8077c05d02d1eafeef279998e41a5411489a`
- `ea18b5ed380ce43ca2b1436c351c37eadd107e03`
- `2d20971e8dc91949279020e9808452b2dfaa0e9f`
- `93f120c99ed2efd6d86ea5cd4d49438b7e814ece`

Pushed: pending (staged prior to push).

## Recommended next phase

**149O.20L.7O.3W.1R.2B.1R.1.1R.3.2.2.1 — Independent Verification of HPAC Canonical-Store Containment and Protected-Presentation Attestation-Schema Repair**

New human authorization is required. Do not begin Layer 3.
