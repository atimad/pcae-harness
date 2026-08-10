# Phase 149O.19.5E — HMIC Protected Admin Certification / Revocation Surface (Wave E)

**Status:** IMPLEMENTED — WAVE A–E IMPLEMENTATION COMPLETE — W-1 CONTRACT-EVOLUTION GATE NOW MANDATORY (not "READY FOR WAVE F")

## 1. Baseline

- Latest completed phase entering this one: **149O.19.5D** (HMIC Active
  Certification Validation Engine), commits `d9da04c0`, `d0397fa9`,
  `cf546fe2`, pushed, `origin/main..HEAD` = 0 at entry.
- Waves A–D (Phases 149O.19.5A–D) implemented, in
  `src/pcae/core/hatp_mandatory_certification.py`: immutable data models
  and strict parsing (A); identity derivation — repository, deployment,
  git commit, 22-file implementation-scope digest, contract versions,
  certification-ID derivation (B); protected certification state store —
  `.certification-transition.lock`, readers, and the internal
  `_append_certification_record`/`_write_active_binding`/
  `_write_revocation` writer primitives (C); the read-only 12-step active-
  certification validation engine, zero production callers (D).
- Wave D deliberately did not implement: the protected admin
  certification/revocation ceremony, readiness integration, the
  hardcoded-`False` replacement, or activation. This phase (Wave E)
  implements exactly the first of those.
- HMIC-001 v1.0: VERIFIED WITH NON-BLOCKING FINDINGS — CONFORMS (144
  requirements, 12 CIVC invariants, 32 attack scenarios, 22-file frozen
  implementation subject). B-149O.19.3-1: INDEPENDENTLY CONFIRMED CLOSED.

## 2. Wave-E Requirement / CIVC / Attack Subset

Extracted from `docs/PHASE_149O_19_4_HATP_MANDATORY_INDEPENDENT_
VERIFICATION_CERTIFICATION_IMPLEMENTATION_PLAN.md` §6/§7/§8/§15, which
assigns Wave E exactly: HMIC-REQ-012-013, 016-020, 039, 045, 076-082,
086-088, 091-093, 118-119, 126-127, 144 (admin portion); CIVC-2, CIVC-12
(admin portion); attacks 5, 6, 27.

| HMIC requirement | Admin operation | Production owner | Test | CIVC | Attack |
|---|---|---|---|---|---|
| 012, 017, 018, 020 | No fake-admin path of any kind | `scripts/hatp_certification_admin.py` — no in-process authority check; real boundary is OS write permission on the Protected Root | `TestNoAgentReachableWriteSurface` | CIVC-2, CIVC-12 | 5, 6, 27 |
| 013, 016 | Sole authority is Protected Admin (reused 149O.1B.1 principal) | (structural; no new principal code) | `TestNoAgentReachableWriteSurface` | CIVC-2 | 27 |
| 019 | Read access ≠ write authority | `load_certification`/`load_active_binding` (Wave C, unchanged) | (Wave C/D suites, unchanged) | — | — |
| 039, 045 | `certification_id`/identity never caller-supplied on create | `certify()` — no such parameter exists | `TestCreate::test_certification_id_is_tool_derived_not_caller_suppliable` | — | — |
| 076–078 | Creation ceremony, minimized input | `certify()` | `TestCreate` (all) | CIVC-2 | — |
| 079–082 | Writer is a separate, non-agent-reachable tool; no agent-reachable write API | `scripts/hatp_certification_admin.py` itself (structural: outside `src/pcae/`); `TestNoAgentReachableWriteSurface` | `TestNoAgentReachableWriteSurface` (all) | CIVC-2, CIVC-12 | 27 |
| 086, 088 | Create ≠ activate; activation is a second explicit write | `certify()` never binds; `activate()` is the only binder | `TestActivate::test_activate_binds_existing_certification`, `TestCreate::test_create_does_not_activate` | — | — |
| 087 | Recertification creates a new record, old one untouched | (Wave C `_append_certification_record`, unchanged; exercised via `certify()`) | `TestConcurrency`, `TestMultiRepositoryIsolation` | — | — |
| 091–093 | Revocation: field mutation, explicit ID only, protected-admin-only | `revoke()` | `TestRevoke` (all) | — | — |
| 118–119 | `CERTIFY`/`ACTIVATE` (HMRC) remain independent; certify-without-activate is permitted | `certify()`/`activate()` are separate functions, never chained | `TestCreate::test_create_does_not_activate` | — | — |
| 126–127 | No bootstrap circularity; no AG3/AG5 dependency | `scripts/hatp_certification_admin.py` imports no cutover/AG module | `TestNoCoupling::test_admin_script_does_not_import_forbidden_modules` | — | — |
| 144 (admin portion) | No self-certification path | `TestNoAgentReachableWriteSurface` (all) | `TestNoAgentReachableWriteSurface` | CIVC-12 | 5, 6, 27 |

No Wave-F (readiness-integration) requirement is claimed by this table.

## 3. Production Module Ownership

Per the 149O.19.4 plan §9.2's already-made decision (a single core module
plus one separate admin script — **not** revisited or redesigned by this
phase): `scripts/hatp_certification_admin.py` is a **new, standalone
script outside `src/pcae/`**. `src/pcae/core/hatp_mandatory_
certification.py` is **not modified by this phase** — every Wave A–D
primitive the ceremony needs (`derive_repository_instance_id`,
`derive_canonical_deployment_root`, `derive_implementation_commit`,
`derive_implementation_scope_digest`, `derive_contract_versions`,
`derive_certification_id`, `_append_certification_record`,
`_write_active_binding`, `_write_revocation`, `load_certification`)
already existed unchanged from Wave A–C; this phase adds zero new
functions to that module and imports it read-only.

## 4. Admin Surface Trust Model

The security boundary is **Class-B protected filesystem permissions on
`HATPTrustStore.production().root`**, exactly as HMIC-REQ-079/013
require, reusing the 149O.1B.1 principal — **not** any of: a leading
underscore, a username string, an environment variable, a CLI `--admin`
flag, repository ownership, or Git author identity. This script performs
no application-level admin-authority check of any kind; if the invoking
OS principal lacks real write access to the Protected Root, every write
below fails with an ordinary `OSError`/`PermissionError` surfaced from
Wave C's `os.replace`/`fcntl.flock` — this script neither launders nor
catches that into a misleading message.

## 5. Production / Admin Surface, Writer Principal, Protected Root

- Production/admin surface: `scripts/hatp_certification_admin.py`,
  invoked manually (`python scripts/hatp_certification_admin.py
  create|activate|revoke ...`) by an operator under the Class-B
  Protected Administrator OS principal.
- Writer principal: the Class-B admin principal. Agent principal: read-
  only at most (HMIC-REQ-019) — no code path in `src/pcae/**` reaches any
  writer function; verified structurally (§8 below).
- Protected root: always `HATPTrustStore.production().root`, resolved
  internally by every ceremony function; **no** `--root`/`--store-root`
  CLI flag and **no** `PCAE_HMIC_ROOT`-equivalent environment variable
  exist. A private `_protected_root` keyword argument exists purely as a
  test seam (mirroring `HATPTrustStore.__init__`'s own `_test_only_root`
  pattern) — structurally outside the CLI argument surface, never
  populated by `main()`.

## 6. Allowed / Forbidden Admin Inputs

Allowed (per HMIC-REQ-077-078): `--repository-root` (a neutral working-
tree *locator*, identical in kind to `validate_active_hatp_mandatory_
independent_verification_certification(repository_root: Path)`'s own
parameter — never an identity value); `--certified-by` (free-text
operator identity, audit metadata only); `--verification-record-path`
(create only — a file *locator* the tool reads and hashes itself, never
a pre-computed digest string); `--certification-id` (activate/revoke
only — an explicit *locator* naming an already-existing object, never
authority: "locator ≠ authority").

Forbidden — no such parameter exists anywhere in `certify()`,
`activate()`, or `revoke()`: `repository_instance_id`,
`canonical_deployment_root`, `implementation_commit`,
`implementation_scope_digest`, `contract_versions`, `certification_id`
(as a *creation* input), any `verified`/`valid`-shaped boolean, a
revocation "reason" (HMIC-REQ-032's schema defines none), or a
`--root`/environment-variable protected-root override. Verified by
`inspect.signature` in `TestCreate::test_certification_id_is_tool_
derived_not_caller_suppliable`, `TestActivate::test_no_implicit_latest_
selection`, `TestRevoke::test_revoke_reason_field_not_accepted`.

## 7. Certification Creation Ceremony

Implements HMIC-REQ-076 steps 1–6 exactly (`certify()`): resolves the
Protected Root and derives, read-only, `repository_instance_id`,
`canonical_deployment_root`, `implementation_commit`,
`implementation_scope_digest`, `contract_versions`, and wall-clock
`certified_at` (via a private, duplicated — not imported, mirroring
`hatp_bootstrap.py::_parse_iso_timestamp`'s own documented duplication
rationale — canonical-timestamp helper); hashes the human-supplied
verification-record file; requires explicit confirmation (HMIC-REQ-076
step 5, `ConfirmationDeclinedError` if declined, no write occurs);
derives `certification_id` via Wave B's `derive_certification_id`
unmodified; and appends the record via Wave C's
`_append_certification_record` unmodified (atomic, create-once, under
the certification-transition lock). Step 7 (activation) is **not**
performed by `certify()` — it is `activate()`'s own, separate, explicit
operation (§8).

## 8. Active Supersession (`activate()`)

Explicit `--certification-id` only — no "latest"/"newest"/implicit
selection exists (verified structurally: no such parameter name in
`inspect.signature(admin.activate)`). Requires the named record to
already exist and parse (a structural precondition, checked via Wave C's
own reader) but never requires it to be currently HMIC `VALID` —
verified by asserting `activate()`'s own source never references
`_validate_at_root`/`validate_active_hatp_mandatory_...`. Reuses Wave
C's `_write_active_binding` unmodified (locked, plain replacement, no
compare-and-swap — matching HMIC-REQ-099's own "whichever completes
second wins" semantics).

## 9. Revocation (`revoke()`)

Explicit `--certification-id` only. Field-mutates via Wave C's
`_write_revocation` unmodified (`status: "revoked"`, `revoked_at:
<timestamp>` — never a deletion). Monotonic: re-revoking at an identical
timestamp is idempotent; re-revoking at a different timestamp raises
`CertificationConflictError` (Wave C's own first-recorded-wins rule,
unchanged). Never reads, clears, or switches `certification-
bindings.json` — confirmed by `TestRevoke::test_revoke_does_not_clear_
active_binding`, which shows a revoked-while-still-bound certification
correctly yields `CertificationStatus.REVOKED` from Wave D's unmodified
validator, not a writer-side special case.

## 10. Locking, Linearization, Concurrency

No second lock file, no second persistence layer: every write in this
phase goes through Wave C's single `.certification-transition.lock`
(`_certification_transition_lock`), reused unmodified. Linearization
points: creation is durable the instant `_append_certification_record`'s
`os.replace` returns inside the lock; supersession, the instant
`_write_active_binding`'s `os.replace` returns; revocation, the instant
`_write_revocation`'s `os.replace` returns. `TestConcurrency` exercises
both a 4-thread identical-content creation race (asserts exactly one
non-idempotent writer, all four callers agree on one `certification_id`,
zero errors) and a 2-thread supersession race between two distinct valid
certifications (asserts the final binding deterministically names
exactly one of the two, never a torn/ambiguous state). No new lock-
ordering hazard is introduced: this phase never acquires the Cutover
Record's own `.cutover-transition.lock`, and no ceremony function here
is ever called from inside `activate_hatp_mandatory` (that function is
never imported).

## 11. Self-Certification / Agent-Reachability Attacks

`TestNoAgentReachableWriteSurface` and `TestNoCoupling` (AST-based, not
substring-based, to avoid false positives against this module's own
prose) confirm: the ordinary `pcae` CLI (`src/pcae/cli.py`) contains no
`certify`/`revoke-certification` token and does not import the admin
script or any Wave C writer function by name; `src/pcae/commands/
agent.py` and `src/pcae/core/agent.py` likewise import neither; **no**
file anywhere under `src/pcae/**` imports `hatp_certification_admin`
(verified across every `.py` file in that tree via `ast.walk`, not a
sampled subset); `hatp_mandatory_certification.py` itself exposes no
public `create_certification`/`activate_certification`/
`revoke_certification`/`mark_independently_verified`/`set_certified`
name. `certification_id` is never combined with a filesystem path
anywhere in the loader/writer/ceremony functions (source-inspected), so
a path-traversal-shaped or otherwise malformed certification ID cannot
escape the Protected Root — it can only ever fail as
`CertificationRecordNotFoundError`, confirmed directly by
`test_path_traversal_shaped_certification_id_rejected_as_not_found`.

## 12. No-Readiness / No-PB / No-Rollback-Approval Proof

`CreateCeremonyResult`, `ActivateCeremonyResult`, and
`RevokeCeremonyResult` (this phase's own typed return values — never
`HMICValidationResult`, never a bare boolean) carry no
`ready`/`readiness`/`activation_allowed`/`pb_result`/`approved`/
`rollback_approval`/`capability`-named field (`inspect.signature`-
verified). `scripts/hatp_certification_admin.py` imports neither
`hatp_mandatory_cutover.py`, `permission_broker.py`,
`permission_broker_foundation.py`, `hatp_ag_authority.py`, nor
`rollback_approval_evidence.py` (AST-verified). `hatp_mandatory_
cutover.py` itself is confirmed byte-unchanged in intent: it still names
the hard-coded `mandatory_consumption_implementation_independently_
verified` ceiling and still does not import `hatp_mandatory_
certification`/`hatp_certification_admin` at all
(`TestNoCoupling::test_hatp_mandatory_cutover_module_unchanged_by_this_
phase`).

## 13. W-1 Source Inventory (Inputs to the Mandatory HMIC v1.1 Amendment)

Per the 149O.19.4 plan §10.3, Stop Condition W-1 is now concrete: any
HMIC-owned production source file whose mutation could change
certification parsing, identity derivation, storage interpretation,
validation outcome, admin certification content, active binding, or
revocation semantics must be inventoried here as an input to the next
phase's HMIC-001 v1.1 contract amendment. As of this phase's exit, that
set is exactly:

1. `src/pcae/core/hatp_mandatory_certification.py` — parsing, identity
   derivation, storage, and the Wave D validation algorithm all live
   here; this was already true and named at Wave D's own exit (149O.
   19.5D), unchanged by this phase.
2. `scripts/hatp_certification_admin.py` — **new this phase.** This file
   determines what content a certification *asserts* (the exact fields
   it derives and packages into a `CertificationRecord` before Wave C
   persists it) and what active-binding/revocation state ever gets
   written. An edit to this script's derivation logic — e.g. weakening
   `derive_implementation_scope_digest`'s call, or constructing a
   `CertificationRecord` with a caller-influenced field — could produce
   a record that is internally self-consistent (Wave D's own
   self-consistency re-derivation, HMIC-REQ-040, only re-checks
   `certification_id` against the record's *own* stored fields, not
   against this script's *source code integrity*) yet does not reflect
   what a Protected Admin actually reviewed. This is the precise
   analogue of the risk Wave D's own module docstring named for the
   validator itself (§10.2 of the 149O.19.4 plan) — it now applies
   symmetrically to the writer. Per the plan's own §10.4 analysis, this
   is a defense-in-depth concern rather than a soundness break (a
   compromised writer can at worst produce a record Wave D's validator
   fails to certify VALID, since Wave D re-derives every authority-
   sensitive value fresh and never trusts the writer's own stored
   values) — but it is still named here, exhaustively, as W-1 requires,
   not narrowly restricted to the two Wave D validator functions per
   governing-prompt item 97's explicit instruction.

No other new production file exists at this phase's exit.

## 14. Proposed v1.1 Binding Target (Not Amended This Phase)

The next phase (contract-only, no production changes) should widen
HMIC-REQ-050's frozen 22-file enumeration to 24 files: the existing 22,
plus `core/hatp_mandatory_certification.py` (already identified at Wave
D exit) and `scripts/hatp_certification_admin.py` (identified by this
phase, §13 item 2) — both relative-path entries following the existing
`core/...`/bare-relative-to-repo-root convention (the script would be a
repo-root-relative entry, `scripts/hatp_certification_admin.py`, exactly
as the 8 `docs/contracts/...` entries already are). This phase does
**not** perform that amendment — it is produced here only as the
required inventory for that dedicated, separately-governed,
independently-verified future phase (149O.19.5E.1 or repository-
conventional equivalent).

## 15. Tests

`tests/test_phase_149o_19_5e_hmic_protected_admin_certification_
revocation.py` — 33 tests: `TestCreate` (6), `TestActivate` (5),
`TestRevoke` (8), `TestConcurrency` (2), `TestMultiRepositoryIsolation`
(2), `TestNoAgentReachableWriteSurface` (5), `TestNoCoupling` (3),
`TestMalformedAndPathSafety` (2). All write-path tests use isolated
`tmp_path` protected roots and isolated git-fixture repositories,
mirroring the 149O.19.5D suite's `env` fixture exactly; none ever
touches `HATPTrustStore.production().root`.

One pre-existing sibling-suite test was updated as a direct, expected
consequence of this phase's legitimate work (exactly mirroring Wave D's
own prior precedent of updating Wave C's test file when it shipped):
`tests/test_phase_149o_19_5a_hmic_certification_models_canonical_
parsing.py::test_no_admin_script_created` asserted, as of Wave A, that
no admin script existed yet. Renamed to `test_admin_script_absent_or_
exactly_wave_e_owned` and restated to assert what remains permanently
true instead: if `scripts/hatp_certification_admin.py` exists, it is the
one sole Wave-E-owned file at that exact path, and no
`*certification_admin*`-named file exists anywhere under `src/pcae/`.

## 16. Regressions

- Wave A/B/C/D full suites: pass (`tests/test_phase_149o_19_5a_*`
  through `tests/test_phase_149o_19_5d_*`, plus `tests/test_hatp_
  mandatory_certification_models.py`).
- Full, untruncated `python -m pytest -m fast_green -q` (single clean
  process, no concurrent test runs against the same working tree):
  **33 failed, 6059 passed, 1 skipped, 25639 deselected** — reproduced
  identically across two independent clean runs (432.26s and 439.57s).
  All 33 failing node IDs, individually inspected, fall into exactly two
  pre-existing, phase-unrelated classes, none touching
  `hatp_mandatory_certification.py`, `scripts/hatp_certification_
  admin.py`, or either of this phase's own test files:
  - **32 nodes**: "diff since a fixed historical phase-entry commit"
    self-checks belonging to *earlier* phases' own boundary-verification
    suites (149O.13, 149O.14, 149O.15, 149O.16, 149O.16.2, 149O.17,
    149O.18A–D, 149O.19.2, 149O.19.3R, 149O.19.4) — each asserts
    `git diff --name-only <that phase's own fixed entry SHA>..HEAD --
    src/pcae/` is empty or matches a fixed set. This is a structural,
    permanent property: **any** later phase that legitimately touches
    `src/pcae/` after an earlier phase's own entry commit (as Waves
    B/C/D of *this same* HMIC-001 implementation already did) makes
    that earlier phase's own snapshot assertion fail forever after,
    independent of what the later phase actually is. A representative
    sample of 17 of these 32 nodes was directly re-run against this
    phase's own true entry commit (`git stash -u` A/B, working tree
    fully restored to `17a45b63`) and failed identically with zero
    Wave-E changes present, confirming the class.
  - **1 node**: `tests/test_hatp_mandatory_cutover.py::
    test_accept_strict_timestamp[2026-08-08T12:00:00.0Z]` — a
    parametrized timestamp-acceptance test in the unrelated
    `hatp_mandatory_cutover.py` HMRC-001 test suite; inspected directly
    (source-read) and confirmed to concern only `CutoverRecord`
    timestamp parsing, with no reference to `hatp_mandatory_
    certification`/`hatp_certification_admin` anywhere in the test file.
  - Two prior background runs during this phase's own development
    session that appeared to show additional, spurious failures inside
    this phase's *own* test file were traced to two *concurrent* `pytest`
    processes racing against the same live working tree while a
    `git stash pop` was in flight mid-run — an artifact of this session's
    own tooling sequencing, not a real defect; killing the contaminated
    process and re-running cleanly (twice, independently) reproduced the
    exact same 33/6059/1/25639 counts with zero Wave-E-file failures
    both times.
- HMRC/HATP regression: unaffected — no file in HMRC-001/HATP-001's own
  scope was touched.

## 17. Fast Green

`python -m pytest -m fast_green` with all 33 pre-existing node IDs named
in §16 passed as `--deselect` arguments (the exact 33-line list is
reproduced verbatim in this phase's own commit history via the shell
command used to generate it) yields **0 failed**, confirming every
Wave-E-introduced test and the one updated Wave-A sibling test are
fully green and that the deselected set is exactly, and only, the
pre-existing class.

## 18. Broad HMIC/HATP Sweep

`python -m pytest -k "hmic or hatp_mandatory_certification or 149o_19_5"`
— 566 passed, 3 failed (a narrower, HMIC/149O.19.5-scoped slice of the
same §16 pre-existing class: `test_phase_149o_19_3r_...` and the two
`test_phase_149o_19_4_...TestNoProductionOrContractMutation` nodes), 0
Wave-E failures.

## 19. Findings

None blocking. All 33 pre-existing failures named above are outside
this phase's allowed-file scope and outside this phase's own change set
(individually source-inspected and, for a representative sample,
A/B-confirmed via `git stash -u` against this phase's true entry
commit), consistent with `tasks/DONE.md`'s own already-recorded
historical-debt entries for this lineage. This phase does not remediate
them — doing so is outside this phase's allowed-file scope and would be
undocumented scope creep into unrelated earlier phases' own boundary
suites.

## 20. Implementation Verdict

**HMIC PROTECTED ADMIN CERTIFICATION / REVOCATION SURFACE: IMPLEMENTED
— WAVE A–E IMPLEMENTATION COMPLETE — W-1 CONTRACT-EVOLUTION GATE NOW
MANDATORY.** Not "READY FOR WAVE F."

## 21. Mandatory Next Phase

**149O.19.5E.1 — HMIC v1.1 Validator/Admin Implementation Identity
Contract Evolution** (or repository-conventional equivalent). Scope:
contract-only; widen HMIC-REQ-050's frozen enumeration per §14 above;
preserve the original 22-file HMRC/HATP-adjacent certified subject
byte-for-byte plus the exact two new entries; resolve versioning (HMIC-
001 v1.0 → v1.1); update attack/traceability clauses as needed; no
production changes; no readiness integration. Then: independent contract
verification. Only after that verification passes may 149O.19.5F (or
equivalent Wave F readiness-integration phase) be considered — **not**
recommended directly by this phase.

---

## Required Final-Report Field Confirmations

- Phase ID: 149O.19.5E — Status: completed — Report completeness:
  complete
- Files changed: 2 new (`scripts/hatp_certification_admin.py`,
  `tests/test_phase_149o_19_5e_hmic_protected_admin_certification_
  revocation.py`), 1 modified (`tests/test_phase_149o_19_5a_hmic_
  certification_models_canonical_parsing.py`, §15), plus this doc,
  `PROJECT_STATUS.md`, `CHANGELOG.md`
- Production files changed: 1 new (`scripts/hatp_certification_admin.py`)
  — **zero** files changed under `src/pcae/`
- Tests: 33 new (Wave E) + 1 updated (Wave A sibling) — see §15–18
- HMIC ID/version/status: HMIC-001 / v1.0 / VERIFIED WITH NON-BLOCKING
  FINDINGS — CONFORMS (unchanged this phase)
- HMIC byte status: unchanged — all 8 upstream contracts and the 22-file
  frozen subject remain byte-identical
- Wave-E requirement count: 18 requirement IDs (§2 table); CIVC count: 2
  (CIVC-2, CIVC-12); attack count: 3 (5, 6, 27)
- Admin surface type: standalone script outside `src/pcae/`
  (`scripts/hatp_certification_admin.py`)
- Admin production entrypoints: `certify()`, `activate()`, `revoke()`,
  `main()`
- Ordinary agent callers: none (verified, §11)
- Ordinary CLI writer exists? **NO**
- Protected root: `HATPTrustStore.production().root`; production root
  override? **NO**
- Writer authority model: OS filesystem permission on the Protected
  Root; agent principal role: read-only at most; admin principal role:
  sole write authority (Class-B, reused from 149O.1B.1)
- Caller repo ID / deployment ID / implementation digest / Git identity /
  contract digest / "verified" boolean allowed as creation input? **NO**
  (all six)
- Repository/deployment/implementation/contract identity derivation:
  internal, read-only, via unmodified Wave B functions
- Verification-record semantics: locator (file path) supplied by the
  human, hashed by the tool — never a caller-supplied digest
- Certification ID / `certified_at` derivation: internal, tool-derived,
  never caller input
- Certifier metadata authority? **NO** — audit metadata only
- Artifact create result: typed `CreateCeremonyResult`
  (`certification_id`, `already_existed`, `record`)
- Idempotent repeat: yes (byte-identical content); different-byte
  collision: rejected (`CertificationConflictError`, Wave C unchanged)
- Cert creation automatically active? **NO** (per contract, HMIC-REQ-086)
- Active supersession semantics: explicit `--certification-id` only;
  implicit latest? **NO**
- Revocation semantics: field mutation, monotonic; un-revoke API? **NO**;
  revoking active cert clears binding? **NO** (per contract; validator
  alone interprets it as `REVOKED`); revocation changes HMRC mode? **NO**
- Concurrent creation/supersession/revocation result: deterministic,
  single winner, no torn state (§10, `TestConcurrency`)
- Store primitives reused? **YES** (Wave C, unmodified); validator reused
  where contract requires? **N/A** — contract does not require
  pre-validation before binding, none invented; duplicate persistence
  implementation? **NO**
- Admin operation returns readiness/PB result/rollback approval/activates
  HMRC? **NO** (all four)
- PROJECT_STATUS/phase-report/tests/env/source-Boolean authority? **NO**
  (all five)
- Ordinary CLI changed? **NO**; `agent.py`/`commands/agent.py` changed?
  **NO**; `hatp_mandatory_cutover.py` changed? **NO**
- Hardcoded False status: unchanged
- Validator production callers after Wave E: zero (unchanged from Wave D)
- Cutover/readiness callers? **NO**
- Runtime/executed-source binding implemented? **NO**; HMIC-REQ-063
  retained? **YES**
- W-1 status: **MANDATORY**. A–E HMIC source files requiring v1.1
  binding: `src/pcae/core/hatp_mandatory_certification.py`,
  `scripts/hatp_certification_admin.py` (§13)
- Current 22-file subject changed? **NO**; contracts changed? **NO**;
  real protected root changed? **NO**; real certification state created?
  **NO**; real activation? **NO**; Class-B provisioned? **NO**; PB
  changed? **NO**; POL-005 changed? **NO**; COMP-002 implemented? **NO**
- Wave-A/B/C/D regression: pass; HMIC contract regression: pass except
  the pre-existing nodes named in §16; plan regression: pass except
  same; HATP/HMRC regression: pass (unaffected)
- Fast Green: 33 failed / 6059 passed / 1 skipped / 25639 deselected
  raw (all 33 failures pre-existing, §16); 0 failed with the full
  33-node deselect list applied (§17); broad HMIC/149O.19.5-scoped
  sweep: 566 passed / 3 failed (pre-existing subset) / 0 Wave-E
  failures (§18); report trust: to be confirmed at push time
- Implementation verdict: IMPLEMENTED — W-1 MANDATORY (§20)
- Recommended next phase: W-1 contract evolution
  (149O.19.5E.1), **NOT** Wave F (§21)
- B-149O.19.3-1 status: unchanged, independently closed
- B-149O-1..4 status: unchanged, independently confirmed closed at the
  system implementation/enforcement boundary; deployment/operational
  activation deferred
- HATP production readiness: **NOT READY** (unchanged)
- Runtime state: Observed / observe / unavailable (unchanged)

Explicitly confirmed: only Wave-E-authorized production files were
modified (exactly one new file, `scripts/hatp_certification_admin.py`;
zero files under `src/pcae/`). HMIC-001, HMRC-001, HATP-001, HSCE-001,
RAE-001, RWMPC-001/PBPA-001/PBPC-001 remained byte-unchanged. The
existing HMIC v1.0 22-file frozen subject remained byte-unchanged. The
hardcoded `False` readiness ceiling remained byte-unchanged. No
readiness integration occurred. No ordinary PCAE certification writer
was added. No real certification artifact, active binding, or
revocation state was created (every write test used an isolated
`tmp_path` protected root). No Cutover Record/activation marker was
created or modified. No real `HATP_MANDATORY` activation occurred. No
Class-B provisioning occurred. No Permission Broker behavior changed.
POL-005 remained unchanged. No COMP-002 capability was implemented.
Runtime/executed-source binding remained deferred under HMIC-REQ-063.
W-1 is now mandatory before Wave F. The next phase is contract
evolution, not readiness integration. B-149O.19.3-1 remains
independently closed. B-149O-1..4 remain INDEPENDENTLY CONFIRMED CLOSED
AT SYSTEM IMPLEMENTATION/ENFORCEMENT BOUNDARY — DEPLOYMENT/OPERATIONAL
ACTIVATION DEFERRED. HATP production remains NOT READY. Runtime remains
Observed / observe / unavailable.
