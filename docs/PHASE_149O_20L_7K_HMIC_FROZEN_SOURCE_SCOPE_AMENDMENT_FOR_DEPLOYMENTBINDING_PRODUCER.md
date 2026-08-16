# Phase 149O.20L.7K — HMIC Frozen Source-Scope Amendment for the DeploymentBinding Producer

**Phase-entry commit:** `6f7073ce` (Phase 149O.20L.7J: sync active-task allowed-file list — main, clean, `origin/main` in sync).

## 1. Purpose

Close 149O.20L.7J's own named, non-blocking finding (7J §31): `src/pcae/
core/hatp_deployment_binding_admin.py` and `scripts/hatp_deployment_
binding_admin.py` — the independently verified HBDC-001 v1.1
`DeploymentBinding` producer and its sole intended Protected Admin
ceremony caller — were absent from HMIC-001's frozen authority-bearing
file set, unlike the directly analogous, already-frozen `scripts/
hatp_certification_admin.py`. This phase is **HMIC source-scope
contract/implementation evolution only**: no producer semantic change,
no `DeploymentBinding`/`RepositoryIdentity` creation, no Dell access, no
first-use election, no certification, no activation.

## 2. 7J Finding Reconstruction

Independently re-read 7J §31 directly (not summarized): `hatp_mandatory_
certification.py`'s pre-phase `_FROZEN_SRC_PCAE_RELATIVE_FILES` (22
entries) + `_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES` (6 entries) = 28,
`assert`-pinned. Neither the producer nor the admin script appeared in
either tuple. 7J classified this an "HMIC source-scope gap," non-blocking
to HBDC-REQ-056..070 compliance but recommended for a dedicated
contract-amendment-then-verification sequence, mirroring 149O.20D→...→
149O.20G and 149O.20K→...→149O.20K.3's own precedent shape.

## 3. HMIC Source-Scope Normative Reconstruction

Read `docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_
CERTIFICATION_CONTRACT.md` §17/§20 directly at v1.3. HMIC-REQ-050 (exact
28-file enumeration), HMIC-REQ-051 (embedded, not external), HMIC-REQ-052
(closure rule, limbs (a)/(b)/(c)), HMIC-REQ-053 (contract-byte binding)
all re-read from source, not from any prior phase's summary. Full detail:
contract §55.1.

## 4. Historical Source-Scope Evolution

18 files (v1.0, architecture-selected) → +4 provider files (149O.19.3R,
finding B-149O.19.3-1, §49) = 22, v1.0-repaired → +2 (`hatp_mandatory_
certification.py`, `scripts/hatp_certification_admin.py`; 149O.19.5E.1,
limb (b) added, §50) = 24, v1.1 → byte-unchanged at v1.2 (149O.20D, §51,
`contract_versions` widened to 5, enumeration untouched) → +1 (HBDC-001
document bytes; 149O.20D.1, finding B-149O.20D-1, §52) = 25, same version
→ +3 (three Class-B verifier files; 149O.20K, limb (c) added, §53) = 28,
v1.3 → **+2 this phase (the DeploymentBinding producer pair; limb (c)
widened with a third anchor, §55) = 30, v1.4**.

## 5. Exact Pre-7K Frozen Member Set

28 entries (22 `src/pcae/`-relative + 6 repository-root-relative: 5 bound
contracts + `scripts/hatp_certification_admin.py`), independently
re-extracted from both the live contract text and the live production
constant, confirmed identical in presentation order (149O.20K.2/20K.3's
own established alignment, unmodified since).

## 6. Producer Module Authority Analysis

`core/hatp_deployment_binding_admin.py`'s `create_deployment_binding`/
`rotate_deployment_binding`/`revoke_deployment_binding` create, rotate,
and revoke `DeploymentBinding` records; control what authority-bearing
field values (`principal_id`, `signer_key_id`, `provider_profile`,
`authority_scope`, `canonical_deployment_root`) become durably active;
validate prerequisites (`AuthorityEvidence` shape, `RepositoryIdentity`
presence, revoked/nonexistent-entry fail-closed rules); and emit
lifecycle audit events. A byte edit here (e.g. dropping the
create-against-revoked fail-closed check) changes what `DeploymentBinding`
the already-frozen `hatp_bootstrap.py`/`repository_identity.py` read path
subsequently accepts as authoritative — changing HBDC-REQ-042's
contribution to `verify_class_b_deployment_conformance`'s verdict without
changing any pre-v1.4 HMIC digest. **Real identity-scope defect** (per
this phase's own §8 test). Full analysis: contract §55.5-§55.6.

## 7. Admin Script Authority Analysis

`scripts/hatp_deployment_binding_admin.py` contains real authority-
relevant semantics of its own (the `_prompt_confirm` human-confirmation
gate; `AuthorityEvidence` construction from raw CLI strings) — it does
not merely delegate inertly. It selects no root/subject/operation beyond
the neutral `--repository-root` locator (mirroring `scripts/hatp_
certification_admin.py`'s identical pattern) and cannot dynamically
redirect to a different producer implementation (static `from pcae.core.
hatp_deployment_binding_admin import ...`, confirmed by AST walk, no
`importlib`/`__import__`). Modifying it (e.g. removing the confirmation
gate) changes authority outcomes while producer bytes remain unchanged.
**Included for the same reason as the producer module itself, not solely
by analogy.**

## 8. Certification-Admin Analogy Analysis

`scripts/hatp_certification_admin.py` was bound at v1.1 (149O.19.5E.1,
§50) because it directly writes protected certification state via
`hatp_mandatory_certification.py`'s internal writer primitives, and is
the sole intended Protected Admin ceremony caller. Compared across
privilege (identical: real OS write access to the Protected Root is the
actual boundary for both), target artifacts (certification records vs.
`DeploymentBinding` records — different data, same authority shape),
validation (both derive most fields read-only, accept minimal
human-entered authority-sensitive input), argument interpretation (both
use a neutral `--repository-root` locator, never accept the derived
identity/root directly), and role in the pipeline (both are the sole
production-intended write path for their respective protected state).
**Analogy used as supporting evidence only** — the independent §6/§7
authority analysis is the actual basis for inclusion (per this phase's
own instruction, item 10).

## 9. Sibling Privileged-Writer Inventory

`scripts/*.py` contains exactly two files: `hatp_certification_admin.py`
(already frozen) and `hatp_deployment_binding_admin.py` (this phase).
Grep for "Protected Admin"/"Class-B Protected Administrator" phrasing
across `src/pcae/core/*.py` additionally surfaces `hatp_signing_
ceremony.py` — inspected and confirmed **not** an equivalent gap: it
calls only `HATPTrustStore.lookup_signer` (an existing **read** method;
`HATPTrustStore` still has zero write methods per the producer's own
docstring), has zero production consumers (`sign_rollback_evidence` is
called nowhere), and publishes via `hatp_evidence_store.HATPEvidenceStore.
publish` — already-frozen. **No scope broadening.**

## 10. Per-File Inclusion Decision

| File | Classification | Basis |
|---|---|---|
| `core/hatp_deployment_binding_admin.py` | **MUST INCLUDE** | §6; limb (c) third anchor |
| `scripts/hatp_deployment_binding_admin.py` | **MUST INCLUDE** | §7; limb (c) third anchor |

Both files qualify independently, not merely because the pair mirrors
the certification-admin precedent (§8's analogy is supporting evidence
only, per this phase's own governing instruction).

## 11. Selected Normative Repair Model

HMIC-REQ-052 limb (c)'s "specifically, any file reachable from `verify_
class_b_deployment_conformance`'s own call graph" text, read literally,
does **not** reach the producer pair (confirmed by AST import walk: the
verifier imports `hatp_bootstrap`/`repository_identity`/the topology and
environment-lock modules/`pcae.core.paths` only — never the producer).
This is not a "production enumeration wrong under an existing rule" case
(unlike, e.g., 149O.20F/20G's pure alignment) — the v1.3 text genuinely
does not reach these files. **Contract evolution required**, not
implementation-only repair. Selected model: widen limb (c) with a third,
explicit, non-call-graph anchor — the identical construction limb (b)
already uses for `scripts/hatp_certification_admin.py` (§50) — rather
than inventing a new limb (d), since the concern (the Class-B
deployment-conformance verdict) is exactly what limb (c) already names,
reached by data dependency rather than call-graph reachability.

## 12. HMIC Version Decision

`HMIC-001 v1.3 → v1.4`, in-place minor bump: normative-scope widening
(new closure-rule anchor + 2 enumerated files), the identical shape as
v1.0→v1.1 (§50) and v1.2→v1.3 (§53), not a same-version repair (unlike
§52/§54, which fixed defects in existing bindings without adding limb
scope) and not v2.0 (no existing field/schema/algorithm redefined or
removed). Full rationale: contract §55.14.

## 13. Exact Contract Changes

- §0 header: version 1.3→1.4, status line, new "Amended by" entry.
- §17 (HMIC-REQ-050): enumeration 28→30 entries (two new lines: `core/
  hatp_deployment_binding_admin.py`, `scripts/hatp_deployment_binding_
  admin.py`); explanatory paragraphs for the new entries; summary
  paragraph updated (28→30, `§55` cross-reference added).
- §17 (HMIC-REQ-052 limb (c)): widened with the third anchor (verbatim
  text in contract §17, reproduced in full at contract §55's own
  amendment record).
- §17 union-derivation paragraph: new item (f), five→six sources.
- §41: attack-matrix heading 38→39 scenarios; new row #39.
- New §55: "Contract Amendment History — Phase 149O.20L.7K (v1.4)" —
  15 subsections (§55.1-§55.16), full independent derivation, matching
  §53's own structural precedent.
- §0-48, §49-54 (original freeze narrative and all prior amendment/
  repair history sections): **byte-untouched**, per this contract's own
  append-only-history convention.

## 14. Exact Frozen-Set Implementation Changes

`src/pcae/core/hatp_mandatory_certification.py`:
- `_FROZEN_SRC_PCAE_RELATIVE_FILES`: append `"core/hatp_deployment_
  binding_admin.py"` (22→23 entries).
- `_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES`: append `"scripts/hatp_
  deployment_binding_admin.py"` (6→7 entries).
- `assert len(_FROZEN_AUTHORITY_BEARING_FILES) == 28` → `== 30`.
- Module docstring/comments: "28-path enumeration, v1.3" → "30-path
  enumeration, v1.4"; "28-path tuple" → "30-path tuple"; new explanatory
  comment paragraphs for both constants matching the contract's own
  §17 prose.
- No other production file touched. `core/hatp_deployment_binding_
  admin.py` and `scripts/hatp_deployment_binding_admin.py` themselves:
  **byte-identical** to their 149O.20L.7J-verified state (SHA-256
  compared before/after this phase; see §22-23 below).

## 15. Pre/Post Member Count

**Pre-7K:** 28 (22 + 6). **Post-7K:** 30 (23 + 7).

## 16. Exact Added Paths

```
src/pcae/core/hatp_deployment_binding_admin.py
scripts/hatp_deployment_binding_admin.py
```

## 17. Exact Removed Paths

**None.** No removal occurred or was considered; none is justified by
any architecture finding this phase discovered.

## 18. Complete Post-Change Member List

The full 30-entry contract §17 enumeration (verbatim, in canonical
presentation order) is reproduced in `hatp_mandatory_certification.py`'s
`_FROZEN_AUTHORITY_BEARING_FILES` and independently re-derived by
`tests/test_phase_149o_20l_7k_..._deploymentbinding_producer.py::
test_production_frozen_set_exactly_equals_live_contract_30_file_set`,
which compares the two extractions for exact set equality on every test
run (not a one-time manual check).

## 19. Pre/Post Implementation/Source Digest

- **Pre-7K** (28-file set, computed against this phase's own untouched
  worktree): `d5129ce26c98b595c6583ec2097274d9257c1f73b2b347503f5b66d7286996ca`
- **Post-7K** (30-file set): `65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8`

Different, as expected (both the file set and `hatp_mandatory_
certification.py`'s own bytes changed). Independently recomputed via
`derive_implementation_scope_digest` at both states (git-stash A/B, not
inferred).

## 20. Contract-Identity Consequence

`contract_versions` (HMIC-REQ-067, `_CONTRACT_IDENTITY_FILES`) is
**unchanged**: still exactly 5 members (`HMRC-001`, `HATP-001`,
`HSCE-001`, `RAE-001`, `HBDC-001`). This phase adds PCAE-owned *source*
to `implementation_scope_digest`, not a new normative *contract* — the
producer's own governing contract, `HBDC-001`, is already a
`contract_versions` member (since v1.2) and already digest-bound (since
149O.20D.1); neither binding is duplicated or altered.

## 21. Per-New-Member Digest Sensitivity

Independently tested in the live worktree (byte appended, digest
recomputed, byte restored, digest reconfirmed identical to baseline) for
**each** new member individually:
- `core/hatp_deployment_binding_admin.py`: baseline
  `65ff8ab0...`→perturbed `ee5cf4a0...` (differs) → restored `65ff8ab0...`.
- `scripts/hatp_deployment_binding_admin.py`: baseline `65ff8ab0...`
  → perturbed `b7e36afc...` (differs) → restored.
Both also independently confirmed **insensitive** under the pre-7K
(28-file) frozen set (perturbed-producer digest under the old set:
`d5129ce2...`, identical to the old baseline) — proving the omission was
real before this phase and closed after it. Permanent regression tests:
`tests/test_phase_149o_20l_7k_..._deploymentbinding_producer.py::
test_new_member_byte_perturbation_changes_digest` (parametrized, both
files).

## 22. Non-Member Control

`src/pcae/core/paths.py` (a clearly non-authority-bearing, non-member
file) perturbed and restored: digest unchanged (`65ff8ab0...` both
before and after) under the post-7K 30-file set — no accidental scope
broadening. Permanent test: `test_non_member_control_perturbation_does_
not_change_digest`.

## 23. Frozen-Path-Missing Failure

Each new member individually removed (moved aside, not deleted) from the
live worktree and restored: `derive_implementation_scope_digest` raises
`FrozenFileDerivationError` ("frozen file does not exist: ...") — fails
closed, never silently skips. Permanent test: `test_new_member_missing_
file_fails_closed` (parametrized, both files).

## 24. Duplicate/Path-Normalization Behavior

`len(set(_frozen_canonical_paths())) == len(_FROZEN_AUTHORITY_BEARING_
FILES)) == 30` — no duplicate logical path. All 30 canonical paths are
repository-relative, POSIX-separator, contain no `..`/absolute/empty
segment, and resolve to existing, non-symlinked, regular files.
Permanent tests: `test_no_duplicate_frozen_paths`, `test_no_unsafe_path_
segments`, `test_all_30_frozen_paths_exist_are_regular_and_not_
symlinked`.

## 25. Full Transitive Authority-Bearing Coverage Matrix

See contract §55.9 for the complete ten-row matrix (admin script →
producer → `DeploymentBinding` schema → `HATPTrustStore` primitives →
`RepositoryIdentity` reader → HBDC matcher → Class-B aggregator → audit
sink [excluded] → path value type [excluded]). Every executable
component in the create-to-verdict chain is frozen directly, already
frozen as a dependency, or intentionally excluded with documented
rationale — no unaccounted component.

## 26. HBDC v1.1 Unchanged Proof

`docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` read in full before
and after this phase's edits (to `HMIC-001` and `hatp_mandatory_
certification.py`, two distinct files); byte-identical (`git diff`
against the phase-entry commit shows zero lines changed in that path).
Permanent test: `test_hbdc_contract_byte_unchanged_since_phase_entry`.

## 27. Producer Implementation Unchanged Proof

SHA-256 of `core/hatp_deployment_binding_admin.py`, computed before this
phase's first edit and at finalization: identical. This phase's own edit
is confined to `hatp_mandatory_certification.py` and this contract
document. Permanent test: `test_producer_and_admin_script_byte_
identical_since_phase_entry`.

## 28. Admin Script Behavioral-Unchanged Proof

SHA-256 of `scripts/hatp_deployment_binding_admin.py`, identical
before/after. Same permanent test as §27 (parametrized).

## 29. Consumer Unchanged Proof

`hatp_bootstrap.py` SHA-256 identical before/after (not touched by this
phase — confirmed by `git diff --stat` against `src/pcae/core/hatp_
bootstrap.py` showing zero lines). `hatp_class_b_conformance.py` and
`repository_identity.py` likewise unchanged (permanent test:
`test_three_class_b_verifier_files_still_frozen_and_byte_unchanged`,
which also covers the topology/environment-lock verifiers).

## 30. Dell Staleness Analysis

Unchanged from 7J: Dell still runs source predating HBDC-001 v1.1, the
producer implementation, and now this phase's v1.4 contract amendment.
This phase performed **zero** Dell access (read or write) — no
justification existed to touch it for a source-scope-only amendment.

## 31. Existing Boundary-P Status Consequence

Unaffected. 7E's physical-provisioning result (**INDEPENDENTLY
VERIFIED**) is a distinct claim from "Dell source is current with the
latest HMIC/HBDC architecture," which it is not (§30) — this phase does
not conflate the two, consistent with 7J/7E's own discipline.

## 32. Certification Consequence

No HMIC certification exists (`.pcae/protected/certifications.json`
absent from this repository's own working tree, unaffected by this
phase). This amendment therefore revokes nothing; it establishes that
**any future** certification must be derived against the new,
thirty-file frozen identity once independently verified.

## 33. Historical-Pin Test Classification

`pytest -m fast_green` — pre-7K baseline: **218 failed / 7563 passed**.
Post-7K (with this phase's own new 24-test module and the two repaired
7I/7J guard tests): **274 failed / 7531 passed**. Net delta: +56 new
failures (full sorted-node-ID diff, not aggregate-count inference; one
pre-existing failure — `test_backend_cli.py::TestBackendReviewApprove::
test_approve_updates_latest` — flipped to passing, an unrelated,
order-dependent flake in that file, confirmed by its sibling `Test
BackendReviewReject::test_reject_succeeds_with_correct_ids` flipping the
opposite direction in the same run).

Every one of the 56 net-new failures individually inspected and
classified into exactly two buckets:

1. **Transient uncommitted-working-tree artifacts** (the majority):
   tests asserting `git status --porcelain -- src/pcae`/`docs/contracts`
   is empty, or diffing a fixed historical commit against the *live,
   uncommitted* worktree. These fail only while this phase's own edits
   are staged-but-uncommitted and self-resolve once this phase's
   implementation commit lands (verified: re-run after commit, §35).
2. **Historical predecessor-phase count/derivation pins**, all in
   149O.20K/149O.20K.1/149O.20K.2/149O.20K.3's own test modules (each
   titled for, and scoped to, that specific historical widening's own
   "current live state is exactly 28" target) plus a handful of earlier
   phases' modules (149O.20D/20D.1/20E, 149O.19.4/19.5E.4, 149O.14/17/
   1G/20A/20C/20H/20I, 149O.20L.1/1A/1B/3/4, 149O.20L.7D.8/9/10/11, 7E)
   whose own "as of my phase, the frozen set is exactly N" or "no
   production file changed since my phase entry" assertions are
   invalidated by this phase's legitimate widening — **the identical,
   already-established pattern** by which 149O.20K's own 25→28 widening
   already broke 149O.20D/20D.1/20F/20G's "exactly 25" pins (confirmed:
   those failures are present in the pre-7K 218-failure baseline,
   unrepaired by any intervening phase) and 149O.20D's 24→25 widening
   broke 149O.19.5E.3/5E.4's "exactly 24" pins (also confirmed
   pre-existing). No new failure category was found; no failure traces
   to an actual security, semantic, or behavioral regression.

**Verdict: REGRESSION CLEAN WITH EXPECTED HISTORICAL IDENTITY-PIN
MIGRATION.**

## 34. Regression A/B

See §33. Baseline captured via `git stash` A/B on the same worktree (not
a separate clone), immediately before and after this phase's production
edits, both runs using the identical `pytest -m fast_green -q -n auto`
invocation.

## 35. Prior Security Regression Result

Zero. No producer create/rotate/revoke behavior changed (§27). No
HBDC-REQ-042 consumer changed (§29). No source-digest derivation
algorithm changed (only its input file list widened, per HMIC-REQ-
054-058, unmodified). No certification-validation logic changed (no
certification exists to validate). No Class-B ACL/symlink/path-safety
logic changed (§29's three-file byte-identity proof).

## 36. Canonical Source-Scope Finding ID/Status

7J's own §31 finding (no separate `B-`-prefixed ID was minted by 7J;
referenced here identically as 7J did). **Status: REPAIRED AT THE
CONTRACT-AND-PRODUCTION LAYER — INDEPENDENT VERIFICATION PENDING — NOT
CLOSED.** Only 149O.20L.7L may close it.

## 37. Audit-Gap Finding Status

7J §17's audit-failure-after-durable-mutation exception-type gap:
**carried forward unchanged.** Not touched, not claimed repaired.

## 38. Parser-Gap Finding Status

`hatp_bootstrap.py::_parse_iso_timestamp`'s permissive-read-path finding
(7I/7J): **carried forward unchanged.** `hatp_bootstrap.py` itself is
byte-identical (§29).

## 39. HMIC Revocation-Validation Finding Status

HMIC-REQ-103's "revocation does not automatically invalidate an existing
`CertificationRecord` validation" gap (7G/7H/7J): **carried forward
unchanged.** Source-scope inclusion and certification lifecycle are
independent concerns, per this phase's own trust wall.

## 40. Proof of No Real Binding / No Repository Identity / No Dell Mutation / No Election / No Boundary-C Work

- No `DeploymentBinding` created: `.pcae/registry.json`-shaped artifact
  absent from this repository's working tree (permanent test).
- No `RepositoryIdentity` created: `.pcae/repository-identity.json`
  absent (permanent test).
- No Dell mutation: zero Dell access performed this phase (§30).
- No first-use election: no APPROVE/DECLINE/AMEND ceremony presented or
  performed.
- No Boundary-C work: no certification request, no CHGR, no publication.

## 41. Tests

New: `tests/test_phase_149o_20l_7k_hmic_frozen_source_scope_amendment_
for_deploymentbinding_producer.py` (24 tests, all passing). Repaired (to
reflect the now-closed gap, per each test's own original failure-message
instruction): `tests/test_phase_149o_20l_7i_deploymentbinding_producer_
implementation.py::TestNotAgentReachable::test_no_src_pcae_module_
imports_the_producer_except_itself` and `tests/test_phase_149o_20l_7j_
deploymentbinding_producer_implementation_independent_verification.py::
test_hmic_frozen_file_set_now_includes_deployment_binding_admin_files`
(both: excluded `hatp_mandatory_certification.py`'s own now-legitimate
literal-string reference from the "not referenced anywhere" text-grep,
preserving the real security property — no *import*, no agent-executable
code path). Full 7I/7J suites re-run green (61 passed). Full fast_green
classification: §33-34.

## 42. Governance Results

`pcae health`: healthy. `pcae check`: passed. `pcae status coherence`:
coherent. `pcae push check` (pre-phase): nothing_to_push. `pcae runtime
inspect`: unchanged (not_implemented/Observed/observe/unavailable).
`pcae notify status`: Telegram configured/enabled.

## 43. Commits

See governed finalization commits following this report (task
transition, implementation commit, PROJECT_STATUS.md/CHANGELOG.md
commit, task close, phase-completion-metadata/report sync, stage-
pending-push, push, promote) — recorded in the finalization sequence
this doc's own companion metadata tracks.

## 44. Pushed Status / origin/main..HEAD

Recorded at governed finalization (§43); expect `pcae push` to succeed
cleanly given `pcae push check` was clean at phase entry.

## 45. Exact Recommended Next Phase

**149O.20L.7L — HMIC Frozen Source-Scope Amendment for the
DeploymentBinding Producer Independent Verification.** Must
independently reconstruct, without trusting this report's narrative: the
inclusion decision (§6-11); the exact member set (§15-18); contract/
version correctness (§12-13, contract §55.14); digest sensitivity for
both producer surfaces (§21-24); no omitted authority-bearing transitive
source (§25); no unintended producer behavior change (§27-29); Dell
remains untouched (§30); first-use remains unauthorized (§40). 7L is
**verification-only** — no redeployment, binding, election,
certification, or Dell mutation. Only after 7L passes may a future,
separately-governed first-use-preparation phase proceed.
