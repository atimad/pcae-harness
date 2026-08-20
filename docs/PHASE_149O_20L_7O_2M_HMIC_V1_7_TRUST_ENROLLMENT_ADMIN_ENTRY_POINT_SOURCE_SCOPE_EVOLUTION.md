# Phase 149O.20L.7O.2M — HMIC v1.7 Trust-Enrollment Admin Entry-Point Source-Scope Evolution

## Outcome

**HMIC v1.7 TRUST-ENROLLMENT ADMIN ENTRY-POINT SOURCE SCOPE EVOLVED —
38-MEMBER AUTHORITY IDENTITY IMPLEMENTED — EXACT +2 DELTA ESTABLISHED —
INDEPENDENT VERIFICATION PENDING — NO REAL HOST EFFECT PERFORMED.**

This phase widens HMIC-001's frozen authority-bearing source/content
identity from v1.6/36 members to v1.7/38 members by binding the two
standalone Trust-Enrollment administrative CLI entry points,
`scripts/hatp_hardware_credential_admin.py` and
`scripts/hatp_principal_signer_admin.py`, that Phase 149O.20L.7O.2L.4
independently verified as authority-bearing and not yet HMIC-bound. It
does not independently verify its own amendment, certify anything,
provision trust state, create any real Trust-Enrollment record,
redeploy any host, or activate HATP.

## Fixed entry and primary evidence

- Phase-entry commit: `fd782695c90a8d6ac4e6dd6f985aaf3a9540101a`
  ("Phase 149O.20L.7O.2L.4: task lifecycle sync (close task, open idle
  placeholder)").
- Entry state: clean `main`, zero commits ahead of `origin/main`;
  health/check passed; latest completed phase 149O.20L.7O.2L.4
  (VERIFIED WITH NON-BLOCKING FINDINGS).
- HMIC entry identity: v1.6, 27 `src/pcae/`-relative + 9
  repository-root-relative = 36 frozen members, seven contract
  identities, seven required `contract_versions` keys.

## Primary-source re-derivation (§3 of the governing prompt)

Independently re-read (not merely restated from 149O.20L.7O.2L.4's own
report): `HMIC-001` v1.6 in full, `src/pcae/core/hatp_mandatory_
certification.py`'s `_FROZEN_SRC_PCAE_RELATIVE_FILES`/`_FROZEN_
REPOSITORY_ROOT_RELATIVE_FILES` constants, and both scripts'
`scripts/hatp_hardware_credential_admin.py` /
`scripts/hatp_principal_signer_admin.py` complete source and import
graphs (direct and lazy imports).

## HMIC-REQ-052 authority-sensitivity test (§4)

For each script, independently: if only that script changed while
every v1.6 frozen member remained byte-identical, could an
authoritative Trust-Enrollment result differ?

- `scripts/hatp_hardware_credential_admin.py` owns operation selection
  (`enroll`/`revoke`), the confirmation boundary, provider-enrollment
  invocation, registration retry orchestration, and revoke dispatch.
  **Answer: YES.**
- `scripts/hatp_principal_signer_admin.py` owns operation selection
  (`enroll-principal`/`revoke-principal`/`enroll-signer`/
  `revoke-signer`), the confirmation boundary, and exact core-writer
  invocation dispatch. **Answer: YES.**

Both are therefore authority-bearing under HMIC-REQ-052(d)'s existing
dual-anchor construction, one layer further out than the already-bound
core writer modules.

## Complete transitive closure (§5)

Fresh AST/import walk of both scripts:

| Script | Direct imports | Lazy imports |
|---|---|---|
| `scripts/hatp_hardware_credential_admin.py` | `pcae.core.hatp_hardware_credential_admin`, `pcae.core.hatp_hardware_credentials`, `pcae.core.hatp_providers` | `pcae.core.hatp_fido2_provider` |
| `scripts/hatp_principal_signer_admin.py` | `pcae.core.hatp_bootstrap`, `pcae.core.hatp_hardware_credentials`, `pcae.core.hatp_principal_signer_admin` | none |

Every reached module is ALREADY inside `_FROZEN_SRC_PCAE_RELATIVE_
FILES` at v1.6. No helper, path, authority, parsing, provider,
confirmation/election, serialization, or lock module reachable from
either script resolves outside the pre-v1.7 frozen set. **Exact delta:
+2, both entries the scripts themselves — no third file, unlike the
`core/paths.py` omission Phase 149O.20L.7O.2H.2 had to repair.**

## Exact target membership (§6)

- Pre-evolution (v1.6): 27 `src/pcae/`-relative + 9 repository-root-
  relative = **36 members**.
- Post-evolution (v1.7): 27 `src/pcae/`-relative + 11 repository-root-
  relative = **38 members**.
- New entries (both repository-root-relative, appended after
  `scripts/hatp_deployment_binding_admin.py`):
  - `scripts/hatp_hardware_credential_admin.py`
  - `scripts/hatp_principal_signer_admin.py`
- No other membership reordered.

## HMIC version evolution (§7/§8)

`HMIC-001` v1.6 → v1.7: a new authority-bearing digest input widens
HMIC-REQ-050/052(d), the same minor scope-evolution shape as
v1.1/v1.3/v1.4/v1.5/v1.6 (repository contract-versioning precedent,
§60.5/§61.5 of the amended contract) — not a schema/algorithm change,
so not v2.0. Contract identity (`_CONTRACT_IDENTITY_FILES`/
`contract_versions`) remains exactly **seven** members, unchanged;
only `HMIC-001`'s own version header value changes. `HMIC-001`'s own
document bytes join neither `contract_versions` nor the frozen file
set (no self-reference is created).

## Contract and production changes

- `docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_
  CERTIFICATION_CONTRACT.md`: version 1.6 → 1.7; new `**Amended by:**`
  header line; HMIC-REQ-050 enumeration widened to 38 (both new script
  paths appended to the fenced list); HMIC-REQ-052(d) prose extended
  with the standalone-admin-entry-point anchor; HMIC-REQ-067/068/069
  cross-references updated to "unchanged at v1.7"; new §61 recording
  this amendment's own worked closure/self-consistency/finding
  disposition, mirroring §60's precedent.
- `src/pcae/core/hatp_mandatory_certification.py`:
  `_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES` widened 9 → 11 (both new
  script paths appended); `_FROZEN_AUTHORITY_BEARING_FILES` assertion
  36 → 38; header comments ("36-path tuple") updated to 38.

## Self-consistency (§11)

HMIC contract-enumerated count (38) == production
`_FROZEN_AUTHORITY_BEARING_FILES` count (38) == independently
re-derived source-membership count (38); contract identity count (7)
== `CertificationRecord contract_versions` key count (7). Exact-member
comparison performed (`TestExactMembership`/
`TestContractProductionMembershipEquality` in the new focused test
module), not count-only.

## Current-certification consequence (§13) and Mac/Dell divergence (§14)

The real Dell `CertificationRecord` remains immutable historical truth
for its deployed v1.6/36-member source identity — not revoked by this
phase. A v1.6-stored digest evaluated against the live v1.7/38-member
source fails `_validate_at_root`'s step 9 as `IMPLEMENTATION_MISMATCH`
(demonstrated by `TestOldCertificationAgainstNewSource` — real,
unmocked `derive_implementation_scope_digest`, only the stored
comparison value mocked to stand in for the historical digest; no real
Protected Root, binding, or `certifications.json` touched). Mac
development source is now v1.7/38-member; the real Dell remains on its
prior v1.6/36-member certified generation, internally consistent for
what it actually runs — that divergence is intentional until a later,
separately-governed redeployment.

## New scripts remain unused (§15) / No-Go compliance (§16, §27-§31, §37)

No mutating subcommand of either new script was invoked against real
state. No `pcae hatp` certification/activation/DeploymentBinding
command was run. No Dell SSH/checkout/restart. No HATP activation. No
Protected Root mutation. No NB-2L.4-1 retry-loop repair was bundled
into this phase (out of scope by design, §16).

## Focused tests (§17-§22, §32)

New module: `tests/test_phase_149o_20l_7o_2m_hmic_v1_7_trust_
enrollment_admin_entrypoint_source_scope_evolution.py` — 28 tests, all
passing:

- `TestExactMembership` (8 tests): exact 38-member set, +2 delta, both
  scripts bound, no third file, no duplicates, all 38 exist on disk,
  deterministic canonicalization, both paths resolve.
- `TestContractProductionMembershipEquality` (4 tests): contract
  enumerates exactly 38; contract == production membership
  (set-equal); contract declares v1.7; both scripts appear in the
  contract fence.
- `TestDigestParticipation` (4 tests, incl. 2 parametrized): each new
  script's byte mutation changes `implementation_scope_digest` (real
  disposable-fixture derivation); a non-bound documentation file's
  mutation does NOT change the digest; digest is deterministic.
- `TestContractVersionsExactness` (4 tests): `_CONTRACT_IDENTITY_
  FILES` is exactly the seven known IDs; live `derive_contract_
  versions` returns exactly those seven; `HMIC-001` itself is not a
  `contract_versions` member; no unknown/missing key in a disposable
  copy.
- `TestParserCompatibility` (4 tests): accepts a well-formed
  seven-member record; rejects a missing key, an extra key
  (`HMIC-001` itself), and a malformed (list-shaped) mapping.
- `TestOldCertificationAgainstNewSource` (2 tests): the old v1.6/
  36-member digest construction differs from the live v1.7/38-member
  digest; `_validate_at_root` (real, unmocked digest derivation)
  rejects an old-digest-carrying record as `IMPLEMENTATION_MISMATCH`,
  never `VALID`.
- `TestHistoricalSnapshotPreservation` (2 tests): the phase-entry
  commit's own historical `== 36` literal is preserved verbatim; the
  contract's own v1.6 §60 history section is preserved verbatim.

## Stale-assumption sweep (§25/§26)

Searched production/tests/docs for CURRENT-NORMATIVE assumptions of
"36"/"v1.6"/"thirty-six". Classified and repaired:

- **CURRENT NORMATIVE, updated** (8 test files, 18 individual test
  functions): `test_phase_149o_20l_7o_2h_3_...py` (6),
  `test_phase_149o_20l_7o_2k_2_...py` (2),
  `test_phase_149o_20l_7o_2l_1_...py` (3),
  `test_phase_149o_20l_7o_2l_post_...py` (2),
  `test_phase_149o_20l_7o_2l_3_...py` (3),
  `test_phase_149o_20l_7o_2l_4_...py` (2) — each asserted a hardcoded
  `36`/"not yet bound" against a LIVE production import or the live
  contract text; each phase's own docstring already anticipated this
  exact future widening. Repaired by either (a) confirming the new
  live count (38) where the test's own purpose was to check current
  state, or (b) pinning the assertion to that phase's own fixed
  entry/exit commit (via `git show`/`git archive`) where the test's
  purpose was a historical, phase-scoped claim that a later,
  unrelated, legitimate phase should not be able to falsify.
- **HISTORICAL SNAPSHOT, preserved unmodified**: all `==25`/`==28`/
  `==30`/`==35` assertions from phases 149O.19.5B through
  149O.20L.7O.2H.0/2H (pre-dating this phase) — confirmed via a
  git-worktree baseline run that these already fail identically at the
  phase-149O.20L.7O.2L.4 entry commit (pre-existing, unrelated to this
  phase; e.g. `test_phase_149o_20j_2_...py::test_hmic_frozen_scope_
  excludes_all_three_verifier_modules` fails identically at both
  baseline and after this phase's own change) — none are marked
  `fast_green` and none are touched.

## Regression (§33)

Fixed git-worktree baseline at the phase-entry commit
(`fd782695c90a8d6ac4e6dd6f985aaf3a9540101a`) vs. the repaired working
tree, same relevant-suite selection (`-k "hmic or hhce or hpse or
trust_enrollment or certification or hbdc or class_b or readiness or
deployment_binding or signing_ceremony or fido2 or piv or hardware_
credential or principal_signer"`) and `fast_green` marker set.

- **Relevant-suite raw counts**: baseline 347 failed / 5313 passed / 5
  skipped / 9 errors; after this phase's changes, 18 of those 347
  failures are resolved (the CURRENT-NORMATIVE tests repaired above),
  28 new tests added and passing, and the remaining pre-existing
  failure population is unchanged in kind (same historical
  `==25`/`==28`/`==30`/`==35` snapshot tests, still failing identically
  to baseline for reasons unrelated to this phase).
- **`fast_green` raw counts**: baseline 333 failed / 8498 passed / 4
  skipped / 9 errors (raw marker set, no phase-specific deselects
  applied — matches the established pattern in this repository where
  the raw `fast_green` marker query includes many known pre-existing/
  historical-snapshot failures not gated at commit time).
- **Attributable regressions**: 0. Every failing-node difference
  between baseline and the repaired tree is explained either by (a)
  this phase's own intentional, disclosed repair of CURRENT-NORMATIVE
  36-count assumptions (an improvement, not a regression), or (b) a
  pre-existing, unrelated historical-snapshot test whose failure is
  identical at both checkpoints.

## Findings (§35)

No Blocking finding is opened. None of the Blocking triggers fired:
the transitive closure is not broader than expected (+2 exactly, no
third file); contract/source counts do not diverge (38 == 38 == 38,
7 == 7); both new scripts independently and demonstrably affect
`implementation_scope_digest`; the old v1.6 certification does not
remain `VALID` against the new v1.7 source (`IMPLEMENTATION_MISMATCH`
confirmed); no authority dependency remains outside the widened frozen
scope.

## Verdict

**HMIC v1.7 TRUST-ENROLLMENT ADMIN ENTRY-POINT SOURCE SCOPE EVOLVED —
38-MEMBER AUTHORITY IDENTITY IMPLEMENTED — EXACT +2 DELTA ESTABLISHED —
INDEPENDENT VERIFICATION PENDING — NO REAL HOST EFFECT PERFORMED.**

## Recommended next phase

**149O.20L.7O.2M.1 — HMIC v1.7 Trust-Enrollment Admin Entry-Point
Source-Scope Evolution Independent Verification.** No governed
hac-dell redeployment, no fresh `CertificationRecord`, no activation,
and no real FIDO2/PIV hardware enrollment is authorized before that
independent verification passes.
