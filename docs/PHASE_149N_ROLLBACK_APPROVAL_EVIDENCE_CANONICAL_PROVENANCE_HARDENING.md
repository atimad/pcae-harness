# Phase 149N — Rollback Approval Evidence Canonical-Provenance Hardening

## 0. Phase Identity

**Phase:** 149N
**Type:** Bounded production hardening of canonical provenance for RAE-001 evidence.
**Governing findings:** Phase 149M's four BLOCKING findings (F1, F2, F4a, F4b / B-149M-1..4)
against the Phase 149L production implementation of RAE-001 v1.0.
**Runtime posture, unaffected:** State **Observed**, maximum capability **observe**, execution
availability **unavailable**.

## 1. Baseline

```
git status --short                      -> clean
git rev-list --count origin/main..HEAD  -> 0
```

Latest completed phase: 149M (verdict: NOT VERIFIED — BLOCKING RAE-001 IMPLEMENTATION FINDINGS).
`pcae health` -> healthy. `pcae check` -> passed. `pcae status coherence` -> coherent.
`pcae doctor task-memory` -> clean. `pcae push check` -> nothing_to_push. `pcae runtime inspect`
-> Observed / observe / unavailable. `pcae phase-report show --latest` and
`pcae phase-report reconcile --phase-id 149M` both confirm 149M complete and recommend exactly
`149N — Rollback Approval Evidence Canonical-Provenance Hardening`.

Test-environment note: this repository's real, `pcae`-CLI-linked interpreter is
`/opt/homebrew/opt/python@3.14/bin/python3.14` (pytest 9.0.3) — matching the interpreter every
prior 149-chapter phase report's numbers were generated against. The repository's own `.venv` is
Python 3.9.6, under which `datetime.fromisoformat` cannot parse the `Z`-suffixed, microsecond
timestamps CHGR's publication pipeline produces, causing spurious, environment-only failures
unrelated to this phase. All regression numbers in this report were produced under
`python3.14`, reproducing 149M's own baseline numbers exactly before any change was made.

## 2. Root Cause (independently reconstructed from 149M)

All four 149M BLOCKING findings share one root cause: **canonicality was implemented as digest
self-consistency plus reference-field agreement, never as proof that the artifact's creating
process was the legitimate one.** Concretely, pre-149N:

- `_resolve_decision_ref` treated a CHGR record as "published" because the record's own
  `lifecycle_state` field said so — a fact the record itself declares, not one an independent
  second artifact confirms (**F2**).
- `create_rollback_approval_binding` enforced RAE-REQ-019's "at most one active Binding per
  Decision" only at its own call site; `resolve_rollback_approval_evidence` never re-checked that
  a Binding it was asked to resolve had actually been produced by that function (**F1**).
- The store's lookup was keyed by filename (`evidence_id`), but `content_digest` only validated
  the payload's *internal* `evidence_id` field — the two were never cross-checked, so one
  legitimate byte-sequence could be presented for lookup under an unbounded number of filenames
  (**F4a**).
- `_is_superseded` scanned every Binding file in the store directory with no check that a
  competing record was itself canonically created, so a hand-authored file with a forged, later
  `created_at` could suppress a legitimate, still-fresh Binding (**F4b**).

None of these are fixable by checking "is this file under the canonical directory" (149M already
proved canonical-path placement is forgeable) or "does `hash(record) == record.digest`" (an
attacker can compute both sides of that equation itself). Both are explicitly excluded as repair
strategies by this phase's own governing prompt (items 3-4), and neither is used below.

## 3. Root Trust Anchor

**`PublicationRecordStore.commit_publication`'s own idempotency marker**
(`<publication_root>/published/<package_id>.json`, `src/pcae/governance/publication/storage.py`)
is the root trust anchor this hardening relies on for CHGR-side provenance. It is written via an
exclusive (`O_CREAT | O_EXCL`) filesystem create, exactly once, only at the successful conclusion
of `PublicationCoordinator.execute` — after CHGR's own Authorization/Confirmation/replay/
readiness checks have already passed (`coordinator.py:166-198`). Its payload records `record_id`
and `chgr_record_ids` (the full family-to-record-id map for that publication's four companion
artifacts). This is a second, independently-written artifact, produced by a different code path
than the one that writes `records/<record_id>.json` itself — exactly the "trace the root trust
anchor to an existing PCAE canonical state transition" requirement (item 33).

For the Binding side, no equivalent pre-existing artifact exists (RAE-001's Binding record type
is new as of Phase 149L, per §3/§9 of this phase's own governing prompt: "if legitimate CHGR
creation has no independently trusted external marker, determine the narrowest additive
mechanism"). This phase adds one: the **canonical creation registration**
(`<evidence_root>/creation-registry/<evidence_id>.json`), written by `create_rollback_approval_binding`
alone, via the identical exclusive-create technique, immediately after (and only after) the
Binding file itself is durably written.

## 4. CHGR Impact Analysis (Item 7 classification)

**Classification: A — RAE-local.** The Publication Coordinator's idempotency-marker mechanism
already existed, already established real creation provenance, and was simply never consulted by
`_resolve_decision_ref`. This is not a CHGR-level defect: CHGR-001 v1.0's own contract text makes
no promise that every consumer of a Decision Template extension point (§6) independently
cross-checks publication-marker provenance — that is a consuming module's own responsibility. No
CHGR-001 amendment, no CHGR schema change, and no change to
`src/pcae/governance/publication/**` was required or performed. `git diff --stat <pre-149N>..HEAD`
confirms the only production file touched is `src/pcae/core/rollback_approval_evidence.py`.

No historical CHGR record is invalidated by this change for any *other* CHGR consumer: the new
`_chgr_record_has_publication_receipt` predicate is called only from within
`rollback_approval_evidence.py`, gating only `resolve_rollback_approval_evidence`'s
`approval_present` derivation — it is not wired into CHGR's own lifecycle code, so no other CHGR
Decision Template's evidence semantics are affected (item 6/70/71 of the governing prompt: "if
CHGR itself cannot distinguish..." does not apply here, since CHGR already could, via its own
existing idempotency marker — RAE simply had not consumed it).

## 5. Decision Canonicality Repair

New predicate `_chgr_record_has_publication_receipt(record_id, *, publication_root)`
(`rollback_approval_evidence.py`): scans `published/*.json` under the publication root and returns
`True` iff some marker's `record_id` field, or some value in its `chgr_record_ids` map, equals the
CHGR record_id being resolved. `False` (never an exception) if the `published/` directory is
absent or no marker matches.

This check is called from **`resolve_rollback_approval_evidence`** only, immediately after
`_resolve_decision_ref` succeeds — deliberately *not* folded into `_resolve_decision_ref` itself,
which remains shared, unchanged in its four original checks, by both creation-time
(`create_rollback_approval_binding`) and resolution-time callers. Creation-time permissiveness
(a Binding MAY still be *created* referencing a Decision that will later fail the resolution-time
receipt check) is not itself a security boundary — RAE-REQ-018/RAE-REQ-038's `approval_present`
gate is, and that gate is `resolve_rollback_approval_evidence` alone (RAE-REQ-034). Layering the
check at the resolution call site only also preserves 149M's own independent adversarial suite's
exact test structure (§9 below).

## 6. Binding Canonicality Repair — Creation Registration

New store methods on `RollbackApprovalEvidenceStore`:

- `write_creation_registration(binding)` — writes
  `<evidence_root>/creation-registry/<evidence_id>.json` via `O_CREAT | O_EXCL`, containing
  `evidence_id`, `binding_content_digest`, `governance_record_reference`, `rollback_site`, and
  `rollback_operation_reference` — all derived from the Binding object itself at the moment of
  creation, never caller-suppliable.
- `read_creation_registration(evidence_id)` — returns the parsed registration or `None`.
- `remove_binding(evidence_id)` — rollback helper (§8 below).

New predicate `_binding_is_canonically_created(binding, store, *, lookup_key=None)`: `True` only
if a registration exists for `lookup_key` (the store's filename-based key — **not**
`binding.evidence_id`, see §7), and that registration's `evidence_id`, `binding_content_digest`,
`governance_record_reference`, `rollback_site`, and `rollback_operation_reference` all exactly
match the Binding's own current, already-digest-verified content.

`create_rollback_approval_binding` now calls `store.write_creation_registration(binding)`
immediately after `store.write_binding(binding)` succeeds. `resolve_rollback_approval_evidence`
calls `_binding_is_canonically_created(binding, store, lookup_key=evidence_id)` immediately after
its pre-existing `content_digest` self-consistency check and before any other RAE-REQ-038
condition is evaluated — no other condition (operation match, TTL, revocation, supersession) is
ever reached for a non-canonically-created Binding.

This closes **F1**: a hand-authored Binding, however well-formed and however genuine its
referenced Decision, has no registration entry (test:
`test_149n_b1_hand_authored_binding_rejected`).

## 7. Copied-Record Defense (F4a)

The critical design point: `binding.evidence_id` is the payload's own *internal*, self-declared
field, digest-covered but not filename-bound. A verbatim byte-copy of a legitimate Binding placed
under a new filename is still digest-self-consistent (the digest covers the unchanged internal
`evidence_id`), so checking the registration under `binding.evidence_id` would have looked up the
*original* record's registration and passed. The fix keys the canonicality check by `lookup_key`
— the actual filename/store-key used to retrieve the Binding — and additionally requires
`registration.get("evidence_id") == lookup_key` **and** `binding.evidence_id == lookup_key`. A
copy under a new filename fails both: no registration exists for the new filename at all, and
even if one were forged/copied alongside it, the registration's internal `evidence_id` (old) would
disagree with the new filename. `RollbackApprovalEvidenceStore.list_bindings_with_keys()` was
added so `_is_superseded`'s directory scan can apply the identical `lookup_key`-based check to
every candidate it considers, not only to the entry point's own explicitly-requested `evidence_id`.

Closes **F4a** (test: `test_149n_b3_copied_binding_new_id_rejected`, plus a same-ID
content-replacement regression control, `test_149n_b3_same_id_content_replacement_rejected`).

## 8. Modified-Record Defense

Unchanged from Phase 149L and independently re-confirmed: `resolve_rollback_approval_evidence`'s
pre-existing `content_digest` recomputation-and-compare step (RAE-REQ-055) already rejects any
post-persistence field tampering of an already-canonically-created record. This phase adds no new
digest mechanism for this case — the pre-existing one already worked correctly (149M §18-20
confirmed CONFORMS here); 149N's own regression suite re-confirms it is undisturbed
(`test_149n_b3_same_id_content_replacement_rejected`).

## 9. Forged-Later-Record (Supersession) Defense

`_is_superseded` previously compared `created_at` across *every* Binding sharing an operation
reference, with no canonicality filter. It now calls
`_binding_is_canonically_created(other, store, lookup_key=other_key)` (using the
`list_bindings_with_keys()` pair, not the payload's own `evidence_id`) and skips any candidate
that fails — **before** comparing `created_at` at all, matching item 23's required ordering
("filter candidates to canonical... before considering `created_at`"). A hand-authored Binding
with a forged, later `created_at` is therefore never even considered as a supersession candidate,
regardless of its timestamp.

Closes **F4b** (test: `test_149n_b4_noncanonical_newer_binding_cannot_supersede`). A companion
positive control (`test_149n_b4_positive_control_legitimate_later_binding_still_supersedes`)
confirms two genuinely, API-created Bindings for the same operation reference still supersede
correctly.

`created_at` itself remains non-caller-suppliable at the creation API boundary
(`create_rollback_approval_binding` computes it from `_now_utc()` internally; no parameter
accepts a caller-supplied value) — unchanged from 149L, independently re-confirmed by signature
inspection, so a legitimate caller cannot manufacture a future-dated canonical Binding either.

## 10. Denial / Revocation Non-Interference (Item 46)

A forged (hand-authored, noncanonical) `deny_rollback` Binding for the same operation reference
fails the identical canonicality gate as any other noncanonical record and is excluded from
consideration entirely — not merely from supersession — so it cannot invalidate a legitimate,
canonical `approve_rollback` Binding for that operation. Confirmed by
`test_149n_forged_deny_binding_cannot_invalidate_canonical_approval`. Revocation itself is
untouched by this phase (still append-only, `store.is_revoked()`, checked unconditionally); a
forged revocation record was not separately modeled as a distinct artifact type in RAE-001 v1.0's
frozen shape (§8's `revocation_metadata` is a Binding-file field, not a separate directory), so no
new noncanonical-revocation vector exists beyond the general Binding-canonicality gate already
closing F1/F4a/F4b.

## 11. Directory-Injection / Atomicity Hardening (Items 34-38, 51)

Two additional, narrowly-scoped hardenings surfaced while writing adversarial controls for the
four primary findings:

- **Directory injection (item 51):** `list_bindings_with_keys()` previously propagated any
  exception raised while parsing a malformed file in `bindings/` (e.g. invalid JSON) out of
  `list_bindings()`/`_is_superseded()`, which — via `resolve_rollback_approval_evidence`'s own
  fail-closed umbrella — turned an *unrelated* legitimate resolution into `INVALID` merely because
  an unrelated garbage file existed nearby. Malformed files are now skipped (never treated as
  canonical evidence either way; skipping does not weaken any check, since a skipped file was
  never going to pass the canonicality gate regardless). Confirmed:
  `test_149n_directory_injection_extra_file_ignored`.
- **Atomicity (items 34-38):** `create_rollback_approval_binding` now rolls back (removes) the
  just-written Binding file if `write_creation_registration` fails for any reason, so a Binding
  file can never exist on disk without a matching registration — no orphan-trusted state.
  Confirmed: `test_149n_atomic_creation_failure_leaves_no_orphan_binding` (registration write
  monkeypatched to raise; asserts zero Binding files remain).

## 12. Compatibility / Migration Decision (Items 39-40, 94-95)

RAE evidence was introduced only in Phase 149L and has zero AG3/AG5 production consumers (§67,
independently re-confirmed below) — no historical evidence exists outside this repository's own
test fixtures. Per the governing prompt's own default ("given no production consumer exists,
invalidation is likely safer"): **pre-149N-created evidence that lacks a canonical creation
registration is NOT trusted, unconditionally, with no migration path.** No 149L or 149M test
fixture required modification — every one of 149L's 77 self-tests and 149M's 49-passing (pre-149N)
tests already constructed evidence exclusively through the real `create_rollback_approval_decision`/
`create_rollback_approval_binding` APIs, which now transparently produce registrations as part of
normal operation; all 77+49 continue to pass unmodified post-hardening (§14).

## 13. F-149M-5 Repair (Non-Blocking)

The module's docstring (lines 23 and 33 pre-149N) contained the literal substrings
`pcae.cltr.authority.*` and `pcae.cltr.authority.authorization_candidate`, tripping three
naive-string-scan TAM/CLTR regression guards
(`test_136z_no_production_module_string_references_authority_import`,
`test_no_production_module_imports_authority_package`,
`test_136av_no_production_runtime_module_imports_authority_package`) despite zero actual imports
existing (AST-confirmed by 149M itself). Reworded both occurrences to describe the CLTR Typed
Authority Model's authority package by name without the exact dotted-path substring — no code
change, no semantic change to what the module does or does not import, and the TAM/CLTR wall
guard tests themselves were **not** weakened or modified. Confirmed: the same three tests, run
unmodified, now pass (§14).

## 14. Regression Results (all under `python3.14`, matching prior phases' interpreter)

| Suite | Result |
|---|---|
| `pytest tests/test_phase_149m_...py -q` (149M's own suite, unmodified) | **53 passed** (was 49 passed, 4 failed) |
| `pytest tests/test_rollback_approval_evidence_*.py -q` (149L self-tests, unmodified) | **77 passed** (unchanged) |
| `pytest tests/test_phase_149n_...py -q` (new 149N suite) | **11 passed** |
| `pytest -k '149j' -q` | **49 passed** (unchanged) |
| `pytest -k chgr -n auto -q` | **228 passed, 2 failed** (both pre-existing packaging/build-environment failures, identical to 149L/149M baseline) |
| `pytest -k 'tam or cltr' -n auto -q` | **5675 passed, 58 failed** (58 pre-existing; the 3 F5 failures are gone — baseline was 5672/61) |
| `pytest -k 'iwc or interactive_workflow' -n auto -q` | **693 passed** (unchanged) |
| `pytest -k 'aesic or authority_evaluation' -n auto -q` | **431 passed** (unchanged) |
| `pytest -k 'permission_broker or pol_004 or pol_001 or pol_005' -n auto -q` | **981 passed** (unchanged) |
| `pytest -k rollback -n auto -q` | **476 passed, 0 failed** (149M's own 4 deliberately-failing adversarial tests now pass) |
| `pytest -k 'wave_1 or wave1' -n auto -q` | **34 passed** (unchanged) |
| `pytest -m fast_green -n auto -q` | **4391 passed** (exact match to entering baseline) |
| Three F5 guard tests, individually | **3 passed** (were 3 failed) |

`pcae runtime inspect` before and after: **Observed / observe / unavailable**, identical.

## 15. Production / Contract Diff Audit

```
git diff --stat <pre-149N>..HEAD
 src/pcae/core/rollback_approval_evidence.py | 258 ++++++++++++++++++++++++++--
 1 file changed, 247 insertions(+), 11 deletions(-)

git diff --name-only <pre-149N>..HEAD -- docs/contracts/     -> empty
git diff --name-only <pre-149N>..HEAD -- src/pcae/core/agent.py \
  src/pcae/commands/agent.py                                 -> empty
git diff --name-only <pre-149N>..HEAD -- src/pcae/core/mutation_permission.py -> empty
git diff --name-only <pre-149N>..HEAD -- src/pcae/core/permission_broker_foundation.py \
  src/pcae/core/permission_broker.py                         -> empty
```

Every production hunk in `rollback_approval_evidence.py` classifies as: `CHGR_PROVENANCE`
(`_chgr_record_has_publication_receipt` and its call site), `BINDING_CANONICALITY`
(`_registration_to_dict`, `write_creation_registration`, `read_creation_registration`,
`_binding_is_canonically_created` and its call sites), `CREATION_REGISTRATION`
(`create_rollback_approval_binding`'s new registration write + rollback), `SUPERSESSION`
(`_is_superseded`'s canonicality filter, `list_bindings_with_keys`), `FAIL_CLOSED`
(directory-injection skip in `list_bindings_with_keys`), or `TEST_GUARD_REPAIR` (the two docstring
rewords). No `UNRELATED` hunk exists.

## 16. Blocking Closure Matrix

| Finding | Pre-149N reproduction | Repair | Post-149N adversarial result | Closed? |
|---|---|---|---|---|
| B-149M-1 (hand-authored Binding) | Reproduced: `resolve` returned `VALID`/`True` | Canonical creation registration, checked at resolution time | `resolve` returns `INVALID`/`False` | **CLOSED** |
| B-149M-2 (hand-authored CHGR record) | Reproduced: `resolve` returned `VALID`/`True` | Publication-marker receipt cross-check | `resolve` returns `INVALID`/`False` | **CLOSED** |
| B-149M-3 (copied Binding, new evidence_id) | Reproduced: `resolve` returned `VALID`/`True` under new filename | Registration keyed by filename, cross-checked against internal `evidence_id` | `resolve` returns `INVALID`/`False` under new filename; original unaffected | **CLOSED** |
| B-149M-4 (forged newer Binding supersedes) | Reproduced: legitimate Binding resolved `SUPERSEDED` | Supersession candidates filtered to canonically-created records before `created_at` comparison | Legitimate Binding resolves `VALID`; forged Binding itself resolves `INVALID` | **CLOSED** |

All four BLOCKING findings independently reproduced via 149M's own unmodified adversarial suite
both before (49 passed/4 failed) and after (53 passed/0 failed) this phase's changes.

## 17. Root-Cause Closure

The shared root cause — **canonicality implemented as digest self-consistency plus reference-field
agreement** — is structurally removed for both CHGR-Decision provenance (now additionally requires
an independently-written Publication Coordinator idempotency-marker receipt) and Binding
provenance (now additionally requires an independently-written, filename-keyed creation
registration). Neither new check derives trust from the artifact's own declared content alone,
from its storage path alone, or from a caller-suppliable trust boolean (item 65: no new public
function accepts a `canonical=True`/`trusted=True`/`provenance_valid=True` parameter — confirmed
by signature inspection of every function added or modified in this phase).

## 18. Provenance Invariant (Final Statement)

> A Rollback Approval Decision is eligible for RAE validation only if PCAE can independently
> verify, via `PublicationRecordStore`'s own idempotency-marker receipt, that its exact
> `record_id` was produced by a completed `PublicationCoordinator.execute` call. A Rollback
> Approval Binding is eligible only if PCAE can independently verify, via its own dedicated
> creation registration keyed by the exact filename/`evidence_id` used to look it up, that its
> exact identity and content digest were produced by `create_rollback_approval_binding`. Neither
> fact is derivable from the artifact's own declared content, its storage path, or a caller-
> supplied trust boolean.

## 19. Hardening Verdict

```
CANONICAL-PROVENANCE HARDENING COMPLETE
— ALL 149M BLOCKING FINDINGS CLOSED
```

## 20. Integration Readiness

```
RAE EVIDENCE SUBSTRATE: READY FOR INDEPENDENT RE-VERIFICATION
```

Not yet: `READY FOR AG3/AG5 INTEGRATION` — that classification is reserved for a future,
independent verification phase per this report's own recommended next phase.

## 21. No-Go Confirmations

RAE-001 v1.0 remains unchanged. RWMPC-001 v1.0 remains unchanged. PBPC-001 v1.2 remains unchanged.
PBPA-001 v1.0 remains unchanged. CHGR-001 remains unchanged. No AG3 Permission Broker integration
was implemented. No AG5 Permission Broker integration was implemented. No rollback execution
behavior was changed. No production rollback request consumes `approval_present=True`
(`grep -rn "derive_rollback_approval_present\|resolve_rollback_approval_evidence" src/pcae/`
matches only inside `rollback_approval_evidence.py` itself). No self-declared legacy flag was
promoted to trusted approval. IWC remains confirmation-only. AESIC/AEM remain disclosure-only. No
illegal CHGR/TAM authority-family composition was introduced (import boundary re-confirmed clean;
AST scan, zero matches). No POL-001..012 meaning was changed. No POL-013+ was added. TK1/TK2/TK3
remain deferred. No Runtime Enforcement behavior was changed. No Prompt Generation, Prompt
Dispatch, or agent invocation capability was implemented. Runtime remains Observed, maximum
capability remains observe, and execution availability remains unavailable.

## 22. Recommended Next Phase

```
149O — Rollback Approval Evidence Canonical-Provenance Hardening Independent Verification
```

149O should independently reconstruct and attack all four closed findings without relying on
149N's own test suite (`tests/test_phase_149n_rollback_approval_evidence_canonical_provenance_hardening.py`)
or importing its fixtures — mirroring 149M's own independent-construction discipline against
149L. It should additionally probe: compound canonicality-plus-lifecycle states not exhaustively
attacked here (revoked-then-noncanonical-supersession-attempt, TTL-expired-but-canonical
candidates in the supersession scan), symlink/path-replacement against the new
`creation-registry/` directory, and whether the new registration mechanism itself introduces any
new forgery surface (e.g., can an attacker who can write files pre-create a registration for a
not-yet-issued `evidence_id` to make a *later* hand-authored Binding at that same filename appear
canonical — the exclusive-create ordering in `create_rollback_approval_binding` writes the Binding
file first, then the registration, so a pre-planted registration alone, with no matching Binding
file yet, resolves `MISSING`; only if the attacker can *also* win the Binding write is there any
risk, at which point they could have written a legitimate-shaped Binding directly, which is
exactly the pre-149L threat model this repository already discloses as unsolved,
STRATEGIC_GAP RAE-REQ-009). Do not proceed directly to rollback integration planning; only after
149O verifies clean should a dedicated "149P — Rollback Permission Integration Plan" be chartered.
