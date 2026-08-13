# Phase 149O.20K: HMIC Class-B Verifier Source-Scope Contract Evolution

**Status:** COMPLETE — CONTRACT EVOLUTION ONLY — NOT PRODUCTION-ALIGNED — NOT INDEPENDENTLY VERIFIED
**Addresses:** CBV-S1 (verifier source outside independently verified HMIC source identity)
**Contract amended:** `docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md` (HMIC-001), v1.2 → v1.3, new §53

This phase is a **contract/source-scope evolution phase**. It is not
production HMIC source-set alignment, readiness integration, Class-B
provisioning, certification, activation, Permission Broker work, or
runtime capability elevation.

---

## 1. Purpose

Evolve the HMIC source-identity contract so the now independently
verified (149O.20J.8) Class-B verifier authority derivation can
eventually become HMIC-bound. Independently derive the exact
transitive authority-dependency closure HMIC-REQ-052 requires — never
assuming `25 + 3 = 28` in advance.

## 2. HMIC-REQ-052 — independently reconstructed (before analysis)

Read directly from the contract, not from prior-phase summaries. At
v1.2, HMIC-REQ-052 bound a PCAE-owned file only if reachable,
transitively, from:

- limb (a): `assess_hatp_mandatory_activation_readiness`'s own call
  graph; or
- limb (b) *(v1.1)*: `validate_active_hatp_mandatory_independent_
  verification_certification`'s call graph, or the Protected Admin
  ceremony functions in `scripts/hatp_certification_admin.py`.

Direct source search (`grep` across all of `src/`) confirmed neither
limb reaches `verify_class_b_deployment_conformance` or its two
sub-verifiers anywhere in production. Under the v1.2 text alone, the
three Class-B verifier files are **not** bound by HMIC-REQ-052 — a
genuine scope gap, not an oversight, since neither limb existed to
cover a verifier island with zero consumers. This phase adds a new
limb (c), anticipatory in the same sense limb (b) was at v1.1: it binds
the verifier's authority-sensitive source now, before any consumer
exists.

## 3. Current HMIC source scope — independently reconstructed

Read directly from `src/pcae/core/hatp_mandatory_certification.py`:

- `_FROZEN_SRC_PCAE_RELATIVE_FILES`: 19 entries.
- `_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES`: 6 entries (five bound
  contract documents + `scripts/hatp_certification_admin.py`).
- `_FROZEN_AUTHORITY_BEARING_FILES` = concatenation of the two, with a
  live runtime `assert len(...) == 25` in the module itself.
- `_CONTRACT_IDENTITY_FILES`: exactly 5 `(contract_id, path)` pairs
  (`HMRC-001`, `HATP-001`, `HSCE-001`, `RAE-001`, `HBDC-001`).

Compared entry-for-entry against the pre-amendment HMIC-REQ-050 text:
identical, confirming production and contract were already in
alignment at 25/5 before this phase (149O.20F/149O.20G/149O.20J.8's own
prior reconfirmations restated).

## 4. Fresh Class-B verifier dependency graph

An independent `ast`-based import walk (`ast.parse` + `ast.walk`) was
run against the current on-disk bytes of all three verifier modules —
not against any prior phase's dependency list:

| Module | PCAE-owned imports | Other imports |
|---|---|---|
| `hatp_class_b_topology_verifier.py` | `pcae.core.hatp_bootstrap` | stdlib only (`ast`, `inspect`, `os`, `re`, `stat`, `subprocess`, `sys`, `dataclasses`, `enum`, `pathlib`, `typing`, `grp`, `pwd`) |
| `hatp_environment_lock_verifier.py` | symbols from the sibling `hatp_class_b_topology_verifier` module | stdlib only (`importlib.metadata`, `importlib.util`, `os`, `site`, `sys`, `pathlib`, `typing`, `shutil.which`) |
| `hatp_class_b_conformance.py` | `pcae.core.hatp_bootstrap`, `pcae.core.repository_identity`, `pcae.core.paths` (`HarnessPath`), symbols from both sibling verifiers | stdlib only (`importlib.metadata`, `pathlib`, `typing`, `json`) |

No fourth PCAE-owned module is reached by any import statement. No
dynamic (`importlib.import_module`/`__import__`) PCAE-owned import
found. No `docs/contracts/**` document is read at runtime by any of the
three modules (the sole `Path(__file__).read_text(...)` call is the
topology verifier reading its own source for a self-scan, not a
contract document).

## 5. Zero-consumer and no-duplicate-logic confirmation

Text search of all of `src/` for the three module names and
`verify_class_b_deployment_conformance`/`verify_class_b_topology_
conformance`/`verify_environment_lock_conformance`, excluding the three
files themselves: **zero matches**. `hatp_mandatory_cutover.py` and
`human_approval_trusted_provenance.py` reference only the unrelated
string/concept "Class-B" (`class_b_protected_storage_available`,
`class_b_bootstrap_environment_safe` — CBV-S10's own pre-existing
readiness terms), never the verifier island's symbols. No parallel or
duplicate Class-B decision logic exists elsewhere in production.

## 6. Dependency classification (A–E)

- **Category A (bind).** The three root modules themselves —
  `hatp_class_b_topology_verifier.py`, `hatp_environment_lock_
  verifier.py`, `hatp_class_b_conformance.py`. Each independently alters
  the `COMPLIANT`/`NON_COMPLIANT`/`INDETERMINATE` verdict.
- **Category B (exclude, PCAE-owned but non-authority-sensitive).**
  `pcae.core.paths` (`HarnessPath`) — used only as a lightweight path
  value type, carries no ACL/identity/verdict logic. Identical exclusion
  precedent already named in the contract for limbs (a)/(b) (§49/§50).
  `hatp_bootstrap.py`/`repository_identity.py` are authority-sensitive
  but already bound via limb (a) — no new decision needed.
- **Category C (standard library, disclosed residual trust).** `ast`,
  `inspect`, `os`, `re`, `stat`, `subprocess`, `sys`, `dataclasses`,
  `enum`, `pathlib`, `typing`, `grp`, `pwd`, `importlib.metadata`,
  `importlib.util`, `site`, `shutil` — per HMIC-REQ-065, already frozen.
- **Category D (external/system tools — relate to HBDC, not
  HMIC-solvable).** `git`, the `ls`-based macOS ACL text format, the
  `pcae` launcher (`shutil.which`), the Python interpreter, the
  filesystem/kernel ACL subsystem. Related to HMIC-REQ-067's HBDC-001
  binding and HMIC-REQ-063's residual limitation, not overclaimed as
  solved by this amendment.
- **Category E (contract/document inputs).** None of the three modules
  reads contract document bytes at runtime; HBDC-001 is already bound
  via HMIC-REQ-050/053/067 — not duplicated by this phase.

## 7. Aggregator and sub-verifier semantics (worked)

`hatp_class_b_conformance.py::verify_class_b_deployment_conformance`
calls `verify_class_b_topology_conformance()`,
`verify_environment_lock_conformance()`, `_check_model_a_deployment`,
and `_check_deployment_identity`, folding all four through shared
`_aggregate_status`/`_build_result` primitives. All four inputs —
including the aggregator's own two additional checks — are
authority-sensitive and are covered by `hatp_class_b_conformance.py`'s
own Category-A membership. `hatp_environment_lock_verifier.py` and
`hatp_class_b_topology_verifier.py` were each independently traced for
every dependency capable of affecting their respective verdicts: all
logic is local or already accounted for (§4).

## 8. Cycle / self-binding analysis

`hatp_environment_lock_verifier.py` defines
`_AUTHORITY_MODULE_RELATIVE_PATHS`, a 19-entry literal tuple
hand-reproduced from HMIC-REQ-050's `src/pcae/`-relative bucket, used
only by `_check_module_origin_containment`. Its own comment states it
is deliberately **not imported** from `hatp_mandatory_certification.py`
"since that would make this diagnostic-only module a runtime dependent
of an already-HMIC-bound file for no authority reason." Independently
confirmed by AST walk: zero `Import`/`ImportFrom` nodes in any of the
three verifier modules name `hatp_mandatory_certification` or
`hatp_certification_admin`; neither of those two files imports any of
the three verifier modules. No HMIC validator/admin self-reference, no
digest-construction cycle, no Class-B→HMIC→Class-B recursion. W-1 is
not reopened — this finding does not disturb the distinct file pair W-1
concerned.

## 9. Regression checks

- **B-149O.19.3-1:** `hatp_providers.py`, `hatp_fido2_provider.py`,
  `hatp_piv_provider.py`, `hatp_hardware_credentials.py` remain present,
  unremoved, unmodified in `_FROZEN_SRC_PCAE_RELATIVE_FILES`.
- **B-149O.20D-1:** `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`
  remains present, unremoved, unmodified in `_FROZEN_REPOSITORY_ROOT_
  RELATIVE_FILES`, still receiving both the `contract_versions` and
  `implementation_scope_digest` bindings.
- This phase edits only the HMIC-001 contract document; it does not
  touch `src/pcae/core/hatp_mandatory_certification.py`.

## 10. Threat analysis

- **Incomplete binding.** Omitting any one of the three files leaves a
  channel by which the aggregate verdict can change while every *bound*
  file's digest stays identical — closure violated. No transitive
  PCAE-owned helper was found omitted beyond the three roots.
- **Over-binding.** `pcae.core.paths` was inspected and excluded
  specifically to avoid unnecessary digest volatility/recertification
  churn. `git`/`ls`/the interpreter cannot be brought into HMIC scope by
  naming a PCAE file — binding them would misrepresent HMIC as covering
  environment/kernel assumptions it cannot cover.

## 11. Derived target source set

- **Current (pre-amendment):** 25 files / 5 contract-identity members.
- **Added:** exactly 3 — `core/hatp_class_b_topology_verifier.py`,
  `core/hatp_environment_lock_verifier.py`,
  `core/hatp_class_b_conformance.py` (all `src/pcae/`-relative).
- **Excluded (inspected, not added):** `pcae.core.paths` (Category B,
  §6).
- **Derived new total:** 28 files / 5 contract-identity members
  (unchanged — no new contract document introduced).

The count (28) is the *result* of the closure walk (§4-§8), not a
starting assumption — confirmed by the fresh AST/text-search evidence
recorded above and reproduced independently in
`tests/test_phase_149o_20k_hmic_class_b_verifier_source_scope_contract_evolution.py`.

## 12. Contract-version determination

This amendment widens HMIC-REQ-050's enumeration (25 → 28) and adds a
new limb (c) to HMIC-REQ-052 — the same shape of change as the v1.0 →
v1.1 amendment (§50: widened HMIC-REQ-050/052 by adding limb (b) and two
files), not a same-version repair like 149O.20D.1 (§52). No existing
requirement's meaning is narrowed; every prior mechanism continues to
apply unmodified to a longer file list. Following the repository's own
established minor-bump convention for scope-widening amendments:
**HMIC-001 v1.2 → v1.3**, an in-place minor bump.

## 13. Contract amendment made

- Header block: Version 1.2 → 1.3; status line updated; new
  "Amended by: Phase 149O.20K" line added.
- HMIC-REQ-050: enumeration widened from 25 to 28 entries (three new
  `src/pcae/`-relative entries added); prose updated to explain the
  widening and attribute it to this phase.
- HMIC-REQ-052: new limb (c) added, naming
  `verify_class_b_deployment_conformance`'s call graph as the anchor;
  union-derivation prose updated to name source (e).
- Attack matrix: "37 Scenarios" → "38 Scenarios"; new row 38 added,
  modeled on the existing "not yet operative" convention (attacks
  #33/#34/#36/#37).
- New §53 "Contract Amendment History — Phase 149O.20K (v1.3)" added,
  documenting §53.1–§53.14: the full reconstruction, dependency graph,
  classification, aggregator semantics, cycle analysis, regressions,
  threat analysis, target-set derivation, version-bump rationale, and
  verdict.

## 14. What this phase explicitly did NOT do

- Did not update `_FROZEN_AUTHORITY_BEARING_FILES`/`_CONTRACT_IDENTITY_
  FILES` in `src/pcae/core/hatp_mandatory_certification.py` — production
  remains 25/5, intentionally and disclosed-ly stale relative to the
  contract's new 28/5 target (mirroring the identical contract-ahead-
  of-production sequencing at v1.1 and v1.2/149O.20D.1).
- Did not modify any of the three Class-B verifier production modules.
- Did not modify HBDC-001 or any other bound contract.
- Did not wire `verify_class_b_deployment_conformance`'s result into
  any readiness/certification/activation code path.
- Did not touch CBV-S10, readiness schemas, certification/activation
  logic, Permission Broker, POL-005, COMP-002, or Runtime Enforcement.
- Did not provision Class-B (no OS user/group, Protected Root, venv
  lockdown, Cutover Record, or activation marker).

## 15. Tests

New test module
`tests/test_phase_149o_20k_hmic_class_b_verifier_source_scope_contract_evolution.py`
(40 tests, all passing) independently re-verifies: version/status
lines; HMIC-REQ-050's 28-entry enumeration matches the derived target
set exactly; HMIC-REQ-052's new limb (c) and union-derivation text;
attack matrix widened to 38 rows with row 38 present; §53's CBV-S1/
CBV-S10 restatement, no-HBDC-amendment, next-phase recommendation, W-1/
prior-finding non-reopening, and `pcae.core.paths` exclusion reasoning;
a **fresh, independent** re-derivation (not merely trusting the
contract's own prose) of zero production consumers, no import cycle
with `hatp_mandatory_certification.py`/`hatp_certification_admin.py`,
and bounded PCAE-owned imports across all three verifier modules via a
second, independently-written AST walk; HBDC-001 and the four other
pre-existing bound contracts byte-unchanged in the working tree; no
`src/pcae/**` or `scripts/**` file dirty; production still 25/5; no
real certification state anywhere in the repository.

### Test results

- New module: **40/40 passed.**
- Targeted HMIC/HBDC/Class-B/149O.20\* sweep (`pytest -k "hmic or hbdc
  or class_b or 149o_20"`): baseline (pre-phase, git-stashed) 47
  failed/1 error/1522 passed; post-phase 86 failed/10 errors/1514
  passed. Exact node-ID diff (`comm`): **zero previously-failing nodes
  fixed or newly passing; exactly 50 new failing/error nodes**, all
  traced to prior phases' own "contract byte-unchanged since phase
  entry" / "live enumeration currently equals N files" / "attack matrix
  currently has N rows" self-checks in
  `test_phase_149o_14_*`/`test_phase_149o_19_4_*`/
  `test_phase_149o_19_5b_*`/`test_phase_149o_19_5e_3_*`/
  `test_phase_149o_19_5e_4_*`/`test_phase_149o_1g_*`/
  `test_phase_149o_20a_*`/`test_phase_149o_20c_*`/
  `test_phase_149o_20d_*`/`test_phase_149o_20d_1_*`/
  `test_phase_149o_20e_*`/`test_phase_149o_20f_*`/
  `test_phase_149o_20g_*`/`test_phase_149o_20h_*` — the same structural
  breakage pattern every prior HMIC version bump (v1.0→v1.1, v1.1→v1.2)
  produced against its own predecessors' live-text/git-diff self-checks
  (confirmed: `test_phase_149o_1g_hatp_proof_models_canonical_
  serialization.py::test_hatp_contract_byte_unchanged` fails on a bare
  `git diff docs/contracts/` self-check with no file-name pin — fails
  for *any* contract edit whatsoever, by construction). None of these
  historical files are in this phase's allowed-file scope; none is a
  new defect in this phase's own content.
- Full Fast Green (`pytest -m fast_green -n auto`, `fido2` module
  ignored — pre-existing/unrelated): baseline (git-stashed) 71 failed/1
  error/6771 passed/5 skipped; post-phase 112 failed/10 errors/6761
  passed/5 skipped. Exact node-ID diff: zero fixed, exactly 50 new
  nodes — the identical set from the targeted sweep above (`comm -23`
  baseline-vs-after is empty; `comm -13` is the same 50-node set).
  **Clean-deselected citation** (argv-list `--deselect` per exact raw
  node ID, not shell string interpolation): deselecting the full
  122-node post-phase failing/error set yields **1 failed
  (`test_shell_gate.py::TestAuditPersistence::test_audit_verify_cli`,
  the same pytest-xdist `-n auto` ordering flake 149O.20J.8's own
  report already documented), 6760 passed, 5 skipped, 1 pre-existing
  collection error** — confirmed via isolated rerun of the entire
  `TestAuditPersistence` class passing cleanly 7/7, and a separate,
  independent `test_backend_cli.py::TestBackendReviewReject::
  test_reject_json_no_secrets` flake observed on one earlier deselected
  run, also confirmed passing cleanly in isolation. Both flakes are
  order/parallelism-dependent, reproduced independently across multiple
  runs with different single nodes flipping, and touch neither
  HMIC/Class-B/contract logic nor any file this phase modified.

## 16. Governance results

- `pcae check`: passed.
- `pcae health`: healthy.
- `pcae status coherence`: coherent.
- `pcae push check` / `pcae runtime inspect`: Observed / observe /
  unavailable (unchanged).
- `pcae notify status`: Telegram configured/enabled.

## 17. Status summary

- **CBV-S1:** OPEN — HMIC SOURCE-SCOPE CONTRACT EVOLVED — PRODUCTION
  ALIGNMENT + INDEPENDENT VERIFICATION PENDING — NOT CLOSED.
- **CBV-S10:** OPEN — READINESS CONTRACT/INTEGRATION GAP — unchanged,
  untouched.
- **Class-B:** CONTRACT VERIFIED — VERIFIER REPAIR LINE INDEPENDENTLY
  VERIFIED — HMIC SOURCE-SCOPE CONTRACT EVOLVED — PRODUCTION ALIGNMENT
  PENDING — NOT PROVISIONED.
- **HATP production:** NOT READY.
- **Runtime:** Observed / observe / unavailable.

## 18. Recommended next phase

**Phase 149O.20K.1 — HMIC Class-B Verifier Source-Scope Contract
Independent Verification.** Must independently reconstruct, without
trusting this phase's narrative: HMIC-REQ-052 (pre- and post-amendment
text); the current 25/5 production identity; the Class-B verifier
dependency graph (static and semantic); the authority-sensitive/
excluded classification; the target 28-file set; the v1.2 → v1.3
version-bump rationale; the cycle/self-binding analysis; the
W-1/B-149O.19.3-1/B-149O.20D-1 regression; and HBDC-001 identity
preservation. Does not authorize production alignment or readiness
integration. Only after it passes may a future, separately-governed
production-alignment phase (updating `_FROZEN_AUTHORITY_BEARING_FILES`
to the verified 28-file set) and its own independent verification
proceed — in that order.
