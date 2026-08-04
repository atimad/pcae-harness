# Phase 149O — Rollback Approval Evidence Canonical-Provenance Hardening Independent Verification

## 0. Identity and Status

- **Phase ID:** 149O
- **Type:** Independent verification only (no production repair)
- **Subject:** Phase 149N's canonical-provenance hardening of `src/pcae/core/rollback_approval_evidence.py`, closing Phase 149M's four BLOCKING findings (B-149M-1/2/3/4)
- **Verdict:** **NOT VERIFIED — BLOCKING CANONICAL-PROVENANCE FINDINGS**
- **Root-provenance verdict:** **PROVENANCE ROOT NOT VERIFIED — BLOCKING**
- **Evidence substrate readiness:** **NOT READY**

## 1. Methodology

Independent, from primary sources only: `docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md`, the full 1430-line `src/pcae/core/rollback_approval_evidence.py`, `src/pcae/governance/publication/storage.py`, and `src/pcae/governance/publication/coordinator.py`. No 149N claim was trusted without independent reproduction. A dedicated, independently-authored test suite (`tests/test_phase_149o_rollback_approval_evidence_canonical_provenance_hardening_independent_verification.py`, 17 tests, zero fixture/helper reuse from 149L/149M/149N) reconstructs the original four findings and, per the governing phase prompt's "Critical New Adversarial Question," directly attacks the two new provenance mechanisms 149N introduced.

**Environment note (not a 149N defect):** this repository's committed local `.venv` is Python 3.9.6. `pcae.governance.publication.coordinator._parse_timestamp` calls `datetime.fromisoformat` directly on `Z`-suffixed timestamps (`chgr_timestamp`'s required output format); Python's `fromisoformat` only accepts a literal `Z` suffix starting in 3.11. Under 3.9.6 every call path through `PublicationCoordinator.execute` (including `create_rollback_approval_decision`) raises `StaleAuthorizationError`, producing 32/53 spurious failures in 149M's suite unrelated to any code change. This was independently isolated (traceback points at `coordinator.py:70`, present unchanged since Phase 144C/146G, long before 149N) and worked around by building a disposable Python 3.14.5 venv (`/tmp/pcae-venv-314`) from the same `pyproject.toml`/`src/`, in which the entire 149M suite passes 53/53 unmodified. All test-suite results in this report were produced under that verified-working interpreter. This finding is recorded as a **non-blocking environmental observation**, not part of the 149O verdict.

## 2. Exact 149N Production Diff (reconstructed independently)

`git diff 93579dc6~1..93579dc6 -- src/pcae/` — exactly one file, `src/pcae/core/rollback_approval_evidence.py`, 247 insertions / 11 deletions. Hunks classified:

| Hunk | Class |
|---|---|
| Module docstring (2 hunks) | DOCSTRING_ONLY |
| `_write_atomic_json` / `remove_binding` / `write_creation_registration` / `read_creation_registration` additions | ATOMIC_CREATION |
| `_chgr_record_has_publication_receipt` (new function) | CHGR_RECEIPT_VALIDATION |
| `_resolve_decision_ref` docstring | DOCSTRING_ONLY |
| `create_rollback_approval_binding` registration write + rollback-on-failure | ATOMIC_CREATION, BINDING_REGISTRATION |
| `_binding_is_canonically_created` (new function) | BINDING_REGISTRATION |
| `_is_superseded` candidate filtering | SUPERSESSION |
| `resolve_rollback_approval_evidence` registration check + receipt check call sites | BINDING_REGISTRATION, CHGR_RECEIPT_VALIDATION |
| `list_bindings_with_keys` (new, replaces bare glob) | DIRECTORY_HARDENING |

No `UNRELATED` hunk found. Matches 149N's own claim of a single production file. Confirmed independently.

## 3. Production/Contract Boundary — this phase (149O)

`git diff --stat 93579dc6~1..HEAD -- src/pcae/` still shows only the 149N hunk above; 149O added zero production lines. `git diff --name-only 93579dc6~1..HEAD -- docs/contracts/` is empty. `agent.py`, `commands/agent.py`, `mutation_permission.py`, `permission_broker_foundation.py`, `permission_broker.py` are byte-unchanged since before 149N. **CONFORMS.**

## 4. Root-Cause Reconstruction (149N's own repair, independently re-derived)

Before 149N: canonicality collapsed to (schema validity) + (digest self-consistency) + (declared-reference agreement) — never proof of legitimate creation. 149N's repair adds two new provenance objects, checked at `resolve_rollback_approval_evidence` time:

1. **CHGR publication receipt** (`_chgr_record_has_publication_receipt`): scans `<publication_root>/published/*.json` for a marker whose `record_id` (or `chgr_record_ids` values) names the referenced record.
2. **Binding canonical creation registration** (`_binding_is_canonically_created`): requires a file at `<evidence_root>/creation-registry/<lookup_key>.json` whose declared `evidence_id`, `binding_content_digest`, `governance_record_reference`, `rollback_site`, and `rollback_operation_reference` all exactly match the Binding being resolved, keyed by the store's filename-derived lookup key rather than the payload's own internal `evidence_id` field.

Both are written, in the legitimate path, only by trusted producers: the receipt by `PublicationRecordStore.commit_publication` (exclusive `O_CREAT|O_EXCL`, called only at the end of a successful `PublicationCoordinator.execute`), the registration by `RollbackApprovalEvidenceStore.write_creation_registration` (also exclusive create, called only by `create_rollback_approval_binding`, with atomic Binding rollback if registration fails).

## 5. B-149M-1/2/3/4 — Independent Reconstruction (Part 1 of the 149O suite)

| Finding | Independent exploit | 149N mechanism | Result | Status |
|---|---|---|---|---|
| B-149M-1 | Hand-authored Binding referencing a genuine published Decision, written directly to `bindings/` | No canonical creation registration for that filename | INVALID / `approval_present=False` | **CLOSED** |
| B-149M-2 | Fully hand-authored CHGR-record-shaped file at `records/<id>.json`, real `create_rollback_approval_binding` call referencing it | No matching `published/*.json` receipt naming that `record_id` | INVALID / `approval_present=False` | **CLOSED** |
| B-149M-3 | Verbatim byte-copy of a legitimate Binding under a new filename; original untouched | Registration keyed by lookup filename, not payload's internal `evidence_id` | New filename INVALID; original still VALID | **CLOSED** |
| B-149M-4 | Hand-authored Binding, same operation reference, forged far-future `created_at` | Supersession candidates filtered to canonically-registered records first | Genuine Binding remains VALID; forgery itself INVALID | **CLOSED** |

All four independently reproduced as CLOSED — `tests/test_phase_149o_...py::test_149o_b{1,2,3,4}_*`, 4/4 passed. 149M's own unmodified 53-test suite: **53/53 passed** (was 49/53 before 149N).

## 6. CHGR Publication Receipt — Trust Chain Trace

`_chgr_record_has_publication_receipt` globs every `*.json` under `<publication_root>/published/` and string-compares `marker.get("record_id")` (or membership in `marker.get("chgr_record_ids")`'s values) against the target `record_id`. **No cryptographic tie between the marker and the record it names beyond this string comparison.** `PublicationRecordStore.commit_publication` (`storage.py:116-136`) writes this marker via `O_CREAT|O_EXCL` — but `O_CREAT|O_EXCL` only prevents *overwriting an existing marker for the same `package_id`*; it places **zero constraint on what `package_id` or `record_id` value a brand-new, attacker-chosen marker file may declare.** Any process with filesystem write access to `<publication_root>/published/` (the same access 149M's original attack already used against `<publication_root>/records/`) can create a syntactically-valid marker for any `record_id` of its choosing, including one it also just hand-authored.

## 7. Publication Receipt Trust Root — Answer

**There is no independent trust property.** The question posed by the governing phase prompt — "why can an attacker who can hand-author the CHGR record not also hand-author the corresponding publication receipt?" — has no defensible answer in this implementation: nothing distinguishes a marker written by `PublicationRecordStore.commit_publication` from one written by any other process with the same directory-write access. The `O_CREAT|O_EXCL` flag defends only against a *second* writer racing an *existing* marker for the *same* `package_id` — a concurrency guarantee, not a provenance guarantee. `package_id` itself is entirely attacker-chosen and carries no authentication.

## 8. Hand-Authored CHGR + Hand-Authored Receipt Attack — **BLOCKING**

`tests/test_phase_149o_...py::test_149o_fake_chgr_record_plus_fake_publication_receipt` — a schema-valid, self-digest-consistent, hand-authored CHGR record at `records/<id>.json`, paired with a hand-authored marker at `published/<pkg>.json` naming that `record_id` (neither ever touching `PublicationCoordinator`), used with the **real** `create_rollback_approval_binding` API:

```
RESULT: VALID   approval_present: True
```

**Expected INVALID. Observed VALID. BLOCKING — reproduced live, independent of the test suite, via a standalone script before the pytest test was even written.**

## 9. Binding Creation Registration — Trust Chain Trace

`_binding_is_canonically_created` requires a `creation-registry/<lookup_key>.json` file whose declared fields exactly match the Binding. `write_creation_registration` (`rollback_approval_evidence.py:637-661`) writes it via `O_CREAT|O_EXCL`, called only from inside `create_rollback_approval_binding`. Exactly parallel to §6/§7: the exclusive-create flag prevents *overwriting an existing registration for a given filename*, but places **no constraint on what filename or field values a brand-new registration may declare.** `_registration_to_dict` is a plain, publicly-importable module function (`rollback_approval_evidence.py:570-590`) whose output an attacker can trivially reconstruct field-for-field from a Binding they also control.

## 10. Registration Trust Root — Answer

**No independent trust property exists.** "Why can a process that can hand-author a Binding not also hand-author the matching registration?" — it can, without restriction, because `write_creation_registration`'s exclusive-create guarantee is a race-detection mechanism for the *lookup key*, not an authentication mechanism for the *registration's content*. The registration is computed deterministically and reproducibly from the Binding by `_registration_to_dict`, a function available to any caller of the module.

## 11. Hand-Authored Binding + Hand-Authored Registration Attack — **BLOCKING**

`tests/test_phase_149o_...py::test_149o_fake_binding_plus_fake_creation_registration` — a real, genuinely-published Decision (via `create_rollback_approval_decision`), paired with a fully hand-authored Binding **and** a hand-authored, field-matching registration, both written directly to their canonical paths (no `create_rollback_approval_binding` call):

```
RESULT: VALID   approval_present: True
```

**Expected INVALID. Observed VALID. BLOCKING — B-149M-1's root cause persists exactly one layer outward, per the governing phase prompt's item 14 hypothesis.**

## 12. Full End-to-End Forgery — **BLOCKING**

`tests/test_phase_149o_...py::test_149o_full_end_to_end_forgery_zero_legitimate_api_calls` combines §8 and §11: every artifact (CHGR record, publication receipt, Binding, creation registration) is hand-authored; **zero** calls anywhere in the test to `create_rollback_approval_decision` or `create_rollback_approval_binding`:

```
RESULT: VALID   approval_present: True
```

An attacker with the same filesystem-write capability 149M's original threat model already assumes can manufacture a fully trusted `approval_present=True` rollback approval **without the real CHGR Confirmation→Publication pipeline or the real Binding creation API ever executing once.**

## 13. Copied/Forged Registration Under a New Key — **BLOCKING**

`tests/test_phase_149o_...py::test_149o_copied_registration_under_new_key_with_matching_fields_rejected`: a hand-authored Binding at a fresh `evidence_id`, paired with a freshly hand-authored (not copied-and-reused) registration self-consistent with it:

```
RESULT: VALID   approval_present: True
```

Confirms §11/§12 are not edge cases specific to reusing a real Decision's exact shape — any self-consistent (Binding, registration) pair at a fresh key validates. The filename-keying defense (closing B-149M-3, "copy under a *different, unregistered* key") is real and independently confirmed (§5, §15 below) but does not generalize to "mint your own key with its own matching registration."

## 14. Recursive Provenance Analysis — Where the Chain Terminates

```
Binding trusted  ⟵  because a creation-registration file agrees with it
creation-registration trusted  ⟵  because it was found at the expected path with matching fields
   (no further anchor — the registration is itself just JSON on disk)

Decision trusted  ⟵  because a publication-receipt marker names its record_id
publication-receipt marker trusted  ⟵  because it was found at the expected path with a matching field
   (no further anchor — the marker is itself just JSON on disk)
```

Both chains terminate in **another writable, self-describing file**, not in an independently governed canonical creation fact (a signature, an append-only log a filesystem-only attacker cannot rewrite, or genuine coupling to a governed API's internal, non-reconstructible state). Per the governing phase prompt's item 21, this is recorded as the **Blocking finding**, since the project's own disclosed threat model (149M) already treats direct-filesystem-write to these exact directories as in-scope, and both new mechanisms are defeated by exactly that capability, applied once more.

## 15. Threat-Model Alignment — Not Overreach

PCAE's disclosed threat-model ceiling (no OS privilege separation between human and agent) does not, by itself, excuse this finding. 149M's four original attacks used the *identical* capability (writing a new, self-consistent JSON file into a canonical directory) against `records/` and `bindings/`; 149N was built specifically to defeat that. §8/§11/§12/§13 apply the *same, already-in-scope* capability to two directories 149N itself introduced (`published/`, `creation-registry/`) and it succeeds identically. This is not a demand for cryptographic signatures or OS-level provenance beyond what RAE-001/CHGR-001 promise — it is the same disclosed adversary the project already commits to defending against, applied one hop further along the trust chain 149N built.

## 16. Provenance-Mismatch Negative Controls — CONFORMS

Where 149N's mechanisms genuinely operate on *existing, mismatched* provenance, they work correctly and were independently reconfirmed:

- Registration file deleted after genuine creation → `INVALID` (`test_149o_registration_missing_...`).
- Registration exists but no matching Binding at that key → `MISSING`, not treated as valid evidence (`test_149o_orphan_registration_...`).
- Registration's `binding_content_digest` field tampered → `INVALID` (`test_149o_registration_mismatch_wrong_digest_rejected`).
- `write_creation_registration` forced to fail (`OSError`) → Binding file is rolled back; no orphan-trusted Binding on disk (`test_149o_atomic_creation_registration_failure_rolls_back_binding`), independently reproducing 149N's own atomicity claim.
- Forged newer *denial* Binding cannot invalidate a canonical earlier *approval* (`test_149o_forged_later_denial_cannot_invalidate_canonical_approval` — VALID preserved).
- Malformed JSON dropped into `bindings/` does not poison resolution of an unrelated, legitimate Binding (`test_149o_invalid_newer_candidate_does_not_suppress_older_valid_one`).
- Canonical positive control and canonical supersession both still work exactly as RAE-001 requires (`test_149o_canonical_positive_control_still_valid`, `test_149o_canonical_supersession_still_works`).

All 9 of these pass. The hardening is genuinely effective at rejecting *mismatched* or *incomplete* provenance between two already-fixed artifacts — it is specifically **fresh, mutually-consistent forgery of both artifacts at once** that defeats it.

## 17. RAE-REQ-019 / Contract Compatibility

`docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md`'s RAE-REQ-019 (at most one active Binding per Decision) is enforced only inside `create_rollback_approval_binding` (§1038-1042 of the module), not inside `resolve_rollback_approval_evidence` — unchanged from 149L/149M, and outside 149O's mandate to repair. RAE-001 v1.0, RWMPC-001 v1.0, PBPC-001 v1.2, PBPA-001 v1.0, and CHGR-001 are unmodified by 149N or 149O (`git diff --name-only ... -- docs/contracts/` empty across both phases). 149N's mechanisms are implementation-layer only; no contract amendment was required or made.

## 18. AG3/AG5 / Permission Broker Non-Interference — CONFORMS

`agent.py`, `commands/agent.py`, `mutation_permission.py`, `permission_broker_foundation.py`, `permission_broker.py` byte-unchanged (§3). No `approval_present=True` consumer exists in production request-construction code. No import of `PermissionBroker`, `mutation_permission`, `pcae.core.agent`, or the CLTR Typed Authority Model package from `rollback_approval_evidence.py` (confirmed by direct import-statement inspection, §9 of this module's own docstring, unaltered).

## 19. Regression Suites (Python 3.14.5 verified-working interpreter)

| Suite | Result | Baseline (149N) | Match |
|---|---|---|---|
| 149M (unmodified) | 53 passed | 53 passed | ✅ |
| 149N hardening | 11 passed | 11 passed | ✅ |
| 149L self-tests | 77 passed | 77 passed | ✅ |
| 149J | 49 passed | 49 passed | ✅ |
| CHGR | 230 passed, 2 pre-existing failed (packaging) | 228 passed, 2 pre-existing failed | ✅ |
| TAM/CLTR | 5675 passed, 58 pre-existing failed | 5675 passed, 58 pre-existing failed | ✅ |
| IWC | 693 passed | 693 passed | ✅ |
| AESIC | 431 passed | 431 passed | ✅ |
| Permission Broker | 981 passed | 981 passed | ✅ |
| Rollback (existing) | 489 passed | 476 passed | ✅ (+13 = new 149O positive/negative-control tests) |
| Wave-1 | 34 passed | 34 passed | ✅ |
| Fast Green | 4391 passed | 4391 passed | ✅ |
| **149O (new, this phase)** | **13 passed, 4 failed (documented BLOCKING findings)** | n/a | — |

Zero regressions anywhere. The four 149O failures are intentional, repo-conventional (`pytest.fail("BLOCKING: ...")`, matching 149M's own §274-345 convention) documented evidence of the findings in §8/§11/§12/§13, not defects in the test file.

## 20. Runtime Boundary

`pcae runtime inspect` before and after this phase: **Observed / observe / unavailable**, unchanged. `pcae health`, `pcae check`, `pcae status coherence`, `pcae doctor task-memory`, `pcae push check` all report healthy/coherent/clean throughout.

## 21. Root-Provenance Verdict

**PROVENANCE ROOT NOT VERIFIED — BLOCKING.**

The trust chain for both new provenance mechanisms terminates only in another forgeable file — a JSON marker or registration an attacker with the same filesystem-write capability already assumed by 149M's own threat model can produce, mutually self-consistent with a companion artifact they also control. Neither mechanism ties itself to a fact external to the two files it compares. This is not a demand for guarantees beyond PCAE's disclosed threat model (§15); it is the exact disclosed adversary defeating the exact new mechanism built to stop it, one hop further along the same chain.

## 22. Blocking Findings

**B-149O-1 (CHGR publication-receipt forgery).** A hand-authored CHGR record paired with a hand-authored `published/*.json` marker validates as canonical, with the real `create_rollback_approval_binding` API accepting it downstream. §6-§8.

**B-149O-2 (Binding creation-registration forgery).** A hand-authored Binding paired with a hand-authored `creation-registry/*.json` registration validates as canonical, referencing either a real or a forged Decision. §9-§11, §13.

**B-149O-3 (combined end-to-end forgery).** Both of the above combined: a complete, trusted rollback approval manufactured with zero calls to any legitimate creation API. §12.

These three findings share one root cause (§14) and are recorded as a single conceptual defect with three independent proofs, not three unrelated bugs.

## 23. Non-Blocking Findings

- **Environmental:** committed local `.venv` (Python 3.9.6) cannot execute the CHGR publication pipeline at all (`fromisoformat` rejects `Z`-suffixed timestamps pre-3.11), producing 32 spurious 149M failures unrelated to any code change. Recorded for repo hygiene; not part of this verdict. §1.
- RAE-REQ-019 (at-most-one-active-Binding) remains enforced only at creation time, not at resolution time — a pre-existing, disclosed 149D observation, unchanged by 149N/149O, out of this phase's scope.
- The `chgr` keyword's 2 pre-existing packaging test failures (`test_143e_wheel_contains_all_six_chgr_record_schemas`, `test_143e_installed_wheel_offline_registry_resolves_in_isolated_venv`) reproduced identically to the 149N baseline; unrelated to this phase.

## 24. Verification Verdict

**NOT VERIFIED — BLOCKING CANONICAL-PROVENANCE FINDINGS.**

149N genuinely closed all four original B-149M findings (§5) and its atomicity, directory-injection, and supersession-filtering mechanisms are independently confirmed correct against mismatched/incomplete provenance (§16). But per the governing phase prompt's Critical New Adversarial Question, both new provenance primitives 149N introduced are themselves forgeable by the same disclosed threat-model adversary, and three independent live exploits (§8, §11, §12) confirm `approval_present=True` is reachable without any legitimate creation API ever executing.

## 25. Evidence Substrate Readiness

**RAE EVIDENCE SUBSTRATE: NOT READY.**

## 26. AG3 / AG5 Readiness

Not ready for AG3 or AG5 Permission Broker integration planning while B-149O-1/2/3 stand: wiring either integration today would let the same forgery reach a real rollback-permission decision.

## 27. Chapter 149 Status

Chapter 149 remains incomplete. Outstanding: a bounded provenance-root repair (below), AG3/AG5 Permission Broker integration (design deferred pending that repair), independent rollback-integration verification, and TK1/TK2/TK3 deferred-coverage re-affirmation (all still deliberately deferred, unaffected by this phase).

## 28. Recommended Next Phase

Per the governing phase prompt's §109 ("If provenance root is still forgeable, do not proceed to AG3/AG5 planning; recommend the narrowest next repair"):

**149N.1 — RAE Trusted Provenance Root Hardening**

This is classified as an **RAE-local implementation defect** in how `rollback_approval_evidence.py` *reuses* the publication substrate (`_chgr_record_has_publication_receipt`'s marker-matching logic, and the module's own `creation-registry` design), not a defect in `PublicationRecordStore`/CHGR-wide canonicality itself: `PublicationRecordStore.commit_publication`'s `O_CREAT|O_EXCL` marker is only ever consumed, correctly, by `PublicationCoordinator` in its own normal flow — nothing in this phase found CHGR's own `is_published`/idempotency semantics violated for a *package_id CHGR itself minted*. The gap is that `_chgr_record_has_publication_receipt` accepts *any* marker naming the target `record_id` regardless of what wrote it or what `package_id` produced it, and that the Binding registration mechanism has no analogous tie back to a fact `create_rollback_approval_binding`'s own caller could not also fabricate. A future 149N.1 should scope narrowly to strengthening these two specific checks (e.g., requiring the marker/registration to be independently, non-reconstructibly bound to a fact of a real `PublicationCoordinator.execute`/`create_rollback_approval_binding` call — not merely matching declared fields) without touching CHGR-001, RAE-001, or any Permission Broker boundary.

---
*149O findings summary: B-149O-1, B-149O-2, B-149O-3 — provenance root relocated, not removed. See §22.*
