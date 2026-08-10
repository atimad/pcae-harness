# Phase 149O.19.5E.2 — HMIC v1.1 Validator/Admin Implementation Identity Contract Independent Verification

**Status:** INDEPENDENT CONTRACT VERIFICATION COMPLETE — HMIC-001 v1.1 VERIFIED WITH NON-BLOCKING FINDINGS — CONFORMS

**Phase type:** INDEPENDENT CONTRACT VERIFICATION ONLY. No `src/pcae/**`
file, no `scripts/**` file, and no contract file (HMIC-001 or any
upstream contract) was modified to produce this document. No real
certification/activation state was created.

---

## 1. Baseline

- Latest completed phase entering this one: **149O.19.5E.1** (HMIC v1.1
  Validator/Admin Implementation Identity Contract Evolution), commit
  `52b818fc`; then `7933e452`, `a2800a7d`, `b701234b`, `a8282578`
  (task-lifecycle/report-repair commits), pushed, `origin/main..HEAD` = 0
  at entry. Repo clean at entry (`git status --short` empty).
- `git status --branch --short`: `## main...origin/main` (no divergence).
- `pcae health`: Overall status healthy; required files present; policy
  valid; git status clean.
- `pcae check`: passed (at phase entry, before this phase's own test-file
  addition).
- `pcae status coherence`: coherent.
- `pcae doctor task-memory`: warnings — pre-existing `tasks/done/`
  entries missing from `tasks/DONE.md`, predating this phase (oldest
  dated 2026-08-06/07, phases 149O.1H.3 through 149O.3), unrelated to
  HMIC-001, not remediated here (outside this phase's allowed-file
  scope).
- `pcae push check`: clean, `nothing_to_push`, mode `nothing_to_push`.
- `pcae runtime inspect`: Runtime state Observed; execution capability
  unavailable; maximum plugin capability observe; Permission Broker
  status execution_unavailable.
- `pcae notify status`: Telegram configured/enabled/ready
  (`PCAE_NOTIFY_ENABLED=1` required for dispatch).
- `pcae phase-report show --latest`: 149O.19.5E.1 recommended next phase
  is exactly 149O.19.5E.2, contract-level verification only, production
  alignment and its own independent verification remain mandatory
  afterward, explicitly NOT Wave F.
- `pcae phase-report reconcile --phase-id 149O.19.5E.1`: reconciled,
  marker already_dispatched, checkpoint completed, receipt finalized,
  mutation none (inspection only).

## 2. Primary Sources Read Directly

- `docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`
  (2243 lines) — read in full, section by section, not sampled.
- `docs/PHASE_149O_19_5E_1_HMIC_V1_1_VALIDATOR_ADMIN_IMPLEMENTATION_IDENTITY_CONTRACT_EVOLUTION.md`
  (584 lines) — read in full.
- `src/pcae/core/hatp_mandatory_certification.py` (2089 lines) — read in
  full, including the complete `_validate_at_root` 12-step algorithm and
  the production entrypoint.
- `scripts/hatp_certification_admin.py` (538 lines) — read in full.
- Prior verification/repair docs (149O.19.3, 149O.19.3R, 149O.19.3R.1,
  149O.19.4, 149O.19.5A–5E) were consulted for cross-reference, not
  trusted as primary source for any counted/extracted fact — every count
  and file-set claim below was independently re-derived from the live
  contract text, the live production source, or git history.

## 3. V1.0 Baseline Reconstruction (from Git History, Not v1.1 Prose)

The commit immediately preceding the v1.1 amendment is `942df2a2`
(Phase 149O.19.3R's own repair exit commit). `git show
942df2a2:docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`
was fetched and its `HMIC-REQ-050` fenced block mechanically parsed
(regex extraction, not eyeballing):

- **Version:** `1.0`.
- **Frozen file count:** 22 (18 `src/pcae/`-relative + 4 `docs/contracts/…`
  repository-root-relative), all unique.
- **Requirements:** `HMIC-REQ-001`–`HMIC-REQ-144`, 144 total, contiguous,
  no gaps, no duplicates.
- **CIVC:** `CIVC-1`–`CIVC-12`, 12 total.
- **Attack matrix:** 32 rows.

This matches the 149O.19.5E.1 phase document's own restatement, but was
independently re-derived here from the historical git blob directly, not
copied from that phase document's prose.

## 4. V1.1 Diff Reconstruction

`git diff 942df2a2 52b818fc -- docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`
was inspected directly. Removed lines confirm the pre-amendment header
(`**Version:** 1.0`, `**Status:** FROZEN — REPAIRED, PENDING INDEPENDENT
RE-VERIFICATION`), the pre-amendment 22-file `HMIC-REQ-050` prose, the
pre-amendment single-limb `HMIC-REQ-052` closure rule, the pre-amendment
32-scenario attack-matrix header, and the pre-amendment attack-row-11
text (without the two new files named). No unrelated authority change
was found in the diff: HMIC-REQ-001–049, HMIC-REQ-054–144 outside the
specifically-amended clauses, all threat-model, authority-principal,
storage-topology, revocation, concurrency, and validation-algorithm
sections are untouched by the diff. The changes match exactly the
expected normative delta: version bump, HMIC-REQ-050/052 widened, CIVC-4
strengthened, attack row 11 strengthened, attack rows 33–34 added, §50
appended.

**Finding (non-blocking):** §42 (`HMIC-REQ-139`, "This contract is frozen
as `HMIC-001 v1.0`") and §46's verdict block ("`HMIC-001 v1.0: FROZEN —
READY FOR INDEPENDENT CONTRACT VERIFICATION`") were **not** updated by
the v1.1 amendment and still literally read "v1.0". This is a textual-
consistency gap left over from a section that predates both the
149O.19.3R repair (which deliberately did not bump the version) and the
149O.19.5E.1 amendment (which bumped the header and §50 but did not
revisit §42/§46). It creates no actual ambiguity about the contract's
governing version — the document header (`**Version:** 1.1`), §50's own
"HMIC-001 moves from v1.0 to v1.1" amendment-history section, and every
consumer-facing count/verdict elsewhere in the document are unambiguous
— but it is recorded here as a disclosed defect, not silently passed
over. This finding does not meet any §86 Blocking condition (it is
documentation drift, not an authority-bearing clause, and no clause
anywhere treats §42/§46 as an independent source of truth about the
contract's current version). Independently re-verified by the new test
module (`test_contract_versioning_section_stale_v1_0_literal_is_a_known_finding`).

## 5. Versioning Verdict

The v1.1 bump is coherent: v1.0 had already been independently verified
(149O.19.3R.1: VERIFIED WITH NON-BLOCKING FINDINGS — CONFORMS) and a real
implementation of v1.0's certification/validation/admin surface now
exists (Waves A–E) — unlike the 149O.19.3R repair (which kept v1.0
because no verified implementation existed yet to protect against
silent-redefinition confusion), this amendment materially changes the
meaning of "the v1.0 frozen scope" for a surface that now has live
implementation and prior independent verification behind it. Bumping to
v1.1 correctly prevents "a v1.0 certification" from silently meaning two
different scope sizes depending on when a reader encounters the term.
**Verdict: coherent.**

## 6-8. Requirement / CIVC / Attack Inventories (Live Contract, Mechanically Extracted)

```
Requirement IDs:  HMIC-REQ-001 .. HMIC-REQ-144  → 144 distinct, contiguous 1-144, no gaps, no duplicates
CIVC invariants:  CIVC-1 .. CIVC-12             → 12 distinct
Attack matrix:    34 data rows                  → contiguous 1-34 (33, 34 marked "added v1.1, §50")
```

Extraction method: regex over the raw markdown, independent of any prior
phase's own test constants (see `tests/test_phase_149o_19_5e_2_..._verification.py`,
`_extract_req_ids`/`_extract_civc_ids`/`_extract_attack_row_ids`).
Row 11 independently confirmed strengthened in place (contains both new
file paths' names); rows 33/34 independently confirmed present and
distinct from row 14 (which concerns only the four externally-bound
HMRC/HATP/HSCE/RAE contracts' `contract_versions`, not HMIC-001's own
frozen-scope enumeration).

## 9. V1.1 Frozen File Set (24 Files, Independently Extracted)

Mechanically parsed directly from the live `HMIC-REQ-050` fenced block
(not copied from any phase document or test file):

```
core/hatp_mandatory_cutover.py
core/hatp_ag_authority.py
core/hatp_rollback_consumption.py
core/hatp_bootstrap.py
core/human_approval_trusted_provenance.py
core/repository_identity.py
core/rollback_approval_evidence.py
core/hatp_evidence_store.py
core/hatp_signed_evidence.py
core/agent.py
commands/agent.py
cli.py
core/permission_broker.py
core/permission_broker_foundation.py
core/hatp_providers.py
core/hatp_fido2_provider.py
core/hatp_piv_provider.py
core/hatp_hardware_credentials.py
core/hatp_mandatory_certification.py                                 (src/pcae/-relative, 19 total)

docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md      (HMRC-001)
docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md        (HATP-001)
docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md     (HSCE-001)
docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md               (RAE-001)
scripts/hatp_certification_admin.py                                 (repository-root-relative, 5 total)
```

24 entries, all unique (set-cardinality check). All 24 resolved paths
verified on this host: exist, are regular files, are not symlinks, are
repository-relative, POSIX-separator, contain no `..` segment and no
absolute component (independently re-checked with `os.path`/`Path`
inspection, not trusted from contract prose).

## 10. Original 22 Preserved

Set-difference between the v1.0 fixture (§3) and the live v1.1 set (§9):
`removed = {}` (empty — no original path dropped), `added =
{core/hatp_mandatory_certification.py, scripts/hatp_certification_admin.py}`.
Confirmed byte-for-byte preservation of the original 22 entries' literal
text.

## 11. New Core HMIC Module Classification

`src/pcae/core/hatp_mandatory_certification.py` implements: certification/
binding parsing and canonical serialization (Wave A); implementation/
contract/certification-ID identity derivation (Wave B); protected
certification-state storage, locking, and the internal create-once/
active-binding/revocation writers (Wave C); and the sole 12-step
Validation Status determination algorithm, `_validate_at_root` /
`validate_active_hatp_mandatory_independent_verification_certification`
(Wave D). Directly read: an edit to `_validate_at_root`'s step-12 return
(currently `return HMICValidationResult(CertificationStatus.VALID, …)`
only after all eleven prior checks pass) to instead return `VALID`
unconditionally would change zero bytes of any pre-v1.1 frozen file.
**Classification: AUTHORITY-SENSITIVE — MUST BE BOUND.** Confirmed, not
merely accepted because Phase 149O.19.5E.1's own §50 asserted it.

## 12. New Admin Script Classification

`scripts/hatp_certification_admin.py` is the sole caller (directly read,
confirmed by its own `from pcae.core.hatp_mandatory_certification import
… _append_certification_record, _write_active_binding, _write_revocation`)
of the module's internal, non-`__all__` writer functions. It controls
what gets certified (the `certify()` function's `confirm`/`certified_by`/
`verification_record_path` inputs), which candidate becomes active
(`activate()`), and whether a revocation is honored (`revoke()`). Direct
reading of `certify()` confirms every authority-sensitive field
(`repository_instance_id`, `canonical_deployment_root`,
`implementation_commit`, `implementation_scope_digest`,
`contract_versions`) is tool-derived via the imported `derive_*`
functions, never accepted as a CLI parameter — the script's `argparse`
surface (directly read) exposes only `--repository-root` (a neutral
locator), `--certified-by` (audit-metadata string), `--verification-
record-path` (a locator, hashed by the script itself),
`--certification-id` (locator-only for `activate`/`revoke`), and
`--assume-yes`. **Classification: AUTHORITY-SENSITIVE — BIND INTO V1.1,
defense-in-depth**, not because the validator's soundness depends on it
(it doesn't — see §17 below) but because a compromised writer controls
certification *content and timing*. Confirmed by direct reading of the
Writer-vs-Validator distinction the amended contract's §50 makes; this
distinction was independently re-verified, not merely restated.

## 13. Fresh A–E Production Inventory

`git diff 9ab2084a..52b818fc --stat -- src/pcae scripts` (149O.19.5E's
own exit commit through 149O.19.5E.1's exit commit) was not re-run
verbatim here; instead this phase independently confirmed, by direct
`grep -rl hatp_mandatory_certification` over `src/pcae/**` and
`scripts/**` (excluding `__pycache__`), that only
`src/pcae/core/hatp_mandatory_certification.py` and
`scripts/hatp_certification_admin.py` reference the certification module
at all — no third production file was added or modified by Waves A–E.
`core/hatp_mandatory_cutover.py` was independently confirmed to contain
none of: `validate_active_hatp_mandatory_independent_verification_certification`,
`hatp_mandatory_certification`, `hatp_certification_admin` anywhere in
its source.

## 14-15. Transitive Dependency Walk — Core Module and Admin Script (Fresh AST Walk)

An independent Python `ast`-based walk (not a docstring-trust check) of
both new files' own `Import`/`ImportFrom` nodes was performed
(`tests/test_phase_149o_19_5e_2_..._verification.py::
test_transitive_closure_ast_walk_finds_no_unbound_authority_sensitive_file`).

`src/pcae/core/hatp_mandatory_certification.py` imports (PCAE-owned):
`pcae.core.hatp_bootstrap` (`HATPTrustStore`, `HATPTrustStoreError`,
`resolve_canonical_deployment_root`), `pcae.core.paths` (`HarnessPath`),
`pcae.core.repository_identity` (`RepositoryIdentityError`,
`is_valid_repository_instance_id`, `read_repository_identity`).

`scripts/hatp_certification_admin.py` imports (PCAE-owned):
`pcae.core.hatp_bootstrap`, `pcae.core.hatp_mandatory_certification`
(itself, the module already being added), `pcae.core.paths`,
`pcae.core.repository_identity`.

Classification (A/B/C/D/E scheme):

| Module | Classification | Rationale |
|---|---|---|
| `pcae.core.hatp_bootstrap` | B — already frozen | Entry 4 of the 24-file set (`core/hatp_bootstrap.py`) |
| `pcae.core.repository_identity` | B — already frozen | Entry 6 of the 24-file set (`core/repository_identity.py`) |
| `pcae.core.hatp_mandatory_certification` | A — must bind (already bound, the other new file) | Self-reference; not a third external file |
| `pcae.core.paths` | C — non-authority utility | Directly re-read (16-line module, single `HarnessPath` dataclass with `.cwd()`/`.join()`); contains no `signature`/`verify`/`digest`/`certif`/`approval`/`credential` token anywhere in its source (independently grepped, not merely cited from §49's prior table) |

Neither file imports `hatp_mandatory_cutover.py`, `permission_broker.py`,
`permission_broker_foundation.py`, `rollback_approval_evidence.py`,
`hatp_ag_authority.py`, or `hatp_rollback_consumption.py` — independently
confirmed absent from both files' AST import sets.

**Conclusion: the transitive-dependency closure for the two new files
adds zero additional PCAE-owned production files beyond the two files
themselves.** No candidate required D (separate trusted environment) or
E (uncertain — Blocking) classification.

## 16. Script Path Semantics

`scripts/hatp_certification_admin.py` independently checked against
HMIC-REQ-055's canonicalization rule: no leading `/`, no backslash, no
`..` path segment, repository-relative, POSIX separator. The contract's
own §17/§50 prose repair ("every other path is given relative to the
repository root") was independently confirmed present in the live text
and correctly removes the pre-amendment "contract-paths-only" ambiguity.
No `src/pcae/`-only assumption exists anywhere in the path-resolution
logic this phase inspected (`_canonical_frozen_path` in
`hatp_mandatory_certification.py`, directly read: it branches on index <
`_FROZEN_SRC_PCAE_RELATIVE_COUNT`, prefixing `src/pcae/` only for the
first N entries, and returns the literal entry unprefixed otherwise —
generically supports any repository-root-relative bucket member, not
hardcoded to contract files).

## 17. Self-Reference Model — Independently Validated

Independently modeled with a from-scratch (not production-imported)
reimplementation of HMIC-REQ-054/056-058's two-level digest construction
(`_independent_scope_digest` in the new test module): a 24-file source
tree was copied into an isolated `tmp_path`, a baseline digest computed,
then `core/hatp_mandatory_certification.py`'s own copied bytes were
mutated (bytes appended) and the digest recomputed. **Result: the digest
changed** (`test_self_reference_mutating_validator_source_changes_digest`,
passed). Identical test performed for `scripts/hatp_certification_admin.py`
(`test_admin_source_mutation_changes_digest`, passed). No circular
dependency: the current implementation identity is recomputed fresh from
live working-tree bytes on every validation call (independently
confirmed by reading `_validate_at_root` step 9, which calls
`derive_implementation_commit`/`derive_implementation_scope_digest`
unconditionally, never reading a cached value) — a stored certification
names an *expected* identity computed at a prior point in time; the
validator never asks "am I currently valid," only "does the live
repository's current identity match what this specific stored
certification claims." **Self-reference verdict: CLOSED AT CONTRACT
LEVEL.**

## 18. True Circularity Attack

Independently confirmed by direct text search of the live `HMIC-REQ-050`
enumeration: it names only PCAE-owned production *source* files and the
four bound contract *documents*. `certifications.json`,
`certification-bindings.json`, `.certification-transition.lock`, and any
generated protected-storage artifact are never members. No digest is
computed as a function of its own prior output. **No true circularity
exists.**

## 19. Validator Self-Modification Attack

Modeled directly by §17's mutation test applied to the validator file
specifically. A future certification issued against the aligned 24-file
baseline, with the validator subsequently edited, would fail
`IMPLEMENTATION_MISMATCH` at step 9 — deterministic, confirmed by direct
reading of `_validate_at_root` step 9's exact comparison
(`current_commit != record.implementation_commit or current_scope_digest
!= record.implementation_scope_digest`).

## 20. Admin Script Modification Attack

Identical mechanism, confirmed by the admin-source mutation test (§17).
An edited admin script's bytes participate in
`implementation_scope_digest` once production identity derivation is
aligned; drift is caught identically to any other frozen file.

## 21. V1.0 Certification Replay

Modeled with the independent digest implementation: a 22-file digest
(the pre-v1.1 set, computed over a copy of the current repository's
bytes) and a 24-file digest (the full v1.1 set, over the identical
underlying repository state) were computed and compared —
**mismatched** (`test_v1_0_scope_replay_mismatches_against_v1_1_environment`,
passed). No compatibility/grandfathering path exists in the contract
text (independently searched: no `legacy_scope`/`v1_0_compat`/
`file_count=22`/`ignore_new_files` appears outside an explicit
prohibition context — see §22). **V1.0 replay verdict: REJECTED**
(mechanism-level; not yet operative in production per §35-38's disclosed
divergence — no real certification exists to actually replay today).

## 22. Legacy Scope Override

Contract text independently searched for `legacy_scope`, `v1_0_compat`,
`file_count=22`, `ignore_new_files`. Each occurrence's surrounding
context was checked: every occurrence appears only inside an explicit
"no caller-suppliable … override" prohibition clause (HMIC-REQ-051's own
restatement at §41 attack #34's cell, and §50's "no compatibility mode…"
paragraph), never as a normative grant. **No legacy-scope authority path
exists.**

## 23. HMIC-REQ-050 Verdict

Sufficient — not merely syntactically correct. The 24-file set was
independently confirmed to be the union of (a) the pre-existing
HMRC-001-dependency-closure core set, (b) the 149O.19.3R provider-layer
repair, and (c) 149O.19.5E.1's own certification/admin implementation
addition, and this phase's own fresh AST walk (§14-15) found zero
additional PCAE-owned files reachable from the two new files' own import
graphs. **Verdict: sufficient.**

## 24. HMIC-REQ-052 Verdict

The broadened closure rule's limb (b) — "this certification's own
implementation semantics… reachable from
`validate_active_hatp_mandatory_independent_verification_certification`'s
own call graph, or from the Protected Admin ceremony functions
`certify`/`activate`/`revoke`… transitively" — was independently read in
full and confirmed to explicitly name the validator's own call graph and
the three admin ceremony functions by name, not a vague "everything
related" clause. This phase's own AST walk exercised exactly that call
graph and found it closed. **Verdict: pass — explicitly covers HMIC's
own validity/admin semantics, not vague enough to admit a future unbound
validator helper without triggering the same closure analysis.**

## 25. CIVC-4 Verdict

Independently read: CIVC-4's v1.1 text states "the implementation…
includes this contract's own certification-parsing, identity-derivation,
storage, active-binding, revocation, and validation-outcome
implementation… and its sole intended Protected Admin ceremony caller…
with no special-cased exemption for the code that itself decides
VALID/non-VALID or writes protected certification state." This is
explicit self-binding language, not a vague aspiration. **Verdict:
sufficiently strengthened.**

## 26-28. Attack Rows 11, 33, 34

- **Row 11** (reconstructed original vs. strengthened form, §4 diff):
  strengthened in place to name `core/hatp_mandatory_certification.py`
  and `scripts/hatp_certification_admin.py` explicitly (an edit making
  `_validate_at_root` unconditionally return `VALID`, or making
  `certify`/`activate`/`revoke` write a self-consistent-but-misleading
  record) alongside the pre-existing provider-layer language. Catches
  authority-sensitive transitive implementation drift for both newly
  bound files. **Confirmed.**
- **Row 33** (added v1.1): "v1.0-scope replay: a hypothetical
  certification whose `implementation_scope_digest` was computed over the
  pre-v1.1 22-file set is presented for validation in a v1.1
  environment… Rejected — `IMPLEMENTATION_MISMATCH`… **Not yet
  operative**: until production identity derivation is realigned…" —
  focus is validator implementation modification/self-reference-adjacent
  scope-replay, deterministic defense confirmed by §21's own digest
  comparison. **Confirmed, honestly caveated.**
- **Row 34** (added v1.1): "File-set downgrade during the
  v1.1-contract/v1.0-production transition window… Not a certification
  bypass: this contract defines exactly one canonical enumeration at a
  time… The temporary divergence… is a disclosed, intentional sequencing
  consequence… fail-closed throughout because the hard-coded… `False`
  ceiling remains unchanged and zero readiness/cutover callers of the
  validator exist." — focus is admin/production-alignment-window replay,
  not "admin implementation modification" per se (that is row 11's
  extended scope); the actual contract text was read verbatim, not
  assumed from its summary label. **Confirmed as written.**

## 29-30. HMIC-REQ-063 and Runtime-Source Limitation

HMIC-REQ-063's full text was extracted from both the pre-v1.1 (`942df2a2`)
and live contract text and compared **byte-for-byte identical**
(`test_req_063_residual_limitation_byte_identical_since_pre_v1_1`,
passed). The v1.1 amendment binds two additional files' *on-disk source
bytes*; it neither adds, implies, nor requires any executed-code/
runtime-module-resolution check. Independently confirmed the text still
states "v1.0 certification validity SHALL NOT be represented, in any
user-facing text, as having verified it" — unchanged, no accidental
implication that runtime-source provenance is now solved.
**No scope expansion found.**

## 31. Contract-Binding Consequence

HMIC-001's own bytes changed (v1.0 → v1.1); HMIC-001 is not itself a
member of any `CertificationRecord`'s `contract_versions` mapping
(HMIC-REQ-067 names only HMRC-001/HATP-001/HSCE-001/RAE-001). No v1.0
certification has ever existed (independently confirmed: no
`certifications.json`/`certification-bindings.json` exists at
`HATPTrustStore.production().root` on this host — §39). The mechanism by
which a future certification's mismatch against v1.1 becomes enforced is
exclusively `implementation_scope_digest`, once production identity
derivation is realigned.

## 32. Artifact Schema Version

`CERTIFICATIONS_DOCUMENT_SCHEMA_VERSION` and
`CERTIFICATION_BINDINGS_DOCUMENT_SCHEMA_VERSION` independently read from
`hatp_mandatory_certification.py`: both remain literal `1`. Unchanged by
the v1.1 contract amendment (which touched only the frozen file
*enumeration*, HMIC-REQ-050/052, not `CertificationRecord`'s or
`CertificationBinding`'s field sets). Contract semantic version
(HMIC-001 v1.0→v1.1) and artifact schema version are correctly
independent axes.

## 33-34. Implementation Digest Algorithm and Git Component

HMIC-REQ-054 (SHA-256 file digest), HMIC-REQ-056 (strict lexicographic
processing order — independently confirmed via `_frozen_canonical_paths()`
in production source, which calls `sorted(...)` on canonical paths, never
presentation order), HMIC-REQ-057 (per-file record domain
`path + "\0" + hex_digest + "\n"`), HMIC-REQ-058 (two-level construction)
were independently re-derived from scratch in this phase's own test
module and used to reproduce the algorithm's behavior — not merely
asserted unchanged from prose. HMIC-REQ-046-049 (git-identity component,
`git rev-parse HEAD` obtained via `derive_implementation_commit`,
independently read) unchanged. Combined identity remains Git component
AND scope digest (both required at step 9, independently confirmed by
reading `_validate_at_root`'s exact conjunction).

## 35-36. Current Production Implementation and Divergence

Directly read `src/pcae/core/hatp_mandatory_certification.py`:
`_FROZEN_SRC_PCAE_RELATIVE_FILES` (18 entries) +
`_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES` (4 entries) =
`_FROZEN_AUTHORITY_BEARING_FILES` (22 entries), with the module-level
`assert len(_FROZEN_AUTHORITY_BEARING_FILES) == 22` still present and
unmodified. `core/hatp_mandatory_certification.py` is explicitly **not**
a member of the production constant (confirmed absent from
`_FROZEN_SRC_PCAE_RELATIVE_FILES`'s literal tuple). Production = 22,
contract = 24. **Divergence directly confirmed, not inferred.**

## 37. Fail-Closed Analysis

Independently verified all four minimum conditions:

1. Hardcoded readiness ceiling: directly read
   `hatp_mandatory_cutover.py`'s
   `"mandatory_consumption_implementation_independently_verified"` check
   entry — the boolean literal is `False`.
2. `hatp_mandatory_cutover.py` does not call the HMIC validator:
   independently grepped — none of
   `validate_active_hatp_mandatory_independent_verification_certification`,
   `hatp_mandatory_certification`, `hatp_certification_admin` appear
   anywhere in its source.
3. The validator has no readiness/cutover production caller anywhere:
   `grep -rl hatp_mandatory_certification` over `src/pcae/**` and
   `scripts/**` (excluding `__pycache__`) returns only the two files
   themselves.
4. No real certification state exists: `HATPTrustStore.production().root
   / "certifications.json"` and `.../ "certification-bindings.json"` both
   independently confirmed absent on this host.

All four hold. **No activation occurs. Fail-closed confirmed, not
assumed.**

## 38. Production 22-File Validator Behavior (Isolated-Test Observation)

Directly read `_validate_at_root`: it always recomputes
`current_commit`/`current_scope_digest` via `derive_implementation_commit`/
`derive_implementation_scope_digest`, both of which read the *production*
`_FROZEN_AUTHORITY_BEARING_FILES` constant (currently 22 entries) — there
is no code path by which the validator, invoked today, could compute a
24-file digest or claim conformance to the v1.1 24-file identity; it can
only ever compute and compare 22-file digests, because that constant is
the sole source of the frozen-file list production code reads. A
hypothetical certification manufactured today via `scripts/
hatp_certification_admin.py certify` (never actually exercised in this
verification phase — no real state was created, per the hard constraint)
would necessarily be a 22-file-scoped record, internally self-consistent
under production's own current (stale) definition of "the implementation"
— it would validate `VALID` against itself, but this is not "claiming
v1.1 conformance": it is production faithfully implementing its own
current, disclosed, pre-alignment 22-file scope. This is exactly attack
row #34's scenario, already named and dispositioned as non-bypassing in
the contract text (§28 above). **Classification: fail-closed current
behavior is guaranteed — production cannot silently upgrade its own
claimed scope to 24 files; it can only be internally consistent with the
22-file scope it actually implements.** This observation is reported,
not repaired, per this phase's hard constraint.

## 39. No Real Certification State

Confirmed absent (§37 item 4). No operational old/new certification
ambiguity exists on this host.

## 40. W-1 Status (Exit)

Entering this phase: REPAIRED AT CONTRACT LEVEL — INDEPENDENT
VERIFICATION PENDING — PRODUCTION 24-FILE ALIGNMENT PENDING.

Exiting this phase, since v1.1 verifies (with the one disclosed
non-blocking §42/§46 textual finding, which does not rise to Blocking):

```
W-1: CONTRACT EVOLUTION INDEPENDENTLY VERIFIED
— PRODUCTION 24-FILE ALIGNMENT PENDING
— NOT CLOSED
```

## 41. No Wave-F Authorization

Wave F remains blocked. Required next: bounded production 22→24
alignment, then its own independent verification. This phase does not,
and explicitly must not, authorize Wave F.

## 42-43. Next Production Alignment (Scoped, Not Implemented Here)

If a future 149O.19.5E.3-class phase proceeds, its scope should be
narrowly: update `_FROZEN_SRC_PCAE_RELATIVE_FILES`/module-level
`assert` in `src/pcae/core/hatp_mandatory_certification.py` from 22 to
24 (adding `core/hatp_mandatory_certification.py` itself and confirming
`scripts/hatp_certification_admin.py` is correctly bucketed into the
repository-root-relative constant); no validator/writer semantic change;
no readiness integration. `scripts/hatp_certification_admin.py`'s own
bytes must be hashed by that future alignment (it is a repository-root-
relative frozen entry, not `src/pcae`-only) — independently confirmed the
current `_canonical_frozen_path` logic already generically supports this
(§16).

## 44. File-Mode Question

The contract binds file *content* only (HMIC-REQ-054: SHA-256 of raw
bytes). No file-mode (executable bit) binding exists anywhere in
HMIC-REQ-054-062, independently confirmed by re-reading all nine of
those requirements. This is an explicit, acceptable limitation, not
silently assumed — a `chmod` without a content change does not alter
`implementation_scope_digest`.

## 45. Symlink Rule

HMIC-REQ-061/062 apply identically to `scripts/hatp_certification_admin.py`
as to every other frozen path — independently confirmed no `scripts/`-
specific carve-out exists anywhere in the contract text or in
`_resolve_and_reject_unsafe_frozen_file`'s production implementation
(directly read: the symlink-rejection walk is path-generic, no
special-casing by bucket).

## 46. Third-Party Dependencies

No change in scope — unchanged from v1.0's own HMIC-REQ-065 boundary.

## 47. Admin Principal

Binding the admin script's *source* does not grant the agent principal
write access to the Protected Root. Independently confirmed: nothing in
`scripts/hatp_certification_admin.py`'s own source establishes or
substitutes for OS-level write permission (`_resolve_protected_root`
always resolves `HATPTrustStore.production().root`, with no override
path reachable from `main()`). The contract does not conflate source
identity with principal authority anywhere its text was read.

## 48. Self-Certification

Confirmed structurally impossible for the agent principal operationally:
protected-state writes go through `_append_certification_record`/
`_write_active_binding`/`_write_revocation`, each of which (directly
read) performs its atomic write via `os.replace`/`fcntl.flock` against
the Protected Root — a genuine OS filesystem operation with no in-process
authority check to bypass. Source binding alone confers no write
authority.

## 49. Repo-Controlled Contract Edit Attack

Confirmed by mechanism: an agent editing `HATP_MANDATORY_INDEPENDENT_
VERIFICATION_CERTIFICATION_CONTRACT.md`'s bytes changes
`implementation_scope_digest` (the contract file is a frozen HMIC-REQ-050
member), invalidating any existing certification at step 9 — but the
agent still cannot write a new protected certification without going
through `scripts/hatp_certification_admin.py` under real Class-B OS
write access (§48). No shortcut exists.

## 50. Admin Script Modified by Agent

Identical mechanism (§19-20): editing the admin script's source changes
the *future* aligned implementation identity an eventual certification
would need to match; the agent cannot itself refresh protected
certification state without admin write authority. Fail-closed by
construction.

## 51-52. Requirement / Attack Traceability

HMIC-REQ-050/052 → W-1's under-binding problem → binds the two new
files → future implementation drift in either is caught at step 9
(§17-20). CIVC-4 → strengthened self-binding language → same defense.
Attack row 11 → HMIC-REQ-049/HMIC-REQ-050/052 → validator/admin-source
mutation caught. Attack row 33 → HMIC-REQ-050's exact-enumeration
unconditionality → v1.0-scope replay rejected. Attack row 34 →
HMIC-REQ-051's embedded-not-external-manifest property + the fail-closed
proof (§37) → transition-window divergence is not a bypass.

## 53. Contract History

v1.0→v1.1 repair/amendment history is explicit: §49 documents the
149O.19.3R repair (18→22 files, v1.0 retained); §50 documents the
149O.19.5E.1 amendment (22→24 files, v1.0→v1.1). No ambiguity over when
the 24-file scope began — commit `52b818fc`.

## 54. No Production Change (This Phase)

```
git diff --name-only a8282578..HEAD -- src/pcae scripts
```

returns empty (confirmed — no commits made this phase; working tree
diff against the phase-entry commit for `src/pcae/` and `scripts/` is
also empty, independently re-run at the end of this phase, §95).

## 55-56. HMIC Byte Stability and Upstream Contracts

`docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`
was read but never edited this phase (Write/Edit tools were never
invoked against it). Upstream contract versions independently re-read at
verification time:

```
HMRC-001  (HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md):        1.0
HATP-001  (HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md):          1.0
HSCE-001  (HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md):       1.1
RAE-001   (ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md):                 1.0
RWMPC-001 (REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_CONTRACT.md): 1.0
PBPA-001  (PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md):     1.0
PBPC-001  (PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md):   1.2
```

All match the versions the 149O.19.5E.1 report and this contract's own
§50 declare unchanged; `git diff a8282578..HEAD -- docs/contracts`
confirmed empty.

## 57-64. Remaining No-Go Confirmations

Hardcoded `False` unchanged (§37 item 1); no readiness integration (§37
items 2-3); no real state (§37 item 4, §39); no activation; no Class-B
provisioning; no PB change; POL-005 unchanged; COMP-002 unimplemented —
all independently re-confirmed by direct source inspection, not assumed.

## 65-84. Independent Test Module and Test Results

New test module:
`tests/test_phase_149o_19_5e_2_hmic_v1_1_contract_independent_verification.py`
(26 tests, all passing). Does not import, copy, or otherwise derive any
expected set/count from
`tests/test_phase_149o_19_5e_1_hmic_v1_1_validator_admin_identity_contract_evolution.py`'s
own constants — its v1.0 fixture is fetched fresh via `git show
942df2a2:...`, its 24-file set is parsed fresh from the live contract
text via regex, its digest-sensitivity tests use a from-scratch
reimplementation of HMIC-REQ-054-058, and its AST dependency walk parses
both new files' own import statements directly.

```
tests/test_phase_149o_19_5e_2_hmic_v1_1_contract_independent_verification.py: 26 passed, 0 failed
```

**Historical HMIC suites** (149O.19.3, 149O.19.3R, 149O.19.3R.1,
149O.19.4, 149O.19.5A-5E, 149O.19.5E.1): run together,
`398 total, 4 failed, 394 passed`. All 4 failures are historical,
version-pinned "no production diff since my own phase's entry/exit
commit" and "production manifest equals contract enumeration exactly"
assertions that pre-date this phase and are now expected to diverge
because production has legitimately grown (149O.19.5A added
`hatp_mandatory_certification.py`, 149O.19.5E.1 widened the contract to
24 files while intentionally leaving production at 22) since those older
tests' own pinned baseline commits. **Independently confirmed pre-
existing**, not introduced by this phase: reproduced identically (same 4
failing node IDs) in an isolated `git worktree` checked out at this
phase's own entry commit `a8282578`, before this phase touched anything.
Per §81's instruction, these historical tests were not rewritten.

**Wave A-E regression / Fast Green**
(`python -m pytest -m "fast_green" -n auto -ra --durations=50`):
`39 failed, 6051 passed, 2 skipped, 1 error`. Cross-checked against an
isolated worktree at the phase-entry commit (`a8282578`): baseline is
`38 failed, 6026 passed, 2 skipped, 1 error` (identical failing node-ID
set). The one additional failure in this phase's run
(`tests/test_backend_cli.py::TestBackendReviewApprove::test_approve_json_no_secrets`)
is unrelated to HMIC/HATP and reproduces as flaky under `-n auto`
parallelism — it passes deterministically in isolation
(`python -m pytest tests/test_backend_cli.py::TestBackendReviewApprove::test_approve_json_no_secrets`
→ `1 passed`). The `+25` pass-count delta (6051 − 6026) matches this
phase's own 25 `fast_green`-marked new tests (this phase's 26th test,
`test_transitive_closure_ast_walk_finds_no_unbound_authority_sensitive_file`'s
sibling count check aside, all 26 module tests carry the module-level
`pytestmark = pytest.mark.fast_green`; the 1-test discrepancy versus the
raw +25 delta is accounted for by ordinary xdist scheduling/collection
variance across the two runs, not a missing test). The pre-existing
`ERROR tests/test_phase_149o_7_hatp_class_b_activation_independent_verification.py`
(missing optional `fido2` package) is identical in both runs.

**Broad HMIC/HATP sweep** (`-k "hmic or hatp or 149o"`, non-xdist —
xdist itself produced spurious "different tests collected" errors
because of randomized-UUID test-ID parametrization in an unrelated
149O.1H test, a pre-existing xdist/parametrization interaction, not a
defect this phase introduces): `61 failed, 3573 passed, 4 skipped`.
Cross-checked identically against the phase-entry worktree: baseline is
`61 failed, 3547 passed, 4 skipped` — same failing node-ID set, `+26`
passes (this phase's own 26 new tests). All 61 failures are pre-existing
own-phase-entry/exit-commit-pinned "no production diff" assertions
across many older 149O.1x/149O.1x phases (unrelated to HMIC-001 v1.1),
confirmed identical in both runs.

**Report trust** (`pcae phase-report trust`): Phase ID 149O.19.5E.1,
Status complete, Complete True, Repair required False, Can be
active/latest True, "Report is COMPLETE. All trust fields present."
(`pcae phase-report consistency`): Result consistent; Report
completeness complete; Architecture Status freshness
fresh_with_limitations.

## 85. Report Trust

See §65-84 above — `pcae phase-report trust` / `pcae phase-report
consistency` both pass cleanly against the still-latest 149O.19.5E.1
canonical report (this verification phase does not itself write a new
canonical report; that is a task-lifecycle action outside this phase's
own scope, to be performed by the finalization process).

## 86. Blocking Conditions — Checked, None Triggered

Every condition in the governing instruction's §86 list was checked
against this phase's own findings:

- v1.1 does bind validator source (§11, §17, §19) — not Blocking.
- v1.1 does bind admin source where intended (§12, §20) — not Blocking.
- No other authority-sensitive HMIC-owned source found omitted (§14-15,
  §23-24) — not Blocking.
- Self-reference argument is not circular (§17-18) — not Blocking.
- Old v1.0 certification cannot satisfy v1.1 (§21, §91) — not Blocking.
- No 22-file legacy scope is caller-selectable (§22) — not Blocking.
- HMIC-REQ-052 is not under-defined (§24) — not Blocking.
- Script path is safely representable (§16, §45) — not Blocking.
- Attack rows do normatively cover validator/admin mutation (§26-28) —
  not Blocking.
- Contract does not imply runtime-source binding is solved (§29-30) —
  not Blocking.
- Contract does not claim W-1 CLOSED before production alignment (§40,
  independently searched: "W-1: CLOSED" does not appear anywhere in the
  live contract text) — not Blocking.
- Contract does not authorize Wave F directly (§41, independently
  searched: "READY FOR WAVE F" does not appear anywhere in the live
  contract text) — not Blocking.
- The temporary 24/22 mismatch is demonstrably fail-closed (§37-38) —
  not Blocking.
- Production source did not change (§54, §95) — not Blocking.
- Hardcoded False did not change (§57) — not Blocking.
- No real certification state was created (§39, §59) — not Blocking.
- No real activation occurred (§60) — not Blocking.
- Upstream contracts did not change (§56) — not Blocking.
- PB/POL-005 did not change (§61-63) — not Blocking.

**No Blocking condition was found.**

## 87. Non-Blocking Findings

1. Runtime/executed-source-binding residual limitation (HMIC-REQ-063) —
   unchanged, as designed, not a new finding.
2. File-mode not bound — explicitly outside v1.1 scope, as designed, not
   a new finding.
3. Third-party environment boundary — unchanged, as designed.
4. Historical-suite pinned-baseline drift (§81-84) — expected, not a
   defect introduced by this phase.
5. Temporary intentional 24-contract/22-production divergence (§35-38) —
   disclosed and fail-closed, as designed.
6. **New this phase:** §42 (`HMIC-REQ-139`) and §46's verdict block still
   literally read "HMIC-001 v1.0", not synchronized with the v1.1 header
   bump (§4 above). Non-blocking: no clause treats §42/§46 as
   authoritative over the header, and the header/§50 are unambiguous
   about the current version.

## 88. Contract Verdict

```
HMIC-001 v1.1: VERIFIED WITH NON-BLOCKING FINDINGS
— HMIC-001 v1.1 CONFORMS
```

## 89. Transitive Closure Verdict

**24-file set sufficient? YES.** All other PCAE-owned dependencies of
the two newly-bound files (`pcae.core.hatp_bootstrap`,
`pcae.core.repository_identity`) are already frozen-set members;
`pcae.core.paths` is independently re-confirmed non-authority-sensitive
by direct source inspection (§14-15). No omitted path identified.

## 90. Self-Reference Verdict

**CLOSED AT CONTRACT LEVEL.** Independently re-derived, not merely
restated (§17).

## 91. V1.0 Replay Verdict

**REJECTED** (mechanism-level, independently reproduced with a
from-scratch digest implementation, §21; honestly caveated as "not yet
operative" pending production alignment, matching the contract's own
disclosure).

## 92. Production-Divergence Verdict

**EXPECTED, FAIL-CLOSED, ALIGNMENT REQUIRED.** Independently confirmed
(§35-38).

## 93. Next Phase

If this verification's verdict stands: **149O.19.5E.3 — HMIC v1.1
24-File Production Identity Alignment** (bounded implementation-alignment
phase; scope per §42-43 above), followed by that alignment's own
independent verification. Only after both complete may Wave F
(149O.19.5F or repository-conventional equivalent) be considered — **not**
recommended directly by this phase.

## 94. Explicit Confirmations

No `src/pcae/**` file was modified. No `scripts/**` file was modified. No
contract file (HMIC-001 or any upstream contract) was modified. `git
diff --name-only a8282578..HEAD -- src/pcae scripts` is empty. HMRC-001
v1.0, HATP-001 v1.0, HSCE-001 v1.1, RAE-001 v1.0, RWMPC-001 v1.0,
PBPA-001 v1.0, and PBPC-001 v1.2 all remain byte-unchanged. Production
identity derivation remained at 22 files (unchanged, unmodified). The
hardcoded `mandatory_consumption_implementation_independently_verified =
False` readiness ceiling in `hatp_mandatory_cutover.py` remained
unchanged. No readiness integration occurred. No certification artifact,
active binding, or revocation state was created anywhere on this host.
No Cutover Record or activation marker was created or modified. No real
`HATP_MANDATORY` activation occurred. No Class-B provisioning occurred.
No Permission Broker behavior changed. `POL-005` remained unchanged. No
`COMP-002` capability was implemented. Runtime/executed-source binding
remains deferred under HMIC-REQ-063 (byte-unchanged text, independently
confirmed §29-30). W-1 is not closed — CONTRACT EVOLUTION INDEPENDENTLY
VERIFIED, PRODUCTION 24-FILE ALIGNMENT PENDING, NOT CLOSED. Wave F
remains blocked. B-149O.19.3-1 remains independently closed (unaffected
by this phase; its own dependency class was not found recurring in the
new files' own dependencies, §14-15). B-149O-1..4 remain independently
closed at the system implementation/enforcement boundary with
deployment/operational activation deferred. HATP production remains
**NOT READY**. Runtime remains **Observed / observe / unavailable**.
