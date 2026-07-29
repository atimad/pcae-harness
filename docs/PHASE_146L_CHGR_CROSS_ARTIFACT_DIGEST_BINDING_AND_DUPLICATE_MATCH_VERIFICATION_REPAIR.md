# Phase 146L: CHGR Cross-Artifact Digest-Binding and Duplicate-Match Verification Repair

## 1. Executive Summary

Repaired both Blocking defects Phase 146J established and Phase 146K's
CHGR-001 v1.3 Sec.30 contract clarification (CHGR-REQ-210 through
CHGR-REQ-216) authorized this phase to fix: `governance/verification.py`'s
related-artifact resolver (`_find_related`) matched on `record_type` +
`record_id` only, first-match, order-dependent, with no digest-reference
enforcement. Replaced it with a role-aware resolver (`_resolve_related`)
that identifies every supplied candidate sharing the referenced identity
(`record_id`), fails closed on zero-or-many matches, enforces family
identity, and -- for the confirmation and provenance roles only --
enforces exact `record_digest` equality against the Human Governance
Record's own reference (CHGR-REQ-212). The directed one-way integrity
binding CHGR-REQ-211 already implemented (`integrity.payload_digest ==
human_governance_record.record_digest`) is preserved verbatim and is now
explicitly never compared against `integrity_ref.record_digest`, matching
the frozen Model C contract. Three new stable error codes
(`RELATED_ARTIFACT_AMBIGUOUS`, `RELATED_ARTIFACT_FAMILY_MISMATCH`,
`REFERENCE_DIGEST_MISMATCH`) distinguish these outcomes from the existing
nine.

Both Sec.2 defects were independently reconfirmed live against the current
repository state before any code change, and independently re-verified
fixed after the repair, via both the internal `verify_artifact_at_path`
API and the real `pcae governance-record verify` CLI subprocess: (A)
duplicate-match ambiguity, previously order-dependent (`verified` one
order, `CONFIRMATION_UNBOUND` the other), now rejects
`RELATED_ARTIFACT_AMBIGUOUS` in both orders; (B) cross-bundle sibling
substitution, previously accepted despite
`supplied_sibling.record_digest != target_reference.record_digest`, now
rejects `REFERENCE_DIGEST_MISMATCH`.

Three pre-existing test fixtures (`valid_record_published.json`,
`valid_integrity.json`, `adversarial_assurance_overclaim_selfconsistent.json`)
encoded the old, unenforced reference-digest shape and were migrated to
carry a real matching digest, mirroring the 146H.3 precedent. Six 146H.3
unit tests that isolated a specific downstream semantic check by
mutate-then-resign a sibling (without re-pointing the record's own
reference) now correctly hit the new, earlier `REFERENCE_DIGEST_MISMATCH`
gate first; updated via a new `_rereferenced` test helper that re-points
the reference alongside the resign, restoring each test's original
isolation intent. 45 new tests
(`tests/test_phase_146l_chgr_cross_artifact_digest_binding_and_duplicate_match_verification_repair.py`)
cover the full adversarial matrix. 169 combined targeted CHGR/publication
regression passed, fast_green 4391/4391 passed (identical baseline), broad
sweep results in Sec.14.

**Verdict: REPAIR COMPLETE.**

## 2. Authorization and Scope

Human Authorization (verbatim, this phase's prompt): implement the
verifier-only repair required by CHGR-REQ-212 and CHGR-REQ-213 while
preserving the already-implemented directed integrity relationship
required by CHGR-REQ-211, per Phase 146K's frozen CHGR-001 v1.3 Sec.30
Model C (Directed One-Way Integrity Binding).

Authorized production file: `src/pcae/governance/verification.py`.
Authorized-with-necessity: tests (new module plus updates to
`tests/test_chgr_verification.py`, `tests/test_phase_146h3_confirmation_binding_verification_repair.py`,
and `tests/fixtures/chgr/**` -- all changes are digest/error-code value
corrections or new-behavior test additions, never a semantic-check
removal or weakening). No change to CHGR-001, CHGR schemas, the schema
manifest, publication construction (`governance/publication/record.py`
untouched), the Publication Coordinator, persistence, Interactive
Workflow, lifecycle sequencing, or authority ownership. No-Go boundary
confirmed clean in Sec.16.

## 3. Independent Defect Reconfirmation

Reconfirmed against the current repository state, before any production
code change, using two genuine `build_publication_record` bundles (A, B)
differing in every confirmation/provenance-bearing field
(`preview_digest`, `confirmation_statement`, identity `identifier`,
`decision_subject`) so no cross-bundle comparison is a coincidental
digest match.

### 3.A Duplicate-match ambiguity

Constructed a genuine confirmation sibling and a second, self-consistent
artifact sharing the same `record_id` but with a deliberately wrong
`confirmed_content_digest` (would independently fail `CONFIRMATION_UNBOUND`
if resolved alone). Supplied both, in both argument orders, to
`verify_artifact_at_path`.

```
order1 (genuine, forged): outcome=verified
order2 (forged, genuine): outcome=rejected, error_code=CONFIRMATION_UNBOUND
```

Order-dependent result confirmed: the old `_find_related` returned
`related_records[0]` matching `record_type` + `record_id`, silently
ignoring the second candidate.

### 3.B Digest-reference bypass

Took bundle B's confirmation sibling, retargeted its `record_id` to
bundle A's `confirmation_evidence_ref.record_id`, and recomputed its own
`record_digest` (content otherwise unchanged -- a different confirmer,
different `preview_digest`, different statement than bundle A's genuine
sibling). Supplied it as bundle A's confirmation sibling via both the
internal API and the real CLI.

```
target_ref.record_digest:     3c5c...d3bc6
forged sibling record_digest: 456e...3ddda6  (differs)

API:  outcome=verified, confirmation_binding=passed
CLI:  exit_code=0, "outcome: verified"
```

Bypass confirmed: `supplied_sibling.record_digest != target_reference.record_digest`
was never checked; the old resolver matched on `record_type` +
`record_id` only.

## 4. Contract Mapping

| Contract element (CHGR-001 v1.3 Sec.30) | Requirement | Implementation |
|---|---|---|
| Confirmation evidence reference | `record_family`/`record_id`/`record_digest` exact match | `_resolve_related(..., enforce_reference_digest=True)` for `confirmation_evidence_ref` |
| Provenance reference | Same | `_resolve_related(..., enforce_reference_digest=True)` for `provenance_ref` |
| Integrity reference | Identity-only; `integrity.payload_digest == human_governance_record.record_digest`; `integrity_ref.record_digest` never compared to the integrity artifact's own digest | `_resolve_related(..., enforce_reference_digest=False)` for `integrity_ref`; unchanged `payload_digest == declared_digest` check retained below it |
| Duplicate related artifacts | Fail closed on any role with >1 candidate satisfying the referenced identity, including byte-identical duplicates | `_resolve_related` returns `"ambiguous"` whenever `len(identity_candidates) > 1`, before any content/validity comparison |
| CHGR-REQ-215 (legacy compatibility) | Existing Chapter 146 bundles must not require regeneration | `enforce_reference_digest=False` for integrity role; Sec.13 and Sec.12-F reprove a genuine bundle's real (mismatching) provisional `integrity_ref.record_digest` shape still verifies |

## 5. Related-Artifact Resolution Repair

Replaced the `_find_related` closure with `_resolve_related`
(`src/pcae/governance/verification.py`, nested inside
`verify_artifact_at_path`, same scoping discipline as before -- captures
`related_records`, `registry`, `manifest` by closure, no new module-level
mutable state):

```python
def _resolve_related(expected_family, ref, *, enforce_reference_digest):
    ref_id = ref.get("record_id")
    identity_candidates = [c for c in related_records if c.get("record_id") == ref_id]
    if not identity_candidates:
        return None, "not_supplied"
    if len(identity_candidates) > 1:
        return None, "ambiguous"
    candidate = identity_candidates[0]
    if candidate.get("record_type") != expected_family:
        return None, "family_mismatch"
    ok, _ = _shape_check(candidate, registry=registry, manifest=manifest)
    if not ok or _record_digest_of(candidate) != candidate.get("record_digest"):
        return None, "malformed"
    if enforce_reference_digest and candidate.get("record_digest") != ref.get("record_digest"):
        return None, "digest_mismatch"
    return candidate, "matched"
```

Resolution order, deliberately: (1) identify every candidate sharing the
referenced `record_id` -- this is the "referenced identity" CHGR-REQ-213
speaks of, matched independent of family so a family-mismatched
same-`record_id` candidate is diagnosable rather than silently treated as
absent; (2) reject on zero or >1 candidates *before* validating any of
them, so ambiguity is never resolved by picking whichever candidate
happens to validate; (3) for the single surviving candidate, enforce
family, then self-consistency (schema shape + self-digest), then (where
applicable) the exact reference-digest match. This ordering is what makes
byte-identical duplicates fail closed too (Sec.9): two identical files
still produce `len(identity_candidates) == 2`, rejected before either is
inspected. `related_records` is a plain Python list built by iterating
`related_bytes` in caller-supplied order (unchanged), but resolution
never indexes into it positionally or returns early on first match, so
the result is independent of that order (proven in Sec.12 by the
`test_*_reordered_input_remains_identical` cases, which assert
byte-identical `to_dict()` output across both orders).

## 6. Confirmation Reference Enforcement

`confirmation_evidence_ref` resolution now calls
`_resolve_related("human_confirmation_evidence", ref, enforce_reference_digest=True)`.
Every non-`"matched"`/`"not_supplied"` status returns immediately with a
distinct `_fail(...)` (Sec.9 codes), *before* the pre-existing semantic
checks (`confirmed_content_digest == preview_rendering_digest`, assurance
truthfulness) run -- exact reference matching is a gate ahead of, not a
replacement for, semantic verification, per the phase's own Sec.5
requirement. All originally-implemented semantic checks are byte-for-byte
unchanged; only the code path that resolves `confirmation` before
reaching them changed.

## 7. Provenance Reference Enforcement

Identical structure and identical enforcement discipline for
`provenance_ref` (`_resolve_related("governance_record_provenance", ref,
enforce_reference_digest=True)`), ahead of the pre-existing
`selected_option_id` agreement check and the provenance/confirmation
preview-digest cross-check.

## 8. Directed Integrity Binding Enforcement

`integrity_ref` resolution calls `_resolve_related("governance_record_integrity",
ref, enforce_reference_digest=False)` -- the one and only call site that
passes `False`, verified directly by a dedicated regression test
(`test_integrity_final_self_digest_equality_is_not_enforced`, Sec.12-C)
that inspects the live source rather than only exercising fixtures, so a
future accidental flip to `True` fails immediately and explicitly rather
than only showing up as a mysteriously-rejected genuine bundle. Family
identity and duplicate-match are still enforced identically to the other
two roles. The pre-existing `integrity.get("payload_digest") !=
declared_digest` check (comparing against the Human Governance Record's
own already-verified `record_digest`, the actual CHGR-REQ-211 binding) is
untouched.

## 9. Duplicate-Match Fail-Closed Behavior

Implemented once, uniformly, inside `_resolve_related`'s identity-match
step (Sec.5), applied identically to all three roles (confirmation,
provenance, integrity). Covers every case CHGR-REQ-213 and the phase's
Sec.8 enumerate: byte-identical duplicate files
(`test_*_duplicate_exact_match_fails`), two distinct same-`record_id`
different-digest files (`test_*_duplicate_same_id_different_digest_fails`),
duplicates across roles simultaneously
(`test_bundle_duplicate_siblings_of_multiple_roles_all_fail_ambiguous`).
No deduplication by path, object identity, or content equality occurs
anywhere in the new code -- `identity_candidates` is built by a plain list
comprehension over every supplied related artifact with no `set`/`dict`
collapsing step. Result independence from argument order, filesystem
enumeration order, and process restart follows directly from `_resolve_related`
containing no ordering-sensitive operation (no early return inside the
candidate-scan loop, no reliance on dict insertion order); the parser
(`_parse`) that builds `related_records` from `related_bytes` also
preserves input order without deduplicating, so this holds transitively
from `verify_artifact_at_path`'s public argument order down to the
resolver.

## 10. Error Semantics

Three new stable codes added to `_ERROR_CODES` (frozenset, now 12
members): `RELATED_ARTIFACT_AMBIGUOUS` (zero-or-fewer distinguishable from
too-many was already impossible to express with the original nine -- the
closest, `DIGEST_MISMATCH`, means "content was altered," a different
defect from "which of several candidates should never have been chosen at
all"), `RELATED_ARTIFACT_FAMILY_MISMATCH` (a unique `record_id` match
belonging to the wrong record family), `REFERENCE_DIGEST_MISMATCH` (a
unique, family-correct, self-consistent candidate whose own
`record_digest` does not equal what the record's reference cites --
distinct from `DIGEST_MISMATCH`'s "this artifact was tampered with after
its own digest was computed," since a `REFERENCE_DIGEST_MISMATCH`
candidate is perfectly self-consistent, just not the artifact this record
actually cites). `DIGEST_MISMATCH` is retained, unextended in meaning, for
self-inconsistency/tampering and for the integrity role's
`payload_digest` binding (which is not a reference-identity check). No
existing error code's meaning was widened or repurposed. `_fail()`'s
existing `error_code not in _ERROR_CODES` guard (unchanged) means any
typo in a new call site would raise `VerificationError` immediately at
test time, not silently misclassify. JSON output remains deterministic
(`VerificationFailure.to_dict()`/`VerificationObservation.to_dict()`
unchanged); no raw candidate artifact content is included in any new
failure message, only field-name-level descriptions.

## 11. Legacy Compatibility

CHGR-REQ-215 implemented by construction, not by a special-cased
exemption: `enforce_reference_digest=False` for the integrity role means
every already-produced Chapter 146 bundle's provisional
`integrity_ref.record_digest` (Phase 146F Sec.3.3's forward-reference-cycle
resolution, unchanged in `record.py` this phase) continues to verify
without regeneration. Regression proof:
`test_integrity_genuine_provisional_reference_digest_bundle_passes` and
`test_live_existing_directed_integrity_relationship_passes` (Sec.12)
construct a real `build_publication_record` bundle, assert its
`integrity_ref.record_digest` genuinely differs from
`governance_record_integrity.record_digest` (proving the fixture
exercises the real provisional shape, not a coincidentally-matching one),
and assert it still verifies. `test_legacy_genuine_chapter_146_bundle_still_verifies`
repeats this with a second, independently-parameterized bundle (B) as a
stand-in for the broader population of already-produced bundles.

## 12. Adversarial Test Matrix

45 new tests in
`tests/test_phase_146l_chgr_cross_artifact_digest_binding_and_duplicate_match_verification_repair.py`,
organized into six sections:

- **A. Confirmation evidence** (10 tests): exact match passes; ID-match/digest-mismatch fails (`REFERENCE_DIGEST_MISMATCH`); digest-coincidence/ID-mismatch never resolves as bound (reports `skipped`, documented in Sec.13); family mismatch fails; duplicate exact match fails; duplicate same-ID different-digest fails (both orders); cross-bundle forged artifact fails; reordered input identical; malformed artifact fails; self-digest-invalid artifact fails.
- **B. Provenance** (8 tests): the same matrix, minus the two skip/malformed-duplication cases already proven structurally identical in Sec.A.
- **C. Integrity** (9 tests): exact match passes; wrong ID treated as absent (not a false match); wrong family fails; wrong `payload_digest` fails; duplicate exact identity fails; cross-bundle sibling fails (via the real `payload_digest` binding, not reference-digest, per Sec.8); reordered input identical; genuine provisional-reference-digest bundle passes; **and a direct source-inspection test proving `enforce_reference_digest=False` is the code the integrity call site actually runs**, not merely a fixture-level absence of failure.
- **D. Bundle-level** (10 tests): each of missing confirmation/provenance/integrity sibling reports `skipped` without failing the overall check; extra unrelated (distinct-ID) siblings from another bundle are harmlessly ignored; duplicate siblings across multiple roles simultaneously fail ambiguous; one sibling belonging to another bundle among otherwise-genuine siblings still fails; primary-record and sibling tampering (pre-existing protections) still rejected; CLI/API outcome agreement.
- **E. Live production-bundle verification** (8 tests): mirrors the phase's Sec.13 checklist exactly -- genuine bundle A via API and via a real CLI *subprocess* (not `main()` called in-process, an actual `pcae` executable invocation, distinct from the CLI calls in sections A-D which use the in-process `main()` for speed); bundle A with bundle B's confirmation/provenance/integrity; record-ID-rewrite-plus-resign bypass re-proof; duplicate-match order-reversal re-proof; existing directed integrity relationship re-proof.
- **F. Legacy compatibility** (1 test): a second genuine bundle, standing in for the existing-bundle population CHGR-REQ-215 protects.

## 13. Live Production-Bundle Results

Two genuine bundles (A, B) built via `build_publication_record` from
independent `PublicationReadinessPackage`s (different `preview_digest`,
`confirmation_statement`, identity `identifier`, `decision_subject` --
never a coincidental digest match), verified through the real `pcae`
executable as a subprocess:

```
1. genuine bundle A passes through API   -> verified, all 7 applicable checks passed
2. genuine bundle A passes through CLI   -> exit 0, "outcome: verified"
3. bundle A + bundle B confirmation      -> exit 1, REFERENCE_DIGEST_MISMATCH
4. bundle A + bundle B provenance        -> exit 1, REFERENCE_DIGEST_MISMATCH
5. bundle A + bundle B integrity         -> exit 1, DIGEST_MISMATCH (payload_digest binds to bundle B's HGR, not A's)
6. record-ID rewrite + self-digest recompute no longer bypasses -> exit 1, REFERENCE_DIGEST_MISMATCH
7. duplicate-match order reversal        -> both orders: exit 1, RELATED_ARTIFACT_AMBIGUOUS
8. existing directed integrity relationship -> exit 0, "outcome: verified"
```

Scenario 5's code differs from 3/4's (`DIGEST_MISMATCH` vs.
`REFERENCE_DIGEST_MISMATCH`) precisely because the integrity role does not
enforce reference-digest equality (Sec.8) -- the forged bundle-B integrity
artifact is *resolved* successfully (unique ID match, correct family,
self-consistent), then rejected by the pre-existing `payload_digest`
binding check because it still binds to bundle B's Human Governance
Record digest, not bundle A's. This is the correct, contract-mandated
outcome, not an inconsistency.

## 14. Regression Assessment

Targeted CHGR/publication/phase suite (as enumerated in the phase's
Sec.14, plus the new 146L module):

```
python -m pytest tests/test_chgr_verification.py tests/test_chgr_authority_boundary.py \
  tests/test_chgr_phase_separation.py tests/test_chgr_schema_family.py \
  tests/test_phase_146g_chgr_schema_envelope_implementation.py \
  tests/test_phase_146h1_governance_verification_schema_version_repair.py \
  tests/test_phase_146h3_confirmation_binding_verification_repair.py \
  tests/test_phase_146l_chgr_cross_artifact_digest_binding_and_duplicate_match_verification_repair.py
-> 169 passed
```

Also independently ran the remaining CHGR-adjacent suites not explicitly
named in Sec.14 but sharing the migrated fixtures
(`tests/test_chgr_143f_independent_verification.py`,
`tests/test_chgr_inspection.py`) -- 102 passed, confirming the fixture
digest corrections (Sec.11 below) had no collateral effect there.

`fast_green` tier: `python -m pytest -m fast_green -n auto -q` ->
**4391/4391 passed**, identical count to the 146K baseline.

Broad sweep: `python -m pytest -k "chgr or publication or governance or
verification" -n auto -q` -> **9 failed, 4039 passed, 4 skipped**. All 9
failures are wheel/sdist packaging-build tests
(`test_cltr_authority_136ah_publication.py`,
`test_cltr_authority_136ai_publication_independent.py`,
`test_cltr_cutover_136u_notification_marker_receipt_binding_independent_verification.py`,
`test_cltr_cutover_136k_authority_core_independent_verification.py`,
`test_chgr_packaging.py`) -- none touch `governance/verification.py`,
the related-artifact resolution logic, or any migrated fixture.
Independently reconfirmed pre-existing via an isolated `git stash push -u`
baseline (this phase's changes fully removed, working tree returned to
146K's committed state) re-run of the identical command: **9 failed, 3994
passed, 4 skipped** -- the exact same 9 test IDs fail, with a smaller
`passed` count only because 45 fewer tests exist (146L's own new module)
when stashed. Stash popped and restored cleanly (`git status`
post-restore matches pre-stash); targeted 146L/146H.3/143E suites
re-verified passing after restore (86/86).

## 15. Findings

None Blocking. None Non-Blocking identified beyond the one disclosed,
deliberate limitation below (Informational, explicitly authorized by the
phase's own Sec.10).

**Informational:** `verify_artifact_at_path`'s pre-existing "no related
artifact supplied at all for this role" -> `skipped` (never a failure)
semantics is retained unchanged, per the phase's explicit Sec.10
instruction not to redesign optional verification modes. This means a
caller who supplies *zero* related artifacts still gets an overall
`"verified"` outcome for a Human Governance Record whose siblings were
simply never presented -- indistinguishable, at the `verify_artifact_at_path`
API level, from a caller who omitted a sibling by attempted evasion. This
phase's actual security fix is orthogonal and unaffected: it closes the
gap where a *supplied* related artifact could satisfy a reference without
being the genuine referenced artifact (ambiguity, wrong family, wrong
digest) -- that bypass is fully closed (Sec.13). Whether "verify a
complete bundle" callers (e.g. a future strict-mode CLI flag) should
require all three sibling roles to resolve `"matched"` is a policy
decision for a future phase, not a verifier-implementation defect this
phase's authorization covers.

## 16. No-Go Confirmation

- CHGR-001: unmodified (`git diff` confirms no `docs/CHGR-001*` change).
- CHGR schemas / schema manifest: unmodified (`src/pcae/schema_resources/chgr/**` untouched except test fixture data files under `tests/fixtures/chgr/`, which are not schemas).
- Publication construction / Publication Coordinator: `src/pcae/governance/publication/record.py` and coordinator files unmodified.
- Artifact fields / schema versions: unchanged.
- Fixture migration: exactly three pre-existing fixtures had a `record_digest` value corrected to match the sibling they claim to reference (a value the schema always shape-checked but the verifier never content-checked before this phase) -- directly required because CHGR-REQ-212 makes that check load-bearing for the first time; no field added, removed, or renamed.
- Artifact identity / persistence / lifecycle sequencing / authority ownership: unchanged.
- Execution capability / policy / strategic lineage: unchanged.
- Independent verification of this repair: not begun (recommended as 146LV, Sec.18).

## 17. Overall Verdict

**REPAIR COMPLETE.**

Live proof obtained this phase: genuine production bundles still verify
(Sec.13 scenarios 1, 2, 8; Sec.12 sections E/F); confirmation and
provenance sibling digest impersonation is rejected (Sec.13 scenarios 3,
4, 6); duplicate related artifacts fail closed (Sec.13 scenario 7; Sec.12
section D); argument order cannot change the outcome (Sec.5, Sec.9,
Sec.12's `reordered_input_remains_identical` tests); directed integrity
binding remains valid (Sec.8, Sec.13 scenarios 5, 8); existing
verification protections remain intact (Sec.14 regression: 169 targeted +
102 adjacent + fast_green 4391/4391, no code paths for schema validity,
lifecycle legality, assurance truthfulness, or the pre-existing
integrity/provenance semantic checks were touched).

## 18. Recommended Next Phase

**146LV -- CHGR Cross-Artifact Digest-Binding and Duplicate-Match
Verification Repair Independent Verification.** Independent
re-derivation from CHGR-001 v1.3 directly, and independent testing of:
exact confirmation reference enforcement, exact provenance reference
enforcement, directed integrity binding, duplicate-match rejection,
argument-order determinism, cross-bundle substitution resistance, and
compatibility with genuine existing Chapter 146 bundles. This
recommendation is not authorization.

## Appendix: Bootstrap and Governance Validation

`pcae session bootstrap --agent-id claude-code`, `pcae check`, `pcae
health`, `pcae doctor task-memory`, `pcae runtime inspect`, `pcae push
check` all run at phase start (clean repository, `main` branch,
`origin/main..HEAD` = 0, `HEAD..origin/main` = 0, runtime
Observed/observe/unavailable) and re-run at phase end before promotion
(Sec.19 of the phase authorization).
