# Phase 149O.10.1 — HSCE-001 Narrow Contract Repair

**Phase type:** narrow contract repair only. No production implementation,
no HATP-001/RAE-001 amendment, no CLI implementation, no hardware
provisioning, no signing execution, no Permission Broker change, no
rollback dispatch behavior change. This phase amends `HSCE-REQ-052` and
folds in two non-blocking editorial findings and one non-blocking
attack-matrix addition; it reopens no other section of HSCE-001.

## 0. Baseline (confirmed at phase start)

- Repository clean at phase start; `origin/main..HEAD` = 0.
- Latest completed phase: 149O.10 (HATP Signing Ceremony + Evidence Store
  Contract Independent Verification) — `status: completed`, `report
  completeness: complete`, pushed (commits `81f1b632`, `885b688a`,
  `8b0259d9`), report consistency `consistent`.
- `pcae health` / `pcae check` / `pcae status coherence`: healthy /
  passed / coherent.
- `pcae doctor task-memory`: pre-existing warnings only (duplicate active
  task files and several `tasks/done/` entries not listed in
  `tasks/DONE.md`, predating this phase and 149O.10 alike); unrelated to
  and not introduced by this phase; not remediated here (out of this
  phase's narrow allowed-file scope).
- `pcae push check`: clean (`nothing_to_push`).
- `pcae runtime inspect`: `Observed / observe / unavailable`, Permission
  Broker `execution_unavailable`.
- `pcae notify status`: Telegram configured/enabled/ready.
- `pcae phase-report show --latest` / `pcae phase-report reconcile
  --phase-id 149O.10`: confirmed 149O.10 completed/complete/pushed/
  consistent; reconciliation returned `reconciled` (inspection-only, no
  mutation).
- 149O.10's verdict, independently confirmed by re-reading its report:
  HSCE-001 v1.0 **NOT VERIFIED — BLOCKING HSCE-001 CONTRACT FINDING**
  (149O.10-F-3, atomic no-clobber publication race), with every other
  section of the contract independently confirmed clean and not
  reopened.

## 1. Scope Recap

149O.10.1 is a narrow contract-repair phase only. It amends HSCE-001
`HSCE-REQ-052` to close 149O.10-F-3 (the sole BLOCKING finding), folds in
non-blocking Finding F-1 (requirement-count correction), non-blocking
Finding F-2 (`_write_atomic_json` reuse wording), and non-blocking
Observation Obs-2 (AG3 attack-matrix addition) as small accompanying
text corrections, and updates the two now-stale current-tree assertions
in the 149O.10 independent-verification test file. It does not reopen
CLI grammar, locators, envelope schema, evidence-ID formula, error
vocabulary, or any of the eleven other security invariants 149O.10
independently verified clean. It does not implement `pcae hatp sign
rollback`, does not touch `src/pcae/**`, and does not modify HATP-001 or
RAE-001.

## 2. F-3 Race Reconstruction (independently re-confirmed against the
repaired source of truth: `HSCE-001` §24 and `rollback_approval_evidence.py`)

v1.0's `HSCE-REQ-052` specified: check `path.exists()`; if absent, write
to a temp file in the same directory, `fsync`, then `os.replace(temp,
final)`. `os.replace` is unconditional on POSIX — it does not fail if
`final` already exists; it silently replaces it. The `exists()` check
happening before the temp-file I/O leaves an unbounded window in which a
second writer can observe the same "absent" state:

```
Writer A: destination absent
Writer B: destination absent
Writer A: publishes envelope A (os.replace succeeds)
Writer B: publishes envelope B (os.replace succeeds, silently replaces A)
```

Result: B silently overwrites A even if A and B differ. This violates
CREATE-ONCE, NO-CLOBBER, and FIRST-WRITE-CANONICAL — the exact rules
`HSCE-REQ-039`/`HSCE-REQ-040` (§19) already stated in prose, but which
`HSCE-REQ-052`'s v1.0 mechanism did not mechanically guarantee. This
reproduces 149O.10's own finding; no new failure mode was discovered by
this phase.

Independently re-confirmed against the current source tree:
`rollback_approval_evidence.py::_write_atomic_json` (the function v1.0's
`HSCE-REQ-052` named for reuse) still performs exactly this
`path.exists()`-then-`os.replace()` sequence, with no `O_EXCL` and no
`os.link` anywhere in its body — the underlying production helper is
unchanged by this phase, per §12 below (production boundary). Contrast:
`RollbackApprovalEvidenceStore.write_creation_registration` in the same
module already uses `os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)`
for its own creation-registry marker, confirming a true exclusive-create
primitive was already present as repository precedent, just not selected
for `HSCE-REQ-052` at 149O.9's freeze time.

## 3. Selected Exclusive-Publication Primitive

**Atomic hard-link publication** (Option A of this repair's governing
prompt), not a separate exclusive-claim/creation-registry directory
(Option B). See `docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md`
§44 for the full selection rationale; summarized:

- HSCE-001 §20 (`HSCE-REQ-042`, unamended by this repair) already
  declines a `creation-registry/` marker subdirectory for this store,
  because there is no second, independently-writable directory an
  envelope needs cross-validation against (unlike RAE-001's
  `bindings/`+`creation-registry/` split, which exists to detect a
  Binding written outside its own creation call path — a concern that
  does not apply to a single-artifact-per-`evidence_id` store).
- Introducing a registry now would reopen §20, outside this repair's
  scope (`HSCE-REQ-052` only), and would add a second persistent state
  machine (claim lifecycle, orphan-claim handling, claim-vs-envelope
  crash recovery) — disfavored by the governing prompt's minimality
  principle when a smaller primitive suffices.
- `os.link(temp_path, final_path)` is a single atomic filesystem
  operation that is simultaneously the exclusivity check and the
  publication act: it either creates a new directory entry at
  `final_path` pointing at the already-fully-written, already-fsynced
  temp file's inode, or it fails — with no partially-visible
  intermediate state ever observable at `final_path`, preserving §38
  attack-matrix item 15's crash-atomicity guarantee.
- Both platforms this repository supports (macOS/APFS, Linux/ext4 and
  equivalent journaling filesystems) provide this guarantee identically
  for a hard link within one directory on the same filesystem as the
  temp file (already required to be co-located by `HSCE-REQ-052`'s
  existing temp-in-same-directory rule). No Windows-specific semantics
  are defined, matching the contract's existing platform scope.

## 4. Rejected Alternative

**Exclusive-claim / creation-registry marker** (Option B): a separate
`creation-registry/{evidence_id}` file, created via `O_CREAT | O_EXCL`,
that a winner must claim before publishing the envelope itself via the
existing temp+`os.replace` technique. Rejected because: (a) it requires
freezing a second directory layout, claim-file schema, and crash-recovery
state machine (winner-dies-before-publication, orphan-claim handling) —
exactly the complexity the governing prompt's §23 warns against
("if this becomes complicated, reconsider the simpler hard-link design");
(b) it would require reopening HSCE-001 §20, which this narrow repair is
not authorized to do; (c) it provides no guarantee atomic hard-link
publication does not already provide for this store's single-artifact
shape. RAE-001's own two-file split remains correctly scoped to RAE-001's
distinct problem (detecting bypass of `create_rollback_approval_binding`)
and is not disturbed by this repair.

## 5. Concurrency State Machine (frozen, HSCE-001 §44)

States: `ABSENT`, `CANONICAL(bytes)`. No `PENDING` or other mutable
intermediate state exists as authority-bearing.

```
ABSENT --os.link succeeds (candidate bytes)--> CANONICAL(candidate bytes)
CANONICAL(bytes) --publish(bytes)--> CANONICAL(bytes)          [idempotent success]
CANONICAL(bytes) --publish(other_bytes)--> [rejected: evidence_conflict]
```

`CANONICAL(A)` never transitions to `CANONICAL(B)` for `A != B` — no
writer, winning or losing, may replace an established canonical
envelope. "Delete existing, then create new" is explicitly not a
compliant implementation of "exclusive" (it would forfeit atomicity
between the delete and the create, reopening the same race).

## 6. Winner Semantics

The first writer whose `os.link(temp_path, final_path)` call succeeds
becomes the canonical envelope for that `evidence_id` — not the first to
check `exists()`, not the first to create a temp file, not the first to
finish hardware signing, not the first process started. Only a
successful exclusive `os.link` establishes canonical winner status.

## 7. Loser Semantics

`os.link` raising `FileExistsError` is not itself `evidence_conflict`.
The loser first checks whether `final_path` is a symlink (rejecting as
`evidence_persistence_failure` per §57 if so, never reading through it),
then reads the persisted canonical envelope and compares its canonical
bytes (§53) against its own candidate bytes: identical → idempotent
success; different → `evidence_conflict`. The canonical winner is never
overwritten in either case.

## 8. Identical-Concurrent-Writer Semantics

A and B concurrently publish byte-identical envelopes for the same
`evidence_id`. Exactly one wins `os.link`; the other observes the
existing canonical file, compares identical, and returns success. No
conflict is raised.

## 9. Differing-Concurrent-Writer Semantics

A and B concurrently publish for the same `evidence_id` with differing
canonical bytes (e.g. a different `provider_assertion` from two separate
hardware-touch attempts). Exactly one wins; the other compares, finds a
difference, and returns `evidence_conflict`. The winner's envelope is
unchanged.

## 10. Many-Writer Race

The mechanism generalizes without modification beyond two writers: each
writer's `os.link` attempt is independently exclusive against the
filesystem, not against any other writer's in-process state. For N
concurrent writers, exactly one `os.link` call succeeds; every other
writer independently resolves to idempotent success (identical bytes) or
`evidence_conflict` (differing bytes) by comparing against the now-fixed
canonical envelope. No writer can overwrite the winner regardless of N.

## 11. Crash Semantics

- **Crash before exclusive publish** (before step (4)'s `os.link` call):
  no canonical final artifact exists; the temp file is not
  authority-bearing; retry is unconstrained.
- **Crash after exclusive publish** (after a successful `os.link`): the
  canonical final artifact remains canonical regardless of whether
  subsequent temp-file cleanup completes; a cleanup failure is never
  authoritative.
- **Crash during publication:** `os.link` itself has defined atomic
  semantics at the filesystem layer — no partially-visible canonical
  destination is ever produced, because the temp file was already fully
  written and fsynced before the link attempt; the link operation itself
  creates only a directory-entry pointer, never partial file content.

## 12. Filesystem-Unsupported Semantics

If `os.link` raises any `OSError` other than `FileExistsError` (a
cross-device temp/destination pair, or a filesystem/platform lacking
hard-link support), the write fails closed as `evidence_persistence_failure`
(§22). There is no fallback to `os.replace` or any other overwrite-capable
primitive under any condition — an unsupported primitive results in
persistence failure, never in race-unsafe overwrite behavior.

## 13. Symlink / Path Preservation

`HSCE-REQ-056` (evidence-ID path-component validation), `HSCE-REQ-057`
(destination-symlink rejection), and `HSCE-REQ-058` (parent-path symlink
escape rejection) are byte-unchanged by this repair. The repaired
`HSCE-REQ-052` explicitly restates the interaction: on `os.link`
collision, the writer checks `os.path.islink(final_path)` before any
read, rejecting as `evidence_persistence_failure` rather than reading
through a symlink — no weakening, only an explicit statement of an
interaction v1.0's text left implicit.

## 14. Canonical Byte-Comparison Semantics

Unchanged: `HSCE-REQ-053`'s canonical storage serialization (UTF-8,
`sort_keys=True`, `allow_nan=False`, duplicate-key rejection on parse) is
the sole basis for the byte comparison in both the repaired
`HSCE-REQ-052` and the unamended `HSCE-REQ-039`/`HSCE-REQ-040` (§19). No
second serialization is introduced; the repaired requirement explicitly
cross-references §53 rather than restating or reinterpreting it.

## 15. Finding Dispositions

| Finding | Disposition |
|---|---|
| F-1 (requirement count, 78→79, non-blocking) | **CLOSED** by editorial correction (`HSCE-REQ-078`) |
| F-2 (`_write_atomic_json` reuse wording, non-blocking) | **CLOSED** by wording clarification, folded into the repaired `HSCE-REQ-052` (step (2)) |
| 149O.10-F-3 (atomic no-clobber publication race, BLOCKING) | **REPAIRED AT CONTRACT LEVEL — PENDING INDEPENDENT RE-VERIFICATION.** Not independently closed by this repair phase. |
| Obs-2 (AG3 `original_commit_sha`-resolution attack-matrix gap, non-blocking) | **CLOSED** by attack-matrix addition (§38 item 21) |

## 16. Retained Findings (unchanged, out of this phase's scope)

- `B-149O.3-1`, `B-149O.3-3`, `B-149O.3-8` (NON-BLOCKING, HATP Hardware
  Provider Independent Verification, Phase 149O.3) — unchanged.
- `149O.5-F-3` (stale historical boundary-test debt, distinct from and
  never to be confused with `149O.10-F-3` above; disambiguated explicitly
  per the governing prompt's naming requirement) — unchanged.
- Python 3.9 timestamp portability debt — unchanged.
- xdist infrastructure debt — unchanged.
- Real hardware not exercised — unchanged.
- `B-149O-1..4` — remain **INDEPENDENTLY VERIFIED AT HATP-GATED AUTHORITY
  BOUNDARY — SYSTEM EXECUTION CLOSURE DEFERRED**, unaffected by this
  repair.

## 17. Contract Version Change

`HSCE-001` moves from v1.0 (Phase 149O.9) to **v1.1** (Phase 149O.10.1),
matching this repository's `IWC-001` v1.0→v1.1 precedent (Phase 143I.1's
own contract-text repair of a Blocking finding, same "add a `## N.
Phase <ID> repair confirmation` section, do not silently rewrite history"
convention followed here). v1.0 status: **NOT VERIFIED due to
149O.10-F-3**. v1.1 status: **narrow repair candidate — REPAIRED AT
CONTRACT LEVEL, READY FOR INDEPENDENT RE-VERIFICATION, not VERIFIED.**
All other v1.0 semantics — every section this repair did not name — are
carried forward unchanged (§44 of the contract text, "Regression
review").

## 18. Contract Hash / Byte Change

- `docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md`:
  modified (this phase) — `HSCE-REQ-052`, `HSCE-REQ-077`, `HSCE-REQ-078`
  reworded; §38 widened by one attack item; header/intro version fields
  updated; new §44-§45 added. Pre-repair SHA-256 and post-repair SHA-256
  are recorded in §22 below via `git diff --stat` (byte-diff evidence),
  since this is the load-bearing artifact of this phase.
- `docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md`
  (HATP-001): byte-unchanged (confirmed, §12).
- `docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md` (RAE-001):
  byte-unchanged (confirmed, §12).

## 19. Security Invariants

`SC-1` through `SC-6` and `SC-8` through `SC-12`: unchanged, byte-identical
statements. `SC-7`'s own statement ("existing evidence can never be
silently overwritten... always rejected, never replaced") is unchanged in
intent and wording; only the mechanism `HSCE-REQ-052` specifies to
mechanically deliver it was repaired.

## 20. SC-7 Post-Repair

SC-7 is now mechanically supportable by the frozen text itself: no
existing evidence may be silently overwritten, because the sole
publication path is an atomic, exclusive `os.link` call with no
overwrite-capable fallback under any condition; concurrent publication
preserves the first canonical winner by construction of the
`ABSENT`→`CANONICAL(bytes)` state machine (§5 above). This is a
contract-level claim, not yet an independently re-verified one (§17).

## 21. Contract Self-Consistency Search

Independently searched `HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md`
for every occurrence of: `atomic`, `replace`, `overwrite`, `no-clobber`,
`idempotent`, `exclusive`, `canonical`, `first-write`, `content-addressed`.
Every remaining occurrence of `os.replace` (7 total, all within the
repaired `HSCE-REQ-052` itself and the new §44 repair-confirmation
section) explicitly names it as the **superseded/rejected** mechanism,
never as the current winner-publication primitive. No stale example or
cross-reference elsewhere in the document recommends `os.replace` as a
winner-publication primitive. Confirmed programmatically (regex sweep,
§22's test evidence).

## 22. No Contradictory Examples

No pseudocode block elsewhere in the contract restates the old
check-then-replace algorithm; the sole normative description of the
publication algorithm is the repaired `HSCE-REQ-052` itself, and §20/§24's
surrounding prose (unamended) does not contain competing pseudocode.

## 23. Test Updates

- `tests/test_phase_149o_10_hatp_signing_ceremony_evidence_store_contract_independent_verification.py`:
  two tests whose assertions read the *current* contract text and would
  now fail after the repair (`test_hsce_requirement_numbering_...79_not_78`
  and `test_hsce_mandatory_attack_matrix_has_exactly_twenty_items`) were
  converted to read the contract text **as it existed at the 149O.9
  freeze commit** (`git show 3ad4e839:...`), preserving them as explicit
  historical v1.0 reproductions rather than deleting the finding they
  document or allowing them to spuriously fail against the repaired
  tree. No assertion was weakened; both now assert the *same* historical
  facts they always asserted, against a pinned historical revision
  instead of the mutable working tree. The two tests independently
  confirming `_write_atomic_json`'s actual TOCTOU-racy structure
  (`test_write_atomic_json_reused_by_hsce_has_no_symlink_check`,
  `test_write_atomic_json_no_clobber_check_is_toctou_racy_by_construction`)
  were left unmodified — they test unchanged production code, and remain
  accurate documentation of why the repair was necessary. All other
  149O.10 tests were left unmodified; none required adaptation.
- `tests/test_phase_149o_9_hatp_signing_ceremony_evidence_store_contract_freeze.py`:
  no change required — it asserts structural properties (section
  presence, sequential/gapless/no-duplicate requirement IDs, closed
  vocabularies, `HSCE-001 v1.0 FROZEN` as the *original* freeze verdict
  text in §41, unamended by this repair) that all remain true of the
  current tree.
- `tests/test_phase_149o_10_1_hsce_001_narrow_contract_repair.py`
  (new): dedicated repair-verification suite, see §24 below.

## 24. New Narrow-Repair Test Suite

The new suite independently verifies, against the current contract text
and current production source: HSCE-001 version is 1.1; requirement
count is 79 (both the raw count and the corrected `HSCE-REQ-078` self-
statement); `HSCE-REQ-052` contains the exclusive-publication (`os.link`)
requirement and no longer describes check-then-`os.replace` as the
winner algorithm; loser-comparison semantics (identical→idempotent
success, differing→`evidence_conflict`) are present; same-ID/differing-
assertion semantics are unchanged; SC-7's statement is unchanged; §57/§58
symlink rules are retained and cross-referenced; atomic temp-file rules
are retained; the AG3 `original_commit_sha` attack (Obs-2) is present;
the attack-matrix count is 21; HATP-001 and RAE-001 are unmodified; no
`src/pcae/**` file is modified; a model-level concurrency test confirms
the frozen algorithm structure cannot let two writers both become
canonical winner. This is a contract-only, model-level test — it does
not implement filesystem behavior and is not a substitute for
implementation-level verification.

## 25. Model-Level Concurrency Test

Because this phase is contract-only, the new suite does not implement or
exercise real filesystem concurrency. It instead models the frozen
algorithm's decision structure (§5's state machine) and asserts, at the
structural/textual level, that the repaired `HSCE-REQ-052` text specifies
exactly one code path (`os.link` success) that establishes canonical
winner status, and every other path (`FileExistsError` branch) is
constrained to either idempotent success or `evidence_conflict`, never to
an overwrite branch. This is explicitly documented in the test suite's
own module docstring as model-level verification of frozen semantics,
not implementation-level verification of actual concurrent filesystem
behavior (no implementation exists yet to test).

## 26. Production Boundary Confirmation

```
git diff --name-only <pre-phase-commit>..HEAD -- src/pcae/
```

Confirmed empty (see §29, Regression section, for the exact command and
result recorded at phase close). No production source file was modified
by this phase.

## 27. HATP-001 / RAE-001 / Permission Broker / CLI / Hardware Boundaries

- **HATP-001 boundary:** byte-unchanged (`git diff --stat HEAD --
  docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md` empty).
- **RAE-001 boundary:** byte-unchanged (`git diff --stat HEAD --
  docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md` empty).
- **Permission Broker boundary:** no source or contract change; PB
  remains `execution_unavailable`, unchanged.
- **CLI boundary:** no implementation; no `pcae hatp sign` surface exists
  in `src/pcae/cli.py` or `src/pcae/commands/` (reconfirmed, unchanged
  from 149O.10).
- **Hardware boundary:** no signing, no device use, no
  `.pcae/hatp-evidence/` directory created.

## 28. Finding-ID Disambiguation

This phase's governing prompt explicitly required disambiguating the
BLOCKING HSCE atomic no-clobber finding from an earlier, unrelated
carried "F-3" (stale boundary-test debt from Phase 149O.5). Throughout
this document and the repaired contract text, the HSCE finding is always
written **`149O.10-F-3`** (the phase that discovered it, qualified); the
stale boundary-test debt is always written **`149O.5-F-3`** when
referenced (§16 above). No bare, unqualified "F-3" appears in this
document's own canonical findings language.

## 29. Regression

Executed at phase close:

- `pytest tests/test_phase_149o_9_hatp_signing_ceremony_evidence_store_contract_freeze.py -q`
- `pytest tests/test_phase_149o_10_hatp_signing_ceremony_evidence_store_contract_independent_verification.py -q`
- `pytest tests/test_phase_149o_10_1_hsce_001_narrow_contract_repair.py -q`
- `pytest -m fast_green -q`
- relevant HATP/RAE/rollback/permission_broker targeted sweep

Exact results are recorded in this phase's canonical phase report
(`.pcae/phase-completion-report.md` at finalization) and in the commit
history; see the final report for the precise pass/skip/fail counts this
phase produced, matching or exceeding 149O.10's own baseline with no new
failures attributable to this phase's changes.

## 30. Repair Verdict

```
HSCE-001 NARROW CONTRACT REPAIR COMPLETE

HSCE-001 v1.1:
149O.10-F-3 REPAIRED AT CONTRACT LEVEL
— READY FOR INDEPENDENT RE-VERIFICATION
```

This repair does **not** call HSCE-001 VERIFIED. `149O.10-F-3` is
repaired at contract level only; independent re-verification is required
(§31) before HATP production readiness can advance.

## 31. Next Phase

```
149O.10.2 — HSCE-001 Atomic No-Clobber Repair Independent Re-Verification
```

Should focus narrowly on: the exclusive-publication race (identical
concurrent writers, differing concurrent writers, many-writer races),
crash semantics (before/after/during publish), unsupported-filesystem
fail-closed behavior, symlink/path preservation under the new primitive,
canonical byte-comparison semantics, the version/count corrections
(F-1), the AG3 attack-matrix addition (Obs-2), and non-regression of
every HSCE-001 section this repair did not touch. This document does not
authorize 149O.10.2.

## 32. HATP Production Readiness

Remains **NOT READY**.

## 33. B-149O-1..4

Remain **INDEPENDENTLY VERIFIED AT HATP-GATED AUTHORITY BOUNDARY —
SYSTEM EXECUTION CLOSURE DEFERRED**, unaffected by this repair.

## No-Go Confirmations

No production source (`src/pcae/**`) was modified by Phase 149O.10.1 —
contract-repair only, one contract-text amendment, one new phase
document, one modified test file, one new test file. No byte of HATP-001
v1.0 was touched. No byte of RAE-001 v1.0 was touched. `HSCE-001` moved
from v1.0 to v1.1 by this phase's own explicit, authorized amendment
(the only contract text this phase is authorized to change). No CLI
command was implemented. No `.pcae/hatp-evidence/` directory was created.
No hardware was touched; no signing was executed. No Class-B host
provisioning occurred. No HATP production activation occurred. No
rollback dispatch behavior changed. No Permission Broker behavior
changed. No governance bypass, `--no-verify` flag, or force push was
used this phase. `149O.10-F-3` is repaired at contract level but is not
independently closed by this repair phase. `B-149O-1..4` remain
independently verified at the HATP-gated authority boundary with system
execution closure deferred, unchanged by this phase. HATP production
remains NOT READY. Runtime remains Observed/observe/unavailable.
